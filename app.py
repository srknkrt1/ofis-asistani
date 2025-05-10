from flask import Flask, render_template, request
import pandas as pd
import bar_chart_race as bcr
import uuid
import os

app = Flask(__name__)
os.makedirs("static", exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("viz.html")

@app.route("/viz", methods=["POST"])
def viz():
    # Tablodan gelen başlıkları al
    headers = []
    colors = []
    i = 0
    while True:
        header = request.form.get(f"header_{i}")
        if not header:
            break
        headers.append(header)
        color = request.form.get(f"color_{i}")
        if color:
            colors.append(color)
        i += 1

    # Veri satırlarını oku
    data = []
    row_index = 0
    while True:
        row = []
        empty_row = True
        for col_index in range(len(headers)):
            val = request.form.get(f"row_{row_index}_{col_index}")
            if val:
                empty_row = False
            row.append(val.strip() if val else '')
        if empty_row:
            break
        data.append(row)
        row_index += 1

    if not data:
        return "Veri girişi yapılmadı."

    df = pd.DataFrame(data, columns=headers)
    df.set_index(headers[0], inplace=True)
    df = df.apply(pd.to_numeric, errors="coerce")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join("static", filename)

    try:
        bcr.bar_chart_race(
            df=df,
            filename=filepath,
            orientation='h',
            sort='desc',
            n_bars=min(10, len(df.columns)),
            fixed_order=False,
            fixed_max=True,
            steps_per_period=20,
            period_length=1500,
            interpolate_period=False,
            bar_size=.95,
            period_label={'x': .99, 'y': .25, 'ha': 'right', 'va': 'center'},
            period_fmt='{x}',
            cmap=colors if len(colors) == len(df.columns) else 'dark12'
        )
    except Exception as e:
        return f"Hata oluştu: {e}"

    return f"""
    <div style='text-align:center; margin-top:40px;'>
        <h3>Grafiğiniz Oluşturuldu 🎉</h3>
        <video width='720' height='480' controls autoplay>
            <source src='/static/{filename}' type='video/mp4'>
        </video>
        <br><br>
        <a href="/">🔙 Yeni Grafik Oluştur</a>
    </div>
    """

if __name__ == "__main__":
    app.run(debug=True)
