import boto3
import PyPDF2
import os
import json

s3 = boto3.client("s3")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    try:
        # Extract bucket name and PDF file key from the event
        bucket_name = "extraction-buck"
        pdf_key = event["Records"][0]["s3"]["object"]["key"]
        print(f"Attempting to process file: {pdf_key}")

        pdf_local_path = "/tmp/" + os.path.basename(pdf_key)
        output_key = pdf_key.replace("uploads/", "results/").replace(".pdf", ".txt")
        output_local_path = "/tmp/" + os.path.basename(output_key)

        # Download PDF from S3
        print(f"Downloading {pdf_key} from bucket {bucket_name}")
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
        print(f"Uploading {output_local_path} to {output_key} in S3")
        s3.upload_file(output_local_path, bucket_name, output_key)
        print(f"Uploaded {output_local_path} to {output_key} in S3")

        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {pdf_key}')
        }

    except Exception as e:
        print(f"Error processing file: {pdf_key}")
        print(f"Error details: {str(e)}")
        raise e

# Test the S3 connection and permissions
def test_s3_connection():
    try:
        response = s3.list_objects_v2(Bucket="extraction-buck", MaxKeys=1)
        print("Successfully connected to S3 and listed objects:")
        print(json.dumps(response, indent=2, default=str))
    except Exception as e:
        print(f"Error connecting to S3: {str(e)}")

# Uncomment the following line to test S3 connection when the Lambda function is initialized
# test_s3_connection()
