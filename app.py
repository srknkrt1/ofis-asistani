from flask import Flask, render_template, request, send_file
from pdf_tools import birlestir_pdf_listesi
from pdf_tools import bol_pdf
from pdf_tools import dondur_pdf
from pdf_tools import sikistir_pdf
from video_tools import indir_video
import os, tempfile

app = Flask(__name__)

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
    input_paths = []
    for file in files:
        filepath = os.path.join(tempdir, file.filename)
        file.save(filepath)
        input_paths.append(filepath)
    output_path = os.path.join(tempdir, "merged.pdf")
    birlestir_pdf_listesi(input_paths, output_path)
    return send_file(output_path, as_attachment=True)

@app.route("/pdf/split", methods=["POST"])
def pdf_split():
    file = request.files["pdf"]
    bas = int(request.form["start"])
    bit = int(request.form["end"])

    tempdir = tempfile.mkdtemp()
    input_path = os.path.join(tempdir, file.filename)
    file.save(input_path)

    output_path = os.path.join(tempdir, "split.pdf")
    bol_pdf(input_path, bas, bit, output_path)

    return send_file(output_path, as_attachment=True)

@app.route("/pdf/rotate", methods=["POST"])
def pdf_rotate():
    file = request.files["pdf"]
    sayfa_no = int(request.form["page"])
    aci = int(request.form["angle"])

    tempdir = tempfile.mkdtemp()
    input_path = os.path.join(tempdir, file.filename)
    file.save(input_path)

    output_path = os.path.join(tempdir, "rotated.pdf")
    dondur_pdf(input_path, sayfa_no, aci, output_path)

    return send_file(output_path, as_attachment=True)

@app.route("/pdf/compress", methods=["POST"])
def pdf_compress():
    file = request.files["pdf"]
    kalite = request.form["quality"]

    tempdir = tempfile.mkdtemp()
    input_path = os.path.join(tempdir, file.filename)
    output_path = os.path.join(tempdir, "compressed.pdf")
    file.save(input_path)

    kalite_map = {
        "ekstrem": "/screen",
        "düşük": "/ebook",
        "orta": "/printer",
        "yüksek": "/prepress"
    }
    sikistir_pdf(input_path, output_path, kalite_map.get(kalite, "/ebook"))
    return send_file(output_path, as_attachment=True)

@app.route("/video/youtube", methods=["POST"])
def youtube_download():
    url = request.form["url"]
    secenek = request.form["type"]
    indir_video(url, secenek)
    return "İndirme başlatıldı. Sunucudan kontrol edin.<br><a href='/'>← Geri</a>"

if __name__ == "__main__":
    app.run(debug=True)
