import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
from processor import analyze_video
import zipfile
from io import BytesIO
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__, static_url_path=f'/audio-detect/static')
# 配置
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['OUTPUT_FOLDER'] = OUTPUT_DIR
# 最大上传大小设为 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
# URL 前缀，所有路由都加这个前缀
URL_PREFIX = '/audio-detect'


@app.route(f'{URL_PREFIX}/')
def index():
    return render_template('index.html')


@app.route(f'{URL_PREFIX}/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    f = request.files['file']
    if f.filename == '':
        return redirect(url_for('index'))
    filename = secure_filename(f.filename)
    base = os.path.splitext(filename)[0]
    in_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(in_path)
    # 获取自定义片段长度
    min_duration = request.form.get('min_duration', type=float, default=5.0)
    # 限制最小长度不小于1秒
    min_duration = max(1.0, min_duration)
    
    # analyze video and produce results
    error_msg = None
    results = None
    try:
        results = analyze_video(in_path, app.config['OUTPUT_FOLDER'], min_clip_duration=min_duration)
    except Exception as e:
        # capture error and show to user
        error_msg = str(e)
    finally:
        # 清理旧任务文件（保留最近 5 个上传）
        try:
            prune_old_tasks(app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], keep=5)
        except Exception:
            # 不要因为清理失败而中断流程
            pass

    return render_template('results.html', results=results, video=filename, base=base, error=error_msg)


def prune_old_tasks(upload_dir, output_dir, keep=5):
    """只保留最近 keep 个上传任务的文件。

    依据 upload_dir 中按修改时间排序的文件名（最新的保留），然后在 output_dir 中保留与这些名字前缀匹配的输出文件。
    """
    # collect uploaded files (full paths)
    uploads = [os.path.join(upload_dir, p) for p in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, p))]
    # sort by mtime desc
    uploads.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    keep_uploads = uploads[:keep]
    keep_basenames = set(os.path.splitext(os.path.basename(p))[0] for p in keep_uploads)

    # remove old uploads
    for p in uploads[keep:]:
        try:
            os.remove(p)
        except Exception:
            pass

    # In outputs, we remove files that don't start with any of the keep basenames
    for fn in os.listdir(output_dir):
        full = os.path.join(output_dir, fn)
        if not os.path.isfile(full):
            continue
        keep_this = False
        for b in keep_basenames:
            if fn.startswith(b):
                keep_this = True
                break
        if not keep_this:
            try:
                os.remove(full)
            except Exception:
                pass


@app.route(f'{URL_PREFIX}/file/<path:filename>')
def download_file(filename):
    """下载单个文件（音频或视频）"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


@app.route(f'{URL_PREFIX}/clips-zip/<name>')
def download_clips_zip(name):
    # zip all files that start with name (convention used when exporting clips)
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for fn in os.listdir(app.config['OUTPUT_FOLDER']):
            if fn.startswith(name):
                zf.write(os.path.join(app.config['OUTPUT_FOLDER'], fn), arcname=fn)
    buf.seek(0)
    return send_file(buf, mimetype='application/zip', as_attachment=True, download_name=f"{name}.zip")


@app.errorhandler(413)
def request_entity_too_large(error):
    """处理文件过大的错误（通常不会触发，因为前端会阻止）"""
    return render_template('results.html', 
                         error="上传的文件超过大小限制（500MB），请选择较小的文件。",
                         video=None, base=None, results=None)


if __name__ == '__main__':
    app.run(debug=True)
