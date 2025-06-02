from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request, jsonify, send_from_directory, redirect, flash
import os, tempfile
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote
import subprocess
import pandas as pd
import bar_chart_race as bcr
from docx import Document  # eksiktiyse eklenmeli
from transkript import transkripte_cevir
from video_tools import indir_video, indir_instagram, indir_twitter,split_audio, create_kumeleme_html, create_timeline_video, generate_wordcloud_from_text
import fitz  # PyMuPDF
import threading
import uuid
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from uuid import uuid4
from PyPDF2 import PdfReader, PdfWriter
from mimetypes import guess_type
from io import BytesIO
from pdf_tools import (
    birlestir_pdf_listesi, bol_pdf, dondur_pdf, sikistir_pdf,
    pdf_to_word
)
from video_tools import (
    create_animated_line_chart,
    create_animated_bar_chart,
    create_animated_pie_chart,
    create_animated_radar_chart,
    create_animated_timeseries
)

app = Flask(__name__)
app.secret_key = 'Gu0z_4VlbNzNwJ8nHD3E2xz5G9p1J5HMIw5ZlGiZ8HI'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
app.config['UPLOAD_FOLDER'] = 'uploads'  # veya senin istediğin başka bir dizin
UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = 'static/temp_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

AudioSegment.converter = "/usr/bin/ffmpeg"

# app.py içinde en üstte
transkript_kilit = threading.Lock()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pdf")
def pdf():
    return render_template("pdf.html")

@app.route("/video")
def video():
    return render_template("video.html")

@app.route('/hakkimizda')
def hakkimizda():
    return render_template('hakkimizda.html')

@app.route('/iletisim', methods=['GET', 'POST'])
def iletisim():
    return render_template('iletisim.html')

@app.route('/gizlilik')
def gizlilik():
    return render_template('gizlilik.html')

@app.route('/kullanim')
def kullanim():
    return render_template('kullanim.html')

@app.route('/dmca')
def dmca():
    return render_template('dmca.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')


@app.route("/iletisim-gonder", methods=["POST"])
def iletisim_gonder():
    isim = request.form.get("isim")
    email = request.form.get("email")
    mesaj = request.form.get("mesaj")

    icerik = f"Yeni iletişim mesajı:\n\nAd: {isim}\nE-posta: {email}\nMesaj:\n{mesaj}"

    # Mail ayarları
    gönderici = "srknkrtqaz@gmail.com"
    alici = "srknkrtqaz@gmail.com"
    konu = "Yeni İletişim Formu Mesajı"
    sifre = "bfll rzmo eeup wkis"  # buraya uygulama şifresi gelecek

    msg = MIMEText(icerik)
    msg["Subject"] = konu
    msg["From"] = gönderici
    msg["To"] = alici

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gönderici, sifre)
            server.sendmail(gönderici, alici, msg.as_string())
        flash("Mesajınız başarıyla gönderildi.", "success")
        return redirect("/iletisim")  # Gönderildikten sonra iletişim sayfasına geri dön
    except Exception as e:
        return f"Bir hata oluştu: {e}"


# Veri görselleştirme sayfası (viz.html)
@app.route('/viz')
def viz():
    return render_template("viz.html")

