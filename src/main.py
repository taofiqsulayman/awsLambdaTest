import json
import boto3
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import process_pdf, process_docx, process_csv

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

BUCKET_NAME = "extraction-buck"
QUEUE_URL = "https://sqs.eu-west-1.amazonaws.com/266025833015/extraction-queue"

def process_file(bucket, key):
    local_path = "/tmp/" + os.path.basename(key)
    output_key = key.replace("uploads/", "results/").rsplit(".", 1)[0] + ".txt"
    output_local_path = "/tmp/" + os.path.basename(output_key)

    try:
        logger.info(f"Attempting to download file: {key} from bucket: {bucket}")
        s3.download_file(bucket, key, local_path)
        logger.info(f"Successfully downloaded file: {key}")

        if key.lower().endswith('.pdf'):
            text = process_pdf(local_path)
        elif key.lower().endswith('.docx') or key.lower().endswith('.doc'):
            text = process_docx(local_path)
        elif key.lower().endswith('.csv'):
            text = process_csv(local_path)
        else:
            raise ValueError(f"Unsupported file type: {key}")

        with open(output_local_path, "w") as f:
            f.write(text)

        logger.info(f"Attempting to upload result file: {output_key}")
        s3.upload_file(output_local_path, bucket, output_key)
        logger.info(f"Successfully uploaded result file: {output_key}")

        # Delete the original file from uploads folder
        logger.info(f"Attempting to delete original file: {key}")
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Successfully deleted original file: {key}")

        return {"status": "success", "file_key": key, "output_key": output_key}
    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}", exc_info=True)
        return {"status": "error", "file_key": key, "error": str(e)}

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    files_to_process = []
    
    for record in event['Records']:
        # This is an SQS event containing an S3 notification
        try:
            body = json.loads(record['body'])
            for s3_record in body['Records']:
                if 's3' in s3_record:
                    bucket = s3_record['s3']['bucket']['name']
                    key = s3_record['s3']['object']['key']
                    logger.info(f"Found SQS message with S3 event for bucket: {bucket}, key: {key}")
                    files_to_process.append((bucket, key))
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}", exc_info=True)

    results = []
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
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