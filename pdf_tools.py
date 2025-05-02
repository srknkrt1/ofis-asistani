from PyPDF2 import PdfMerger
import os

def birlestir_pdf_listesi(pdf_filepaths, cikti_yolu):
    merger = PdfMerger()
    for path in pdf_filepaths:
        merger.append(path)
    merger.write(cikti_yolu)
    merger.close()
