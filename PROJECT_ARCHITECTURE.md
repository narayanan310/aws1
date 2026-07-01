# Project Architecture

The Photo Manager application is designed with a clean separation of concerns, heavily inspired by Domain-Driven Design (DDD), to keep the codebase maintainable as it scales.

## High-Level Architecture

The system operates as a classic monolithic client-server architecture supplemented by an asynchronous background worker layer.

1. **Client (Browser)**: A Vanilla HTML/CSS interface augmented with Alpine.js for lightweight reactivity (modals, slide-out panels, drag-and-drop).
2. **Web Server (Flask)**: Handles synchronous HTTP requests, authentication, and writes tasks to a database queue.
3. **Database (SQLite)**: Stores user data, photo metadata, relational tags, and the asynchronous task queue.
4. **File System**: Stores the physical raw uploads and processed thumbnail/preview variants.
5. **Background Workers**: A separate Python process (`run_workers.py`) that polls the database for tasks and executes heavy processing off the main web thread.

## Folder Structure & Module Responsibilities

```text
app/
├── application/       # Application Layer (Services)
│   ├── services/      # e.g., PhotoService, CatalogService
├── domain/            # Domain Layer
│   ├── entities/      # Enums and core domain definitions
│   ├── exceptions/    # Business logic exceptions (ValidationError, NotFoundError)
├── infrastructure/    # Infrastructure Layer
│   ├── database/      # SQLAlchemy Models (User, Photo, Tag, ProcessingQueue)
│   ├── repositories/  # Data Access Objects (PhotoRepository)
├── presentation/      # Presentation Layer
│   ├── blueprints/    # Flask Routing Controllers
│   ├── templates/     # Jinja2 HTML Templates
│   ├── static/        # CSS and JS assets
├── workers/           # Asynchronous worker implementations (ImageWorker)
```

## Data Flow: Upload Pipeline

1. **Frontend**: The user drops an image onto the UI. A `FormData` POST request is sent to `/api/upload`.
2. **Blueprint**: `photos.py` intercepts the request and extracts user metadata (like initial tags or descriptions).
3. **Service**: `PhotoService.upload_many()` validates the file extension and MIME type.
4. **Repository**: `PhotoRepository` creates a new `Photo` record in the SQLite database.
5. **Storage**: The raw image is saved to `uploads/users/<uuid>/original/`.
6. **Queue**: The service inserts a new row into the `ProcessingQueue` table with `task_type="IMAGE_PROCESSING"` and links it to the `photo_id`.
7. **Response**: Flask returns a `200 OK` JSON response to the frontend, which dynamically appends the new photo card to the masonry grid in a "Processing" state.

## Background Worker Flow

1. The `run_workers.py` script continuously polls the `ProcessingQueue` table looking for tasks with `status="pending"`.
2. The `ImageWorker` picks up the task and locks it by setting `status="processing"`.
3. It loads the original image from the filesystem using Pillow.
4. It resizes and compresses the image into two variants: `preview` (mid-res for the lightbox) and `thumbnail` (low-res for the grid).
5. Upon successful generation, it sets the `Photo.processing_status` to `"completed"` and marks the queue task as `"completed"`.
6. (If the user refreshes the frontend, the updated status fetches the correct thumbnail URL instead of the loading spinner).
