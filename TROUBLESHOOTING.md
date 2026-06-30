# Troubleshooting Guide

This guide covers common issues you might encounter while setting up or running AI Photo Manager.

## Port 5000 is in Use (Address already in use)

**Symptoms:**
When running `python run.py`, you get an error:
`Address already in use. Port 5000 is in use by another program.`

**Cause:**
On macOS Monterey and later, Apple's "AirPlay Receiver" process listens on Port 5000 by default, conflicting with standard Flask behavior.

**Solution:**
1. The included `run.py` has been explicitly hardcoded to start on `port=5001`. Ensure you are using `python run.py` rather than `flask run`.
2. Alternatively, disable AirPlay Receiver in your Mac's System Settings > General > AirDrop & Handoff.

## AI Metadata is Empty or Not Generating

**Symptoms:**
You upload an image, and it appears in the gallery, but the title, description, and tags remain blank forever.

**Cause 1: Worker is not running**
The Flask app only queues tasks. You **must** have `python run_workers.py` running in a separate terminal window. 

**Cause 2: Model download failed/interrupted**
Check the worker terminal for errors. If the model failed to download from HuggingFace, restart `run_workers.py`.

**Cause 3: AI opted out**
If you checked the "Skip AI" box during upload in the Staging Queue, the AI analysis task is intentionally bypassed.

## Very Slow Uploads / Out of Memory (OOM)

**Symptoms:**
Uploading crashes the application, or `run_workers.py` crashes with a `CUDA out of memory` or `MPS out of memory` error.

**Cause:**
The VLM (Qwen2.5-VL) requires significant VRAM/Unified Memory.

**Solution:**
1. **Close other apps:** Ensure no other heavy ML models, browsers with hundreds of tabs, or games are running.
2. **CPU Fallback:** If your GPU simply cannot handle it, uninstall the GPU version of PyTorch and install the CPU version. (Note: CPU inference is extremely slow, taking upwards of 60 seconds per image).
3. **Wait:** Processing a large batch of images takes time. The UI will show a `processing_status` overlay until the worker catches up.

## Database Locks (`OperationalError: database is locked`)

**Symptoms:**
The Flask app throws a 500 error when uploading or navigating.

**Cause:**
SQLite struggles with heavy concurrent writes. If you upload a massive batch of files and the background worker is trying to write AI results simultaneously, a lock can occur.

**Solution:**
The system is designed to retry gracefully. If the UI errors out, wait a few seconds and refresh. For a permanent fix, you would need to migrate the SQLAlchemy backend to PostgreSQL.

## Missing Dependencies (`ModuleNotFoundError`)

**Symptoms:**
Running `run.py` or `run_workers.py` immediately crashes complaining about missing modules.

**Solution:**
Ensure your virtual environment is activated before running the scripts!
```bash
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```
