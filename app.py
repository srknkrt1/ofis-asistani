import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import matplotlib.pyplot as plt
from moviepy.editor import VideoFileClip
import matplotlib.animation as animation
import numpy as np

app = Flask(__name__)

# Yükleme dosya yolu
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dosya türlerini sınırlama
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('viz.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Excel verisini oku ve işleme başla
        df = pd.read_excel(filename)

        # Burada Excel verisini işleyecek kodları ekleyeceğiz
        # Örneğin, basit bir CSV çıktısı dönebiliriz
        data = df.to_dict(orient='records')
        
        # Yarışan grafik için veri görselleştirme işlemi yapılabilir

        # Video oluşturma fonksiyonunu çağırabilirsiniz

        return jsonify(data)

    return 'Geçersiz dosya formatı', 400

# Grafik oluşturma fonksiyonu
def create_racing_chart(data):
    # Pandas DataFrame kullanarak grafik oluşturma
    # Matplotlib kullanarak görselleştirme yapılacak
    fig, ax = plt.subplots(figsize=(10, 6))

    # Çizgi grafik oluşturma kodları
    categories = data.columns[1:]  # Kategoriler 1. sütundan sonraki sütunlar
    for category in categories:
        ax.plot(data['Dönem'], data[category], label=category)

    ax.set_title('Racing Chart')
    ax.set_xlabel('Dönem')
    ax.set_ylabel('Değer')
    ax.legend()

    # Görseli kaydet
    chart_path = 'static/racing_chart.png'
    plt.savefig(chart_path)
    plt.close()

    return chart_path

@app.route('/generate_video', methods=['POST'])
def generate_video():
    # Excel verisini işleyin ve yarışan grafik oluşturun
    # Verileri al, video oluşturmak için hazırlık yap
    # create_racing_chart fonksiyonunu çağırın

    data = request.json['data']  # JSON olarak gelen veriyi al
    df = pd.DataFrame(data)

    # Burada racing chart grafiği oluşturulacak
    chart_path = create_racing_chart(df)

    # Video oluşturma işlemi
    video_path = create_video(chart_path)

    return jsonify({"video_url": video_path})

def create_video(chart_path):
    # MoviePy kullanarak video oluşturma
    video_path = 'static/racing_chart_video.mp4'

    # Video oluşturma işlemleri (örneğin, sadece bir resim ile video oluşturulabilir)
    clip = VideoFileClip(chart_path)
    clip.write_videofile(video_path, codec="libx264")

    return video_path

if __name__ == '__main__':
    app.run(debug=True)
