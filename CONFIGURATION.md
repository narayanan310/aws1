# Configuration

AI Photo Manager can be configured via environment variables (for server-level settings) and through the in-app UI (for application behavior).

## Environment Variables

These settings must be defined in the `.env` file at the root of the project.

| Variable | Default Value | Description |
|---|---|---|
| `FLASK_APP` | `run.py` | The entry point for the Flask application. |
| `FLASK_ENV` | `development` | Sets the Flask environment. Use `production` for deployment. |
| `SECRET_KEY` | *None* | **Required.** Cryptographic key for securing session cookies. |
| `DATABASE_URL` | `sqlite:///test.db` | The connection string for SQLAlchemy. |
| `UPLOAD_FOLDER` | `uploads/` | Directory where raw and processed images are stored. |
| `MAX_CONTENT_LENGTH` | `16777216` | Maximum file upload size in bytes (default: 16 MB). |

## UI Settings Dashboard

Once logged in, users can access the **Settings** page from the top navigation bar. These settings are stored persistently in the database as a JSON blob attached to the `User` model.

### AI Pipeline
- **Enable automatic AI analysis globally**: Toggles whether the VLM runs automatically on new uploads.
- **Preferred Vision Model**: Dropdown to select the underlying VLM (e.g., Qwen vs LLaVA).
- **AI Confidence Threshold**: Minimum confidence score (0.0 to 1.0) required to save an AI-generated tag.
- **Feature Toggles**: Individually enable or disable Auto-Tags, Auto-Captions, OCR, and Object Detection to save processing time.

### Upload Behavior
- **Maximum Concurrent Uploads**: Limits how many images are sent to the server simultaneously from the Staging Queue to prevent network flooding.
- **Compress images before upload**: If checked, the browser may apply compression (future implementation).
- **Preserve Original EXIF Metadata**: Ensures camera metadata is not stripped during processing.

### Metadata & Interface
- **Default Category/Album**: Automatically places new uploads into a specific category.
- **Merge AI tags with user tags**: If you manually enter tags in the Staging Queue, the AI will append to them rather than replacing them.
- **Enable UI Animations**: Toggles CSS transitions.

## Worker Configuration

The background worker logic is currently configured in `run_workers.py`. 
You can adjust the sleep polling interval directly in the code if you prefer the worker to poll the database less aggressively than the default 5 seconds.
