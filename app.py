from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request
import os, tempfile
import subprocess
from docx import Document  # eksiktiyse eklenmeli
import fitz  # PyMuPDF
import threading
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
IMAGE_FOLDER = 'static/temp_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)


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

if __name__ == "__main__":
    app.run(debug=True)
