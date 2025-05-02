from flask import Flask, render_template, request, send_file
from pdf_tools import birlestir_pdf_listesi
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

if __name__ == "__main__":
    app.run(debug=True)
