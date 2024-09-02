import json
import boto3
import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote_plus
from utils import process_pdf, process_docx, process_csv

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

BUCKET_NAME = "extraction-buck"

def download_with_retry(bucket, key, local_path, retries=2, wait=2):
    for i in range(retries):
        try:
            s3.download_file(bucket, key, local_path)
            return
        except Exception as e:
            if i < retries - 1:
                time.sleep(wait)
                logger.warning(f"Retrying download for {key} (attempt {i+2})")
            else:
                raise

def process_file(bucket, key):
    # Decode key to handle special characters
    decoded_key = unquote_plus(key)
    local_path = "/tmp/" + os.path.basename(decoded_key)
    output_key = decoded_key.replace("uploads/", "results/").rsplit(".", 1)[0] + ".txt"
    output_local_path = "/tmp/" + os.path.basename(output_key)

    try:
        logger.info(f"Attempting to download file: {decoded_key} from bucket: {bucket}")
        download_with_retry(bucket, decoded_key, local_path)
        logger.info(f"Successfully downloaded file: {decoded_key}")

        if decoded_key.lower().endswith('.pdf'):
            text = process_pdf(local_path)
        elif decoded_key.lower().endswith('.docx') or decoded_key.lower().endswith('.doc'):
            text = process_docx(local_path)
        elif decoded_key.lower().endswith('.csv'):
            text = process_csv(local_path)
        else:
            raise ValueError(f"Unsupported file type: {decoded_key}")

        with open(output_local_path, "w") as f:
            f.write(text)

        logger.info(f"Attempting to upload result file: {output_key}")
        s3.upload_file(output_local_path, bucket, output_key)
        logger.info(f"Successfully uploaded result file: {output_key}")

        # # Delete the original file from uploads folder
        # logger.info(f"Attempting to delete original file: {decoded_key}")
        # s3.delete_object(Bucket=bucket, Key=decoded_key)
        # logger.info(f"Successfully deleted original file: {decoded_key}")

        return {"status": "success", "file_key": decoded_key, "output_key": output_key}
    except Exception as e:
        logger.error(f"Error processing file {decoded_key}: {str(e)}", exc_info=True)
        return {"status": "error", "file_key": decoded_key, "error": str(e)}

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    files_to_process = []
    
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            for s3_record in body['Records']:
                if 's3' in s3_record:
                    bucket = s3_record['s3']['bucket']['name']
                    key = unquote_plus(s3_record['s3']['object']['key'])  # Decode key
                    logger.info(f"Found SQS message with S3 event for bucket: {bucket}, key: {key}")
                    files_to_process.append((bucket, key))
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}", exc_info=True)

    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_file = {executor.submit(process_file, bucket, key): (bucket, key) for bucket, key in files_to_process}
        for future in as_completed(future_to_file):
            bucket, key = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Completed processing file: {key}")
            except Exception as e:
                logger.error(f"Error processing file {key}: {str(e)}", exc_info=True)
                results.append({"status": "error", "file_key": key, "error": str(e)})

    logger.info(f"Processed {len(results)} files")
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
