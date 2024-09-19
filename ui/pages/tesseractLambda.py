import streamlit as st
import boto3
import time
import concurrent.futures
import logging
import urllib.parse
from botocore.exceptions import ClientError

def health_check():
    return {"status": "healthy"}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# Constants
BUCKET_NAME = 'extraction-buck'
UPLOAD_PREFIX = 'uploads/'
RESULT_PREFIX = 'results/'

def upload_to_s3_and_queue(file):
    try:
        file_key = f"{UPLOAD_PREFIX}{file.name}"
        s3.upload_fileobj(file, BUCKET_NAME, file_key)
        logger.info(f"Uploaded file: {file_key}")
        
        return {"status": "success", "message": "File uploaded and queued", "file_key": file_key}
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

def get_result(file_key):
    try:
        decoded_file_key = urllib.parse.unquote_plus(file_key)
        logger.info(f"Decoded file key: {decoded_file_key}")

        original_extension = decoded_file_key.split('.')[-1]
        output_key = f"{RESULT_PREFIX}{decoded_file_key.replace(f'.{original_extension}', '.txt')}"
        logger.info(f"Generated output key: {output_key}")

        s3_response = s3.get_object(Bucket=BUCKET_NAME, Key=output_key)
        result_text = s3_response["Body"].read().decode("utf-8")

        return {"result": result_text}
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {"message": "Result not ready yet. Please try again later."}
        else:
            logger.error(f"Error fetching result for {file_key}: {e}", exc_info=True)
            return {"message": f"Error fetching result for {file_key}: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching result for {file_key}: {e}", exc_info=True)
        return {"message": f"Error fetching result for {file_key}: {str(e)}"}

def main():
    if st.query_params.get("health_check") == "true":
        st.json(health_check())
        st.stop()
    
    st.title("File Processor")
    st.subheader("Tesseract powered Lambda Function")

    # Section 1: File Uploading
    st.subheader("1. Upload Files")
    uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx", "csv", "doc"], accept_multiple_files=True)
    
    if st.button("Upload Files"):
        if uploaded_files:
            with st.spinner('Uploading files...'):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    upload_results = list(executor.map(upload_to_s3_and_queue, uploaded_files))
                if all(result['status'] == 'success' for result in upload_results):
                    st.success("All files uploaded successfully.")
                else:
                    st.error("Error uploading files. Please check the logs for details.")
                
                # Store file keys in session state for later use
                st.session_state.file_keys = [result['file_key'] for result in upload_results if result['status'] == 'success']

    # Section 2: Check Results
    st.subheader("2. Check Results")
    if st.button("Check Results"):
        if hasattr(st.session_state, 'file_keys') and st.session_state.file_keys:
            with st.spinner("Checking results..."):
                time.sleep(5)  # Initial delay to simulate processing start
                
                # Concurrently check results
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {executor.submit(get_result, file_key.replace('uploads/', '')): file_key for file_key in st.session_state.file_keys}
                    for future in concurrent.futures.as_completed(futures):
                        file_key = futures[future]
                        result = future.result()
                        if 'message' in result:
                            if "Result not ready yet" in result['message']:
                                st.warning(f"{file_key}: {result['message']}")
                            else:
                                st.error(f"{file_key}: {result['message']}")
                        elif 'result' in result:
                            with st.expander(f"Contents of {file_key.replace('uploads/', '')}"):
                                st.text_area("", result['result'], height=500, key=file_key)
                        else:
                            st.error(f"{file_key}: Unexpected response format: {result}")
        else:
            st.warning("No files have been uploaded. Please upload files first to check results.")

if __name__ == "__main__":
    main()