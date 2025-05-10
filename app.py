from flask import Flask, render_template, request
import pandas as pd
import bar_chart_race as bcr
import uuid
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/viz", methods=["GET", "POST"])
def viz():
    if request.method == "POST":
        # CSV dosyasını al
        csv_file = request.files.get("csv_file")
        if not csv_file:
            return "CSV dosyası yüklenmedi."

        # Geçici dosyaya kaydet
        file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.csv")
        csv_file.save(file_path)

        # CSV'den veri oku
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return f"CSV okuma hatası: {e}"

        # Zaman sütununu al
        time_column = request.form.get("time_column")
        if time_column not in df.columns:
            return f"'{time_column}' sütunu CSV'de bulunamadı."

        df[time_column] = df[time_column].astype(str)
        df.set_index(time_column, inplace=True)

        # Kategori adları ve renkler
        category_names = request.form.getlist("category_names")
        colors = request.form.getlist("colors")

        # Kategori sayısı kadar sütun kullan
        available_columns = df.columns[:len(category_names)]
        df = df[available_columns]

        # Sütun isimlerini kullanıcı tanımlı hale getir
        if category_names and len(category_names) == len(available_columns):
            df.columns = category_names

        # Veriyi sayısal hale getir
        df = df.apply(pd.to_numeric, errors="coerce")

        # Video çıktısı
        fig_id = str(uuid.uuid4())
        out_path = f"static/{fig_id}.mp4"

        try:
            bcr.bar_chart_race(
                df=df,
                filename=out_path,
                orientation='h',
                sort='desc',
                n_bars=len(df.columns),
                fixed_order=False,
                fixed_max=True,
                steps_per_period=20,
                period_length=1500,
                interpolate_period=False,
                bar_size=.95,
                period_label={'x': .99, 'y': .25, 'ha': 'right', 'va': 'center'},
                period_fmt='{x}',
                cmap=colors if all(colors) else 'dark12'
            )
        except Exception as e:
            return f"Grafik oluşturulamadı: {e}"

        return render_template("viz_result.html", video_path=out_path)

    return render_template("viz.html")

if __name__ == "__main__":
    app.run(debug=True)
