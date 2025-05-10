from flask import Flask, render_template, request, send_file
import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt
import uuid
import os

app = Flask(__name__)

@app.route("/viz", methods=["GET", "POST"])
def viz():
    if request.method == "POST":
        # Veri alma
        colors = request.form.getlist("colors")
        duration = int(request.form.get("duration", 10))
        data_dict = {}

        for key in request.form:
            if key.startswith("row_"):
                for val in request.form.getlist(key):
                    if val.strip():  # Boşlukları atla
                        if key not in data_dict:
                            data_dict[key] = []
                        data_dict[key].append(val.strip())

        # Veriyi DataFrame'e dönüştür
        data = pd.DataFrame(data_dict.values()).transpose()
        data.columns = request.form.getlist("colors")  # Kategori isimlerini renk input'larının adlarıyla eşleştir
        data.rename(columns={data.columns[0]: "Dönem"}, inplace=True)
        data.set_index("Dönem", inplace=True)

        # Dönem hatasını düzelt
        data.index.name = None
        data.index = pd.Index(data.index.astype(str))  # Dönemler string olsun
        data = data.apply(pd.to_numeric, errors='coerce')  # Sayıya çevir (NaN olabilecekler dahil)

        # Renkleri ayarla
        fig_id = str(uuid.uuid4())
        out_path = f"static/{fig_id}.mp4"
        try:
            bcr.bar_chart_race(
                df=data,
                filename=out_path,
                orientation='h',
                sort='desc',
                n_bars=len(data.columns),
                fixed_order=False,
                fixed_max=True,
                steps_per_period=20,
                period_length=duration * 1000 // len(data),
                interpolate_period=False,
                bar_size=.95,
                period_label={'x': .99, 'y': .25, 'ha': 'right', 'va': 'center'},
                period_fmt='{x}',
                cmap=colors if all(colors) else 'dark12'
            )
        except Exception as e:
            print("Grafik üretim hatası:", e)
            return "Grafik oluşturulamadı."

        return render_template("viz_result.html", video_path=out_path)

    return render_template("viz.html")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
