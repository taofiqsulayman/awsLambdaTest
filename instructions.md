# Local testing instructions:
# 1. Build the Docker image:
    docker build -t my-lambda-function .

# 2. Run the container locally:
    docker run -p 9000:8080 my-lambda-function:latest

# 3. In a separate terminal, send a test event:
   curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{
      "Records": [
        {
          "body": "{\"file_key\": \"uploads/capstone.csv\"}"
        }
      ]
    }'

# Note: Make sure to replace "uploads/test.pdf" with an actual file key in your S3 bucket.


# Deploying to AWS using CLI

# 1. Authenticate Docker to your Amazon ECR registry
aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com

# 2. Create a new ECR repository (if not already created)
aws ecr create-repository --repository-name my-lambda-repo --image-scanning-configuration scanOnPush=true

# 3. Build your Docker image
docker build -t my-lambda-function .

# 4. Tag the image
docker tag my-lambda-function:latest YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/my-lambda-repo:latest

# 5. Push the image to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/my-lambda-repo:latest

# 6. Create the Lambda function
aws lambda create-function \
  --function-name my-lambda-function \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/my-lambda-repo:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_EXECUTION_ROLE

aws lambda create-function \
  --function-name test-lambda-function \
  --package-type Image \
  --code ImageUri=266025833015.dkr.ecr.eu-west-1.amazonaws.com/extraction-lambda-repo:latest \
  --role arn:aws:iam::266025833015:role/service-role/lambda-test-role-d4yo5xkv



# 7. Update the function if it already exists
aws lambda update-function-code \
  --function-name my-lambda-function \
  --image-uri YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/my-lambda-repo:latest

# Replace YOUR_REGION, YOUR_ACCOUNT_ID, and YOUR_LAMBDA_EXECUTION_ROLE with your actual values.

266025833015

eu-west-1

extraction-lambda-function

extraction-lambda-repo
