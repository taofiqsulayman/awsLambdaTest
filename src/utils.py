import subprocess
from PyPDF2 import PdfReader, PdfWriter
import uuid
from spire.doc import Document
import csv
import os

import tempfile
from pathlib import Path

os.environ['TRANSFORMERS_CACHE'] = '/tmp/.cache/huggingface'



# Constants
BATCH_MULTIPLIER = 3
MAX_PAGES = None
WORKERS = 1
CHUNK_SIZE = 30

def process_docx(file_path):
    document = Document()
    document.LoadFromFile(file_path)
    return document.GetText()
    input_pdf = PdfReader(str(file_path))
    total_pages = len(input_pdf.pages)

    if total_pages <= CHUNK_SIZE:
        content = extract_text_from_pdf(input_pdf)
        return content
    else:
        chunks = split_pdf(file_path, output_dir)
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = process_chunk(chunk, output_dir)
            processed_chunks.append(processed_chunk)
        
        merged_results = merge_chunk_results(processed_chunks, output_dir)
        if merged_results:
            return merged_results[0][1]
        else:
            return ""

def process_csv(csv_path):
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        return "\n".join([",".join(row) for row in reader])
    
    
def split_pdf(input_pdf_path, output_dir, chunk_size=CHUNK_SIZE):
    input_pdf = PdfReader(str(input_pdf_path))
    file_id = str(uuid.uuid4())
    pdf_chunks = []

    for i in range(0, len(input_pdf.pages), chunk_size):
        pdf_writer = PdfWriter()
        start_page = i + 1
        end_page = min(i + chunk_size, len(input_pdf.pages))

        for j in range(i, end_page):
            pdf_writer.add_page(input_pdf.pages[j])

        chunk_file_name = f"{file_id}_chunk_{start_page}_{end_page}.pdf"
        chunk_path = output_dir / chunk_file_name

        with open(chunk_path, "wb") as f:
            pdf_writer.write(f)

        pdf_chunks.append({
            "file_id": file_id,
            "original_file": input_pdf_path.name,
            "chunk_file": chunk_path,
            "start_page": start_page,
            "end_page": end_page,
        })

    return pdf_chunks

def run_marker_on_file(input_file, output_dir):
    command = f"marker_single '{input_file}' '{output_dir}' --batch_multiplier {BATCH_MULTIPLIER}"
    if MAX_PAGES:
        command += f" --max_pages {MAX_PAGES}"

    # Ensure the TRANSFORMERS_CACHE directory exists
    os.makedirs(os.environ['TRANSFORMERS_CACHE'], exist_ok=True)

    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=os.environ)

    if result.returncode != 0:
        raise Exception(f"Marker command failed for {input_file}: {result.stderr}")

    return result.stdout

def process_chunk(chunk, output_dir):
    chunk_output_dir = output_dir / chunk["original_file"].rsplit(".", 1)[0]
    chunk_output_dir.mkdir(parents=True, exist_ok=True)
    run_marker_on_file(chunk["chunk_file"], chunk_output_dir)
    return chunk

def merge_chunk_results(chunks, output_dir):
    results = {}
    for chunk in chunks:
        file_id = chunk["file_id"]
        original_file = chunk["original_file"]
        chunk_folder = output_dir / original_file.rsplit(".", 1)[0] / chunk["chunk_file"].stem
        md_file = chunk_folder / f"{chunk['chunk_file'].stem}.md"

        if md_file.exists():
            with open(md_file, "r") as f:
                content = f.read()
                if file_id not in results:
                    results[file_id] = {"original_file": original_file, "content": []}
                results[file_id]["content"].append((chunk["start_page"], content))

    final_results = []
    for file_id, data in results.items():
        sorted_content = sorted(data["content"], key=lambda x: x[0])
        merged_content = "\n".join([content for _, content in sorted_content])
        final_results.append((data["original_file"], merged_content))

    return final_results

def process_pdf(local_path, output_dir):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        chunk_dir = temp_dir / "chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunks = split_pdf(Path(local_path), chunk_dir)
        
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = process_chunk(chunk, output_dir)
            processed_chunks.append(processed_chunk)

        results = merge_chunk_results(processed_chunks, output_dir)
        
        if results:
            return results[0][1]  # Return the merged content
        else:
            return ""
