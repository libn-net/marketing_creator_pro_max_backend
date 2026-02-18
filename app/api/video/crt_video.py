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
from app.services.fishspeech_service import FishSpeechService
from pathlib import Path
import os
from app.services.transcription_service import TranscriptionService
from app.utils import media_utils, gpu_utils
import subprocess
import platform
import logging
from app.utils.user_utils import get_user_id
import time

# 设置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=ApiResponse)
def create_video(mix_data: ShortVideoDetailBase, db: Session = Depends(get_db)):
    """
    创建口播视频
    """
    logger.info(f"开始创建口播视频，标题: {mix_data.video_title}")

    # 校验视频标题是否存在
    if not mix_data.video_title:
        return error_response(code=400, message="视频标题不能为空")

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
    # video_duration = short_video_detail.video_duration
    target_width = 1080
    target_height = 1920
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
    download_origin_dir =  data_root / 'origin'
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

        # 1. 如果开启真人录制，不使用AI生成声音，否则使用AI生成声音
        stage_start_time = time.time()
        if short_video_detail.voice_switch == 1:
            logger.info("处理真人录制语音")
            short_video_detail.voice_path = media_utils.handle_media_url(short_video_detail.voice_path, download_origin_dir)
            voice_path = voice_path.with_suffix(Path(short_video_detail.voice_path).suffix)
            shutil.copy2(short_video_detail.voice_path, voice_path)
        else:
            voice_output_npy_path = data_root / 'tmp_voice.npy'
            temp_audio_prompt_wav_path = data_root / 'tmp_voice.wav'
            voice_material_type = short_video_detail.voice_material_type
            voice_npy_prompt_text = short_video_detail.voice_npy_prompt_text
            voice_voice_id = short_video_detail.voice_voice_id

            fish_speech_service = FishSpeechService()

            # 公共的配音
            if not voice_voice_id:
                raise ValueError("远端voice_voice_id不能为空")
            voice_dir = download_voice_dir / voice_voice_id
            if not voice_dir.exists():
                media_utils.download_and_extract(short_video_detail.voice_download_url,  # 下载url
                                                 download_delete_dir,  # 下载本地目录
                                                 download_voice_dir)  # 解压目录
            npy_prompt_text = voice_npy_prompt_text
            npy_path = voice_dir / 'prompt' /'audio_prompt.npy'


            fish_speech_service.generate_speech(
                script_content,
                npy_prompt_text,
                npy_path,
                voice_output_npy_path,
                temp_audio_prompt_wav_path
            )
        media_utils.adjust_audio_volume_and_speed(temp_audio_prompt_wav_path, voice_path, volume=short_video_detail.voice_volume, speed=short_video_detail.voice_speed)
        logger.info(f"音频耗时: {time.time() - stage_start_time:.2f}秒")


        # 2. 根据人物生成透明口播视频
        # 使用ultralight生成数字人视频
        ultralight_service = UltralightService()
        # 公共数字人取传值human_id 否则获取 本地human_id
        digitalHumanAvatarObj = db.query(DigitalHumanAvatar).filter(DigitalHumanAvatar.id == short_video_detail.digital_human_avatars_id).first()
        human_id = digitalHumanAvatarObj.human_id
        human_type = digitalHumanAvatarObj.type
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


        # 根据digital_human_avatars_position和digital_human_avatars_scale合并背景视频和透明口播视频
        position = short_video_detail.digital_human_avatars_position.split(',')
        # 将字符串坐标转换为浮点数，然后转换为整数
        x, y = int(float(position[0])), int(float(position[1]))
        scale = short_video_detail.digital_human_avatars_scale

        # 构建ffmpeg命令
        output_path = data_root / 'merged_bg_human.mp4'

        # GPU相关配置
        use_gpu = gpu_utils.check_gpu_available()
        video_codec = 'h264_nvenc' if use_gpu else 'libx264'
        encoding_preset = 'p4' if use_gpu else 'faster'

        command = [
            'ffmpeg',
            '-i', str(adjust_background_video_duration(digital_human_video_path, background_video_path)),
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
        logger.info(f"执行ffmpeg命令: {' '.join(str(x) for x in command)}")
        subprocess.run(command, check=True, capture_output=True)
        background_video_path = output_path
        logger.info(f"更新背景视频路径为合并后的视频: {background_video_path}")
        logger.info(f"生成人物耗时:: {time.time() - stage_start_time:.2f}秒")

        # 4. 生成字幕
        stage_start_time = time.time()
        merge_subtitle_audio_path = background_video_path
        if short_video_detail.subtitle_switch == 1:
            logger.info("处理字幕生成")
            merge_subtitle_audio_path = merge_subtitle(short_video_detail, background_video_path, subtitle_path, voice_path, target_width, target_height)
            logger.info(f"合并字幕：耗时: {time.time() - stage_start_time:.2f}秒")

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


def merge_subtitle(short_video_detail, final_output_video_path, subtitle_path, voice_path, target_width, target_height):
    try:
        # 生成字幕文件（如果不存在）
        if not os.path.exists(subtitle_path):
            transcription_service = TranscriptionService()

            # 准备字体样式配置
            font_temp_dir = Path(os.getenv("PROJECT_ROOT")) / 'data' / 'public' / 'font'
            font_temp_dir.mkdir(parents=True, exist_ok=True)
            font_temp_path = font_temp_dir / Path(short_video_detail.font_path).name

            # 如果本地不存在字体文件则下载
            if not os.path.exists(font_temp_path):
                font_temp_path = media_utils.download_media(short_video_detail.font_path, str(font_temp_dir), keep_name=True)
                if not font_temp_path:
                    raise ValueError("下载字体文件失败")

            # 获取字幕位置
            x, y, r = map(float, short_video_detail.font_position.split(','))

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
                "primary_color": "&H" + short_video_detail.font_color,
                "outline_color": "&H00000000"
            }

            prompt_text = short_video_detail.script_content

            # 使用generate_ass_file生成ASS字幕
            transcription_service.generate_ass_file(voice_path, str(subtitle_path), font_style, resolution=(target_height, target_width), prompt_text=prompt_text)

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


def adjust_background_video_duration(digital_human_video_path, background_video_path):
    '''
        调节背景时长与数字人时长一致
        :param digital_human_video_path: 数字人路径
        :param background_video_path: 背景时长
    '''
    # 获取视频的时长
    background_duration = media_utils.get_video_duration(background_video_path)
    digital_human_duration = media_utils.get_video_duration(digital_human_video_path)

    if not isinstance(background_video_path, Path):
        background_video_path = Path(background_video_path)
    # 创建一个临时文件路径
    temp_adjusted_path = background_video_path.parent / (background_video_path.stem + ".duration.mp4")

    if background_duration > digital_human_duration:
        # 裁剪背景视频到数字人视频的时长
        command = [
            'ffmpeg',
            '-i', background_video_path,
            '-t', str(digital_human_duration),
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-y',
            temp_adjusted_path
        ]
    else:
        # 扩展背景视频到数字人视频的时长
        loop_count = int(digital_human_duration // background_duration) + 1
        command = [
            'ffmpeg',
            '-stream_loop', str(loop_count),
            '-i', background_video_path,
            '-t', str(digital_human_duration),
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-y',
            temp_adjusted_path
        ]

    subprocess.run(command, check=True)

    # 替换原始文件
    os.remove(background_video_path)
    shutil.move(temp_adjusted_path, background_video_path)

    return background_video_path
