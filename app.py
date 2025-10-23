import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
from processor import analyze_video
import zipfile
from io import BytesIO

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
    results = analyze_video(in_path, app.config['OUTPUT_FOLDER'], min_clip_duration=min_duration)
    # results: dict with 'clips' list of {start,end,filename}
    return render_template('results.html', results=results, video=filename, base=base)


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


if __name__ == '__main__':
    app.run(debug=True)
