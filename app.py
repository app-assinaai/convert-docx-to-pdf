"""Flask REST API for DOCX to PDF conversion with variable replacement"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from io import BytesIO
import traceback

from services.docx_service import (
    extract_variables,
    replace_variables,
    extract_variables_and_convert_pdf,
    extract_convert_upload_get_url,
)
from services.pdf_service import convert_docx_to_pdf
from utils.validators import validate_docx_file, validate_variables_mapping

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/extract-variables', methods=['POST'])
def extract_variables_endpoint():
    """
    Extract all variables from a DOCX file
    
    Request: multipart/form-data with 'file' field (DOCX file)
    Response: JSON with list of variable names
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")
        
        file = request.files['file']
        validate_docx_file(file)
        
        # Read file content
        docx_content = file.read()
        
        # Extract variables
        variables = extract_variables(docx_content)
        
        return jsonify({
            'variables': variables,
            'count': len(variables)
        }), 200
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to extract variables',
            'message': str(e)
        }), 500


@app.route('/api/replace-variables', methods=['POST'])
def replace_variables_endpoint():
    """
    Replace variables in a DOCX file
    
    Request: multipart/form-data with:
        - 'file': DOCX file
        - 'variables': JSON string mapping variable names to values
    Response: DOCX file with replaced variables
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")
        
        file = request.files['file']
        validate_docx_file(file)
        
        # Get variables mapping
        variables_json = request.form.get('variables')
        if not variables_json:
            raise BadRequest("Variables mapping is required")
        
        import json
        try:
            variables = json.loads(variables_json)
        except json.JSONDecodeError:
            raise BadRequest("Invalid JSON in variables field")
        
        validate_variables_mapping(variables)
        
        # Read file content
        docx_content = file.read()
        
        # Replace variables
        modified_docx = replace_variables(docx_content, variables)
        
        # Return as binary
        return send_file(
            BytesIO(modified_docx),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='modified.docx'
        )
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to replace variables',
            'message': str(e)
        }), 500


@app.route('/api/convert-to-pdf', methods=['POST'])
def convert_to_pdf_endpoint():
    """
    Convert DOCX file to PDF
    
    Request: multipart/form-data with 'file' field (DOCX file)
    Response: PDF file
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")
        
        file = request.files['file']
        validate_docx_file(file)
        
        # Read file content
        docx_content = file.read()
        
        # Convert to PDF
        pdf_content = convert_docx_to_pdf(docx_content)
        
        # Return as binary
        return send_file(
            BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='converted.pdf'
        )
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to convert to PDF',
            'message': str(e)
        }), 500


@app.route('/api/process-document', methods=['POST'])
def process_document_endpoint():
    """
    Process document: replace variables and convert to PDF
    
    Request: multipart/form-data with:
        - 'file': DOCX file
        - 'variables': JSON string mapping variable names to values
    Response: PDF file with replaced variables
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")
        
        file = request.files['file']
        validate_docx_file(file)
        
        # Get variables mapping
        variables_json = request.form.get('variables')
        if not variables_json:
            raise BadRequest("Variables mapping is required")
        
        import json
        try:
            variables = json.loads(variables_json)
        except json.JSONDecodeError:
            raise BadRequest("Invalid JSON in variables field")
        
        validate_variables_mapping(variables)
        
        # Read file content
        docx_content = file.read()
        
        # Replace variables
        modified_docx = replace_variables(docx_content, variables)
        
        # Convert to PDF
        pdf_content = convert_docx_to_pdf(modified_docx)
        
        # Return as binary
        return send_file(
            BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='processed.pdf'
        )
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to process document',
            'message': str(e)
        }), 500


@app.route('/api/extract-and-convert', methods=['POST'])
def extract_and_convert_endpoint():
    """
    Extract variables and convert DOCX to PDF in one request.

    Request: multipart/form-data with:
        - 'file': DOCX file (required)
        - 'variables': JSON string mapping variable names to values (optional)
    Response: JSON containing variables list and base64-encoded PDF
    {
      "variables": ["name", "date"],
      "pdfBase64": "JVBERi0xLjQK..."
    }
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")

        file = request.files['file']
        validate_docx_file(file)

        # Parse optional variables JSON
        variables = None
        variables_json = request.form.get('variables')
        if variables_json:
            import json
            try:
                variables = json.loads(variables_json)
            except json.JSONDecodeError:
                raise BadRequest("Invalid JSON in variables field")
            validate_variables_mapping(variables)

        # Read file content
        docx_content = file.read()

        # Execute combined operation
        variables_list, pdf_bytes = extract_variables_and_convert_pdf(
            docx_content, variables
        )

        # Encode PDF to base64
        import base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

        return jsonify({
            'variables': variables_list,
            'pdfBase64': pdf_base64,
        }), 200

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to extract and convert',
            'message': str(e)
        }), 500


@app.route('/api/extract-convert-upload', methods=['POST'])
def extract_convert_upload_endpoint():
    """
    Extract variables, optionally replace, convert to PDF, upload to S3, and return a 1-day presigned URL.

    Request: multipart/form-data with:
        - 'file': DOCX file (required)
        - 'variables': JSON string mapping variable names to values (optional)
        - 's3Prefix': Optional path prefix for the S3 object key (e.g., "tenant-123/")
        - 'bucket': Optional S3 bucket override (default: assinaai-temp)
        - 'ttlSeconds': Optional expiration seconds (default: 86400)
    Response: JSON containing variables list and presignedUrl
    {
      "variables": ["name", "date"],
      "presignedUrl": "https://..."
    }
    """
    try:
        # Validate file
        if 'file' not in request.files:
            raise BadRequest("No file provided in request")

        file = request.files['file']
        validate_docx_file(file)

        # Optional variables
        variables = None
        variables_json = request.form.get('variables')
        if variables_json:
            import json
            try:
                variables = json.loads(variables_json)
            except json.JSONDecodeError:
                raise BadRequest("Invalid JSON in variables field")
            validate_variables_mapping(variables)

        # Optional S3 inputs
        s3_prefix = request.form.get('s3Prefix')
        bucket_override = request.form.get('bucket') or 'assinaai-temp'
        ttl_seconds_raw = request.form.get('ttlSeconds')
        try:
            ttl_seconds = int(ttl_seconds_raw) if ttl_seconds_raw else 86400
        except ValueError:
            raise BadRequest("ttlSeconds must be an integer")

        # Read file content
        docx_content = file.read()

        # Execute combined operation with upload
        variables_list, url = extract_convert_upload_get_url(
            docx_content=docx_content,
            variables=variables,
            bucket_name=bucket_override,
            s3_prefix=s3_prefix,
            presign_ttl_seconds=ttl_seconds,
        )

        return jsonify({
            'variables': variables_list,
            'presignedUrl': url,
        }), 200

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': 'Failed to extract, convert and upload',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

