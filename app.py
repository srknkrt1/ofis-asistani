import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import os
import whisper
import yt_dlp
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from docx2pdf import convert
import pytesseract
from pdf2image import convert_from_path
from docx import Document

# ========== Fonksiyonlar ==========
#Transkript
def ses_transkript(dosya_adi, dil="tr"):
    model = whisper.load_model("small")
    sonuc = model.transcribe(dosya_adi, language=dil)
    # Yeni pencere
    pencere = tk.Toplevel()
    pencere.title("Transkript Sonucu")
    
    text_alani = tk.Text(pencere, wrap="word", height=20, width=80)
    text_alani.insert("1.0", sonuc["text"])
    text_alani.pack(padx=10, pady=10)

    def kaydet():
        cikti = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Belgesi", "*.docx")])
        if cikti:
            from docx import Document
            doc = Document()
            doc.add_paragraph(sonuc["text"])
            doc.save(cikti)
            messagebox.showinfo("Kaydedildi", f"Transkript Word dosyasına kaydedildi: {cikti}")

    tk.Button(pencere, text="Word'e Kaydet", command=kaydet).pack(pady=5)

#PDF Birleştirme
def pdf_birlestirme_arayuzu():
    liste = []

    def pdf_sec():
        dosyalar = filedialog.askopenfilenames(filetypes=[("PDF Dosyaları", "*.pdf")])
        for dosya in dosyalar:
            if dosya not in liste:
                liste.append(dosya)
                listekutusu.insert(tk.END, os.path.basename(dosya))

    def yukari():
        secili = listekutusu.curselection()
        if not secili or secili[0] == 0:
            return
        i = secili[0]
        liste[i-1], liste[i] = liste[i], liste[i-1]
        listekutusu.delete(0, tk.END)
        for item in liste:
            listekutusu.insert(tk.END, os.path.basename(item))
        listekutusu.select_set(i-1)

    def asagi():
        secili = listekutusu.curselection()
        if not secili or secili[0] == len(liste) - 1:
            return
        i = secili[0]
        liste[i+1], liste[i] = liste[i], liste[i+1]
        listekutusu.delete(0, tk.END)
        for item in liste:
            listekutusu.insert(tk.END, os.path.basename(item))
        listekutusu.select_set(i+1)

    def birlestir():
        if not liste:
            messagebox.showerror("Hata", "Birleştirilecek PDF seçilmedi.")
            return
        cikti = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Dosyası", "*.pdf")])
        if cikti:
            pdf_birlestir(liste, cikti)
            pencere.destroy()

    pencere = tk.Toplevel()
    pencere.title("PDF Birleştirici")

    listekutusu = tk.Listbox(pencere, width=60, height=10)
    listekutusu.pack(pady=10)

    tk.Button(pencere, text="PDF Ekle", command=pdf_sec).pack()
    tk.Button(pencere, text="Yukarı Taşı", command=yukari).pack()
    tk.Button(pencere, text="Aşağı Taşı", command=asagi).pack()
    tk.Button(pencere, text="Birleştir", command=birlestir).pack(pady=10)

#PDF Bölme
def pdf_bol(dosya_adi, bas_sayfa, bit_sayfa, cikti_adi="bolunmus.pdf"):
    reader = PdfReader(dosya_adi)
    writer = PdfWriter()
    for i in range(bas_sayfa - 1, bit_sayfa):
        writer.add_page(reader.pages[i])
    with open(cikti_adi, "wb") as f:
        writer.write(f)
    messagebox.showinfo("Başarılı", f"Bölme tamamlandı: {cikti_adi}")

#PDF Döndürme
def pdf_dondur(giris_pdf, sayfa_no, aci, cikti_pdf="dondurulmus.pdf"):
    reader = PdfReader(giris_pdf)
    writer = PdfWriter()
    for i, sayfa in enumerate(reader.pages):
        if i == sayfa_no - 1:
            sayfa.rotate(aci)
        writer.add_page(sayfa)
    with open(cikti_pdf, "wb") as f:
        writer.write(f)
    messagebox.showinfo("Başarılı", f"{sayfa_no}. sayfa {aci} derece döndürüldü.")

def ghostscript_pdf_sikistir(giris_pdf, cikis_pdf="Merged.pdf", kalite="ekstrem"):
    kalite_secenekleri = {
        "ekstrem": "/screen",    
        "düşük": "/ebook",       
        "orta": "/printer",      
        "yüksek": "/prepress",   
    }
    gs_path = r"C:\\Program Files\\gs\\gs10.05.1\\bin\\gswin64c.exe"
    subprocess.call([ 
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={kalite_secenekleri.get(kalite, '/ebook')}",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={cikis_pdf}",
        giris_pdf
    ])
    messagebox.showinfo("Başarılı", f"Sıkıştırma tamamlandı: {cikis_pdf}")

