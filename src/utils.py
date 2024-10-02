from multiprocessing import Pool, cpu_count
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
from docx import Document 
import subprocess 
import os
import csv



pytesseract.pytesseract.tesseract_cmd = os.environ["LAMBDA_TASK_ROOT"] + "/bin/tesseract"
os.environ['TESSDATA_PREFIX'] = os.environ["LAMBDA_TASK_ROOT"] + "/tesseract/share/tessdata"
os.environ['LD_LIBRARY_PATH'] = os.environ["LAMBDA_TASK_ROOT"] + "/lib"


def process_word_docs(file_path):
    text = ""
    root_ext = os.path.splitext(file_path) 
    if root_ext[1] == ".doc":
        # Convert .doc to plain text using antiword
        result = subprocess.run(["antiword", file_path], capture_output=True, text=True)
        plain_text = result.stdout
    elif root_ext[1] == ".docx":
        # Load .docx file
        doc = Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        plain_text = "\n".join(full_text)
    else:
        raise ValueError("Unsupported file format. Please use a .doc or .docx file.")
    text = plain_text
    return text

def extract_text_from_pages_single_threaded(pdf_path):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    num_pages = doc.page_count
    for i in range(num_pages):
        page = doc.load_page(i)
        extracted_text += page.get_text("text")
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_path)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text

def extract_text_from_page_indices(pdf_path, indices):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    for i in indices:
        page = doc.load_page(i)
        extracted_text += page.get_text("text")
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_path, pages=[i])
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text

def extract_text_with_tesseract(pdf_path, pages=None):
    extracted_text = ""
    doc = fitz.open(pdf_path)
    page_range = range(doc.page_count) if pages is None else pages
    for i in page_range:
        page = doc.load_page(i)
        pix = page.get_pixmap()
        image = Image.open(BytesIO(pix.tobytes(output="png")))
        extracted_text += pytesseract.image_to_string(image)
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