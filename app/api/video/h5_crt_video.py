import shutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models.digital_human_avatar import DigitalHumanAvatar
from app.schemas.short_video_detail import ShortVideoDetailBase
from app.services.task_service import TaskService

from app.database import get_db
from app.models.short_video import ShortVideo
from app.services.ultralight_service import UltralightService
from app.utils.response_utils import success_response, error_response
from app.schemas.response import ApiResponse
from app.models.short_video_detail import ShortVideoDetail
from app.models.digital_human_voice import DigitalHumanVoice
from app.services.fishspeech_service import FishSpeechService
from pathlib import Path
import os
from app.services.transcription_service import TranscriptionService
from app.utils import media_utils, gpu_utils
import subprocess
import platform
import logging
from app.utils.user_utils import get_user_id

# 设置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=ApiResponse)
def create_video(mix_data: ShortVideoDetailBase, db: Session = Depends(get_db)):
    """
    创建口播视频
    """
    logger.info(f"开始创建口播视频，标题: {mix_data.video_title}")
    

    
    # 检查标题长度
    if len(mix_data.video_title) > 100:
        return error_response(code=400, message="视频标题长度不能超过100个字符")

    if mix_data.digital_human_avatars_type == 0:
        # 校验必填参数
        if not mix_data.digital_human_avatars_download_url:
            return error_response(code=400, message="数字人下载地址不能为空")
            
        if not mix_data.digital_human_avatars_human_id:
            return error_response(code=400, message="数字人human_id不能为空")
            
        if not mix_data.digital_human_avatars_no_green_cover_image_width:
            return error_response(code=400, message="数字人封面图宽度不能为空")
            
        if not mix_data.digital_human_avatars_no_green_cover_image_height:
            return error_response(code=400, message="数字人封面图高度不能为空")

    else:
        # 校验数字人ID是否存在且不为0
        if not mix_data.digital_human_avatars_id or mix_data.digital_human_avatars_id == 0:
            return error_response(code=400, message="数字人ID不能为空或0")

        # 检查数字人是否存在
        digital_human = db.query(DigitalHumanAvatar).filter(
            DigitalHumanAvatar.id == mix_data.digital_human_avatars_id,
            DigitalHumanAvatar.is_deleted == False
        ).first()

        if not digital_human:
            return error_response(code=400, message="指定的数字人不存在")
    
    try:
        logger.info(f"创建短视频详情记录")
        db_short_video_detail = ShortVideoDetail(**mix_data.model_dump())
        db_short_video_detail.user_id = get_user_id()
        db.add(db_short_video_detail)
        db.commit()
        db.refresh(db_short_video_detail) 

        """混剪视频"""
        task_service = TaskService.get_instance()
        task_id = f"crt_video_{db_short_video_detail.id}"  
        task_name = f"创建口播视频_{db_short_video_detail.video_title}"
        task_func = lambda: create_video_by_human(db_short_video_detail)
        task_service.execute_task_immediately(task_func=task_func, task_id=task_id, task_name=task_name)

        return success_response(message="已经开始创建口播视频")
    except Exception as e:
        logger.error(f"创建短视频记录失败: {str(e)}", exc_info=True)
        db.rollback()
        return error_response(code=500, message=f"创建短视频记录失败: {str(e)}")


