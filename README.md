# DOCX to PDF Conversion API

A Flask REST API for extracting variables from DOCX files, replacing them with provided values, and converting documents to PDF format. Designed for AWS Lambda deployment.

## Features

- **Extract Variables**: Extract all variables from DOCX files (variables in `{{variable_name}}` format)
- **Replace Variables**: Replace variables in DOCX files with provided values
- **Convert to PDF**: Convert DOCX files to PDF format
- **Process Document**: Combined operation (replace variables + convert to PDF)

## Tech Stack

- Python 3.9+
- Flask (lightweight REST API)
- python-docx (DOCX manipulation)
- LibreOffice (PDF conversion via command line)
- Flask-CORS (cross-origin support)

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Quick Start

1. Install LibreOffice (required for PDF conversion):

```bash
sudo apt-get update && sudo apt-get install -y libreoffice
```

2. Make the start script executable:

```bash
chmod +x start.sh
```

3. Run the application:

```bash
./start.sh
```

The script will:

- Create a virtual environment (if it doesn't exist)
- Install all dependencies
- Start the Flask server on `http://localhost:5000`

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**

```json
{
  "status": "healthy"
}
```

### 2. Extract Variables

**POST** `/api/extract-variables`

Extract all variables from a DOCX file.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (DOCX file)

**Response:**

```json
{
  "variables": ["name", "date", "company"],
  "count": 3
}
```

**Example (cURL):**

```bash
curl -X POST http://localhost:5000/api/extract-variables \
  -F "file=@document.docx"
```

### 3. Replace Variables

**POST** `/api/replace-variables`

Replace variables in a DOCX file with provided values.

**Request:**

- Content-Type: `multipart/form-data`
- Body:
  - `file` (DOCX file)
  - `variables` (JSON string)

**Response:**

- Binary DOCX file with replaced variables

**Example (cURL):**

```bash
curl -X POST http://localhost:5000/api/replace-variables \
  -F "file=@document.docx" \
  -F 'variables={"name":"John Doe","date":"2024-01-15","company":"Acme Inc"}' \
  -o output.docx
```

### 4. Convert to PDF

**POST** `/api/convert-to-pdf`

Convert a DOCX file to PDF format.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `file` (DOCX file)

**Response:**

- Binary PDF file

**Example (cURL):**

```bash
curl -X POST http://localhost:5000/api/convert-to-pdf \
  -F "file=@document.docx" \
  -o output.pdf
```

### 5. Process Document (Combined)

**POST** `/api/process-document`

Replace variables and convert to PDF in one call.

**Request:**

- Content-Type: `multipart/form-data`
- Body:
  - `file` (DOCX file)
  - `variables` (JSON string)

**Response:**

- Binary PDF file with replaced variables

**Example (cURL):**

```bash
curl -X POST http://localhost:5000/api/process-document \
  -F "file=@document.docx" \
  -F 'variables={"name":"John Doe","date":"2024-01-15"}' \
  -o processed.pdf
```

## Variable Format

Variables in the DOCX file must be in the format: `{{variable_name}}`

**Example:**

```
Hello {{name}}, welcome to {{company}} on {{date}}.
```

## JavaScript Example

```javascript
// Extract variables
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("http://localhost:5000/api/extract-variables", {
  method: "POST",
  body: formData,
});

const data = await response.json();
console.log(data.variables); // ['name', 'company', 'date']

// Process document
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append(
  "variables",
  JSON.stringify({
    name: "John Doe",
    company: "Acme Inc",
    date: "2024-01-15",
  })
);

const pdfResponse = await fetch("http://localhost:5000/api/process-document", {
  method: "POST",
  body: formData,
});

const blob = await pdfResponse.blob();
// Download or display the PDF
```

## File Limits

- Maximum file size: 10MB
- Supported format: `.docx` only
- Variable names must be valid strings

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid file, missing parameters)
- `500` - Internal Server Error

Error response format:

```json
{
  "error": "Error message",
  "message": "Detailed error message"
}
```

## Project Structure

```
/
├── app.py                 # Main Flask application
├── services/
│   ├── __init__.py
│   ├── docx_service.py   # DOCX variable extraction/replacement
│   └── pdf_service.py    # PDF conversion service
├── utils/
│   ├── __init__.py
│   └── validators.py     # File validation utilities
├── requirements.txt       # Python dependencies
├── start.sh              # Script to run locally
└── README.md             # Documentation
```

## Development

### Running in Development Mode

The Flask app runs with debug mode enabled by default when using `start.sh`:

```bash
./start.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## AWS Lambda Deployment

This application is ready for AWS Lambda deployment with full documentation.

### Quick Start

For a quick deployment guide, see [QUICK_START.md](QUICK_START.md)

### Detailed Documentation

- **[LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md)** - Complete step-by-step AWS Lambda deployment guide via AWS Console
- **[spring-boot-integration.md](spring-boot-integration.md)** - How to call the Lambda function from Spring Boot applications

### Deployment Files

- `lambda_handler.py` - Lambda handler wrapper using Mangum
- `requirements-lambda.txt` - Lambda-specific dependencies
- `deploy-lambda.sh` - Automated deployment packaging script

### Key Features

- ✅ Pre-configured Lambda handler
- ✅ Console-based deployment instructions
- ✅ Spring Boot integration examples
- ✅ Full REST API support via Function URL or API Gateway
- ✅ LibreOffice layer integration guide

### Important Notes

- **LibreOffice Layer Required**: PDF conversion requires a LibreOffice Lambda layer
- **Memory**: Recommended 512 MB or higher
- **Timeout**: 30+ seconds for large files
- **File Size**: Lambda has 6MB request limit (use S3 for larger files)

## License

MIT
# convert-docx-to-pdf
