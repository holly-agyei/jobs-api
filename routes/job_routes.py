"""Routes for job-related endpoints."""
from flask import Blueprint, jsonify, request
from models import db, Job
from utils.auth import require_api_key

job_bp = Blueprint('jobs', __name__)


@job_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """
    GET /jobs
    Fetches all available job postings.
    Public endpoint - no authentication required.
    
    Returns:
        200 OK: Array of job objects
    """
    try:
        jobs = Job.query.order_by(Job.posted_at.desc()).all()
        jobs_data = [job.to_dict() for job in jobs]
        
        return jsonify(jobs_data), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch jobs: {str(e)}'
        }), 500


@job_bp.route('/jobs', methods=['POST'])
@require_api_key
def create_job():
    """
    POST /jobs
    Creates a new job posting.
    Protected endpoint - requires API key in x-api-key header.
    
    Request Body:
        {
            "title": "string",
            "role": "string",
            "company": "string",
            "location": "string",
            "description": "string",
            "required_skills": ["string"],
            "required_certifications": ["string"]
        }
    
    Returns:
        201 Created: Created job object
        400 Bad Request: Invalid input data
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'role', 'company', 'location', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create new job
        job = Job(
            title=data['title'],
            role=data['role'],
            company=data['company'],
            location=data['location'],
            description=data['description'],
            required_skills=data.get('required_skills', []),
            required_certifications=data.get('required_certifications', [])
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to create job: {str(e)}'
        }), 500

