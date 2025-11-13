#!/bin/bash
# Setup script for Employer API

echo "Setting up Employer API..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env 2>/dev/null || cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=supersecret-key-change-in-production
PORT=8000
DATABASE_URL=sqlite:///employer.db
EMPLOYER_API_KEY=myemployerkey123
CORS_ORIGINS=*
EOF
    echo ".env file created. Please update it with your values."
else
    echo ".env file already exists."
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
flask db init 2>/dev/null || echo "Database already initialized."
flask db migrate -m "Initial migration" 2>/dev/null
flask db upgrade

# Seed sample data
echo "Seeding sample data..."
python seed_data.py

echo "Setup complete! Run 'python app.py' to start the server."