def get_audio_duration(file_path):
    result = subprocess.run(
        ["/usr/bin/ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path]
        ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

@app.route('/transkript', methods=['GET', 'POST'])
def transkript():
    if request.method == 'GET':
        return render_template("transkript.html")

    # Aynı anda sadece 1 işlem izni
    if not transkript_kilit.acquire(blocking=False):
        return render_template("transkript.html", hata="⚠️ Sunucuda şu anda başka bir transkript işlemi var. Lütfen 5 dakika sonra tekrar deneyiniz.")

    try:
        dosya = request.files.get('audio')
        if dosya:
            dosya_yolu = os.path.join('uploads', dosya.filename)
            dosya.save(dosya_yolu)

            # Süre kontrolü
            sure = get_audio_duration(dosya_yolu)
            if sure > 600:
                os.remove(dosya_yolu)
                return render_template("transkript.html", hata="⚠️ Dosya 10 dakikadan uzun. Lütfen daha kısa bir dosya yükleyin.")

            # Transkript işlemi
            metin = transkripte_cevir(dosya_yolu)
            docx_path = os.path.join("çıktılar", os.path.splitext(dosya.filename)[0] + ".docx")
            os.makedirs("çıktılar", exist_ok=True)
            doc = Document()
            doc.add_paragraph(metin)
            doc.save(docx_path)

            return send_file(docx_path, as_attachment=True)

    except Exception as e:
        return render_template("transkript.html", hata=f"⚠️ Hata oluştu: {str(e)}")
    finally:
        transkript_kilit.release()

@app.route('/video/create', methods=['POST'])
def create_video():
    # Excel dosyasını al
    file = request.files.get('excel')
    if not file:
        return "Dosya yüklenmedi", 400

    # Dosyayı kaydet
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Excel dosyasını oku
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        return f"Excel okunamadı: {e}", 500

    if df.shape[1] < 2:
        return "En az iki sütun içeren bir tablo yükleyin.", 400

    # İlk sütunu zaman ekseni olarak ayarla
    df.set_index(df.columns[0], inplace=True)

    # Video başlığını al
    title = request.form.get("title", "Yarışan Veriler Video")  # Eğer başlık girilmemişse varsayılan olarak "Yarışan Veriler Video" olacak

    # Video oluşturulacak dosya yolu
    unique_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'video_{unique_id}.mp4')

    # Bar chart race video oluştur
    bcr.bar_chart_race(
        df=df,
        filename=output_path,
        orientation='h',
        sort='desc',
        n_bars=10,
        fixed_order=False,
        fixed_max=True,
        steps_per_period=20,
        period_length=500,
        title=title,  # Dinamik başlık burada
        bar_size=.95,
    )

    # İşlem sonrası dosyaları sil
    @after_this_request
    def remove_files(response):
        try:
            os.remove(filepath)
            os.remove(output_path)
        except Exception as e:
            print(f"Hata dosya silerken: {e}")
        return response

    return send_file(output_path, as_attachment=True)

@app.route('/pdf/merge', methods=['POST'])
def merge_pdfs():
    uploaded_files = request.files.getlist('pdfs')
    order = request.form.getlist('order[]')

    if not uploaded_files or not order:
        return "Dosyalar veya sıralama eksik.", 400

    try:
        ordered_files = [uploaded_files[int(i)] for i in order]
    except (ValueError, IndexError):
        return "Geçersiz sıralama verisi.", 400

    temp_paths = []
    for file in ordered_files:
        temp_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(temp_path)
        temp_paths.append(temp_path)

    output_path = os.path.join(UPLOAD_FOLDER, f"merged_{uuid4().hex}.pdf")
    birlestir_pdf_listesi(temp_paths, output_path)

    # Geçici dosyaları temizle
    for path in temp_paths:
        os.remove(path)

    return send_file(output_path, as_attachment=True)

@app.route("/pdf/split", methods=["POST"])
def pdf_split():
    f = request.files["pdf"]
    bas = int(request.form["start"])
    bit = int(request.form["end"])
    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, f.filename)
    f.save(path)
    output = os.path.join(tempdir, "split.pdf")
    bol_pdf(path, bas, bit, output)
    return send_file(output, as_attachment=True)

@app.route('/pdf/rotate', methods=['POST'])
def rotate_pdf():
    file = request.files['pdf']
    angle = int(request.form['angle'])
    pages_input = request.form['pages']  # örn: "1-3"

    try:
        start, end = map(int, pages_input.strip().split('-'))
    except ValueError:
        return "Sayfa aralığı formatı hatalı. Örn: 1-3", 400

    reader = PdfReader(file)
    writer = PdfWriter()
    num_pages = len(reader.pages)

    if not (1 <= start <= end <= num_pages):
        return f"Geçersiz sayfa aralığı. PDF {num_pages} sayfadan oluşuyor.", 400

    for i, page in enumerate(reader.pages):
        if start - 1 <= i <= end - 1:
            page = page.rotate(angle)
        writer.add_page(page)

    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return send_file(output_stream, as_attachment=True, download_name='rotated.pdf')

@app.route("/pdf/compress", methods=["POST"])
def pdf_compress():
    f = request.files["pdf"]
    kalite = request.form["quality"]
    kalite_map = {
        "ekstrem": "/screen", "düşük": "/ebook",
        "orta": "/printer", "yüksek": "/prepress"
    }
    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, f.filename)
    f.save(path)
    output = os.path.join(tempdir, "compressed.pdf")
    sikistir_pdf(path, output, kalite_map.get(kalite, "/ebook"))
    return send_file(output, as_attachment=True)

@app.route("/pdf/pdf2word", methods=["POST"])
def pdf2word():
    f = request.files["pdf"]
    tempdir = tempfile.mkdtemp()
    input_path = os.path.join(tempdir, f.filename)
    output_path = os.path.join(tempdir, "converted.docx")
    f.save(input_path)
    pdf_to_word(input_path, output_path)
    return send_file(output_path, as_attachment=True)

@app.route('/pdf/reorder', methods=['GET', 'POST'])
def reorder_pdf():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        if not pdf_file:
            return "Dosya yüklenmedi", 400

        filename = secure_filename(pdf_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(filepath)

        doc = fitz.open(filepath)
        image_filenames = []

        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=100)
            img_name = f"{uuid4().hex}.png"
            img_path = os.path.join(IMAGE_FOLDER, img_name)
            pix.save(img_path)
            image_filenames.append((img_name, i))  # (filename, page_index)

        doc.close()
        return render_template('reorder.html', images=image_filenames, pdf_path=filepath)

    return render_template('reorder.html', images=None)
    
