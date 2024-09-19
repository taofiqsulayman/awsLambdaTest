import streamlit as st

st.set_page_config(
    page_title="file extractor",
    page_icon="📄",
    layout="wide",
)

st.markdown("# File Extractor")

st.markdown(
    """
    This app allows you to extract text from multiple files using a series of libraries.
    """
)

st.markdown("## What is contained in this app:")

st.markdown(
    """
        1. tesseractLambda: Uses Pymupdf and Tesseract to extract text from PDFs, csv for csv files, spire.doc for docx and docs files. It runs on AWS Lambda which is triggered by a SQS queue as a result of an S3 upload.
        
        2. paddleLambda: Uses pymupdf and PaddleOCR to extract text from images and pdf file, pandas for csv, xlsx and tsv files. Also, spire.doc for docx and docs files. 
        It runs on AWS Lambda which is triggered by a SQS queue as a result of an S3 upload.
        
        3. ppocr: Uses PaddleOCR to extract text from images and pdf file, pandas for csv, xlsx and tsv files. Also, spire.doc for docx and docs files.
        It runs as a standalone streamlit app without any external infrastructure.
    """
)

st.markdown("## Check the sidebar to see the pages in the app")