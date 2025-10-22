"""File validation utilities"""

import os
from typing import Optional
from werkzeug.exceptions import BadRequest


def validate_docx_file(file) -> None:
    """
    Validate uploaded DOCX file
    
    Args:
        file: File object from Flask request
        
    Raises:
        BadRequest: If file is invalid
    """
    if not file:
        raise BadRequest("No file provided")
    
    if not file.filename:
        raise BadRequest("No filename provided")
    
    # Check file extension
    filename = file.filename.lower()
    if not filename.endswith('.docx'):
        raise BadRequest("File must be a .docx file")
    
    # Check file size (max 10MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise BadRequest(f"File size exceeds maximum allowed size of 10MB")


def validate_variables_mapping(variables: Optional[dict]) -> None:
    """
    Validate variables mapping dictionary
    
    Args:
        variables: Dictionary mapping variable names to values
        
    Raises:
        BadRequest: If mapping is invalid
    """
    if variables is None:
        raise BadRequest("Variables mapping is required")
    
    if not isinstance(variables, dict):
        raise BadRequest("Variables must be a dictionary")
    
    # Check if all values are strings
    for key, value in variables.items():
        if not isinstance(key, str):
            raise BadRequest("Variable names must be strings")
        if not isinstance(value, str):
            raise BadRequest("Variable values must be strings")

