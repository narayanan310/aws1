# First-Time Setup Guide

Follow these steps to configure and run the application for the very first time.

## 1. Configure Environment Variables

The application relies on a `.env` file for configuration. 
First, copy the example template to create your active configuration file:

```bash
cp .env.example .env
```

Open `.env` in a text editor. By default, it will look something like this:

```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///test.db
```
For local development, you do not need to change anything! 
If you plan to expose this application to a network, you **must** change the `SECRET_KEY` to a random cryptographic string.

## 2. Initialize the Database

The application uses SQLite by default. The database schema will be automatically created the first time the backend attempts to access it (using SQLAlchemy's `create_all()`).

However, to ensure the `instance` folder and the database file (`test.db`) are created properly, you should start the application once.

## 3. Start the Backend Web Server

In your first terminal window (with your virtual environment activated), start the Flask server:

```bash
python run.py
```
*Note: If you encounter an error stating "Port 5000 is in use" (common on macOS due to AirPlay Receiver), the script is configured to fall back to port 5001. If it still fails, you can run `flask run --port=5001`.*

## 4. Start the Background Workers (AI Pipeline)

The AI models and background tasks (resizing, AI analysis, vector embeddings) run in a separate process to keep the web UI fast and responsive.

Open a **second terminal window**, navigate to the project directory, activate your virtual environment, and run:

```bash
python run_workers.py
```

### Initial Model Download
The first time you start `run_workers.py`, you will see console output indicating that it is downloading `Qwen/Qwen2.5-VL-3B-Instruct` and `all-MiniLM-L6-v2` from the HuggingFace Hub. 
**This can take several minutes** depending on your internet connection. Please be patient. You only need to do this once.

## 5. Verify Installation

1. Open your web browser and navigate to `http://127.0.0.1:5001`.
2. Click **Register** to create a mock local account.
3. Once logged in, navigate to the **Upload** page.
4. Drag and drop a sample image.
5. Click **Upload All**.
6. Check your second terminal (the background worker process). You should see logs indicating the image is being processed and analyzed.
7. Navigate to your **Gallery** to see the image, and click it to view the AI-generated metadata!
