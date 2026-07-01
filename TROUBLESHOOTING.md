# Troubleshooting

This guide addresses common issues you might encounter while installing or running the Photo Manager.

## 1. Database Locking Errors
**Symptom**: `sqlite3.OperationalError: database is locked` in the background worker logs.
**Cause**: SQLite only allows one process to write to the database at a time. If the web server and the background worker try to write to the exact same row simultaneously, a lock occurs.
**Solution**: This is generally harmless as SQLAlchemy will retry. However, if it persists, ensure you do not have multiple `run_workers.py` scripts running concurrently.

## 2. Uploads Failing (HTTP 413)
**Symptom**: The browser network tab shows `413 Request Entity Too Large` when uploading photos.
**Cause**: The uploaded file exceeds the `MAX_CONTENT_LENGTH` defined in `.env`.
**Solution**: Increase the `MAX_CONTENT_LENGTH` in your `.env` file (e.g., set to `52428800` for 50MB) and restart the Flask server.

## 3. Thumbnails Never Generate
**Symptom**: Photos remain in a "Processing" state indefinitely in the gallery.
**Cause**: The background worker process is not running, or it crashed.
**Solution**: Check the terminal running `python run_workers.py`. If it crashed, look for stack traces. Ensure Pillow is correctly installed. Restart the worker.

## 4. Port 5000 is Already in Use
**Symptom**: `OSError: [Errno 98] Address already in use` when running `python run.py`.
**Cause**: Another application (or another instance of Flask) is already bound to port 5000.
**Solution**: 
- Find and kill the existing process.
- Or, run Flask on a different port: `flask run --port=5001`.

## 5. Missing Static Files or Styles
**Symptom**: The web interface looks unstyled (white background, standard blue links).
**Cause**: Static files failed to load.
**Solution**: Check your browser's console. If it's a 404 error, ensure you are running the application from the root directory (`ai-photo-manager/`) so the relative static paths resolve correctly.
