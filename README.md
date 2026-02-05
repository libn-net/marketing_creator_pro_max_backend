# 声明：该项目已合并到 open_tapnow_lovart
# https://github.com/libn-net/open_tapnow_lovart 后续所有更新在新项目完成
# 目前已实现云端和本地双支持的模式，更简洁，支持对外API
# 该项目不在维护

# 基友沟通，不要发广告哦（备注：数字人交流）
<img width="1054" height="1180" alt="Image" src="https://github.com/user-attachments/assets/6af3ddf5-7a5a-43bc-8f0f-30b16fc05e40" />

# Project | 项目
#### 高颜值AI数字人克隆、声音克隆、短视频生成、直播（待发布）、AI配音、AI字幕，包括Windows安装版，Web版，H5版，小程序版，副业必备。
AI digital human cloning with high appearance, voice cloning, short video generation, live streaming (to be released), AI dubbing, AI subtitles, including Windows installation version, Web version, H5 version, Mini Program version, perfect for side business. | 

#### 场景主要用于AI获客、AI私域成交（待发布）、AI超级销售（待发布），避免被割韭菜。
Scenarios mainly used for AI customer acquisition, AI private domain transactions (to be released), AI super sales (to be released), to avoid being scammed. 

#### 做这个事的初衷是35岁程序员失业，被洗脑花了花了一百多万自己建短视频直播运营团队，第一个月效果不好，换了一波人，都是行业顶尖的，3个月过去，投了100多万只回来了不到3万。发现市场上有数字人直播的，害怕再被割，和几个朋友一起开始了研发之路，回归本行。
The original intention of doing this was that a 35-year-old programmer became unemployed, was brainwashed and spent over one million yuan to build his own short video live streaming operations team. The first month's results were not good, changed a group of people who were top in the industry, after 3 months, invested over 1 million but got back less than 30,000. Found digital human live streaming in the market, afraid of being scammed again, started the development journey with several friends, returning to the original profession. | 

#### 有问题请再群里或是issue上提问，请避免"大爷式"提问，如：xxx怎么解决？，有没有人回复下xxx？
For questions, please ask in the group or raise an issue. Please avoid "boss-style" questions like: How to solve xxx? Can someone reply to xxx? | 

#### 退伍军人、失业人员、待业宝妈会优先解答，其他如果回复慢，也请不要责怪。
Veterans, unemployed people, and stay-at-home moms will be given priority in answers. If other responses are slow, please don't blame us. | 

#### Windows安装版、Web版-开源地址：
https://github.com/libn-net/marketing_creator_pro_max_pc
#### H5、小程序版-开源地址：
https://github.com/libn-net/marketing_creator_pro_max_uni
#### 后端API-开源地址：
https://github.com/libn-net/marketing_creator_pro_max_backend

#### 功能列表：
- 形象克隆
  - 上传
  - 训练
  - 列表
- 声音克隆
  - 录音
  - 上传
  - 训练
  - 列表
- 视频生成
  - 全局配置-导出格式
  - 全局配置-指定帧率
  - 全局配置-指定横版/竖版
  - 全局配置-指定分辨率
  - 文案生成-文案仿写（30%）
  - 文案生成-抖音链接仿写（30%）
  - 文案生成-自由仿写
  - 文案生成-文案拆解（30%）
  - 人物选择-私有AI数字人
  - 人物选择-公共AI数字人（50%）
  - 配音生成-私有克隆声音
  - 配音生成-公共克隆声音
  - 配音生成-语速调节
  - 配音生成-音量调节
  - 背景音乐-公共素材
  - 背景音乐-上传素材
  - 背景音乐-音量调节
  - 字幕生成-选择字体
  - 字幕生成-字体大小
  - 字幕生成-字体颜色
  - 贴纸动画-文字贴纸（50%）
  - 贴纸动画-图片贴纸（50%）
  - 贴纸动画-动效贴纸（50%）