def pdf_birlestir(dosya_listesi, cikti_dosyasi):
    merger = PdfMerger()
    for pdf in dosya_listesi:
        merger.append(pdf)
    merger.write(cikti_dosyasi)
    merger.close()
    messagebox.showinfo("Başarılı", f"PDF'ler birleştirildi: {cikti_dosyasi}")

#PDFtoWord
def pdf_to_word(giris_pdf, cikti_docx="donusmus.docx"):
    cv = Converter(giris_pdf)
    cv.convert(cikti_docx)
    cv.close()
    messagebox.showinfo("Başarılı", f"PDF, Word'e dönüştürüldü: {cikti_docx}")

def word_to_pdf():
    docx_path = filedialog.askopenfilename(filetypes=[("Word dosyası", "*.docx")])
    if docx_path:
        output_path = os.path.splitext(docx_path)[0] + ".pdf"
        convert(docx_path, output_path)
        messagebox.showinfo("Başarılı", f"Word, PDF'ye dönüştürüldü: {output_path}")
#PDFtoWord(OCR)
def pdf_ocr_donustur(pdf_dosya, cikti_dosya="ocr_metni.docx"):
    # Tesseract yolu manuel olarak ayarlanabilir (gerekirse)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    sayfalar = convert_from_path(pdf_dosya)
    doc = Document()
    
    for i, sayfa in enumerate(sayfalar, 1):
        metin = pytesseract.image_to_string(sayfa, lang='tur+eng')
        doc.add_paragraph(f"--- Sayfa {i} ---")
        doc.add_paragraph(metin)
        doc.add_page_break()  # Sayfa sonu

    doc.save(cikti_dosya)
    messagebox.showinfo("Başarılı", f"OCR tamamlandı, Word dosyası: {cikti_dosya}")
