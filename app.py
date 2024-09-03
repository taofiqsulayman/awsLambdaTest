import streamlit as st
import os
from PIL import Image
import fitz
import pytesseract
from io import BytesIO
from multiprocessing import Pool, cpu_count
from spire.doc import Document
import csv
import cv2
import numpy as np
import re

# pytesseract.pytesseract.tesseract_cmd = os.environ["LAMBDA_TASK_ROOT"] + "/bin/tesseract"
# os.environ['TESSDATA_PREFIX'] = os.environ["LAMBDA_TASK_ROOT"] + "/tesseract/share/tessdata"
# os.environ['LD_LIBRARY_PATH'] = os.environ["LAMBDA_TASK_ROOT"] + "/lib"

def process_docx(file_path):
    document = Document()
    document.LoadFromFile(file_path)
    return document.GetText()

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    dilation = cv2.dilate(thresh, rect_kernel, iterations=1)
    return gray, dilation

def extract_text_with_tesseract(image):
    gray, dilation = preprocess_image(image)
    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    extracted_text = ""
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cropped = gray[y:y + h, x:x + w]
        text = pytesseract.image_to_string(cropped)
        extracted_text += text + "\n"
    return extracted_text

def post_process_text(text):
    # text = re.sub(r'\s+', ' ', text).strip()
    # text = text.replace('0', 'O').replace('1', 'I').replace('5', 'S')
    common_words = ['the', 'and', 'of', 'to', 'in', 'is', 'it']
    for word in common_words:
        text = re.sub(r'\b' + word + r'\b', word, text, flags=re.IGNORECASE)
    return text

def extract_text_from_page(page):
    text = page.get_text("text")
    if not text.strip():
        pix = page.get_pixmap()
        img = Image.open(BytesIO(pix.tobytes()))
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        text = extract_text_with_tesseract(img_cv)
    return post_process_text(text)

def extract_text_from_pages_single_threaded(pdf_path):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    num_pages = doc.page_count
    for i in range(num_pages):
        page = doc.load_page(i)
        extracted_text += extract_text_from_page(page)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text

def extract_text_from_page_indices(pdf_path, indices):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    for i in indices:
        page = doc.load_page(i)
        extracted_text += extract_text_from_page(page)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text

def parallel_text_extraction(pdf_path, num_pages):
    cpu = cpu_count()
    seg_size = int(num_pages / cpu + 1)
    indices = [range(i * seg_size, min((i + 1) * seg_size, num_pages)) for i in range(cpu)]
    with Pool() as pool:
        results = pool.starmap(extract_text_from_page_indices, [(pdf_path, idx) for idx in indices])
    combined_text = "".join(results)
    return combined_text

def process_pdf(file_path):
    doc = fitz.open(file_path)
    num_pages = doc.page_count
    if num_pages < 10:
        extracted_text = extract_text_from_pages_single_threaded(file_path)
    else:
        extracted_text = parallel_text_extraction(file_path, num_pages)
    return extracted_text

def process_csv(csv_path):
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        return "\n".join([",".join(row) for row in reader])

# Streamlit UI
st.title("Document Text Extraction App")

uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'docx', 'csv', 'doc'])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        with open("uploaded.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        extracted_text = process_pdf("uploaded.pdf")
        st.text_area("Extracted Text", extracted_text, height=400)

    elif file_extension == 'docx':
        with open("uploaded.docx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        extracted_text = process_docx("uploaded.docx")
        st.text_area("Extracted Text", extracted_text, height=400)

    elif file_extension == 'csv':
        with open("uploaded.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        extracted_text = process_csv("uploaded.csv")
        st.text_area("Extracted Text", extracted_text, height=400)

    else:
        st.error("Unsupported file type")
