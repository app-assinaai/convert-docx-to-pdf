"""AWS Lambda handler for DOCX to PDF conversion API"""

import serverless_wsgi
from app import app

def handler(event, context):
    """
    Handle HTTP events using serverless-wsgi adapter for Flask (WSGI)
    """
    return serverless_wsgi.handle_request(app, event, context)