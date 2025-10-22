# Start from the official AWS base image that includes Python 3.12 AND LibreOffice
FROM public.ecr.aws/shelf/lambda-libreoffice-base:25.2-python3.12-x86_64

# Copy your requirements file
COPY requirements.txt .

# Install your Python packages
# This installs them into the image's Python environment
RUN pip install -r requirements.txt

# Copy all your application code into the task root
# (This assumes your lambda_handler.py is in the root
# and pdf_service.py is in a 'services' folder)
COPY lambda_handler.py .
COPY app.py .
COPY services/ ./services/
COPY utils/ ./utils/

# Set the command to your Lambda handler
# This tells Lambda to run the 'handler' function
# inside the 'lambda_handler.py' file.
CMD [ "lambda_handler.handler" ]