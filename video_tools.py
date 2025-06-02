import os
import logging
import re
import unicodedata
import uuid
import tempfile
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from pydub import AudioSegment
from pydub.utils import which
import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import rcParams
import numpy as np
from wordcloud import WordCloud, STOPWORDS

# Genel ayarlar
os.environ["PATH"] += os.pathsep + "/usr/bin"
AudioSegment.converter = "/usr/bin/ffmpeg"
rcParams.update({'figure.autolayout': True})
logging.basicConfig(level=logging.INFO)

DOWNLOADS_DIR = "downloads"
COOKIES_PATH = "cookies.txt"  # Gerekirse tam yolu belirt

def temizle_gecici_dosyalar():
    uzantilar = ('.webm', '.m4a', '.f140.m4a', '.f399.mp4', '.temp')
    for dosya in os.listdir('.'):
        if dosya.endswith(uzantilar):
            try:
                os.remove(dosya)
            except Exception as e:
                logging.warning(f"{dosya} silinirken hata: {e}")

def temizle_dosya_adi(baslik):
    ascii_ad = unicodedata.normalize('NFKD', baslik).encode('ascii', 'ignore').decode('ascii')
    ascii_ad = re.sub(r'[^a-zA-Z0-9 \-_]', '', ascii_ad)
    ascii_ad = re.sub(r'\s+', '-', ascii_ad)
    return ascii_ad[:80]

def indir_video(url, secenek="video"):
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)

    logging.info(f"İndirme başladı: url={url}, secenek={secenek}")

    try:
        base_outtmpl = os.path.join(DOWNLOADS_DIR, f"%(title)s_{uuid.uuid4().hex}.%(ext)s")
        ydl_opts = {
            "cookiefile": COOKIES_PATH,
            "outtmpl": base_outtmpl,
            "quiet": True,
            "noplaylist": True
        }

        if secenek == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts.update({
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4"
            })

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)

            if secenek == "audio":
                downloaded_path = os.path.splitext(downloaded_path)[0] + ".mp3"

            downloaded_path = os.path.abspath(downloaded_path)

            if os.path.exists(downloaded_path):
                logging.info(f"İndirme tamamlandı: {downloaded_path}")
                return downloaded_path
            else:
                logging.warning("Dosya bulunamadı.")
                return None

    except DownloadError as e:
        logging.error(f"YT-DLP Hatası: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Beklenmeyen Hata: {str(e)}")
        return None

def indir_video_genel(url, kaynak="genel"):
    temp_dir = DOWNLOADS_DIR
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'format': 'best',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

            ext = info.get("ext", "mp4")
            temiz_ad = temizle_dosya_adi(info.get("title", "video"))
            yeni_yol = os.path.join(temp_dir, f"{temiz_ad}.{ext}")

            if os.path.exists(yeni_yol):
                yeni_yol = os.path.join(temp_dir, f"{temiz_ad}_{uuid.uuid4().hex}.{ext}")

            os.rename(downloaded_file, yeni_yol)
            return os.path.abspath(yeni_yol)

    except Exception as e:
        logging.error(f"[{kaynak.upper()}] Hata oluştu: {e}")
        return None

def split_audio(file_path, chunk_length_minutes=10, output_dir="static/clips"):
    audio = AudioSegment.from_file(file_path)
    duration_ms = len(audio)
    chunk_length_ms = chunk_length_minutes * 60 * 1000 - 1000

    os.makedirs(output_dir, exist_ok=True)

    parts = []
    for i in range(0, duration_ms, chunk_length_ms):
        part = audio[i:i+chunk_length_ms]
        filename = f"{uuid.uuid4().hex}_part{i // chunk_length_ms + 1}.mp3"
        output_path = os.path.join(output_dir, filename)
        part.export(output_path, format="mp3")

        parts.append({
            "filename": filename,
            "start_min": i // 60000,
            "end_min": min((i + chunk_length_ms) // 60000, duration_ms // 60000)
        })

    return parts

def create_kumeleme_html(file, n_clusters=3):
    df = pd.read_excel(file)
    if df.shape[1] < 2:
        raise ValueError("En az iki sayısal sütun gerekli.")

    X = df.select_dtypes(include=['float64', 'int64']).iloc[:, :2]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(X)
    df['Küme'] = kmeans.labels_

    fig = px.scatter(df, x=X.columns[0], y=X.columns[1], color='Küme',
                     title=f'{n_clusters} Küme ile K-Means Analizi', template='plotly_white')

    unique_id = uuid.uuid4().hex
    output_path = f"static/kumeleme/kumeleme_{unique_id}.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig.write_html(output_path)
    return "/" + output_path

def create_timeline_video(excel_file):
    df = pd.read_excel(excel_file)
    df.columns = [col.strip() for col in df.columns]
    time_col, category_col, value_col = df.columns[:3]
    df = df.sort_values(by=time_col)

    fig, ax = plt.subplots(figsize=(10, 6))

    def animate(i):
        ax.clear()
        current_time = sorted(df[time_col].unique())[i]
        data = df[df[time_col] == current_time]
        data_sorted = data.sort_values(by=value_col, ascending=True)
        ax.barh(data_sorted[category_col], data_sorted[value_col], color='skyblue')
        ax.set_title(f"{time_col}: {current_time}", fontsize=16)
        ax.set_xlabel(value_col)
        ax.set_xlim(0, df[value_col].max() * 1.1)

    unique_times = sorted(df[time_col].unique())
    ani = FuncAnimation(fig, animate, frames=len(unique_times), repeat=False)

    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, "timeline_video.mp4")
    ani.save(output_path, writer="ffmpeg", fps=2)

    plt.close(fig)
    return output_path

