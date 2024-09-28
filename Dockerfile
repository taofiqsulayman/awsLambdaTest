FROM public.ecr.aws/lambda/python:3.11

# Install dependencies for LibreOffice
RUN yum -y update && yum install -y \
    antiword \
    poppler-utils \
    mesa-libGL \
    mesa-libGLU \
    && yum clean all

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy all files in ./src
COPY src/* ${LAMBDA_TASK_ROOT}

# Copy the tesseract files
COPY tess/* ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler.
CMD [ "main.lambda_handler" ]