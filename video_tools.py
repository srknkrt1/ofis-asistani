from yt_dlp import YoutubeDL
import os
import uuid
import shutil

def temizle_gecici_dosyalar():
    uzantilar = ('.webm', '.m4a', '.f140.m4a', '.f399.mp4', '.temp')
    for dosya in os.listdir('.'):
        if dosya.endswith(uzantilar):
            try:
                os.remove(dosya)
            except Exception as e:
                print(f"{dosya} silinirken hata: {e}")

def indir_video(url, secenek="video"):
    ydl_opts = {}

    if secenek == "video":
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'merge_output_format': 'mp4',
            'cookiefile': 'cookies.txt',
            'outtmpl': '%(title)s.%(ext)s',
        }
    elif secenek == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif secenek == "playlist":
        ydl_opts = {
            'ignoreerrors': True,
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(playlist)s/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt',
            'merge_output_format': 'mp4',
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:  # playlist ise
                return None
            else:
                dosya_yolu = ydl.prepare_filename(info)
                _, uzanti = os.path.splitext(dosya_yolu)
                yeni_ad = f"{uuid.uuid4()}{uzanti}"
                shutil.move(dosya_yolu, yeni_ad)
                temizle_gecici_dosyalar()
                return os.path.abspath(yeni_ad)
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None
