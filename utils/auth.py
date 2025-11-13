"""Authentication utilities for API key validation."""
from functools import wraps
from flask import request, jsonify, current_app


def require_api_key(f):
    """
    Decorator to protect routes with API key authentication.
    
    Expects the API key in the 'x-api-key' header.
    Returns 401 Unauthorized if the key is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Missing API key. Please provide x-api-key header.'
            }), 401
        
        expected_key = current_app.config.get('EMPLOYER_API_KEY')
        if api_key != expected_key:
            return jsonify({
                'success': False,
                'error': 'Invalid API key.'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

