"""Script to fetch all jobs from the deployed API."""
import requests
import json
from datetime import datetime

# Your deployed API URL
API_URL = "https://jobs-api-s4o6.onrender.com"

def fetch_jobs():
    """Fetch all jobs from the deployed API."""
    try:
        print(f"Fetching jobs from {API_URL}...")
        print(f"{'='*50}\n")
        
        response = requests.get(f"{API_URL}/jobs")
        
        if response.status_code == 200:
            jobs = response.json()
            
            print(f"✓ Successfully fetched {len(jobs)} job(s)\n")
            print(f"{'='*50}\n")
            
            # Display jobs
            for i, job in enumerate(jobs, 1):
                print(f"Job {i}/{len(jobs)}:")
                print(f"  ID: {job.get('id', 'N/A')}")
                print(f"  Title: {job.get('title', 'N/A')}")
                print(f"  Role: {job.get('role', 'N/A')}")
                print(f"  Company: {job.get('company', 'N/A')}")
                print(f"  Location: {job.get('location', 'N/A')}")
                print(f"  Posted At: {job.get('posted_at', 'N/A')}")
                print(f"  Required Skills: {', '.join(job.get('required_skills', []))}")
                print(f"  Required Certifications: {', '.join(job.get('required_certifications', []))}")
                print(f"  Description: {job.get('description', 'N/A')[:100]}...")
                print()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(jobs, f, indent=2)
            
            print(f"{'='*50}")
            print(f"✓ Jobs saved to {filename}")
            print(f"Total jobs fetched: {len(jobs)}")
            print(f"{'='*50}")
            
            return jobs
            
        else:
            print(f"✗ Failed to fetch jobs - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {str(e)}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return None


def fetch_job_by_id(job_id):
    """Fetch a specific job by ID from the deployed API."""
    try:
        print(f"Fetching job {job_id} from {API_URL}...")
        print(f"{'='*50}\n")
        
        response = requests.get(f"{API_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            
            print(f"✓ Successfully fetched job\n")
            print(f"{'='*50}\n")
            print(f"ID: {job.get('id', 'N/A')}")
            print(f"Title: {job.get('title', 'N/A')}")
            print(f"Role: {job.get('role', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")
            print(f"Posted At: {job.get('posted_at', 'N/A')}")
            print(f"Required Skills: {', '.join(job.get('required_skills', []))}")
            print(f"Required Certifications: {', '.join(job.get('required_certifications', []))}")
            print(f"Description: {job.get('description', 'N/A')}")
            print(f"{'='*50}")
            
            return job
            
        elif response.status_code == 404:
            print(f"✗ Job {job_id} not found")
            return None
        else:
            print(f"✗ Failed to fetch job - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {str(e)}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return None


if __name__ == "__main__":
    import sys
    
    # Check if a specific job ID was provided
    if len(sys.argv) > 1:
        try:
            job_id = int(sys.argv[1])
            fetch_job_by_id(job_id)
        except ValueError:
            print("Error: Job ID must be a number")
            print("Usage: python fetch_jobs_from_api.py [job_id]")
    else:
        # Fetch all jobs
        fetch_jobs()

