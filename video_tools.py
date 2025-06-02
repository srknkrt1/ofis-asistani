import os
os.environ["PATH"] += os.pathsep + "/usr/bin"  # ffmpeg yolunu garanti et
import logging
logging.basicConfig(level=logging.INFO)
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from pydub.utils import which
import uuid
import re
import unicodedata
from yt_dlp.utils import DownloadError
import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tempfile
AudioSegment.converter = "/usr/bin/ffmpeg"

DOWNLOADS_DIR = "downloads"
COOKIES_PATH = "cookies.txt"  # Gerekirse tam yolu yaz


def temizle_gecici_dosyalar():
    uzantilar = ('.webm', '.m4a', '.f140.m4a', '.f399.mp4', '.temp')
    for dosya in os.listdir('.'):
        if dosya.endswith(uzantilar):
            try:
                os.remove(dosya)
            except Exception as e:
                print(f"{dosya} silinirken hata: {e}")

def temizle_dosya_adi(baslik):
    ascii_ad = unicodedata.normalize('NFKD', baslik).encode('ascii', 'ignore').decode('ascii')
    ascii_ad = re.sub(r'[^a-zA-Z0-9 \-_]', '', ascii_ad)
    ascii_ad = re.sub(r'\s+', '-', ascii_ad)
    return ascii_ad[:80]

def indir_video(url, secenek="video"):
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)

    print(f"▶ indir_video başladı: url={url}, secenek={secenek}")

    try:
        ydl_opts = {
            "cookiefile": COOKIES_PATH,
            "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "overwrites": True,
        }

        if secenek == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "outtmpl": os.path.join(DOWNLOADS_DIR, f"%(title)s_{uuid.uuid4().hex}.%(ext)s"),
            })
        elif secenek == "video":
            ydl_opts.update({
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": os.path.join(DOWNLOADS_DIR, f"%(title)s_{uuid.uuid4().hex}.%(ext)s"),
            })

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)

            # Eğer mp3'e dönüştürüldüyse uzantısı değişmiş olabilir
            if secenek == "audio":
                downloaded_path = os.path.splitext(downloaded_path)[0] + ".mp3"

            downloaded_path = os.path.abspath(downloaded_path)

            if os.path.exists(downloaded_path):
                print(f"✔ İndirme tamamlandı: {downloaded_path}")
                return downloaded_path
            else:
                print("⚠ Dosya bulunamadı.")
                return None

    except DownloadError as e:
        print(f"✘ YT-DLP Hatası: {str(e)}")
        return None
    except Exception as e:
        print(f"✘ Beklenmeyen Hata: {str(e)}")
        return None

def indir_instagram(url):
    return indir_video_genel(url, "instagram")

def indir_twitter(url):
    return indir_video_genel(url, "twitter")

def indir_video_genel(url, kaynak):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'format': 'best',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

            # Temizlenmiş adla yeniden adlandır (isteğe bağlı)
            ext = info.get("ext", "mp4")
            temiz_ad = temizle_dosya_adi(info.get("title", "video"))
            yeni_yol = os.path.join(temp_dir, f"{temiz_ad}.{ext}")

            if downloaded_file != yeni_yol:
                os.rename(downloaded_file, yeni_yol)

            return os.path.abspath(yeni_yol)
    except Exception as e:
        print(f"[{kaynak.upper()}] Hata oluştu: {e}")
        return None

def split_audio(file_path, chunk_length_minutes=10, output_dir="static/clips"):
    audio = AudioSegment.from_file(file_path)
    duration_ms = len(audio)
    chunk_length_ms = 599000  # 9 dakika 59 saniye

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    parts = []
    for i in range(0, duration_ms, chunk_length_ms):
        part = audio[i:i+chunk_length_ms]
        filename = f"{uuid.uuid4().hex}_part{i // chunk_length_ms + 1}.mp3"
        output_path = os.path.join(output_dir, filename)
        part.export(output_path, format="mp3")
        
        # Başlangıç ve bitiş dakikalarını düzgün hesapla
        start_min = i // 60000
        end_min = min((i + chunk_length_ms) // 60000, duration_ms // 60000)
        
        parts.append({
            "filename": filename,
            "start_min": start_min,
            "end_min": end_min
        })

    return parts
    
def create_kumeleme_html(file, n_clusters=3):
    df = pd.read_excel(file)
    if df.shape[1] < 2:
        raise ValueError("En az iki sayısal sütun gerekli.")

    X = df.select_dtypes(include=['float64', 'int64']).iloc[:, :2]  # İlk iki sayısal sütun
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

    # Zaman, kategori, değer kolonları varsayalım
    # Örnek: Zaman, Şehir, Nüfus
    df.columns = [col.strip() for col in df.columns]
    time_col = df.columns[0]
    category_col = df.columns[1]
    value_col = df.columns[2]

    # Zaman sırasına göre sırala
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
    ani = animation.FuncAnimation(fig, animate, frames=len(unique_times), repeat=False)

    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, "timeline_video.mp4")
    ani.save(output_path, writer="ffmpeg", fps=2)

    plt.close(fig)
    return output_path
def generate_wordcloud_from_text(text, output_dir="static/wordclouds"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Türkçe stopwords
    turkish_stopwords = {
        "ve", "veya", "ama", "fakat", "ancak", "çok", "gibi", "ise", "de", "da",
        "ile", "bir", "bu", "şu", "o", "ki", "ne", "mi", "mı", "mu", "mü", "çünkü",
        "daha", "en", "her", "bazı", "hiç", "için", "üzere", "artık", "hem", "ya",
        "sadece", "bile", "yani", "ben", "sen", "biz", "siz", "onlar", "vardır", "yoktur"
    }

    combined_stopwords = STOPWORDS.union(turkish_stopwords)

    # Kelime bulutunu oluştur
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        stopwords=combined_stopwords
    ).generate(text)

    # En sık geçen ilk 4 kelimeyi bul
    freqs = wordcloud.words_
    top4 = list(freqs.keys())[:4]

    # Renkleri belirle
    def color_func(word, *args, **kwargs):
        if word == top4[0]:
            return "#e74c3c"  # kırmızı
        elif word == top4[1]:
            return "#2980b9"  # mavi
        elif word == top4[2]:
            return "#27ae60"  # yeşil
        elif word == top4[3]:
            return "#f39c12"  # turuncu
        else:
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

