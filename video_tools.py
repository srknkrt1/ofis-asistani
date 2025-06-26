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
import matplotlib.animation as animation
from scipy.interpolate import make_interp_spline


# Genel ayarlar
os.environ["PATH"] += os.pathsep + "/usr/bin"
AudioSegment.converter = "/usr/bin/ffmpeg"
rcParams.update({'figure.autolayout': True})
logging.basicConfig(level=logging.INFO)

DOWNLOADS_DIR = "downloads"
COOKIES_PATH = "cookies.txt"  # Gerekirse tam yolu belirt
ANIMATED_DOWNLOADS_DIR = os.path.join("static", "animated_downloads")
os.makedirs(ANIMATED_DOWNLOADS_DIR, exist_ok=True)




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

def indir_instagram(url):
    return indir_video_genel(url, "instagram")

def indir_twitter(url):
    return indir_video_genel(url, "twitter")

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
    df = pd.read_excel(file, header=0)

    if df.shape[1] < 2:
        raise ValueError("En az bir etiket ve bir sayısal sütun gerekli.")

    # İlk sütun: etiketler (isimler)
    labels = df.iloc[:, 0]

    # Sayısal sütunları seç (ilk sütun hariç)
    feature_df = df.iloc[:, 1:]
    numeric_features = feature_df.select_dtypes(include=['float64', 'int64'])

    if numeric_features.shape[1] < 1:
        raise ValueError("En az bir sayısal özellik sütunu gerekli.")

    # K-means kümeleme
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df['Küme'] = kmeans.fit_predict(numeric_features)

    # Görselleştirme için sütun sayısına göre çizim seç
    if numeric_features.shape[1] >= 2:
        # İlk iki özellik ile 2D scatter plot
        fig = px.scatter(df, x=numeric_features.columns[0], y=numeric_features.columns[1],
                         color='Küme', text=labels,
                         title=f'{n_clusters} Küme ile K-Means Analizi',
                         template='plotly_white')
        fig.update_traces(textposition='top center')
    else:
        # Tek özellik varsa bar chart ile küme gösterimi
        fig = px.bar(df, x=labels, y=numeric_features.columns[0], color='Küme',
                     title=f'{n_clusters} Küme ile K-Means Analizi (Tek Özellik)',
                     template='plotly_white')

    # HTML çıktısı
    unique_id = uuid.uuid4().hex
    output_path = f"static/kumeleme/kumeleme_{unique_id}.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path)

    return "/" + output_path

