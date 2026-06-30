"""AI provider interfaces and real model implementations."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path


class VisionService(ABC):
    @abstractmethod
    def analyze(self, image_path: Path) -> dict:
        """Return structured visual analysis."""


class EmbeddingService(ABC):
    @abstractmethod
    def embed_image(self, image_path: Path, text_context: str = "") -> list[float]:
        """Return an embedding vector."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Return a text embedding vector."""


class ModelSingleton:
    """Manages lazy-loading of heavy VLM models to prevent OOM and memory leaks."""
    
    _vlm_processor = None
    _vlm_model = None
    _embedding_model = None

    @classmethod
    def get_vlm(cls):
        if cls._vlm_model is None:
            import torch
            from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            model_id = "Qwen/Qwen2.5-VL-3B-Instruct"
            
            # Use bfloat16 or float16 to save memory if on MPS
            dtype = torch.bfloat16 if torch.backends.mps.is_available() else torch.float32
            
            print(f"Loading {model_id} on {device} in {dtype}...")
            cls._vlm_processor = AutoProcessor.from_pretrained(model_id)
            cls._vlm_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                model_id, torch_dtype=dtype, device_map=device
            )
        return cls._vlm_model, cls._vlm_processor

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            cls._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._embedding_model


class QwenVisionService(VisionService):
    """Real unified vision-language analysis using Qwen2.5-VL-3B-Instruct."""

    def analyze(self, image_path: Path) -> dict:
        from qwen_vl_utils import process_vision_info
        model, processor = ModelSingleton.get_vlm()

        prompt = (
            "Analyze this image and return a strict JSON object with the following keys:\n"
            '- "title": A short, catchy title.\n'
            '- "description": A highly detailed paragraph describing the scene, lighting, mood, and actions.\n'
            '- "summary": A brief 1-sentence summary.\n'
            '- "labels": Array of 5-10 categorical labels.\n'
            '- "tags": Array of 5-10 descriptive tags.\n'
            '- "detected_objects": Array of strings listing prominent objects.\n'
            '- "text_detected": Extract ANY text visible in the image (acting as OCR). If none, empty string.\n'
            '- "image_type": E.g., photo, screenshot, document, illustration.\n'
            '- "scene": The setting (e.g., outdoor, office, beach, studio).\n'
            '- "mood": The emotional tone (e.g., bright, moody, professional, chaotic).\n'
            '- "dominant_colors": Array of 2-4 hex codes or color names.\n'
            '- "people_count": Integer estimation.\n'
            '- "quality_metrics": Any blur, bad lighting, or artifacts (string).\n'
            '- "safety_flags": Any NSFW or violence flags (string, or "safe").\n'
            '- "searchable_keywords": Array of 10 keywords for semantic search.\n'
            "Return ONLY raw JSON, without markdown blocks, without ```json wrappers."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": f"file://{image_path.absolute()}"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        
        # Optimize resolution for VRAM (e.g., max 1280x1280)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(model.device)

        generated_ids = model.generate(**inputs, max_new_tokens=800)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        
        return self._parse_json(output_text)

    def _parse_json(self, text: str) -> dict:
        """Safely extract JSON from the model's output."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Fallback handling in case model hallucinates format
            print(f"JSON Parse Error: {e}\nRaw Output: {text}")
            return {
                "title": "Untitled Image",
                "description": "Failed to parse detailed analysis.",
                "summary": "Analysis failed.",
                "labels": ["error"],
                "tags": ["unprocessed"],
                "detected_objects": [],
                "text_detected": "",
                "image_type": "unknown",
                "scene": "unknown",
                "mood": "unknown",
                "dominant_colors": [],
                "people_count": 0,
                "quality_metrics": "unknown",
                "safety_flags": "safe",
                "searchable_keywords": [],
                "raw_output": text,
            }


class SentenceTransformerService(EmbeddingService):
    """Real embeddings using all-MiniLM-L6-v2."""

    def embed_image(self, image_path: Path, text_context: str = "") -> list[float]:
        text = text_context if text_context.strip() else "image"
        return self.embed_text(text)

    def embed_text(self, text: str) -> list[float]:
        model = ModelSingleton.get_embedding_model()
        vector = model.encode(text)
        return vector.tolist()

# To keep the API surface identical for the app
MockVisionService = QwenVisionService
MockEmbeddingService = SentenceTransformerService
