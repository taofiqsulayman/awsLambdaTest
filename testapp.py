import fitz  # PyMuPDF
import pymupdf4llm
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageOps
from io import BytesIO
from multiprocessing import Pool, cpu_count
import numpy as np
import pandas as pd  # Import pandas for CSV, XLSX, and TSV reading
from spire.doc import Document
import streamlit as st
import os


# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text_from_pages_single_threaded(pdf_path):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    num_pages = doc.page_count
    for i in range(num_pages):
        page = doc.load_page(i)
        check_text = page.get_text("text")
        text = pymupdf4llm.to_markdown(pdf_path, pages=[i])
        if not check_text.strip():
            text = extract_text_with_paddleocr(pdf_path, pages=[i])
        extracted_text += text
    return extracted_text

def extract_text_from_page_indices(pdf_path, indices):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    for i in indices:
        page = doc.load_page(i)
        check_text = page.get_text("text")
        text = pymupdf4llm.to_markdown(pdf_path, pages=[i])
        if not check_text.strip():
            text = extract_text_with_paddleocr(pdf_path, pages=[i])
        extracted_text += text
    return extracted_text

def enhance_image(image):
    """Enhance the image quality to improve OCR accuracy."""
    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Apply sharpening
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    # Apply contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    # Apply brightness enhancement
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.5)

    return image

def extract_text_with_paddleocr(pdf_path, pages=None):
    """Extract text from PDF using OCR (PaddleOCR) and convert it to Markdown."""
    extracted_text = ""
    doc = fitz.open(pdf_path)
    page_range = range(doc.page_count) if pages is None else pages

    for i in page_range:
        page = doc.load_page(i)
        pix = page.get_pixmap()  # Get image of the page
        image = Image.open(BytesIO(pix.tobytes(output="png")))

        # Enhance the image for better OCR results
        enhanced_image = enhance_image(image)

        # Run OCR on the enhanced image
        result = ocr.ocr(np.array(enhanced_image), slice=False, cls=True, det=True, rec=True)

        # Extract recognized text and format it as Markdown
        text = "\n".join([line[-1][0] for line in result[0]])
        # markdown_text = text_to_markdown(text)  # Convert OCR result to Markdown

        extracted_text += text
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

def text_to_markdown(text):
    markdown_text = ""
    for line in text.split("\n"):
        markdown_text += f"{line}\n\n"
    return markdown_text

def convert_table_to_markdown(df):
    """Convert pandas DataFrame to Markdown table."""
    return df.to_markdown(index=False) + "\n\n"

def process_csv_xlsx_tsv(file_path):
    """Process CSV, XLSX, and TSV files and convert to Markdown."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext == '.tsv':
        df = pd.read_csv(file_path, sep='\t')
    elif ext == '.xlsx':
        df = pd.read_excel(file_path)
    
    return convert_table_to_markdown(df)

def process_image(file_path):
    """Process image files using OCR and convert to Markdown."""
    image = Image.open(file_path)

    # Enhance the image for better OCR results
    enhanced_image = enhance_image(image)

    # Run OCR on the enhanced image
    result = ocr.ocr(np.array(enhanced_image), slice=False)

    # Extract recognized text and format it as Markdown
    text = "\n".join([line[-1][0] for line in result[0]]) 
    return text_to_markdown(text)

def process_docx(file_path):
    document = Document()
    document.LoadFromFile(file_path)
    return document.GetText()


def process_file(file_path):
    if file_path.endswith('.pdf'):
        extracted_text = process_pdf(file_path)
    elif file_path.endswith('.docx') or file_path.endswith('.doc'):
        extracted_text = process_docx(file_path)
    elif file_path.endswith('.csv') or file_path.endswith('.tsv') or file_path.endswith('.xlsx'):
        extracted_text = process_csv_xlsx_tsv(file_path)
    elif file_path.endswith('.png') or file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        extracted_text = process_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    return extracted_text


#  streamlit app

# Streamlit App
st.title("Multiple File Text Extraction and Markdown Conversion")

uploaded_files = st.file_uploader("Choose files", type=['pdf', 'csv', 'xlsx', 'tsv', 'png', 'jpg', 'jpeg', 'docx', 'doc'], accept_multiple_files=True)

if uploaded_files is not None:
    for uploaded_file in uploaded_files:
        st.write(f"Processing file: {uploaded_file.name}")
        
        try:
            markdown_output = process_file(uploaded_file)
            st.markdown(f"### Output for {uploaded_file.name}")
            st.markdown(markdown_output)
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")