def create_timeline_video(excel_file):
    df = pd.read_excel(excel_file)
    df.columns = [col.strip() for col in df.columns]
    if df.shape[1] < 2:
        raise ValueError("Excel en az iki sütun içermelidir.")

    time_col, value_col = df.columns[:2]
    df = df.sort_values(by=time_col).reset_index(drop=True)

    years = df[time_col].tolist()
    values = df[value_col].tolist()
    n = len(years)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, n - 1)
    ax.set_ylim(-max(values) * 0.7, max(values) * 1.3)
    ax.axis('off')

    pastel_blue = "#4B9CD3"
    time_line_color = "#333333"
    point_color = "#e63946"

    timeline_x = []
    timeline_y = []

    annotations = []

    def ease_out(t):
        return 1 - (1 - t) ** 3

    def animate(frame):
        ax.clear()
        ax.set_xlim(0, n - 1)
        ax.set_ylim(-max(values) * 0.7, max(values) * 1.3)
        ax.axis('off')

        current_index = frame // 15  # her veri noktası 15 frame sürer
        progress_within = (frame % 15) / 15.0
        progress_eased = ease_out(progress_within)

        # timeline noktalarını güncelle
        timeline_x = np.linspace(0, current_index + progress_eased, 100)
        timeline_y = np.zeros_like(timeline_x)

        # spline ile çizgi
        ax.plot(timeline_x, timeline_y, color=time_line_color, lw=2)

        # veri dalları
        for i in range(current_index + 1):
            direction = 1 if i % 2 == 0 else -1
            x = i
            y = 0
            val = values[i]
            height = direction * val * 0.5

            # Son nokta mı? O zaman animasyonlu çıkar
            if i == current_index:
                height *= progress_eased

            # spline benzeri yumuşak eğri
            branch_x = [x, x + 0.05, x + 0.1]
            branch_y = [0, height * 0.6, height]
            spline = make_interp_spline([0, 1, 2], branch_y, k=2)
            smooth_y = spline(np.linspace(0, 2, 50))
            smooth_x = np.linspace(x, x + 0.1, 50)
            ax.plot(smooth_x, smooth_y, color=pastel_blue, lw=2)

            # Nokta
            ax.plot(x, 0, 'o', color=point_color)

            # Değer yazısı
            if i < current_index or progress_within > 0.8:
                ax.text(x + 0.1, height + 1.5 * (1 if direction == 1 else -1),
                        f"{val}", fontsize=9, ha='left',
                        va='bottom' if direction == 1 else 'top',
                        color="#222222")

            # Yıl yazısı (alt kısımda)
            ax.text(x, -max(values) * 0.1, str(years[i]),
                    ha='center', va='top', fontsize=9)

    total_frames = n * 15
    ani = animation.FuncAnimation(fig, animate, frames=total_frames, repeat=False)

    os.makedirs("downloads", exist_ok=True)
    output_path = os.path.join("downloads", f"timeline_{uuid.uuid4().hex}.mp4")
    ani.save(output_path, writer="ffmpeg", fps=15)

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

def _save_animation(fig, ani, ext="mp4", fps=10):
    output_dir = _prepare_output_dir()
    filename = f"{uuid.uuid4().hex}.{ext}"
    full_path = os.path.join(output_dir, filename)
    writer = "pillow" if ext == "gif" else "ffmpeg"
    ani.save(full_path, writer=writer, fps=fps)
    plt.close()
    return f"animations/{filename}"

# ✅ ÇİZGİ GRAFİK – çoklu serileri destekler, etiketli ve estetik
def create_animated_line_chart(data):
    x_labels = data.iloc[:, 0].astype(str).values
    series_names = data.columns[1:]
    y_data = data.iloc[:, 1:].values
    num_points = len(x_labels)

    total_frames = 45  # Toplam süre (3 saniye), fps=15
    fps = 15

    fig, ax = plt.subplots()
    ax.set_xlim(0, num_points - 1)
    ax.set_ylim(0, np.max(y_data) * 1.1)
    ax.set_xticks(range(num_points))
    ax.set_xticklabels(x_labels, rotation=45)
    ax.set_title("Çizgi Grafik")
    ax.set_ylabel("Değer")
    ax.grid(True)

    lines = []
    for col in range(y_data.shape[1]):
        line, = ax.plot([], [], label=series_names[col], lw=2)
        lines.append(line)
    ax.legend()

    x_interp = np.linspace(0, num_points - 1, total_frames)
    y_interp_all = [
        np.interp(x_interp, np.arange(num_points), y_data[:, col])
        for col in range(y_data.shape[1])
    ]

    def ease_out(t):
        return 1 - (1 - t) ** 2

    def init():
        for line in lines:
            line.set_data([], [])
        return lines

    def update(frame):
        t = frame / (total_frames - 1)
        eased_frame = int(ease_out(t) * total_frames)

        for col, line in enumerate(lines):
            line.set_data(x_interp[:eased_frame], y_interp_all[col][:eased_frame])
        return lines

    ani = FuncAnimation(fig, update, frames=total_frames, init_func=init, blit=True)
    return _save_animation(fig, ani, ext="mp4", fps=fps)


