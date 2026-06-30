# AI Photo Manager

AI Photo Manager is a modern, privacy-focused Digital Asset Management (DAM) application built with Python and Flask. It provides professional-grade photo organization, automated metadata generation, and semantic search capabilities entirely on your local machine using state-of-the-art open-source Vision-Language Models.

## Features

- **Professional DAM Interface**: A responsive, two-pane Staging Queue allows you to curate, independently edit, and batch-upload images seamlessly.
- **Local AI Analysis**: Automatically generate rich titles, captions, detailed descriptions, objects, tags, and suggested albums using a local Vision-Language Model (e.g. Qwen2.5-VL), ensuring complete privacy.
- **Semantic Search**: Find your photos using natural language queries powered by local embedding models.
- **Smart Metadata Merging**: Edit your metadata manually, and optionally merge it with AI-generated tags without destructive overwriting.
- **Asynchronous Processing**: Non-blocking upload pipelines handle heavy lifting (resizing, AI analysis, embeddings) in background workers.
- **Comprehensive Settings**: A fully configurable dashboard to toggle AI automation, manage concurrent uploads, switch models, and adjust performance parameters.

## Technology Stack

- **Backend**: Flask, SQLAlchemy (SQLite)
- **Frontend**: Vanilla JS (Single Page App mechanics), custom CSS
- **AI/ML**: `transformers`, `torch`, `qwen-vl` (or compatible VLMs), SentenceTransformers
- **Task Queue**: Custom SQLite-backed background worker queue

## Architecture Overview

The system is split into two primary processes:
1. **Flask Web Server**: Serves the UI, handles synchronous API requests (like `/api/upload` and `/api/settings`), and inserts tasks into the database queue.
2. **Background Workers (`run_workers.py`)**: Continuously polls the database queue to process asynchronous tasks (`IMAGE_PROCESSING`, `AI_ANALYSIS`, `EMBEDDING`), utilizing GPU acceleration when available.

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

## AI Models & Vision Pipeline

When an image is uploaded:
1. It is resized and compressed for preview.
2. If AI analysis is not manually bypassed, a task is queued.
3. The background worker loads the VLM (default: Qwen2.5-VL), formats a highly specific prompt, and generates structured JSON metadata describing the image.
4. The metadata is stored in the `AIResult` table and instantly available in the UI.

For more details on the models used, memory requirements, and alternatives, see [MODELS.md](MODELS.md).

## Configuration

Nearly all aspects of the application (AI thresholds, batch limits, tag merging) can be configured dynamically through the in-app **Settings** dashboard.
For a complete list of environment variables and hardcoded settings, see [CONFIGURATION.md](CONFIGURATION.md).

## Current Limitations & Roadmap

- **Multi-User**: While the database supports users, authentication is currently mocked. A proper JWT/Session auth system is planned.
- **Model Size**: The VLM requires a capable machine. Running 7B+ parameter VLMs on pure CPU is extremely slow.
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