@app.route('/pdf/reorder/submit', methods=['POST'])
def submit_reorder():
    order = request.form.getlist('order[]')
    original_pdf_path = request.form['pdf_path']

    # Geçersiz veya boş değerleri filtrele + kontrol et
    try:
        page_indices = [int(i) for i in order if i.strip().isdigit()]
    except ValueError:
        return "Geçersiz sayfa sıralaması gönderildi", 400

    # Dosya okuma ve yeniden yazma
    reader = PdfReader(original_pdf_path)
    writer = PdfWriter()

    for page_index in page_indices:
        if 0 <= page_index < len(reader.pages):
            writer.add_page(reader.pages[page_index])
        else:
            return f"Geçersiz sayfa indexi: {page_index}", 400

    output_path = os.path.join(UPLOAD_FOLDER, f"reordered_{uuid4().hex}.pdf")
    with open(output_path, 'wb') as f:
        writer.write(f)

    # Geçici dosyaları temizle
    try:
        os.remove(original_pdf_path)
        for filename in os.listdir(IMAGE_FOLDER):
            os.remove(os.path.join(IMAGE_FOLDER, filename))
    except Exception as e:
        print("Silme hatası:", e)

    return send_file(output_path, as_attachment=True)

@app.route("/youtube/download", methods=["POST"])
def youtube_download():
    url = request.form.get("url")
    secenek = request.form.get("secenek", "video")  # "video" veya "audio"

    if not url:
        return jsonify({"error": "URL gerekli."}), 400

    dosya_yolu = indir_video(url, secenek)

    if not dosya_yolu or not os.path.exists(dosya_yolu):
        return jsonify({"error": "İndirme başarısız oldu veya dosya bulunamadı."}), 500

    dosya_adi = os.path.basename(dosya_yolu)
    safe_filename = quote(dosya_adi)

    @after_this_request
    def temizle(response):
        try:
            os.remove(dosya_yolu)
            print(f"✔ Dosya silindi: {dosya_yolu}")
        except Exception as e:
            print(f"✘ Dosya silinemedi: {e}")
        return response

    return send_file(
        dosya_yolu,
        as_attachment=True,
        download_name=dosya_adi,
        mimetype=None,
        conditional=True
    )

@app.route("/video/instagram", methods=["POST"])
def instagram_download():
    url = request.form.get("url")
    if not url:
        return "URL belirtilmedi."

    dosya_yolu = indir_instagram(url)

    if dosya_yolu and os.path.exists(dosya_yolu):

        @after_this_request
        def temizle(response):
            try:
                os.remove(dosya_yolu)
            except Exception as e:
                print(f"Dosya silinemedi: {e}")
            return response

        return send_file(
            dosya_yolu,
            as_attachment=True,
            mimetype="video/mp4"
        )

    return "İndirme başarısız oldu."

@app.route("/video/twitter", methods=["POST"])
def twitter_download():
    url = request.form.get("url")
    if not url:
        return "URL belirtilmedi."

    dosya_yolu = indir_twitter(url)
    if dosya_yolu and os.path.exists(dosya_yolu):

        @after_this_request
        def temizle(response):
            try:
                os.remove(dosya_yolu)
            except Exception as e:
                print(f"Dosya silinemedi: {e}")
            return response

        return send_file(
            dosya_yolu,
            as_attachment=True,
            mimetype="video/mp4"
        )

    return "İndirme başarısız oldu."

@app.route('/split-audio', methods=['POST'])
def split_audio_route():
    if 'audio_file' not in request.files:
        return "No file part", 400

    file = request.files['audio_file']
    if file.filename == '':
        return "No selected file", 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    parts = split_audio(filepath, chunk_length_minutes=10, output_dir="static/clips")

    return render_template('transkript.html', audio_parts=parts)

@app.route("/viz/kumeleme", methods=["POST"])
def viz_kumeleme():
    file = request.files["excel"]
    k = int(request.form.get("k", 3))  # varsayılan 3 küme
    try:
        output_url = create_kumeleme_html(file, n_clusters=k)
        return jsonify({"success": True, "url": output_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/timeline", methods=["POST"])
def timeline():
    if "excel" not in request.files:
        return "Dosya bulunamadı", 400

    file = request.files["excel"]

    try:
        output_path = create_timeline_video(file)
        return jsonify({"success": True, "video_path": output_path})
    except Exception as e:
        return str(e), 500

@app.route('/viz/wordcloud', methods=['POST'])
def wordcloud():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify(success=False, error="Metin boş olamaz.")

        output_path = generate_wordcloud_from_text(text)

        return jsonify(success=True, url=f"/{output_path}")
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/upload-animation', methods=['POST'])
def upload_animation():
    chart_type = request.form.get('chartType')
    file = request.files['file']
    df = pd.read_excel(file)

    if chart_type == 'line':
        path = create_animated_line_chart(df)
    elif chart_type == 'bar':
        path = create_animated_bar_chart(df)
    elif chart_type == 'pie':
        path = create_animated_pie_chart(df)
    elif chart_type == 'radar':
        path = create_animated_radar_chart(df)
    elif chart_type == 'timeseries':
        path = create_animated_timeseries(df)
    else:
        return "Geçersiz grafik tipi", 400

    return jsonify({"path": "/" + path})

if __name__ == "__main__":
    app.run(debug=True)
