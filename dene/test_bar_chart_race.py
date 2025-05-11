import bar_chart_race as bcr
import pandas as pd
import uuid
import matplotlib.pyplot as plt
import matplotlib.animation as animation

plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg'  # Buradaki yolu `which ffmpeg` komutu ile bulduğunuz yol ile değiştirin.

import matplotlib
matplotlib.use("Agg")

# Test veri oluşturun
data = {
    'Week': ['Week 1', 'Week 2', 'Week 3'],
    'Team A': [5, 6, 7],
    'Team B': [4, 5, 6],
    'Team C': [3, 4, 5]
}
df = pd.DataFrame(data)

# Sayısal olmayan değerleri 'NaN' olarak işaretle ve ardından sıfır ile doldur
df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

# Video oluşturulacak dosya adı
video_filename = f"test_video_{uuid.uuid4().hex}.mp4"
output_path = "/root/ofis-asistani/test_video.mp4"

# Bar chart race grafiği oluşturun
bcr.bar_chart_race(
    df=df,
    filename=output_path,
    orientation='h',
    sort='desc',
    n_bars=3,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    period_length=500,
    interpolate_period=False,
    title='Puan Yarışı',
    bar_size=.95,
    cmap='dark12',
    filter_column_colors=True,
    scale='linear',
)

print(f"Video oluşturuldu: {output_path}")
