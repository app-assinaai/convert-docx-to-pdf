#!/bin/bash

# This script automates the build and deployment of the Docker-based
# Lambda function to AWS ECR and Lambda.
#
# It assumes you have already:
# 1. Updated your 'pdf_service.py' to work with Docker (simple _find_libreoffice).
# 2. Updated 'requirements.txt' (e.g., added 'serverless-wsgi').
# 3. Created the 'Dockerfile'.
#
# PREREQUISITES:
# - AWS CLI installed and configured
# - Docker installed and running
# - 'sudo' is used for Docker commands. If your user is in the 'docker'
#   group, you can remove 'sudo' from the docker commands below.

# --- Configuration ---
# 1. SET YOUR LAMBDA FUNCTION NAME HERE
LAMBDA_FUNCTION_NAME="convertDocxToPdfDocker"

# 2. SET YOUR AWS/ECR DETAILS
AWS_ACCOUNT_ID="357579410851"
AWS_REGION="us-east-1"
ECR_REPO_NAME="my-pdf-service"
# ---------------------

# Stop the script if any command fails
set -e

# --- Script ---
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
FULL_IMAGE_URI="${ECR_URI}/${ECR_REPO_NAME}:latest"

echo "🚀 Starting Docker-based Lambda deployment..."
echo "   Function: ${LAMBDA_FUNCTION_NAME}"
echo "   Repository: ${ECR_URI}/${ECR_REPO_NAME}"
echo ""

if [ "${LAMBDA_FUNCTION_NAME}" == "your-lambda-function-name" ]; then
    echo "❌ ERROR: Please edit the 'deploy.sh' script and set"
    echo "         'LAMBDA_FUNCTION_NAME' to your function's name."
    exit 1
fi

echo "Step 1: Creating ECR repository (if it doesn't exist)..."
if ! aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION} 2>/dev/null; then
    echo "   Repository '${ECR_REPO_NAME}' already exists. Skipping creation."
else
    echo "   Successfully created repository '${ECR_REPO_NAME}'."
fi
echo "--------------------------------------------------"

echo "Step 2: Authenticating Docker with ECR..."
aws ecr get-login-password --region ${AWS_REGION} | sudo docker login --username AWS --password-stdin ${ECR_URI}
echo "   Login Succeeded."
echo "--------------------------------------------------"

echo "Step 3: Building the Docker image..."
sudo docker build -t ${ECR_REPO_NAME} .
echo "   Build complete."
echo "--------------------------------------------------"

echo "Step 4: Tagging the image for ECR..."
sudo docker tag ${ECR_REPO_NAME}:latest ${FULL_IMAGE_URI}
echo "   Image tagged as ${FULL_IMAGE_URI}"
echo "--------------------------------------------------"

echo "Step 5: Pushing the image to ECR..."
sudo docker push ${FULL_IMAGE_URI}
echo "   Push complete."
echo "--------------------------------------------------"

echo "Step 6: Deploying the new image to Lambda..."
echo "   (This may take a moment as Lambda updates...)"
aws lambda update-function-code \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --image-uri ${FULL_IMAGE_URI} \
    --region ${AWS_REGION}

echo ""
echo "✅ All steps complete. Your Lambda function has been updated."