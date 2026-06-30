# Requirements

This document lists the software, Python packages, and AI models required to run AI Photo Manager.

## Software

- **Python**: v3.10 or v3.11 (Package manager: `pip`)
- **System Libraries**: On Linux, you may need `libgl1-mesa-glx` for OpenCV image processing.

## Python Packages

The following core packages are required (see `requirements.txt` for exact pinned versions):

### Web & API
- `Flask`: The core web framework.
- `Flask-Login`: Session management and user authentication.
- `Werkzeug`: WSGI utility library (handles secure file uploads).

### Database & Storage
- `SQLAlchemy`: ORM for database interactions.
- `Flask-SQLAlchemy`: Flask extension for SQLAlchemy.

### AI & Machine Learning
- `torch` & `torchvision`: PyTorch framework for running neural networks.
- `transformers`: HuggingFace library used to load and run the Vision-Language Models.
- `sentence-transformers`: Used to generate vector embeddings for semantic search.
- `qwen-vl-utils`: Utility library specific to Qwen models for processing visual inputs.
- `Pillow`: Image processing library (resizing, format conversion).
- `numpy`: Numerical processing required by ML libraries.

## AI Models

AI Photo Manager relies on locally executed open-source models for absolute privacy.

### 1. Vision-Language Model (VLM)
- **Model Name**: `Qwen/Qwen2.5-VL-3B-Instruct`
- **Purpose**: Analyzes the raw image and generates the JSON payload containing the title, caption, detailed description, tags, objects, and OCR text.
- **Why this model?**: It is currently the state-of-the-art open-weight VLM in the sub-5B parameter category. It understands varied aspect ratios natively and excels at OCR and document understanding.
- **Download Size**: ~6 GB.
- **Hardware Requirements**:
  - **Memory (RAM/VRAM)**: Requires ~8GB of VRAM/Unified Memory to run comfortably at `bfloat16` precision.
  - **GPU**: Highly recommended. Runs on NVIDIA GPUs (CUDA) or Apple Silicon (MPS).
  - **CPU Compatibility**: Can run on CPU, but inference will take 30-90 seconds per image instead of 1-3 seconds on a GPU.

### 2. Embedding Model
- **Model Name**: `all-MiniLM-L6-v2` (via SentenceTransformers)
- **Purpose**: Converts the AI-generated descriptions and tags into numerical vectors. These vectors are then compared during Semantic Search (e.g., searching for "a sunny day at the beach").
- **Download Size**: ~90 MB.
- **Hardware Requirements**: Very lightweight. Runs perfectly fine on CPU, taking milliseconds.

### Storage Location
All models are automatically downloaded by the `transformers` library on first run. They are cached in your user directory:
- macOS/Linux: `~/.cache/huggingface/hub/`
- Windows: `C:\Users\<User>\.cache\huggingface\hub\`
