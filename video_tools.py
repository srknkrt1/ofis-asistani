from yt_dlp import YoutubeDL

def indir_video(url, secenek="video"):
    ydl_opts = {}
    if secenek == "video":
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
        }
    elif secenek == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif secenek == "playlist":
        ydl_opts = {
            'ignoreerrors': True,
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(playlist)s/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
        }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
