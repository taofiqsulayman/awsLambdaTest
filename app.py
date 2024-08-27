import streamlit as st
from spire.doc import Document

# Streamlit app title
st.title("Word Document Viewer using Spire.Doc")

# Upload a file
uploaded_file = st.file_uploader("Choose a Word document", type=["doc", "docx"])

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp.docx", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load the document using Spire.Doc
    document = Document()
    document.LoadFromFile("temp.docx")

    # Extract and display text
    doc_text = document.GetText()
    st.text_area("Document Text", doc_text, height=300)

# Adding a download button for the extracted text
# if doc_text:
#     st.download_button(
#         label="Download Text",
#         data=doc_text,
#         file_name="extracted_text.txt",
#         mime="text/plain",
#     )