def create_video_by_human(short_video_detail: ShortVideoDetail):
    """
    创建口播视频
    """
    logger.info(f"开始处理视频生成任务，视频ID: {short_video_detail.id}")
    
    # 全局变量
    script_content = short_video_detail.script_content
    target_width, target_height = media_utils.calculate_target_dimensions(short_video_detail.video_layout, short_video_detail.resolution)
    # 定义文件路径
    voice_id = f"{short_video_detail.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    data_root = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'video' / voice_id
    voice_path = data_root / 'voice.wav'
    digital_human_video_path = data_root / 'human.mp4' 
    music_path = data_root / 'music.wav'
    subtitle_path = data_root / 'subtitle.ass'
    download_material_dir = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'public' / 'material'
    download_avatar_dir = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'public' / 'avatar'
    download_voice_dir = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'public' / 'voice'
    # 用户自己上传的文件，暂不删除
    download_origin_dir = data_root / 'origin'
    # 公共数字人压缩包，需删除
    download_delete_dir = data_root / 'delete'

    # 创建必要的目录
    for path in [data_root, download_material_dir, download_avatar_dir, download_voice_dir, download_origin_dir]:
        path.mkdir(parents=True, exist_ok=True)

    # 在短视频表中新增一条初始记录
    db = next(get_db())
    new_short_video = ShortVideo(
        title=short_video_detail.video_title,
        type=0,
        status=0,
        short_videos_detail_id=short_video_detail.id,
        created_at=datetime.now(),
        user_id=short_video_detail.user_id
    )
    db.add(new_short_video)
    db.commit()
    db.refresh(new_short_video)
    
    try:
        logger.info("初始化短视频记录")

        voice_output_npy_path = data_root / 'tmp_voice.npy'
        temp_audio_prompt_wav_path = data_root / 'tmp_voice.wav'

        fish_speech_service = FishSpeechService()

        # 使用AI生成的声音
        voice = db.query(DigitalHumanVoice).filter(DigitalHumanVoice.id == short_video_detail.voice_id).first()
        if not voice:
            raise ValueError(f"未找到ID为{short_video_detail.voice_id}的声音")

        npy_prompt_text = voice.npy_prompt_text
        npy_path = voice.npy_path
        project_root = os.getenv("PROJECT_ROOT")
        local_host = os.getenv("LOCAL_HOST")
        if npy_path.startswith(local_host):
            npy_path = npy_path.replace(local_host, project_root)

        fish_speech_service.generate_speech(
            script_content,
            npy_prompt_text,
            npy_path,
            voice_output_npy_path,
            temp_audio_prompt_wav_path
        )
        media_utils.adjust_audio_volume_and_speed(temp_audio_prompt_wav_path, voice_path, volume=short_video_detail.voice_volume, speed=short_video_detail.voice_speed)
            
        
        # 2. 根据人物生成透明口播视频
        # 使用ultralight生成数字人视频
        ultralight_service = UltralightService()

        digital_human = db.query(DigitalHumanAvatar).filter(DigitalHumanAvatar.id == short_video_detail.digital_human_avatars_id).first()
        human_id = digital_human.human_id
        no_green_cover_image_height = digital_human.no_green_cover_image_height
        no_green_cover_image_width = digital_human.no_green_cover_image_width
        human_type = digital_human.type
        is_public = True
        if human_type == 1:
            is_public = False

        if not human_id or human_id == 'None':
            raise ValueError(f"未找到ID为{short_video_detail.digital_human_avatars_id}的数字人")

        digital_human_video_path = ultralight_service.generate_video_by_human_id(
            audio_path=voice_path,
            human_id=human_id,
            output_path=str(digital_human_video_path),
            is_public=is_public
        )
        logger.info(f"数字人对口型视频地址: {digital_human_video_path}")

        # 如果没有背景视频，创建一个纯黑色背景视频
        temp_bg_path = data_root / 'tmp_black_bg.mp4'
        command = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=c=black:s={target_width}x{target_height}:r={short_video_detail.video_frame_rate}',
            '-frames:v', '1',
            '-y',
            str(temp_bg_path)
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        background_video_path = str(temp_bg_path)

        x, y, scale,margin_x,margin_y = calculate_position_and_rate(no_green_cover_image_height,
                                                  no_green_cover_image_width,
                                                  short_video_detail.video_layout)

        # 构建ffmpeg命令
        output_path = data_root / 'merged_bg_human.mp4'

        # GPU相关配置
        use_gpu = gpu_utils.check_gpu_available()
        video_codec = 'h264_nvenc' if use_gpu else 'libx264'
        encoding_preset = 'p4' if use_gpu else 'faster'

        command = [
            'ffmpeg',
            '-i', str(background_video_path),
            '-i', str(digital_human_video_path),
            '-filter_complex',
            f'[0]fps={short_video_detail.video_frame_rate},scale={target_width}:{target_height}[bg];'
            f'[1]fps={short_video_detail.video_frame_rate}[fg];'
            f'[fg]scale=iw*{scale}:ih*{scale}[scaled];'
            f'[bg][scaled]overlay={x}:{y}:format=auto[v]',
            '-map', '[v]',
            '-map', '1:a',
            '-c:v', video_codec,
            '-preset', encoding_preset,
            *(['-rc', 'vbr', '-cq', '26'] if use_gpu else ['-crf', '26']),
            '-r', str(short_video_detail.video_frame_rate),
            '-y',
            str(output_path)
        ]

        subprocess.run(command, check=True, capture_output=True)
        background_video_path = output_path
        logger.info(f"更新背景视频路径为合并后的视频: {background_video_path}")

        # 4. 生成字幕
        merge_subtitle_audio_path = background_video_path
        if short_video_detail.subtitle_switch == 1:
            logger.info("处理字幕生成")
            merge_subtitle_audio_path = merge_subtitle(short_video_detail, background_video_path, subtitle_path, voice_path, target_width, target_height,margin_x,margin_y)
        
        # 6. 更新短视频记录状态为已完成
        new_short_video.status = 1  # 1表示已生成
        new_short_video.video_url = str(merge_subtitle_audio_path)
        first_frame_path = media_utils.extract_video_frame(merge_subtitle_audio_path)
        new_short_video.video_cover = str(first_frame_path)
        new_short_video.finished_at = datetime.now()
        db.merge(new_short_video)
        db.commit()
        # print(f"已为第 {i+1} 个视频创建短视频记录，ID: {new_short_video.id}")
    except Exception as e:
        logger.error(f"视频生成过程出错: {str(e)}", exc_info=True)
        # 更新短视频记录状态为生成失败
        new_short_video.status = 2  # 2表示生成失败需要重试
        new_short_video.status_msg = str(e)
        new_short_video.finished_at = datetime.now()
        db.merge(new_short_video)
        db.commit()
        
        # 记录详细的错误堆栈息
        import traceback
        error_trace = traceback.format_exc()
        print(f"错误堆栈信息:\n{error_trace}")
        raise
    finally:
        media_utils.delete_directory(download_delete_dir)

