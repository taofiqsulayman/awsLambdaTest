FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install -r requirements.txt

# Copy all files in ./src
COPY src/* ${LAMBDA_TASK_ROOT}

# Copy the tesseract files
COPY tess/* ${LAMBDA_TASK_ROOT}

# set environment variables
# os.environ['TESSDATA_PREFIX'] = os.environ["LAMBDA_TASK_ROOT"] + "/tesseract/share/tessdata"
# os.environ['LD_LIBRARY_PATH'] = os.environ["LAMBDA_TASK_ROOT"] + "/lib"
ENV TESSDATA_PREFIX = ${LAMBDA_TASK_ROOT}/tesseract/share/tessdata
ENV LD_LIBRARY_PATH = ${LAMBDA_TASK_ROOT}/lib

# Set the CMD to your handler.
CMD [ "main.lambda_handler" ]