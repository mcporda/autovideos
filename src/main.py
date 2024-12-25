#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
from audio_processor import AudioProcessor

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='音频文件静音片段剪辑工具')
    parser.add_argument('-i', '--input', required=True, help='输入音频文件或目录路径')
    parser.add_argument('-o', '--output', required=True, help='输出音频文件或目录路径')
    parser.add_argument('-t', '--threshold', type=float, default=-20,
                        help='静音判断的分贝阈值 (默认: -20dB)')
    parser.add_argument('-d', '--duration', type=int, default=500,
                        help='最小静音长度(毫秒) (默认: 500ms)')
    
    args = parser.parse_args()
    
    # 创建音频处理器实例
    processor = AudioProcessor(
        threshold_db=args.threshold,
        min_silence_len=args.duration
    )
    
    # 处理输入路径
    if os.path.isfile(args.input):
        # 处理单个文件
        processor.process_file(args.input, args.output)
    elif os.path.isdir(args.input):
        # 处理整个目录
        processor.process_directory(args.input, args.output)
    else:
        print(f"错误: 输入路径不存在: {args.input}")
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main()) 