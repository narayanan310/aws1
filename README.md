# Photo Manager

Photo Manager is a modern, privacy-focused Digital Asset Management (DAM) application built with Python and Flask. It provides professional-grade photo organization and search capabilities entirely on your local machine.

## Features

- **Professional DAM Interface**: A responsive, two-pane Staging Queue allows you to curate, independently edit, and batch-upload images seamlessly.
- **Search**: Find your photos using metadata queries.
- **Asynchronous Processing**: Non-blocking upload pipelines handle heavy lifting in background workers.
- **Comprehensive Settings**: A fully configurable dashboard to manage concurrent uploads and adjust performance parameters.

## Technology Stack

- **Backend**: Flask, SQLAlchemy (SQLite)
- **Frontend**: Vanilla JS (Single Page App mechanics), custom CSS
- **Task Queue**: Custom SQLite-backed background worker queue

## Architecture Overview

The system is split into two primary processes:
1. **Flask Web Server**: Serves the UI, handles synchronous API requests (like `/api/upload` and `/api/settings`), and inserts tasks into the database queue.
2. **Background Workers (`run_workers.py`)**: Continuously polls the database queue to process asynchronous tasks.

For detailed architecture diagrams, refer to [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md).

## Folder Structure

```text
ai-photo-manager/
├── app/
│   ├── application/     # Business logic & services (PhotoService, AIPipeline)
│   ├── domain/          # Entities & domain exceptions
│   ├── infrastructure/  # Database models, local storage, LLM integrations
│   └── presentation/    # Flask blueprints, HTML templates, CSS
├── instance/            # Local SQLite database (test.db)
├── uploads/             # Raw and processed images
├── config.py            # Environment configuration
├── run.py               # Flask development server
└── run_workers.py       # Background task processor
```

## Configuration

Nearly all aspects of the application (batch limits, caching) can be configured dynamically through the in-app **Settings** dashboard.
For a complete list of environment variables and hardcoded settings, see [CONFIGURATION.md](CONFIGURATION.md).

## Current Limitations & Roadmap

- **Multi-User**: While the database supports users, authentication is currently mocked. A proper JWT/Session auth system is planned.
- **Cloud Storage**: Currently only Local File Storage is supported. S3 compatibility is on the roadmap.

## Documentation Navigation

- [Installation Guide](INSTALLATION.md)
- [First-Time Setup](SETUP.md)
- [Requirements & Dependencies](REQUIREMENTS.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## License

This project is licensed under the MIT License.

## Author

Developed by [@narayanan310](https://github.com/narayanan310).
