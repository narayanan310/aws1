# Configuration Guide

The Photo Manager application is designed to be easily configurable across development and production environments.

## Environment Variables

The application relies on a `.env` file located in the root directory. If this file is missing, the application will attempt to fall back on defaults, but it is highly recommended to explicitly configure it.

### Core Settings
- `FLASK_APP`: Points to the entry script. Default is `run.py`.
- `FLASK_ENV`: Set to `development` for debug mode and auto-reloading, or `production` for secure deployment.
- `SECRET_KEY`: A cryptographically secure random string used to sign session cookies. **Must be changed in production.**

### Database Settings
- `SQLALCHEMY_DATABASE_URI`: The connection string for the database. 
  - Example: `sqlite:///data/app.db`
- `SQLALCHEMY_TRACK_MODIFICATIONS`: Set to `False` to save memory (Flask-SQLAlchemy specific).

### Storage Settings
- `UPLOAD_FOLDER`: The relative or absolute path where user uploads will be stored.
  - Default: `uploads/`
- `MAX_CONTENT_LENGTH`: The maximum size of a single HTTP request (in bytes). Used to prevent users from uploading massive files and crashing the server.
  - Default: `16777216` (16 Megabytes)

## Internal UI Settings

Users can configure specific preferences through the **Settings** panel in the web interface. These settings are persisted to the user's browser or session.

- **Default View Mode**: Toggle between Grid and List view.
- **UI Animations**: Toggle Alpine.js CSS transitions.
- **Upload Behavior**: Toggle whether EXIF data should be preserved during the upload pipeline.
