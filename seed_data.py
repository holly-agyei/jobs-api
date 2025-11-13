"""Script to seed the database with sample job data."""
from app import create_app
from models import db, Job
from datetime import datetime, timedelta


def seed_jobs():
    """Add sample jobs to the database."""
    app = create_app()
    
    with app.app_context():
        # Clear existing jobs (optional - comment out if you want to keep existing data)
        # Job.query.delete()
        # db.session.commit()
        
        # Check if jobs already exist
        if Job.query.count() > 0:
            print("Jobs already exist in database. Skipping seed.")
            return
        
        # Sample jobs data
        sample_jobs = [
            {
                'title': 'Sous Chef',
                'role': 'Chef',
                'company': 'Culinary Collective',
                'location': 'New York, NY',
                'description': 'Support lead chef with daily kitchen operations and menu execution.',
                'required_skills': ['Cooking', 'Food Safety', 'Inventory Management'],
                'required_certifications': ['Food Handler Certification'],
                'posted_at': datetime.utcnow() - timedelta(days=2)
            },
            {
                'title': 'Senior Software Engineer',
                'role': 'Software Engineer',
                'company': 'Tech Innovations Inc',
                'location': 'San Francisco, CA',
                'description': 'Build scalable web applications using Python and Flask. Lead technical decisions and mentor junior developers.',
                'required_skills': ['Python', 'Flask', 'PostgreSQL', 'REST APIs', 'Git'],
                'required_certifications': [],
                'posted_at': datetime.utcnow() - timedelta(days=5)
            },
            {
                'title': 'Marketing Manager',
                'role': 'Marketing',
                'company': 'Digital Marketing Solutions',
                'location': 'Chicago, IL',
                'description': 'Develop and execute marketing strategies to drive brand awareness and customer acquisition.',
                'required_skills': ['Digital Marketing', 'SEO', 'Content Strategy', 'Analytics'],
                'required_certifications': ['Google Analytics Certification'],
                'posted_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'title': 'Registered Nurse',
                'role': 'Healthcare',
                'company': 'City General Hospital',
                'location': 'Boston, MA',
                'description': 'Provide patient care in a fast-paced hospital environment. Work with a multidisciplinary team.',
                'required_skills': ['Patient Care', 'Medical Documentation', 'IV Therapy'],
                'required_certifications': ['RN License', 'BLS Certification'],
                'posted_at': datetime.utcnow() - timedelta(hours=12)
            },
            {
                'title': 'Graphic Designer',
                'role': 'Design',
                'company': 'Creative Studio',
                'location': 'Los Angeles, CA',
                'description': 'Create visual designs for digital and print media. Collaborate with clients and creative team.',
                'required_skills': ['Adobe Creative Suite', 'Typography', 'Brand Identity', 'UI/UX Design'],
                'required_certifications': [],
                'posted_at': datetime.utcnow() - timedelta(days=3)
            }
        ]
        
        # Add jobs to database
        for job_data in sample_jobs:
            job = Job(**job_data)
            db.session.add(job)
        
        db.session.commit()
        print(f"Successfully seeded {len(sample_jobs)} jobs into the database.")


if __name__ == '__main__':
    seed_jobs()

