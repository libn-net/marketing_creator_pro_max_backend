import subprocess
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
from typing import Union  # 添加这个导入
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UltralightService:
    """Ultralight数字人服务类,用于训练和生成数字人视频。"""

    def __init__(self):
        """初始化UltralightService"""
        load_dotenv()
        project_root = Path(os.getenv("PROJECT_ROOT"))
        self.base_path = project_root / 'external_modules' / 'ultralight'
        self.conda_env = os.getenv("ULTRALIGHT_CONDA_ENV", "dh")  # 从环境变量读取，默认值为 "ultralight"
        logger.info("UltralightService初始化完成，基础路径: %s，Conda环境: %s", self.base_path, self.conda_env)


    def run_command(self, command):
        """在指定的Conda环境中运行命令。"""
        full_command = f"conda run -n {self.conda_env} {command}"
        logger.info("运行命令: %s", full_command)
        subprocess.run(full_command, shell=True, check=True, cwd=str(self.base_path))

    def train(self, video_path: str, avatar_dir: str, asr_type: str = "hubert", use_syncnet: bool = True):
        """
        训练数字人模型。

        参数:
            video_path: 训练视频路径
            avatar_dir: 数字人目录路径
            asr_type: 音频特征提取器类型,可选"hubert"或"wenet"b不是不用
            use_syncnet: 是否使用syncnet预训练

        返回:
            tuple: (best_checkpoint_path, avatar_dir) - 最佳模型文件路径和数据目录路径
        """
        # 创建数字人专属目录
        logger.info("开始训练，视频路径: %s，数字人目录: %s，ASR类型: %s，使用Syncnet: %s", video_path, avatar_dir, asr_type, use_syncnet)
 
        syncnet_dir = avatar_dir / 'syncnet_ckpt'
        checkpoint_dir = avatar_dir / 'checkpoint'

        for dir_path in [syncnet_dir, checkpoint_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info("目录已创建: %s", dir_path)

        # 预处理数据
        # 根据asr类型设置不同的帧率
        fps = "20" if asr_type == "wenet" else "25"
        self.run_command(f"ffmpeg -i {video_path} -r {fps} -y {video_path}_tmp.mp4")
        subprocess.run(f"conda run -n {self.conda_env} python process.py {video_path}_tmp.mp4 --asr {asr_type}", shell=True, check=True, cwd=str(self.base_path / 'data_utils'))
        os.remove(f"{video_path}_tmp.mp4")
        logger.info("临时视频文件已删除: %s_tmp.mp4", video_path)

        # 2. 训练syncnet(如果启用)
        if use_syncnet:
            syncnet_cmd = (f"python syncnet.py "
                          f"--save_dir {syncnet_dir} "
                          f"--dataset_dir {avatar_dir} "
                          f"--asr {asr_type}")
            
            self.run_command(syncnet_cmd)
            logger.info("Syncnet训练完成")

            # 使用get_best_checkpoint方法获取最佳checkpoint
            best_syncnet_checkpoint = self.get_best_checkpoint(syncnet_dir)
            logger.info("最佳Syncnet检查点: %s", best_syncnet_checkpoint)

            # 3. 训练数字人模型(使用syncnet)
            train_cmd = (f"python train.py "
                        f"--dataset_dir {avatar_dir} "
                        f"--save_dir {checkpoint_dir} "
                        f"--asr {asr_type} "
                        f"--use_syncnet "
                        f"--syncnet_checkpoint {best_syncnet_checkpoint}")
            
        else:
            # 3. 训练数字人模型(不使用syncnet)
            train_cmd = (f"python train.py "
                        f"--dataset_dir {avatar_dir} "
                        f"--save_dir {checkpoint_dir} "
                        f"--asr {asr_type}")
            
        self.run_command(train_cmd)
        logger.info("训练完成")

        # 获取最佳checkpoint路径
        best_checkpoint_path = self.get_best_checkpoint(checkpoint_dir)
        logger.info("最佳检查点: %s", best_checkpoint_path)

        # 只返回checkpoint路径，不返回avatar_dir
        return best_checkpoint_path

    def get_best_checkpoint(self, checkpoint_dir: Path) -> Path:
        """
        获取checkpoint目录中最后一个checkpoint文件作为最佳模型。

        参数:
            checkpoint_dir: 存放checkpoint的目录路径

        返回:
            Path: 最佳checkpoint的路径
        """
        # 获取所有pth文件

        logger.info("在目录中查找最佳检查点: %s", checkpoint_dir)
        pth_files = list(checkpoint_dir.glob("*.pth"))
        
        # 提取文件名中的数字并转为整数
        epochs = []
        for f in pth_files:
            try:
                epoch = int(f.stem)  # 去掉.pth后缀,转为整数
                epochs.append((epoch, f))
            except ValueError:
                continue
                
        if not epochs:
            raise ValueError(f"在{checkpoint_dir}中未找到有效的checkpoint文件")
            
        # 按epoch数字排序,取最大的
        best_epoch, best_checkpoint = max(epochs, key=lambda x: x[0])

        # 将最佳checkpoint重命名为best.pth
        best_path = checkpoint_dir / "best.pth"
        best_checkpoint.rename(best_path)
        logger.info("最佳检查点重命名为: %s", best_path)

        return best_path

    def generate_video(self, audio_path: str, avatar_dir: str, checkpoint_path: str, 
                      output_path: Union[str, Path], asr_type: str = "hubert"):
        """
        生成数字人视频。

        参数:
            audio_path: 音频文件路径
            avatar_dir: 数字人目录路径
            checkpoint_path: 训练好的模型路径
            output_path: 指定输出视频的路径（字符串或Path对象）
            asr_type: 音频特征提取器类型
        
        返回:
            Path: 生成的视频文件路径
        """
        logger.info("生成视频，音频路径: %s，数字人目录: %s，检查点路径: %s，输出路径: %s，ASR类型: %s", audio_path,
                    avatar_dir, checkpoint_path, output_path, asr_type)

        # 将所有路径转换为Path对象，然后使用as_posix()确保跨平台兼容
        audio_path = Path(audio_path).as_posix()
        avatar_dir = Path(avatar_dir).as_posix()
        checkpoint_path = Path(checkpoint_path).as_posix()
        output_path = Path(output_path)
        
        # 确保输出目录存在
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("确保输出目录存在: %s", output_dir)

        # 临时文件在输出目录中
        temp_output = output_dir / f"temp_{uuid.uuid4()}.mp4"
        temp_output_str = temp_output.as_posix()
        output_path_str = output_path.as_posix()

        # 1. 提取音频特征
        if asr_type == "hubert":
            logger.info("使用hubert提取音频特征")
            feature_cmd = f"python data_utils/hubert.py --wav {audio_path}"
            feat_path = str(Path(audio_path).parent / f"{Path(audio_path).stem}_hu.npy")
        else:
            logger.info("使用hubert提取音频特征")
            feature_cmd = f"python data_utils/wenet_infer.py {audio_path}"
            feat_path = str(Path(audio_path).parent / f"{Path(audio_path).stem}_wenet.npy")
                
        logger.info("生成人物：提取音频：执行命令:: %s", feature_cmd)
        self.run_command(feature_cmd)
        logger.info("音频特征提取完成，保存路径: %s", feat_path)

        # 2. 生成视频
        generate_cmd = (f"python inference.py "
                       f"--asr {asr_type} "
                       f"--dataset {avatar_dir} "
                       f"--audio_feat {feat_path} "
                       f"--save_path {temp_output_str} "
                       f"--checkpoint {checkpoint_path}")

        logger.info("生成人物：推理视频：执行命令: %s", generate_cmd)
        self.run_command(generate_cmd)
        logger.info("视频生成到临时文件: %s", temp_output_str)

        # 3. 合并音视频
        merge_cmd = f"ffmpeg -y -i {temp_output_str} -i {audio_path} -c:v libx264 -c:a aac {output_path_str}"
        subprocess.run(merge_cmd, shell=True, check=True)
        logger.info("音视频合并完成，输出路径: %s", output_path_str)

        
        # 4. 删除临时文件
        if temp_output.exists():
            temp_output.unlink()
            logger.info("临时文件已删除: %s", temp_output)

        
        return output_path

    def generate_video_by_human_id(self, audio_path: str, human_id: str, output_path: str, is_public: int) -> Path:
        """根据human_id生成视频

        参数:
            audio_path: 音频文件路径
            human_id: 数字人ID
            output_path: 输出视频路径
            is_public: 是否为公共数字人

        返回:
            Path: 生成的视频文件路径
        """
        load_dotenv()
        project_root = Path(os.getenv("PROJECT_ROOT"))
        if is_public:
            avatar_dir = project_root / 'data' / (Path('public') / 'avatar') / human_id
        else:
            avatar_dir = project_root / 'data' / 'avatar' / human_id
        checkpoint_path = avatar_dir / 'checkpoint' / 'best.pth'

        if not checkpoint_path.exists():
            logger.error("模型文件未找到: %s", checkpoint_path)
            raise FileNotFoundError(f"找不到模型文件: {checkpoint_path}")

        return self.generate_video(
            audio_path=audio_path,
            avatar_dir=str(avatar_dir),
            checkpoint_path=str(checkpoint_path),  # 确保转换为字符串
            output_path=output_path,
            asr_type='hubert'
        )