def create_animated_bar_chart(data):
    categories = data.iloc[:, 0].astype(str).values
    values = data.iloc[:, 1].values
    fig, ax = plt.subplots()
    bars = ax.bar(categories, [0]*len(values))
    ax.set_ylim(0, max(values)*1.1)
    ax.set_title("Bar Grafiği")
    ax.set_ylabel("Değer")

    total_frames = 45  # 3 saniye * 15 fps

    def ease_out(t):
        return 1 - (1 - t)**2  # quadratic easing-out

    def update(frame):
        progress = ease_out(frame / (total_frames - 1))
        for i, bar in enumerate(bars):
            bar.set_height(values[i] * progress)
        return bars

    ani = FuncAnimation(fig, update, frames=total_frames, blit=True)
    return _save_animation(fig, ani, fps=15)

def create_animated_pie_chart(data):
    labels = data.iloc[:, 0].astype(str).values
    sizes = data.iloc[:, 1].values
    fig, ax = plt.subplots()
    fig.set_size_inches(6, 6)
    ax.set_title("Pasta Grafiği")

    def easing(t):  # ease-out fonksiyonu
        return 1 - (1 - t)**3

    frames = 45

    def update(frame):
        ax.clear()
        ax.set_title("Pasta Grafiği")
        t = easing(frame / frames)
        slice_count = max(1, int(len(sizes) * t))  # en az 1 dilim
        current_sizes = sizes[:slice_count]
        current_labels = labels[:slice_count]

        if np.sum(current_sizes) > 0 and not np.any(np.isnan(current_sizes)):
            ax.pie(current_sizes, labels=current_labels, autopct='%1.1f%%', startangle=140)
        else:
            ax.text(0.5, 0.5, "Veri Yetersiz", ha='center', va='center', fontsize=14)

    ani = FuncAnimation(fig, update, frames=frames+1, interval=3000/(frames+1), blit=False)
    return _save_animation(fig, ani, fps=15)

def create_animated_radar_chart(data):
    labels = data.columns[1:]
    values = data.iloc[0, 1:].tolist()

    # Radar grafiği kapatmak için baştaki değeri sona ekle
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    fig.set_size_inches(6, 6)
    ax.set_ylim(0, max(values))
    ax.set_title("Radar Grafiği")

    # Etiketleri yerleştir
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    line, = ax.plot([], [], 'b-', linewidth=2)

    total_frames = 45  # 3 saniye * 15 fps

    def ease_out(t):
        return 1 - (1 - t)**2

    def update(frame):
        progress = ease_out(frame / (total_frames - 1))
        end_index = max(2, int(progress * len(values)))  # en az 2 nokta çizilsin
        line.set_data(angles[:end_index], values[:end_index])
        return line,

    ani = FuncAnimation(fig, update, frames=total_frames, blit=True)
    return _save_animation(fig, ani, fps=15)


def create_animated_timeseries(data):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    import matplotlib.dates as mdates

    x = pd.to_datetime(data.iloc[:, 0])
    y_data = data.iloc[:, 1:]

    fig, ax = plt.subplots()
    ax.set_xlim(min(x), max(x))
    ax.set_ylim(y_data.min().min(), y_data.max().max() * 1.1)
    ax.set_title("Zaman Serisi Grafiği")
    ax.set_ylabel("Değer")
    ax.set_xlabel(str(data.columns[0]))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))  # Örn: Jan, Feb
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()

    lines = []
    for i in range(y_data.shape[1]):
        line, = ax.plot([], [], lw=2, label=data.columns[i + 1])
        lines.append(line)
    ax.legend()

    total_frames = 45  # 3 saniye * 15 fps

    def ease_out(t):
        return 1 - (1 - t)**2

    def update(frame):
        progress = ease_out(frame / (total_frames - 1))
        end_index = int(progress * len(x))
        for i, line in enumerate(lines):
            line.set_data(x[:end_index], y_data.iloc[:end_index, i])
        return lines

    ani = FuncAnimation(fig, update, frames=total_frames, blit=True)
    return _save_animation(fig, ani, fps=15)
