from yt_dlp import YoutubeDL
import os
import re
import unicodedata

def temizle_gecici_dosyalar():
    uzantilar = ('.webm', '.m4a', '.f140.m4a', '.f399.mp4', '.temp')
    for dosya in os.listdir('.'):
        if dosya.endswith(uzantilar):
            try:
                os.remove(dosya)
            except Exception as e:
                print(f"{dosya} silinirken hata: {e}")

def temizle_dosya_adi(baslik):
    # Türkçe karakterleri ASCII'ye çevir
    ascii_ad = unicodedata.normalize('NFKD', baslik).encode('ascii', 'ignore').decode('ascii')
    # Sadece harf, rakam, boşluk ve tire karakterlerini bırak
    ascii_ad = re.sub(r'[^a-zA-Z0-9 \-_]', '', ascii_ad)
    # Boşlukları tire ile değiştir
    ascii_ad = re.sub(r'\s+', '-', ascii_ad)
    return ascii_ad[:80]  # Çok uzunsa ilk 80 karakteri al

def indir_video(url, secenek="video"):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best' if secenek == "audio" else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
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
            title = info.get("title", "video")
            extension = "mp3" if secenek == "audio" else "mp4"

            temiz_ad = temizle_dosya_adi(title)
            eski_yol = os.path.join(temp_dir, f"{title}.{extension}")
            yeni_yol = os.path.join(temp_dir, f"{temiz_ad}.{extension}")

            # Yeniden adlandırma
            if os.path.exists(eski_yol):
                os.rename(eski_yol, yeni_yol)
                return yeni_yol
            elif os.path.exists(yeni_yol):
                return yeni_yol
            else:
                return None
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None
