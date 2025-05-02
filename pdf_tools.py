from PyPDF2 import PdfMerger, PdfReader
import os
import subprocess

def birlestir_pdf_listesi(pdf_filepaths, cikti_yolu):
    merger = PdfMerger()
    for path in pdf_filepaths:
        merger.append(path)
    merger.write(cikti_yolu)
    merger.close()
    
def bol_pdf(giris_pdf, bas_sayfa, bit_sayfa, cikti_pdf):
    reader = PdfReader(giris_pdf)
    writer = PdfWriter()
    for i in range(bas_sayfa - 1, bit_sayfa):
        writer.add_page(reader.pages[i])
    with open(cikti_pdf, "wb") as f:
        writer.write(f)

def dondur_pdf(giris_pdf, sayfa_no, aci, cikti_pdf):
    reader = PdfReader(giris_pdf)
    writer = PdfWriter()
    for i, sayfa in enumerate(reader.pages):
        if i == sayfa_no - 1:
            sayfa.rotate(aci)
        writer.add_page(sayfa)
    with open(cikti_pdf, "wb") as f:
        writer.write(f)

def sikistir_pdf(giris_pdf, cikti_pdf, kalite="/ebook"):
    gs_path = "/usr/bin/gs"  # Render sunucusunda Ghostscript varsa
    subprocess.call([
        gs_path, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={kalite}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={cikti_pdf}", giris_pdf
    ])
