"""DOCX file manipulation service"""

import re
from typing import List, Dict
from docx import Document
from io import BytesIO


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

