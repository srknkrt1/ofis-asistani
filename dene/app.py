from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request
import os, tempfile
import subprocess
import pandas as pd
import bar_chart_race as bcr
import json
from docx import Document  # eksiktiyse eklenmeli
from transkript import transkripte_cevir
from video_tools import indir_video, indir_instagram, indir_twitter,split_audio
import fitz  # PyMuPDF
import threading
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from uuid import uuid4
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from pdf_tools import (
    birlestir_pdf_listesi, bol_pdf, dondur_pdf, sikistir_pdf,
    pdf_to_word
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
app.config['UPLOAD_FOLDER'] = 'uploads'  # veya senin istediğin başka bir dizin
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
IMAGE_FOLDER = 'static/temp_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

# Veri görselleştirme sayfası (viz.html)
@app.route('/viz')
def viz():
    return render_template("viz.html")


# Excel dosyasını alıp işleme kısmı
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Dosya yüklenmedi."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Dosya adı boş."}), 400
    
    # Dosyayı kaydediyoruz
    filename = str(uuid.uuid4()) + ".xlsx"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Excel dosyasını okuyoruz
    df = pd.read_excel(file_path)
    
    # JSON olarak döndürülmesi için dataframe'i serialize ediyoruz
    return jsonify(df.to_dict(orient='records'))

# Video oluşturma işlemi
@app.route('/generate_video', methods=['POST'])
def generate_video():
    data = request.json
    if not data or 'data' not in data:
        return jsonify({"error": "Geçersiz veri."}), 400

    # Excel verisini DataFrame olarak alıyoruz
    df = pd.DataFrame(data['data'])
    
    # Videoyu oluşturuyoruz
    video_filename = f"race_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(app.config['STATIC_FOLDER'], video_filename)

    try:
        # Bar chart race videosunu oluşturuyoruz
        bcr.bar_chart_race(
            df=df,
            filename=output_path,
            orientation='h',
            sort='desc',
            n_bars=10,
            fixed_order=False,
            steps_per_period=30,
            period_length=500,
            figsize=(6, 3.5)
        )
    except Exception as e:
        return jsonify({"error": f"Video oluşturulurken bir hata oluştu: {str(e)}"}), 500

    return jsonify({"video_url": f"/static/{video_filename}"})

@app.route('/viz_result')
def viz_result():
    video_path = request.args.get('video_path')  # URL parametre olarak al
    return render_template('viz_result.html', video_path=video_path)

if __name__ == "__main__":
    app.run(debug=True)
