import os
import subprocess
import math
import uuid
import wave
from array import array


def extract_audio_ffmpeg(video_path, out_wav):
    """Extract audio from video using ffmpeg.
    
    Raises:
        RuntimeError: If ffmpeg is not found in PATH
        subprocess.CalledProcessError: If ffmpeg conversion fails
    """
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-ac', '1', '-ar', '16000', '-acodec', 'pcm_s16le', '-f', 'wav', out_wav
    ]
    try:
        subprocess.check_call(cmd, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise RuntimeError(
            "找不到 ffmpeg 命令。请确保已安装 ffmpeg 并添加到系统 PATH。\n"
            "Windows 安装方法：\n"
            "1. 使用 Chocolatey: choco install ffmpeg\n"
            "2. 或从 https://ffmpeg.org/download.html 下载，解压后将 bin 目录添加到 PATH"
        )
    except subprocess.CalledProcessError as e:
        # Try to capture output if available
        msg = getattr(e, 'output', None)
        if msg:
            try:
                msg = msg.decode(errors='ignore')
            except Exception:
                msg = str(msg)
        else:
            msg = f"ffmpeg 返回非零退出状态: {e.returncode}"
        raise RuntimeError(f"ffmpeg 转码音频失败: {msg}")


def compute_rms_from_wav(wav_path, frame_size_samples, hop_size_samples):
    # returns list of rms values (float) and sample rate
    # This implementation assumes 16-bit PCM (pcm_s16le) produced by ffmpeg.
    with wave.open(wav_path, 'rb') as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        data = wf.readframes(nframes)

    bytes_per_sample = sampwidth * nchannels
    frame_bytes = frame_size_samples * bytes_per_sample
    hop_bytes = hop_size_samples * bytes_per_sample
    rms_list = []

    if sampwidth != 2:
        # As a fallback, return empty list (no detections). Ideally ffmpeg outputs 16-bit.
        raise RuntimeError(f"Unsupported sample width: {sampwidth}. Expected 2 (16-bit).")

    # Interpret bytes as signed 16-bit little-endian
    for start in range(0, len(data) - frame_bytes + 1, hop_bytes):
        frame = data[start:start+frame_bytes]
        # convert to array of signed short
        a = array('h')
        a.frombytes(frame)
        if nchannels > 1:
            # when multiple channels, interleaved; average across channels per sample
            # but since we request mono (-ac 1), this branch is unlikely
            samples = a[::nchannels]
        else:
            samples = a
        if len(samples) == 0:
            rms_list.append(0.0)
            continue
        # compute RMS
        ssum = 0
        for v in samples:
            ssum += v * v
        mean_sq = ssum / len(samples)
        rms = math.sqrt(mean_sq)
        rms_list.append(rms)

    # normalize rms to float in [0,1]
    max_val = float(2 ** (8 * sampwidth - 1))
    rms_list = [r / max_val for r in rms_list]
    return rms_list, framerate


def detect_sudden_jumps(rms, sr, frame_size, hop_size, thresh_ratio=2.0, min_duration_s=0.2):
    # rms: list of floats
    import statistics
    win = max(1, int(0.5 / (hop_size / sr)))
    # pad by reflecting edges
    padded = ([rms[0]] * win) + rms + ([rms[-1]] * win)
    med = [statistics.median(padded[i:i+2*win+1]) for i in range(len(rms))]
    intervals = []
    mask = [ (r / (m + 1e-12)) > thresh_ratio for r, m in zip(rms, med) ]
    i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            start_time = i * hop_size / sr
            end_time = (j * hop_size + frame_size) / sr
            if end_time - start_time >= min_duration_s:
                intervals.append((start_time, end_time))
            i = j
        else:
            i += 1
    return intervals


def export_clip_ffmpeg(wav_in, start_s, end_s, out_wav):
    cmd = [
        'ffmpeg', '-y', '-ss', f"{start_s}", '-to', f"{end_s}", '-i', wav_in,
        '-ac', '1', '-ar', '16000', '-f', 'wav', out_wav
    ]
    try:
        subprocess.check_call(cmd, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise RuntimeError("找不到 ffmpeg 命令（export_clip_ffmpeg）。")
    except subprocess.CalledProcessError as e:
        msg = getattr(e, 'output', None)
        if msg:
            try:
                msg = msg.decode(errors='ignore')
            except Exception:
                msg = str(msg)
        else:
            msg = f"ffmpeg 返回非零退出状态: {e.returncode}"
        raise RuntimeError(f"导出音频片段失败: {msg}")


def export_video_clip_ffmpeg(video_in, start_s, end_s, out_video):
    # copy video and audio streams for video clip extraction
    cmd = [
        'ffmpeg', '-y', '-ss', f"{start_s}", '-to', f"{end_s}", '-i', video_in,
        '-c', 'copy', out_video
    ]
    try:
        subprocess.check_call(cmd, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise RuntimeError("找不到 ffmpeg 命令（export_video_clip_ffmpeg）。")
    except subprocess.CalledProcessError as e:
        msg = getattr(e, 'output', None)
        if msg:
            try:
                msg = msg.decode(errors='ignore')
            except Exception:
                msg = str(msg)
        else:
            msg = f"ffmpeg 返回非零退出状态: {e.returncode}"
        raise RuntimeError(f"导出视频片段失败: {msg}")


def get_video_duration(video_path):
    """获取视频总长度（秒）"""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    try:
        duration = float(subprocess.check_output(cmd).decode().strip())
        return duration
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None

def analyze_video(video_path, output_folder, min_clip_duration=5.0):
    base = os.path.splitext(os.path.basename(video_path))[0]
    tmp_wav = os.path.join(output_folder, f'{base}_extracted.wav')
    extract_audio_ffmpeg(video_path, tmp_wav)
    
    # 获取视频总长度
    total_duration = get_video_duration(video_path)
    if total_duration is None:
        raise RuntimeError("无法获取视频长度，请确保已安装 ffprobe")
    
    # parameters
    # use 50ms frame, 20ms hop
    # frame_size in samples
    # We'll read using wave to get sample rate
    with wave.open(tmp_wav, 'rb') as wf:
        sr = wf.getframerate()
    frame_size = int(0.05 * sr)
    hop_size = int(0.02 * sr)
    rms, sr = compute_rms_from_wav(tmp_wav, frame_size, hop_size)
    intervals = detect_sudden_jumps(rms, sr, frame_size, hop_size)
    clips = []
    for st, ed in intervals:
        uid = uuid.uuid4().hex[:8]
        out_name = f"{base}_clip_{uid}.wav"
        out_path = os.path.join(output_folder, out_name)
        # add small padding
        start = max(0, st - 0.05)
        end = ed + 0.05
        # ensure minimum clip duration and don't exceed total video length
        duration = end - start
        if duration < min_clip_duration:
            extra = (min_clip_duration - duration) / 2
            start = max(0, start - extra)
            end = min(total_duration, end + extra)
        export_clip_ffmpeg(tmp_wav, start, end, out_path)
        # export corresponding video clip
        out_video_name = f"{base}_clip_{uid}.mp4"
        out_video_path = os.path.join(output_folder, out_video_name)
        export_video_clip_ffmpeg(video_path, start, end, out_video_path)
        clips.append({'start': round(st,3), 'end': round(ed,3), 'file': out_name, 'video': out_video_name})
    return {'clips': clips, 'audio_file': os.path.basename(tmp_wav)}
