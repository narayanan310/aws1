#!/bin/bash
# Usage: ./deploy.sh /path/to/your-key.pem

if [ -z "$1" ]; then
    echo "Error: Please provide the path to your .pem file."
    echo "Usage: ./deploy.sh /path/to/your-key.pem"
    exit 1
fi

PEM_FILE=$1
SERVER="ubuntu@34.201.10.184"

# Set correct permissions for the key
chmod 400 "$PEM_FILE"

echo "Deploying to EC2 instance $SERVER..."

ssh -i "$PEM_FILE" -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
    # Navigate to project directory (assuming it's cloned to ~/ai-photo-manager)
    cd ~/ai-photo-manager || { echo "Project directory not found!"; exit 1; }

    # Pull latest changes from git
    echo "Pulling latest changes from git..."
    git pull origin main

    # Update dependencies
    echo "Updating dependencies..."
    source .venv/bin/activate
    pip install -r requirements.txt

    # Restart the application (using whatever process manager is configured, e.g. systemctl or pkill)
    echo "Restarting workers..."
    pkill -f run_workers.py || true
    nohup python run_workers.py > workers.log 2>&1 &
    
    echo "Deployment successful!"
EOF
