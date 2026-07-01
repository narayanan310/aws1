# Installation Guide

This guide will walk you through installing the Photo Manager application.

## System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended).
- **Python**: Version 3.10 or higher.
- **Git**: Required to clone the repository.

## Step-by-Step Installation

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/narayanan310/aws1.git ai-photo-manager
cd ai-photo-manager
```

### 2. Set Up a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies:
```bash
# Create a virtual environment named .venv
python -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory. You can copy the provided example:
```bash
cp .env.example .env
```
Ensure that you update the `SECRET_KEY` in `.env` if deploying beyond local development.

### 5. Next Steps
Move on to the [Setup Guide](SETUP.md) to initialize the database and run the application for the first time.