- 短视频发布
  - 抖音
  - 快手
  - 视频号
  - 小红书
- AI数字人直播（20%）
  - 直播方案-主播选择
  - 直播方案-副播选择
  - 直播方案-实时文案
  - 直播方案-自动下播
  - 直播方案-自动上播
  - 直播方案-自动换播
  - 直播方案-大模型知识库
  - 直播方案-沟通记录
- AI优质图文（10%）
  - 随笔内容
  - 软营销内容
  - 专业报道
  - 长篇小说
  - 长篇漫画
- 图文内容发布（10%）
  - 公众号
  - 百家号
  - 今日头条
  - 搜狐号
  - ...等

<img src="./doc/pro_01.jpg" />
<img src="./doc/pro_02.jpg" />
<img src="./doc/pro_03.jpg" />
<img src="./doc/pro_04.jpg" />
<img src="./doc/pro_05.jpg" />
<img src="./doc/pro_06.jpg" />
<img src="./doc/pro_07.jpg" />
<img src="./doc/pro_08.jpg" />
<img src="./doc/pro_09.jpg" />
<img src="./doc/pro_10.jpg" />   


## 感谢开源项目：
- https://github.com/anliyuan/Ultralight-Digital-Human
- https://github.com/fishaudio/fish-speech
- https://github.com/Tzenthin/wenet_mnn
- https://github.com/FFmpeg/FFmpeg

## 感谢开源的贡献者：
- https://github.com/wxc1207
- https://github.com/libn-net
- https://github.com/songyanbin
- https://github.com/star4564
- https://github.com/WangWei974747584
- https://github.com/huminghr


## 1 环境配置
### 1.1 系统环境配置
1. 确保计算机使用的N卡，具有N卡驱动、cuda、cudnn环境

```
import torch
torch.cuda.is_available() # 输出true
```

1. ffmpeg 自行下载，配置到环境变量 

### 1.2 Python环境

#### 1.2.1 backend 环境

进入：**项目的根目录**

```bash
conda create -n backend python=3.9
conda activate backend
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```



#### 1.2.2 ultralight 模块

##### 安装环境

进入：**`项目的根目录\external_modules\ultralight下`**

```bash
conda create -n dh python=3.10
conda activate dh
conda install pytorch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 pytorch-cuda=11.7 -c pytorch -c nvidia
conda install mkl=2024.0
pip install -r requirements.txt
```

##### 测试模型

 数据准备

   ``` bash
cd data_utils
python process.py YOUR_VIDEO_PATH --asr hubert
   ```

   先训练一个syncnet，效果会更好。

   ``` bash
cd ..
python syncnet.py --save_dir ./syncnet_ckpt/ --dataset_dir ./data_dir/ --asr hubert
   ```

   然后找一个loss最低的checkpoint来训练数字人模型。

   ``` bash
cd ..
python train.py --dataset_dir ./data_dir/ --save_dir ./checkpoint/ --asr hubert --use_syncnet --syncnet_checkpoint syncnet_ckpt
   ```

   在推理之前，需要先提取测试音频的特征（之后会把这步和推理合并到一起去），运行

   ``` bash
   python data_utils/hubert.py --wav your_test_audio.wav  # when using hubert

   or

   python data_utils/python wenet_infer.py your_test_audio.wav  # when using wenet

   # 推理
   python inference.py --asr hubert --dataset ./your_data_dir/ --audio_feat your_test_audio_hu.npy --save_path xxx.mp4 --checkpoint your_trained_ckpt.pth

   # 合并音频和视频
   ffmpeg -i xxx.mp4 -i your_audio.wav -c:v libx264 -c:a aac result_test.mp4
   ```



#### 1.2.3 fish-speech 模块

##### 安装环境

进入：**项目的根目录\external_modules\fish-speech下**

