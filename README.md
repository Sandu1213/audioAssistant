# 视频音量突增检测 Web 应用

一个 Flask Web 应用，用于自动检测视频中音量突然增加的时间段，并提供这些片段的音频和视频下载。上传视频后，程序会：

1. 提取音频并分析音量变化
2. 检测出音量突增的时间段
3. 生成并提供这些片段的音频和视频下载（单个下载或打包下载）
4. 支持自定义导出片段最小长度（默认5秒）

## 前置需求

### 1. 安装 FFmpeg

FFmpeg 用于视频音频处理，必须先安装。Windows 下有两种安装方法：

方法一：使用 Chocolatey（推荐，需要先安装 [Chocolatey](https://chocolatey.org/install)）

```powershell
choco install ffmpeg
```

方法二：手动下载安装

1. 访问 [FFmpeg 官网](https://ffmpeg.org/download.html)
2. 下载 Windows 版本（选择 "Windows builds from gyan.dev"）
3. 解压下载的文件
4. 将解压后的 `bin` 目录添加到系统 PATH

验证安装：在 PowerShell 中运行

```powershell
ffmpeg -version
```

如果显示版本信息，说明安装成功。

### 2. 安装 Python 依赖

在项目目录下执行（Windows PowerShell）：
```powershell
# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

## 运行应用

### 方式一：直接运行

```powershell
# 在虚拟环境中运行
python app.py
```

### 方式二：使用 Docker（推荐）

构建并启动服务：

```bash
docker-compose up -d
```

停止服务：

```bash
docker-compose down
```

容器会自动创建 `uploads` 和 `outputs` 目录并与主机共享，文件会保存在这些目录中。

## 使用方法

1. 访问 `http://localhost:5000/audio-detect/`
2. 选择要分析的视频文件
3. 设置导出片段的最小长度（默认5秒）
4. 点击"上传并分析"
5. 等待处理完成后，可以：
   - 预览和下载单个音频/视频片段
   - 下载所有片段的压缩包
   - 查看每个片段的开始和结束时间
# 确保在虚拟环境中
.\.venv\Scripts\Activate.ps1

# 启动 Flask 服务
python app.py
```

打开浏览器访问：[http://127.0.0.1:5000/audio-detect/](http://127.0.0.1:5000/audio-detect/)

## 使用说明

1. 在首页选择并上传视频文件（支持常见格式如 MP4、MOV、AVI 等）
2. 等待处理完成（处理时间与视频长度成正比）
3. 在结果页面可以：
   - 查看检测到的音量突增时间段
   - 试听各个片段（使用内嵌播放器）
   - 下载单个音频片段
   - 打包下载所有片段（ZIP）

## 技术说明

- 使用短时 RMS（均方根）计算音量包络
- 通过局部中位数作为基线，检测相对突增（避免全局阈值的缺陷）
- 所有音频片段导出为 16-bit PCM WAV 格式
