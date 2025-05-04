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
