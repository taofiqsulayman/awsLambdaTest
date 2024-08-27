import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_file_path):
    """
    Extracts text from the provided PDF file using PyMuPDF.
    :param pdf_file_path: Path to the PDF file.
    :return: Extracted text as a string.
    """
    document = fitz.open(pdf_file_path)
    text = ""

    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text += page.get_text()

    return text
