from flask import Flask, render_template

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

if __name__ == "__main__":
    app.run(debug=True)
