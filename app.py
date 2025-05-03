from flask import Flask, render_template, request, send_file, redirect, url_for
import os, tempfile
import fitz  # PyMuPDF
import uuid
from pdf_tools import (
    birlestir_pdf_listesi, bol_pdf, dondur_pdf, sikistir_pdf,
    pdf_to_word
)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

@app.route('/')
def index():
    return redirect(url_for('reorder_pdf'))

@app.route('/reorder', methods=['GET', 'POST'])
def reorder_pdf():
    if request.method == 'POST':
        file = request.files['pdf']
        if file.filename.endswith('.pdf'):
            uid = str(uuid.uuid4())
            filepath = os.path.join(UPLOAD_FOLDER, uid + '.pdf')
            file.save(filepath)

            # Sayfa sayısını kontrol et
            doc = fitz.open(filepath)
            total_pages = len(doc)
            doc.close()

            return render_template('reorder.html', file=uid + '.pdf', total=total_pages)

    return '''
        <h2>PDF Sayfa Sıralayıcı</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="pdf" accept=".pdf" required>
            <button type="submit">Yükle</button>
        </form>
    '''

@app.route('/save_order', methods=['POST'])
def save_order():
    data = request.json
    filename = data['filename']
    new_order = data['order']  # ["0", "2", "1", ...]
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    doc = fitz.open(filepath)
    new_doc = fitz.open()

    for i in new_order:
        new_doc.insert_pdf(doc, from_page=int(i), to_page=int(i))

    output_path = os.path.join(UPLOAD_FOLDER, 'reordered_' + filename)
    new_doc.save(output_path)

    return {'download_url': '/download/' + 'reordered_' + filename}

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
