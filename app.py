from flask import Flask, render_template, request, send_file, redirect, url_for
import os, tempfile
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from uuid import uuid4
from PyPDF2 import PdfReader, PdfWriter
from pdf_tools import (
    birlestir_pdf_listesi, bol_pdf, dondur_pdf, sikistir_pdf,
    pdf_to_word
)

app = Flask(__name__)
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

@app.route("/transkript")
def transkript():
    return render_template("transkript.html")

@app.route("/pdf/merge", methods=["POST"])
def pdf_merge():
    files = request.files.getlist("pdfs")
    tempdir = tempfile.mkdtemp()
    paths = [os.path.join(tempdir, f.filename) for f in files]
    for f, p in zip(files, paths):
        f.save(p)
    output = os.path.join(tempdir, "merged.pdf")
    birlestir_pdf_listesi(paths, output)
    return send_file(output, as_attachment=True)

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

@app.route("/pdf/rotate", methods=["POST"])
def pdf_rotate():
    f = request.files["pdf"]
    sayfa = int(request.form["page"])
    aci = int(request.form["angle"])
    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, f.filename)
    f.save(path)
    output = os.path.join(tempdir, "rotated.pdf")
    dondur_pdf(path, sayfa, aci, output)
    return send_file(output, as_attachment=True)

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

    reader = PdfReader(original_pdf_path)
    writer = PdfWriter()

    for index in order:
        page_index = int(index)
        writer.add_page(reader.pages[page_index])

    output_path = os.path.join(UPLOAD_FOLDER, f"reordered_{uuid4().hex}.pdf")
    with open(output_path, 'wb') as f:
        writer.write(f)

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
