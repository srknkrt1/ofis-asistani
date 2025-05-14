import os
os.environ["PATH"] += os.pathsep + "/usr/bin"  # ffmpeg yolunu garanti et

from yt_dlp import YoutubeDL
from pydub import AudioSegment
from pydub.utils import which
import uuid
import re
import unicodedata

AudioSegment.converter = "/usr/bin/ffmpeg"


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
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best' if secenek == "audio" else 'bestvideo[ext=mp4]+bestaudio/best',
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
    }

    if secenek == "audio":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    if secenek == "playlist":
        ydl_opts['ignoreerrors'] = True
        ydl_opts['merge_output_format'] = 'mp4'
        ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(playlist_title)s/%(title)s.%(ext)s')

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

            # Adı temizle (isteğe bağlı)
            ext = info.get("ext", "mp4")
            temiz_ad = temizle_dosya_adi(info.get("title", "video"))
            yeni_yol = os.path.join(temp_dir, f"{temiz_ad}.{ext}")

            if downloaded_file != yeni_yol:
                os.rename(downloaded_file, yeni_yol)

            return os.path.abspath(yeni_yol)
    except Exception as e:
        print(f"Hata oluştu: {e}")
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
