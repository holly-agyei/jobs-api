"""Routes for application-related endpoints."""
from flask import Blueprint, jsonify, request
from models import db, Application, Job
from utils.auth import require_api_key

application_bp = Blueprint('applications', __name__)


@application_bp.route('/applications', methods=['POST'])
def create_application():
    """
    POST /applications
    Submits a job application from an employee.
    Public endpoint - no authentication required.
    
    Request Body:
        {
            "job_id": "integer or string",
            "user_id": integer,
            "resume_link": "string",
            "skills": ["string"],
            "certifications": ["string"],
            "cover_letter": "string (optional)"
        }
    
    Returns:
        201 Created: Application created successfully
        400 Bad Request: Invalid input data
        404 Not Found: Job not found
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['job_id', 'user_id', 'resume_link']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Convert job_id to integer (handle string input)
        try:
            job_id = int(data['job_id'])
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid job_id format. Must be a number.'
            }), 400
        
        # Check if job exists
        job = Job.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job posting no longer available'
            }), 404
        
        # Validate user_id
        try:
            user_id = int(data['user_id'])
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid user_id format. Must be a number.'
            }), 400
        
        # Create new application
        application = Application(
            job_id=job_id,
            user_id=user_id,
            resume_link=data['resume_link'],
            skills=data.get('skills', []),
            certifications=data.get('certifications', []),
            cover_letter=data.get('cover_letter', '')
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'application_id': application.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to submit application: {str(e)}'
        }), 500


@application_bp.route('/applications', methods=['GET'])
@require_api_key
def get_applications():
    """
    GET /applications
    Fetches all job applications.
    Protected endpoint - requires API key in x-api-key header.
    
    Query Parameters (optional):
        - job_id: Filter applications by job ID
        - user_id: Filter applications by user ID
    
    Returns:
        200 OK: Array of application objects
    """
    try:
        query = Application.query
        
        # Apply filters if provided
        job_id = request.args.get('job_id', type=int)
        if job_id:
            query = query.filter(Application.job_id == job_id)
        
        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(Application.user_id == user_id)
        
        applications = query.order_by(Application.created_at.desc()).all()
        applications_data = [app.to_dict() for app in applications]
        
        return jsonify(applications_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch applications: {str(e)}'
        }), 500

