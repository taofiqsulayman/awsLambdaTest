import streamlit as st
from spire.doc import Document

# Streamlit app title
st.title("Word Document Viewer")

# Upload multiple files
uploaded_files = st.file_uploader(
    "Choose Word documents", type=["doc", "docx"], accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        # Save each uploaded file temporarily
        with open(f"temp_{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load the document using Spire.Doc
        document = Document()
        document.LoadFromFile(f"temp_{uploaded_file.name}")

        # Extract text from the document
        doc_text = document.GetText()

        # Display the filename and its content
        st.subheader(f"Contents of {uploaded_file.name}")
        st.text_area(f"Text from {uploaded_file.name}", doc_text, height=300)

        # Adding a download button for each file's extracted text
        # st.download_button(
        #     label=f"Download Text from {uploaded_file.name}",
        #     data=doc_text,
        #     file_name=f"{uploaded_file.name}_extracted_text.txt",
        #     mime="text/plain",
        # )