def merge_subtitle(short_video_detail, final_output_video_path, subtitle_path, voice_path, target_width, target_height,margin_x,margin_y):
    try:
        # 生成字幕文件（如果不存在）
        if not os.path.exists(subtitle_path):
            transcription_service = TranscriptionService()
            
            font_temp_path = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'public' / 'font' / '1731038051181_longzhuti.ttf'

            # 获取字幕位置
            # x, y, r = map(float, short_video_detail.font_position.split(','))
            resolution=(target_height, target_width)
            is_portrait = resolution[0] > resolution[1]

            # 设置 font_style 的 margin 值
            y = 156 
            r = 30 
            x = 30 
            if is_portrait:
                y = 296 
                r = 30 
                x = 30 
            

            
            # 配置ASS字幕样式
            font_style = {
                "font_name": short_video_detail.font_name,
                "font_file": str(font_temp_path),
                "font_size": short_video_detail.font_size,
                "margin_v": y,
                "margin_l": x,
                "margin_r": r,
                "alignment": 8,
                "outline": 0,
                "shadow": 0,
                "primary_color": "&H00FFFFFF",
                "outline_color": "&H00000000"
            }
            
            # 使用generate_ass_file生成ASS字幕
            transcription_service.generate_ass_file_h5(voice_path, str(subtitle_path), font_style, resolution=(target_height, target_width))
        
        output_file = Path(final_output_video_path).with_name(f"with_subtitle_{Path(final_output_video_path).name}")
        
        # 构建ffmpeg命令 - 简化为直接使用ASS字幕
        if platform.system() == "Windows":
            subtitle_path = str(subtitle_path).replace("\\", "\\\\").replace(":", "\\:")
        ffmpeg_cmd = ' '.join([
            'ffmpeg',
            '-i', str(final_output_video_path),
            '-vf', f"ass='{str(subtitle_path)}'",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_file)
        ])
        
        subprocess.run(ffmpeg_cmd, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"字幕合并命令执行成功，输出文件：{output_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"添加字幕时出错: {str(e)}")
        logger.error(f"FFmpeg命令: {' '.join(ffmpeg_cmd)}")
        # 记录详细的错误堆栈信息
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"错误堆栈信息:\n{error_trace}")
        raise


def calculate_position_and_rate(height, width, video_layout):
    """
    根据数字人的尺寸和视频布局计算x, y坐标和比例rate
    :param short_video_detail: 包含height, width, video_layout的对象
    :return: (x, y, rate)
    """
    h = height
    w = width
    margin_x = 0
    margin_y = 0

    # 计算rate
    if video_layout == 1:  # 横屏
        rate1 = w / 1920
        rate2 = h / 1080
        rate = max(rate1, rate2)

        if rate1 > rate2:
            x = 0
            y = (1080 - h / rate) / 2
            # h / rate 真实视频的宽
        else:
            x = (1920 - w / rate) / 2
            y = 0
        margin_x = (1920 - w / rate) / 2
        margin_y = (1080 - y - h/rate) + 24/(h/rate) * 1080
    elif video_layout == 2:  # 竖屏
        rate1 = w / 1080
        rate2 = h / 1920
        rate = max(rate1, rate2)

        if rate1 > rate2:
            x = 0
            y = (1920 - h / rate) / 2
        else:
            x = (1080 - w / rate) / 2
            y = 0
        margin_x = (1080 - w / rate) / 2
        margin_y = (1920 - y - h/rate) + 24/(h/rate) * 1920

    else:
        raise ValueError("无效的视频布局类型")
    print(f"::::x: {x}, y: {y}, rate: {rate},  h/rate: {h/rate}, w/rate: {w/rate}   ")

    print(f"::::margin_x: {margin_x}, margin_y: {margin_y}, rate: {1/rate}   ")
    """
    x，y 是视频的坐标
    rate 是视频的比例
    1/rate 是视频的缩放比例
    h/rate 是视频的高度
    w/rate 是视频的宽度
    """
    return x, y, 1/rate, margin_x, margin_y