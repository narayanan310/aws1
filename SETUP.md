# First-Time Setup Guide

Once you have completed the [Installation Guide](INSTALLATION.md), follow these steps to get the application running.

## 1. Verify Virtual Environment
Ensure your virtual environment is active in your terminal. You should see `(.venv)` at the beginning of your prompt.

## 2. Initialize the Application
The application uses SQLite as its database. You do not need a separate database server. The database tables will be automatically created the first time the application runs.

Start the Flask web server:
```bash
python run.py
```
You should see output indicating the server is running on `http://127.0.0.1:5000`. Keep this terminal open.

## 3. Start Background Workers
The application relies on a background worker to process image thumbnails asynchronously so that the web interface remains fast. 

Open a **second terminal window**, activate your virtual environment, and run:
```bash
source .venv/bin/activate
python run_workers.py
```
This script will continuously poll the database queue for new tasks.

## 4. Access the Interface
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```
- Since there are no users initially, you will be prompted to create an account or log in. (Note: In development mode, authentication might be mocked or accept any username/password combination based on your configuration).

## 5. Verify the Installation
1. Go to the **Upload** section or drag an image into the Gallery dropzone.
2. The image will be uploaded immediately.
3. Check the second terminal (running `run_workers.py`). You should see logs indicating that the `IMAGE_PROCESSING` task was picked up and completed.
4. Refresh your browser; the newly generated thumbnail should now be visible in the masonry grid.

Congratulations, your local Photo Manager is up and running!
