# Requirements

This document outlines the software requirements and dependencies for the Photo Manager application.

## Software Requirements

- **Python**: 3.10+
- **Package Manager**: `pip` (included with standard Python installations)

## Python Packages (Dependencies)

The project relies on the following key packages:

- **`Flask` (3.0.3)**: The core web framework used to serve the API and frontend HTML.
- **`Flask-SQLAlchemy` (3.1.1)** & **`SQLAlchemy` (2.0.31)**: Used as the ORM to interact with the local SQLite database.
- **`Flask-Login` (0.6.3)**: Manages user authentication and session cookies securely.
- **`Pillow` (10.4.0)**: Required for image resizing, cropping, and generating web-friendly thumbnails.
- **`python-dotenv` (1.0.1)**: Loads configuration settings from the local `.env` file.
- **`loguru` (0.7.2)**: Advanced, thread-safe logging utility used across the web server and background workers.
- **`ImageHash` (4.3.1)**: Used to compute perceptual hashes for uploaded photos to detect duplicates.

### Optional Tools

- **`pytest` (8.2.2)**: Testing framework.
- **`black`, `isort`, `flake8`**: Standard code formatting and linting tools.

*Note: All AI dependencies (such as Torch and Transformers) were intentionally removed from the project during the pivot to a standard DAM architecture to reduce system requirements.*
