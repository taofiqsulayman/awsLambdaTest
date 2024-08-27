import boto3
import PyPDF2
import os

s3 = boto3.client("s3")


def lambda_handler(event, context):
    try:
        # Extract bucket name and PDF file key from the event
        bucket_name = "extraction-buck"
        pdf_key = event["Records"][0]["s3"]["object"]["key"]
        pdf_local_path = "/tmp/" + os.path.basename(pdf_key)
        output_key = pdf_key.replace("uploads/", "results/").replace(".pdf", ".txt")
        output_local_path = "/tmp/" + os.path.basename(output_key)

        # Download PDF from S3
        s3.download_file(bucket_name, pdf_key, pdf_local_path)
        print(f"Downloaded {pdf_key} to {pdf_local_path}")

        # Process the PDF to extract text using PyPDF2
        with open(pdf_local_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

        # Save the extracted text to a file
        with open(output_local_path, "w") as f:
            f.write(text)

        # Upload the result to S3
        s3.upload_file(output_local_path, bucket_name, output_key)
        print(f"Uploaded {output_local_path} to {output_key} in S3")

    except Exception as e:
        print(f"Error processing file: {e}")
        raise e