#YoutubeDownloader
def youtube_indir_gui():
    pencere = tk.Toplevel()
    pencere.title("YouTube Downloader")

    tk.Label(pencere, text="YouTube URL:").pack()
    url_giris = tk.Entry(pencere, width=60)
    url_giris.pack(pady=5)

    secenek = tk.StringVar(value="video")

    tk.Radiobutton(pencere, text="Video (.mp4)", variable=secenek, value="video").pack(anchor="w")
    tk.Radiobutton(pencere, text="Ses (.mp3)", variable=secenek, value="audio").pack(anchor="w")
    tk.Radiobutton(pencere, text="Oynatma Listesi (video)", variable=secenek, value="playlist").pack(anchor="w")

    def indir():
        url = url_giris.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen geçerli bir URL girin.")
            return

        ydl_opts = {}

        if secenek.get() == "video":
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'merge_output_format': 'mp4',
                'outtmpl': '%(title)s.%(ext)s',
            }
        elif secenek.get() == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        elif secenek.get() == "playlist":
            ydl_opts = {
                'ignoreerrors': True,
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': '%(playlist)s/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Başarılı", "İndirme tamamlandı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İndirme başarısız: {e}")

    tk.Button(pencere, text="İndir", command=indir).pack(pady=10)

def instagram_indir_gui():
    pencere = tk.Toplevel()
    pencere.title("Instagram Video İndirici")

    tk.Label(pencere, text="Instagram URL:").pack()
    url_giris = tk.Entry(pencere, width=60)
    url_giris.pack(pady=5)

    def indir():
        url = url_giris.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen geçerli bir URL girin.")
            return

        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'mp4',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Başarılı", "İndirme tamamlandı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İndirme başarısız: {e}")

    tk.Button(pencere, text="İndir", command=indir).pack(pady=10)

def twitter_indir_gui():
    pencere = tk.Toplevel()
    pencere.title("X (Twitter) Video İndirici")

    tk.Label(pencere, text="Tweet Video URL:").pack()
    url_giris = tk.Entry(pencere, width=60)
    url_giris.pack(pady=5)

    def indir():
        url = url_giris.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen geçerli bir URL girin.")
            return

        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'mp4',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Başarılı", "İndirme tamamlandı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İndirme başarısız: {e}")

    tk.Button(pencere, text="İndir", command=indir).pack(pady=10)


# ========== GUI ==========

def dosya_sec():
    dosya = filedialog.askopenfilename()
    if dosya:
        secilen_dosya.set(dosya)

def pdf_liste_sec():
    dosyalar = filedialog.askopenfilenames(filetypes=[("PDF Dosyaları", "*.pdf")])
    if dosyalar:
        pdf_dosyalari.extend(dosyalar)
        messagebox.showinfo("Seçildi", f"{len(dosyalar)} PDF eklendi.")

def transkript_isle():
    if secilen_dosya.get():
        ses_transkript(secilen_dosya.get())

def pdf_to_word_isle():
    if secilen_dosya.get():
        pdf_to_word(secilen_dosya.get())

def ocr_to_word_isle():
    if secilen_dosya.get():
        pdf_ocr_donustur(secilen_dosya.get())

def pdf_bol_isle():
    if secilen_dosya.get():
        bas = simpledialog.askinteger("Başlangıç Sayfası", "Başlangıç sayfa numarası:")
        bit = simpledialog.askinteger("Bitiş Sayfası", "Bitiş sayfa numarası:")
        if bas and bit:
            pdf_bol(secilen_dosya.get(), bas, bit)

def pdf_dondur_isle():
    if not secilen_dosya.get():
        return

    pencere = tk.Toplevel()
    pencere.title("PDF Rotasyon")

    tk.Label(pencere, text="Sayfa Numarası:").pack()
    sayfa_giris = tk.Entry(pencere)
    sayfa_giris.pack()

    aci = [0]

    def dondur_btn():
        aci[0] = (aci[0] + 90) % 360
        aci_label.config(text=f"Açı: {aci[0]}°")

    aci_label = tk.Label(pencere, text="Açı: 0°")
    aci_label.pack()

    tk.Button(pencere, text="⟳ Döndür (90°)", command=dondur_btn).pack(pady=5)

    def uygula():
        try:
            sayfa = int(sayfa_giris.get())
            pdf_dondur(secilen_dosya.get(), sayfa, aci[0])
            pencere.destroy()
        except:
            messagebox.showerror("Hata", "Sayfa numarası geçersiz.")

    tk.Button(pencere, text="Uygula", command=uygula).pack(pady=10)

def pdf_sikistir_isle():
    if not secilen_dosya.get():
        return

    kalite_pencere = tk.Toplevel()
    kalite_pencere.title("Sıkıştırma Kalitesi Seçimi")

    kalite_var = tk.StringVar(value="orta")

    tk.Label(kalite_pencere, text="Kalite Seçin:").pack(pady=5)
    for kalite in ["ekstrem", "düşük", "orta", "yüksek"]:
        tk.Radiobutton(kalite_pencere, text=kalite.capitalize(), variable=kalite_var, value=kalite).pack(anchor="w")

    def uygula():
        kalite = kalite_var.get()
        ghostscript_pdf_sikistir(secilen_dosya.get(), kalite=kalite)
        kalite_pencere.destroy()

    tk.Button(kalite_pencere, text="Sıkıştır", command=uygula).pack(pady=10)

def pdf_birlestir_isle():
    if pdf_dosyalari:
        pdf_birlestir(pdf_dosyalari)

# Arayüz
pencere = tk.Tk()
pencere.title("Ofis Asistanı")

secilen_dosya = tk.StringVar()
pdf_dosyalari = []

tk.Label(pencere, text="Seçilen Dosya:").pack()
tk.Entry(pencere, textvariable=secilen_dosya, width=60).pack()
tk.Button(pencere, text="Gözat", command=dosya_sec).pack(pady=5)

tk.Label(pencere, text="İşlemler").pack(pady=10)

tk.Button(pencere, text="Transkript", command=transkript_isle).pack(fill="x")
tk.Button(pencere, text="PDF to Word", command=pdf_to_word_isle).pack(fill="x")
tk.Button(pencere, text="PDF to Word (OCR)", command=ocr_to_word_isle).pack(fill="x")
tk.Button(pencere, text="Word to PDF", command=word_to_pdf).pack(fill="x")
tk.Button(pencere, text="PDF Böl", command=pdf_bol_isle).pack(fill="x")
tk.Button(pencere, text="PDF Döndür", command=pdf_dondur_isle).pack(fill="x")
tk.Button(pencere, text="PDF Sıkıştır", command=pdf_sikistir_isle).pack(fill="x")
tk.Button(pencere, text="PDF Birleştir", command=pdf_birlestirme_arayuzu).pack(fill="x")
tk.Button(pencere, text="YouTube İndirme", command=youtube_indir_gui).pack(fill="x")
tk.Button(pencere, text="Instagram Video İndir", command=instagram_indir_gui).pack(fill="x")
tk.Button(pencere, text="X (Twitter) Video İndir", command=twitter_indir_gui).pack(fill="x")



pencere.mainloop()
