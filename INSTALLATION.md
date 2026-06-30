# Installation Guide

This document covers how to install AI Photo Manager and its prerequisites on your local machine.

## Supported Operating Systems

- **macOS**: Fully supported (Apple Silicon highly recommended for AI features).
- **Linux**: Fully supported (Ubuntu 22.04+ recommended, NVIDIA GPU highly recommended).
- **Windows**: Supported via WSL2 or natively (NVIDIA GPU recommended).

## Prerequisites

Before installing, ensure you have the following installed on your system:
- **Python**: Version `3.10` or `3.11`. (Python 3.12+ may have compatibility issues with some older ML libraries).
- **Git**: To clone the repository.
- **SQLite**: Comes pre-installed with Python, but ensure the C-extensions are available.

*Note: Node.js is **not** required for this project, as the frontend uses Vanilla JS directly injected into Flask templates.*

## 1. Clone the Repository

```bash
git clone https://github.com/narayanan310/AWS.git
cd AWS
```

## 2. Create a Virtual Environment

It is highly recommended to isolate your dependencies using a Python virtual environment.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

*(See [REQUIREMENTS.md](REQUIREMENTS.md) for a detailed breakdown of what is being installed.)*

## 4. Hardware Acceleration (Optional but Recommended)

By default, PyTorch will install the CPU version on macOS and standard versions on Linux/Windows. If you have an NVIDIA GPU, you should install the CUDA-enabled version of PyTorch to drastically speed up AI inference.

**For NVIDIA GPUs (Linux / Windows WSL2):**
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**For Apple Silicon (M1/M2/M3):**
PyTorch natively supports MPS (Metal Performance Shaders). No additional installation is required! The backend automatically detects `mps` and uses it.

## 5. Model Downloads

You do not need to download models manually!
Upon starting the background workers for the first time, the `transformers` library will automatically download the default Vision-Language Model (`Qwen/Qwen2.5-VL-3B-Instruct`) to your local HuggingFace cache directory (usually `~/.cache/huggingface`).

*Note: The initial download will take a few minutes as the model is several gigabytes in size.*

## Next Steps

Once installation is complete, proceed to [SETUP.md](SETUP.md) for instructions on configuring your environment variables, initializing the database, and running the application.
