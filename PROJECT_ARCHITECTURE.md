# Project Architecture

AI Photo Manager is designed to separate fast web UI interactions from slow, compute-heavy AI inference tasks.

## High-Level Architecture

The system consists of three main components:
1. **Frontend (Vanilla JS SPA)**: Handles responsive UI updates, local file staging, and asynchronous polling.
2. **Backend (Flask API)**: Manages authentication, database state, serves files, and acts as the gatekeeper for task queuing.
3. **Background Worker (`run_workers.py`)**: A separate Python process that polls the database for tasks and executes heavy machine learning pipelines.

## Folder Structure & Module Responsibilities

```text
app/
├── application/       # Business Logic Layer
│   ├── dto/           # Data Transfer Objects
│   └── services/      # Core logic (PhotoService, AIPipelineService)
├── domain/            # Core Domain Logic
│   ├── entities/      # Enums (ActivityType, QueueTaskType)
│   └── exceptions/    # Domain-specific exceptions
├── infrastructure/    # External Dependencies Layer
│   ├── database/      # SQLAlchemy models (Photo, AIResult, User, ProcessingQueue)
│   ├── ml/            # VLM and Embedding model loading & execution
│   ├── repositories/  # Database abstractions
│   ├── security/      # File validation
│   └── storage/       # Local disk I/O
└── presentation/      # Presentation Layer
    ├── blueprints/    # Flask routes (photos.py, auth.py, api.py)
    ├── static/        # CSS and assets
    └── templates/     # Jinja2 HTML templates
```

## Data Flow: Upload & AI Pipeline

### 1. Staging & Upload (Frontend -> Backend)
- User selects files in the UI (`upload.html`). The files are staged in a local JavaScript array, allowing the user to edit metadata independently.
- User clicks "Upload All". JavaScript iterates over the queue, sending a `multipart/form-data` POST request to `/photos/api/upload` for each file.
- The Flask backend (`PhotoService.upload_many`) saves the physical file to disk, creates a `Photo` database record, and creates an empty `AIResult` record.
- **Task Queuing:** Flask pushes a `IMAGE_PROCESSING` task into the `ProcessingQueue` table. If the user did not check the "Skip AI" box, it also queues an `AI_ANALYSIS` task.

### 2. Background Processing (Worker Process)
The `run_workers.py` script continuously polls the `ProcessingQueue` table:
1. **IMAGE_PROCESSING**: Compresses the original image and creates a thumbnail (`thumbnail_path`) and a preview (`preview_path`).
2. **AI_ANALYSIS**:
   - The worker loads the VLM (`infrastructure/ml/vision_model.py`).
   - It reads the image and passes a strict JSON-forcing prompt to the model.
   - The model generates Title, Caption, Description, Tags, and Objects.
   - The worker updates the `AIResult` table with this data, and queues an `EMBEDDING` task.
3. **EMBEDDING**: 
   - The worker loads SentenceTransformers.
   - It converts the newly generated tags and description into a vector array and stores it for Semantic Search.

### Database Schema Highlight

- **`User`**: Core account information and JSON `settings`.
- **`Photo`**: Tracks file paths, hashes, dimensions, and processing status.
- **`AIResult`**: A 1-to-1 mapping with `Photo` that stores the generated tags, captions, and the raw AI JSON payload.
- **`ProcessingQueue`**: The orchestration table that manages task state (`pending`, `processing`, `completed`, `failed`).
