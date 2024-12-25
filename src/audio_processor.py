#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from pydub import AudioSegment
from pydub.utils import db_to_float
from scipy import signal
from scipy.fft import fft
from tqdm import tqdm

class AudioProcessor:
    def __init__(self, threshold_db=-20, min_silence_len=500, crossfade_len=50):
        """
        初始化音频处理器
        :param threshold_db: 静音判断的分贝阈值，默认-20dB
        :param min_silence_len: 最小静音长度(毫秒)，默认500ms
        :param crossfade_len: 交叉渐变长度(毫秒)，默认50ms
        """
        self.threshold_db = threshold_db
        self.min_silence_len = min_silence_len
        self.crossfade_len = crossfade_len
        
    def load_audio(self, file_path):
        """
        加载音频文件
        :param file_path: 音频文件路径
        :return: AudioSegment对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
            
        return AudioSegment.from_file(file_path)
        
    def get_frequency_features(self, samples, sample_rate):
        """
        计算音频片段的频率特征
        :param samples: 音频样本数据
        :param sample_rate: 采样率
        :return: 是否可能包含人声的布尔值
        """
        # 计算频谱
        freqs = fft(samples)
        freqs_abs = np.abs(freqs)
        
        # 人声频率范围大约在85-255Hz
        freq_bins = np.fft.fftfreq(len(samples), 1/sample_rate)
        voice_range_mask = (freq_bins >= 85) & (freq_bins <= 255)
        
        # 计算人声范围内的能量占比
        voice_energy = np.sum(freqs_abs[voice_range_mask])
        total_energy = np.sum(freqs_abs)
        
        # 如果人声范围内的能量占比较大，则认为可能包含人声
        return (voice_energy / total_energy) > 0.1 if total_energy > 0 else False
        
    def smooth_rms_values(self, rms_values, window_size=5):
        """
        对RMS值进行平滑处理
        :param rms_values: RMS值列表
        :param window_size: 平滑窗口大小
        :return: 平滑后的RMS值列表
        """
        return signal.savgol_filter(rms_values, window_size, 2)
        
    def detect_silence(self, audio_segment):
        """
        检测音频中的静音片段
        :param audio_segment: AudioSegment对象
        :return: 静音片段列表，每个元素为(开始时间, 结束时间)
        """
        # 将音频转换为numpy数组进行分析
        samples = np.array(audio_segment.get_array_of_samples())
        
        # 计算音量曲线
        chunk_size = int(audio_segment.frame_rate * 0.1)  # 100ms chunks
        chunks = [samples[i:i + chunk_size] for i in range(0, len(samples), chunk_size)]
        
        # 计算每个chunk的RMS值
        rms_values = []
        for chunk in chunks:
            if len(chunk) > 0:
                rms = np.sqrt(np.mean(chunk.astype(float) ** 2))
                rms_values.append(rms)
                
        # 对RMS值进行平滑处理
        if len(rms_values) > 5:
            rms_values = self.smooth_rms_values(rms_values)
        
        # 转换为dB值并检测静音
        silence_ranges = []
        is_silence = False
        silence_start = 0
        
        for i, rms in enumerate(rms_values):
            if rms == 0:
                db = float('-inf')
            else:
                db = 20 * np.log10(rms / audio_segment.max_possible_amplitude)
            
            # 检查是否可能包含人声
            chunk_start = i * chunk_size
            chunk_end = min((i + 1) * chunk_size, len(samples))
            has_voice = self.get_frequency_features(
                samples[chunk_start:chunk_end],
                audio_segment.frame_rate
            )
            
            # 只有在没有检测到人声的情况下才判断是否为静音
            if db < self.threshold_db and not is_silence and not has_voice:
                silence_start = i * 100  # 100ms per chunk
                is_silence = True
            elif (db >= self.threshold_db or i == len(rms_values) - 1 or has_voice) and is_silence:
                silence_end = i * 100
                if silence_end - silence_start >= self.min_silence_len:
                    # 添加一些余量，避免切割得太紧
                    silence_start = max(0, silence_start - self.crossfade_len)
                    silence_end = min(len(audio_segment), silence_end + self.crossfade_len)
                    silence_ranges.append((silence_start, silence_end))
                is_silence = False
        
        return silence_ranges
        
    def remove_silence(self, audio_segment, silence_ranges):
        """
        移除静音片段
        :param audio_segment: AudioSegment对象
        :param silence_ranges: 静音片段列表
        :return: 处理后的AudioSegment对象
        """
        if not silence_ranges:
            return audio_segment
            
        # 构建保留的音频片段
        kept_ranges = []
        current_pos = 0
        
        for start, end in silence_ranges:
            if start > current_pos:
                kept_ranges.append((current_pos, start))
            current_pos = end
            
        if current_pos < len(audio_segment):
            kept_ranges.append((current_pos, len(audio_segment)))
            
        # 拼接保留的片段，添加交叉渐变效果
        result = AudioSegment.empty()
        for i, (start, end) in enumerate(kept_ranges):
            segment = audio_segment[start:end]
            
            # 对每个片段添加淡入淡出效果
            if i > 0 and len(segment) > self.crossfade_len * 2:
                segment = segment.fade_in(self.crossfade_len).fade_out(self.crossfade_len)
            
            # 使用交叉渐变效果拼接片段
            if len(result) > 0:
                result = result.append(segment, crossfade=self.crossfade_len)
            else:
                result = segment
            
        return result
        
    def process_file(self, input_path, output_path):
        """
        处理单个音频文件
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        print(f"处理文件: {input_path}")
        
        # 加载音频
        audio = self.load_audio(input_path)
        
        # 检测静音片段
        silence_ranges = self.detect_silence(audio)
        
        # 移除静音片段
        processed_audio = self.remove_silence(audio, silence_ranges)
        
        # 保存处理后的音频
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        processed_audio.export(output_path, format=os.path.splitext(output_path)[1][1:])
        
        print(f"处理完成: {output_path}")
        print(f"移除了 {len(silence_ranges)} 个静音片段")
        
    def process_directory(self, input_dir, output_dir):
        """
        批量处理目录中的音频文件
        :param input_dir: 输入目录
        :param output_dir: 输出目录
        """
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        audio_files = [f for f in os.listdir(input_dir) 
                      if f.lower().endswith(('.mp3', '.wav', '.m4a', '.flac'))]
                      
        print(f"找到 {len(audio_files)} 个音频文件")
        
        for audio_file in tqdm(audio_files):
            input_path = os.path.join(input_dir, audio_file)
            output_path = os.path.join(output_dir, audio_file)
            self.process_file(input_path, output_path) 