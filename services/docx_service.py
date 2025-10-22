"""DOCX file manipulation service"""

import re
from typing import List, Dict, Optional, Tuple
from docx import Document
from io import BytesIO
from services.pdf_service import convert_docx_to_pdf
from services.s3_service import upload_bytes_to_s3, generate_presigned_get_url
import os
import uuid


def extract_variables(docx_content: bytes) -> List[str]:
    """
    Extract all variables from DOCX file content
    
    Args:
        docx_content: DOCX file as bytes
        
    Returns:
        List of unique variable names (without {{}})
    """
    doc = Document(BytesIO(docx_content))
    variables = set()
    
    # Pattern to match {{variable_name}}
    pattern = r'\{\{([^}]+)\}\}'
    
    # Extract from paragraphs
    for paragraph in doc.paragraphs:
        matches = re.findall(pattern, paragraph.text)
        variables.update(matches)
    
    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                matches = re.findall(pattern, cell.text)
                variables.update(matches)
    
    # Extract from headers
    for section in doc.sections:
        if section.header:
            for paragraph in section.header.paragraphs:
                matches = re.findall(pattern, paragraph.text)
                variables.update(matches)
        
        if section.footer:
            for paragraph in section.footer.paragraphs:
                matches = re.findall(pattern, paragraph.text)
                variables.update(matches)
    
    return sorted(list(variables))


def replace_variables(docx_content: bytes, variables: Dict[str, str]) -> bytes:
    """
    Replace variables in DOCX file with provided values
    
    Args:
        docx_content: DOCX file as bytes
        variables: Dictionary mapping variable names to replacement values
        
    Returns:
        Modified DOCX file as bytes
    """
    doc = Document(BytesIO(docx_content))
    
    # Replace in paragraphs
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, variables)
    
    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, variables)
    
    # Replace in headers
    for section in doc.sections:
        if section.header:
            for paragraph in section.header.paragraphs:
                _replace_in_paragraph(paragraph, variables)
        
        if section.footer:
            for paragraph in section.footer.paragraphs:
                _replace_in_paragraph(paragraph, variables)
    
    # Save to bytes
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output.read()


def _replace_in_paragraph(paragraph, variables: Dict[str, str]) -> None:
    """
    Replace variables in a paragraph's runs
    
    Args:
        paragraph: Paragraph object from python-docx
        variables: Dictionary mapping variable names to replacement values
    """
    # Get the full text of the paragraph
    full_text = paragraph.text
    
    # Check if any variables exist in the text
    if not any(f'{{{{{key}}}}}' in full_text for key in variables.keys()):
        return
    
    # Clear the paragraph
    paragraph.clear()
    
    # Split the text by variable patterns and build new runs
    pattern = r'(\{\{[^}]+\}\})'
    parts = re.split(pattern, full_text)
    
    for part in parts:
        if part.startswith('{{') and part.endswith('}}'):
            # This is a variable
            var_name = part[2:-2]  # Remove {{ and }}
            replacement = variables.get(var_name, part)  # Keep original if not found
            paragraph.add_run(replacement)
        else:
            # Regular text
            if part:
                paragraph.add_run(part)


def extract_variables_and_convert_pdf(
    docx_content: bytes,
    variables: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], bytes]:
    """
    Extract variables and convert DOCX (optionally with replacements) to PDF.

    Args:
        docx_content: Original DOCX bytes.
        variables: Optional mapping for replacements. If provided, replacements are applied before PDF conversion.

    Returns:
        A tuple of (variables_list, pdf_bytes).
    """
    extracted_variables = extract_variables(docx_content)

    # If variables provided, replace before converting; otherwise convert original
    docx_for_conversion = (
        replace_variables(docx_content, variables) if variables else docx_content
    )

    pdf_bytes = convert_docx_to_pdf(docx_for_conversion)
    return extracted_variables, pdf_bytes


def extract_convert_upload_get_url(
    docx_content: bytes,
    variables: Optional[Dict[str, str]] = None,
    bucket_name: str = "assinaai-temp",
    s3_prefix: Optional[str] = None,
    presign_ttl_seconds: int = 86400,
) -> Tuple[List[str], str]:
    """
    Extract variables, (optionally) replace, convert to PDF, upload to S3, return presigned URL.

    Args:
        docx_content: DOCX bytes input.
        variables: Optional mapping to replace in DOCX prior to conversion.
        bucket_name: S3 bucket to upload the PDF to.
        s3_prefix: Optional key prefix in the bucket.
        presign_ttl_seconds: Expiration for presigned URL (default 1 day).

    Returns:
        (variables_list, presigned_url)
    """
    extracted_variables = extract_variables(docx_content)
    final_docx = replace_variables(docx_content, variables) if variables else docx_content
    pdf_bytes = convert_docx_to_pdf(final_docx)

    # Key generation: optional prefix + uuid-based filename
    prefix = (s3_prefix or "generated-pdfs").strip("/")
    unique_id = uuid.uuid4().hex
    key = f"{prefix}/{unique_id}.pdf" if prefix else f"{unique_id}.pdf"

    # Upload with content type
    upload_bytes_to_s3(
        bucket=bucket_name,
        key=key,
        data=pdf_bytes,
        content_type="application/pdf",
    )

    url = generate_presigned_get_url(
        bucket=bucket_name,
        key=key,
        expires_in_seconds=presign_ttl_seconds,
    )
    return extracted_variables, url

