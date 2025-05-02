import whisper

def transkripte_cevir(dosya_adi, dil="tr"):
    model = whisper.load_model("small")
    sonuc = model.transcribe(dosya_adi, language=dil)
    return sonuc["text"]
