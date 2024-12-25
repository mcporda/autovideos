# 音频文件自动剪辑程序

## 项目目标
开发一个自动处理音频文件的程序,用于剪除音频中符合以下条件的片段:
- 音量低于-20dB
- 持续时间超过0.5秒
的静音/空白段落。

## 安装说明

1. 克隆项目并进入项目目录
```bash
git clone [项目地址]
cd [项目目录]
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 安装ffmpeg
- Mac OS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`
- Windows: 下载ffmpeg并添加到系统环境变量

## 使用说明

### 命令行参数
```bash
python src/main.py -i <输入路径> -o <输出路径> [-t <分贝阈值>] [-d <静音长度>]
```

参数说明：
- `-i, --input`: 输入音频文件或目录路径（必需）
- `-o, --output`: 输出音频文件或目录路径（必需）
- `-t, --threshold`: 静音判断的分贝阈值，默认-20dB
- `-d, --duration`: 最小静音长度(毫秒)，默认500ms

### 使用示例

1. 处理单个文件：
```bash
python src/main.py -i input.mp3 -o output.mp3
```

2. 处理整个目录：
```bash
python src/main.py -i input_dir -o output_dir
```

3. 自定义参数：
```bash
python src/main.py -i input.mp3 -o output.mp3 -t -25 -d 1000
```

## 技术方案

### 核心功能模块
1. 输入模块
   - 支持常见音频格式(wav, mp3, etc.)的读取
   - 支持批量处理多个文件
   - 文件格式验证

2. 音频分析模块
   - 计算音频的音量曲线
   - 检测低于-20dB的片段
   - 计算静音片段的持续时间
   - 标记符合条件的待剪切片段

3. 处理模块
   - 根据标记信息进行音频剪切
   - 无缝拼接保留片段
   - 保持音频质量

4. 输出模块
   - 保存处理后的音频文件
   - 生成处理报告(可选)

### 技术选型
- 开发语言: Python
- 音频处理库: pydub/librosa
- 性能优化: 流式处理,避免一次性加载大文件

### 可配置参数
- 音量阈值(默认-20dB)
- 持续时间阈值(默认0.5秒)
- 输入/输出音频格式
- 处理文件的并发数

### 注意事项
1. 内存管理
   - 采用分块处理方式
   - 及时释放不需要的资源

2. 错误处理
   - 输入文件格式检查
   - 处理过程异常捕获
   - 详细的错误提示

3. 用户体验
   - 处理进度显示
   - 处理结果统计
   - 日志记录

## 后续优化方向
1. 图形界面开发
2. 处理参数可视化调节
3. 音频波形预览
4. 批处理队列管理
5. 自定义处理规则