def generate_wordcloud_from_text(text, output_dir="static/wordclouds"):
    os.makedirs(output_dir, exist_ok=True)

    turkish_stopwords = {
        "ve", "veya", "ama", "fakat", "ancak", "çok", "gibi", "ise", "de", "da",
        "ile", "bir", "bu", "şu", "o", "ki", "ne", "mi", "mı", "mu", "mü", "çünkü",
        "daha", "en", "her", "bazı", "hiç", "için", "üzere", "artık", "hem", "ya",
        "sadece", "bile", "yani", "ben", "sen", "biz", "siz", "onlar", "vardır", "yoktur"
    }

    combined_stopwords = STOPWORDS.union(turkish_stopwords)
    wordcloud = WordCloud(
        width=800, height=400, background_color='white', stopwords=combined_stopwords
    ).generate(text)

    freqs = wordcloud.words_
    top4 = list(freqs.keys())[:4]

    def color_func(word, *args, **kwargs):
        colors = ["#e74c3c", "#2980b9", "#27ae60", "#f39c12"]
        if word in top4:
            return colors[top4.index(word)]
        return "gray"

    wordcloud.recolor(color_func=color_func)

    filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(output_dir, filename)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, format='png')
    plt.close()

    return output_path

def _prepare_output_dir():
    output_dir = "static/animations"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def _save_animation(fig, ani, ext="gif"):
    output_dir = _prepare_output_dir()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(output_dir, filename)
    writer = "pillow" if ext == "gif" else "ffmpeg"
    ani.save(path, writer=writer, fps=10)
    plt.close()
    return path

def create_animated_line_chart(data):
    x = data.iloc[:, 0]
    y = data.iloc[:, 1]
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_xlim(min(x), max(x))
    ax.set_ylim(min(y), max(y))

    def init():
        line.set_data([], [])
        return line,

    def update(frame):
        line.set_data(x[:frame], y[:frame])
        return line,

    ani = FuncAnimation(fig, update, frames=len(x)+1, init_func=init, blit=True)
    return _save_animation(fig, ani)

def create_animated_bar_chart(data):
    categories = data.iloc[:, 0]
    values = data.iloc[:, 1]
    fig, ax = plt.subplots()
    bars = ax.bar(categories, [0]*len(values))
    ax.set_ylim(0, max(values)*1.1)

    def update(frame):
        for i, bar in enumerate(bars):
            bar.set_height(values[i] * frame / 10)
        return bars

    ani = FuncAnimation(fig, update, frames=11, blit=True)
    return _save_animation(fig, ani)

def create_animated_pie_chart(data):
    labels = data.iloc[:, 0]
    sizes = data.iloc[:, 1]
    fig, ax = plt.subplots()

    def update(frame):
        ax.clear()
        ax.pie(sizes[:frame+1], labels=labels[:frame+1], autopct='%1.1f%%')
        ax.set_title("Pasta Grafiği")

    ani = FuncAnimation(fig, update, frames=len(labels), repeat=False)
    return _save_animation(fig, ani)

def create_animated_radar_chart(data):
    labels = data.columns[1:]
    values = data.iloc[0, 1:].tolist()
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.set_ylim(0, max(values))
    line, = ax.plot([], [], 'b-')

    def update(frame):
        line.set_data(angles[:frame+1], values[:frame+1])
        return line,

    ani = FuncAnimation(fig, update, frames=len(labels)+1, blit=True)
    return _save_animation(fig, ani)

def create_animated_timeseries(data):
    x = pd.to_datetime(data.iloc[:, 0])
    y = data.iloc[:, 1]
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_xlim(min(x), max(x))
    ax.set_ylim(min(y), max(y))

    def update(frame):
        line.set_data(x[:frame], y[:frame])
        return line,

    ani = FuncAnimation(fig, update, frames=len(x)+1, blit=True)
    return _save_animation(fig, ani)
