from flask import Flask, render_template, request
import pandas as pd
import bar_chart_race as bcr
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/animations'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/viz")
def viz_page():
    return render_template("viz.html")


@app.route("/viz/render", methods=["POST"])
def render_chart():
    # 1. Süreyi al
    duration = int(request.form.get("duration", 10))
    show_logos = request.form.get("show_logos", "no") == "yes"

    # 2. Excel varsa öncelikli
    if 'excel' in request.files and request.files['excel'].filename != '':
        excel_file = request.files['excel']
        filename = str(uuid.uuid4()) + ".xlsx"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        excel_file.save(file_path)
        df = pd.read_excel(file_path, index_col=0)
    else:
        # 3. Formdan tablo verisini al
        headers = request.form.getlist("headers[]")
        rows = []
        row_index = 0
        while True:
            row = request.form.getlist(f"row{row_index}[]")
            if not row:
                break
            rows.append(row)
            row_index += 1
        df = pd.DataFrame(rows, columns=headers)
        df.set_index(headers[0], inplace=True)
        df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    # 4. Bar Chart Race Oluştur
    filename = f"{uuid.uuid4().hex}.mp4"
    out_path = os.path.join(RESULT_FOLDER, filename)

    try:
        bcr.bar_chart_race(
            df=df,
            filename=out_path,
            orientation='h',
            sort='desc',
            n_bars=min(6, df.shape[1]),
            period_length=(duration * 1000) // len(df),
            steps_per_period=20,
            interpolate_period=True,
            title='Veri Yarışı',
            bar_size=.95
        )
    except Exception as e:
        return f"Bar Chart Race oluşturulamadı: {str(e)}"

    return render_template("viz_result.html", video_file=out_path)
