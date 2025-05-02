from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pdf2docx import Converter
from pdf2image import convert_from_path
from docx import Document
import pytesseract
import subprocess

def birlestir_pdf_listesi(pdf_paths, output_path):
    merger = PdfMerger()
    for path in pdf_paths:
        merger.append(path)
    merger.write(output_path)
    merger.close()

def bol_pdf(pdf_path, start, end, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])
    with open(output_path, "wb") as f:
        writer.write(f)

def dondur_pdf(pdf_path, page_no, angle, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i == page_no - 1:
            page.rotate(angle)
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)

def sikistir_pdf(input_path, output_path, quality="/ebook"):
    gs = "/usr/bin/gs"
    subprocess.call([
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={quality}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path
    ])

def pdf_to_word(input_pdf, output_docx):
    cv = Converter(input_pdf)
    cv.convert(output_docx)
    cv.close()