```bash
conda create -n fish-speech python=3.10
conda activate fish-speech
mkdir -p checkpoints/fish-speech-1.4
huggingface-cli download fishaudio/fish-speech-1.4 --local-dir checkpoints/fish-speech-1.4
pip install torch torchvision torchaudio
pip install -e .
```

##### 测试模型

推理过程分为以下几个步骤：

a. VQGAN编码：

   ```
python tools/vqgan/inference.py \
    -i "paimon.wav" \
    --checkpoint-path "checkpoints/fish-speech-1.4/firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
   ```

   此步骤将生成一个`fake.npy`文件。

b. 语言模型生成：

   ```
python tools/llama/generate.py \
    --text "要转换的文本" \
    --prompt-text "你的参考文本" \
    --prompt-tokens "fake.npy" \
    --checkpoint-path "checkpoints/fish-speech-1.4" \
    --num-samples 2 \
    --compile
   ```

   此命令会在工作目录下创建`codes_N`文件，其中N是从0开始的整数。

c. VQGAN解码：

   ```
python tools/vqgan/inference.py \
    -i "codes_0.npy" \
    --checkpoint-path "checkpoints/fish-speech-1.4/firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
   ```

注意：请确保按顺序执行上述步骤，并在每个步骤之间检查生成的文件。



#### 1.2.4 wav2lip-onnx-256 模块（可选） 

##### 安装环境

进入：**`项目的根目录\external_modules/wav2lip-onnx-256`**

```bash
# 创建目录
mkdir -p checkpoints
# 下载wav2lip_256.onnx 和 wav2lip_256_fp16.onnx到checkpoints文件下
wget https://github.com/instant-high/wav2lip-onnx-256/releases/download/v1.0.0/wav2lip_256.onnx -O checkpoints/wav2lip_256.onnx
wget https://github.com/instant-high/wav2lip-onnx-256/releases/download/v1.0.0/wav2lip_256_fp16.onnx -O checkpoints/wav2lip_256_fp16.onnx
# 创建环境
conda create -n wav2lip_onnx python=3.8
conda activate wav2lip_onnx
pip install -r requirements.txt

```

##### 测试模型

python inference_onnxModel.py --checkpoint_path "checkpoints\wav2lip_256.onnx" --face "D:\some.mp4" --audio "D:\some.wav" --outfile "D:\output.mp4" --nosmooth  --pads 0 10 0 0 --fps 29.97

如果源有问题，请尝试
（-i https://pypi.tuna.tsinghua.edu.cn/simple/）



## 2 文件配置

### 2.1 .env配置文件

请在**项目根目录**创建 `.env` 文件，并添加以下配置：   

```
# 项目安装目录配置 更换为自己的项目路径，注意一定要单斜杠
PROJECT_ROOT=E:\your_path\marketing_creator_pro_max_backend

# 本机地址
LOCAL_HOST=http://127.0.0.1:8000

FISH_SPEECH_CONDA_ENV=fish-speech
ULTRALIGHT_CONDA_ENV=dh

# 阿里云OSS配置
OSS_ENDPOINT=your_oss_endpoint
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_SECRET_ACCESS_KEY=your_secret_access_key
OSS_BUCKET_NAME=your_bucket_name
```



## 3 下载必备的材料

参考网站百度网盘 [点击这里](https://pan.baidu.com/s/1t6W4rNdsDuHmfgHtS05fZw?pwd=nbig)

将网盘的`data/public`目录下的内容放入该项目`项目根目录/data/public`目录下(不存在则自行创建)



## 4 启动项目



1. 返回项目`根目录`，在`backend`环境中启动项目：
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   启动后：数据库会自行创建，并自动创建表结构（**backend_schema.sql的DML语句需要手动执行，即Insert语句**）
2. 访问API文档：
   在浏览器中打开 http://127.0.0.1:8000/docs

注意：请确保在运行主项目之前已经正确配置了fish-speech、ultralight模块。每次使用不同的模块时，需要切换到相应的Conda环境。




