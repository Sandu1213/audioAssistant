# 音频突变检测助手 (Audio Jump Detection Assistant)

一个基于 Flask 的专业 Web 应用程序，用于检测视频或音频中的突变片段（如敲击声、爆破音等）。本应用采用智能算法自动分析上传的媒体文件，精确识别突变区间，并生成相应的音频和视频片段。

## 主要特性

1. 智能音频分析
   - 自动提取并分析音频特征
   - 使用自适应阈值检测突变片段
   - 支持自定义检测灵敏度

2. 视频处理能力
   - 自动提取对应视频片段
   - 保持原始视频质量
   - 支持多种视频格式

3. 便捷的用户界面
   - 简单的拖放上传
   - 实时处理进度显示
   - 在线预览和批量下载

4. 系统优化
   - 自动文件管理（保留最近5个任务）
   - 支持 Docker 部署
   - 生产级别的性能优化

## 快速开始

### 开发环境配置

1. 安装 FFmpeg

FFmpeg 是必需的音视频处理工具。Windows 用户可以选择以下安装方式：

方法一：使用 Chocolatey（推荐）

```powershell
# 需要先安装 Chocolatey (https://chocolatey.org/install)
choco install ffmpeg
```

方法二：手动安装

1. 访问 [FFmpeg 官网](https://ffmpeg.org/download.html)
2. 下载 Windows 版本
3. 解压并将 `bin` 目录添加到系统 PATH

验证安装：

```powershell
ffmpeg -version
```

2. 安装 Python 依赖

```powershell
# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

3. 创建必要的目录

```powershell
mkdir uploads outputs
```

## 部署运行

### 方式一：本地开发环境

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 启动开发服务器
python app.py
```

服务将在 [http://localhost:5000](http://localhost:5000) 运行

### 方式二：Docker 部署（推荐）

基于 Docker 的部署更加稳定可靠，并使用了 Gunicorn 作为生产级 WSGI 服务器。

1. 启动服务

   ```bash
   docker-compose up -d
   ```

1. 查看日志

   ```bash
   docker-compose logs -f
   ```

1. 停止服务

   ```bash
   docker-compose down
   ```

服务将在 [http://localhost:8000](http://localhost:8000) 运行

## 使用指南

1. 上传文件
   - 访问首页上传视频文件
   - 支持常见格式如 MP4、MOV、AVI 等
   - 可设置导出片段的最小长度（默认5秒）

2. 等待处理
   - 系统会自动分析音频特征
   - 处理时间与视频长度成正比
   - 界面会显示处理进度

3. 查看结果
   - 浏览检测到的突变片段列表
   - 使用内嵌播放器预览片段
   - 下载音频或视频文件
   - 支持批量下载所有片段

## 技术细节

### 核心算法

分析过程使用滑动窗口和局部中值比较方法：

1. 提取音频并计算 RMS 能量
2. 使用局部中值作为参考基线
3. 检测能量突变点（超过中值特定倍数）
4. 合并连续突变点形成区间
5. 提取符合时长要求的片段

主要参数：

- `thresh_ratio`: 突变检测阈值比率（默认2.0）
- `min_duration_s`: 最小突变持续时间（默认0.2秒）

### 系统特性

- 自动文件管理：保留最近5个任务的文件
- 并发处理：使用 Gunicorn 多工作进程
- 容器化部署：提供 Docker 支持
- 跨平台兼容：支持主流操作系统

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。提交代码时请确保：

1. 代码符合 PEP 8 规范
2. 添加必要的注释和文档
3. 更新相关的测试用例

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

