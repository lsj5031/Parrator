"""AI-powered text refinement for transcribed speech."""

import re
import threading
from typing import Any, Optional

from .config import Config


class TextRefiner:
    """Handles AI-powered text refinement for transcriptions."""

    def __init__(self, config: Config):
        self.config = config
        self.models_loaded = False
        self.load_lock = threading.Lock()
        self._refinement_pipeline: Optional[Any] = None
        self._prompt_prefix: str = self.config.get(
            "text_refinement_prompt_prefix", "grammar:"
        )
        self._model_name: str = self.config.get(
            "text_refinement_model", "vennify/t5-base-grammar-correction"
        )

    def load_models(self) -> bool:
        """Load text processing models in background."""
        with self.load_lock:
            if self.models_loaded:
                return True

            try:
                from transformers import pipeline  # type: ignore[import]

                device = -1
                try:
                    import torch  # type: ignore[import]

                    if torch.cuda.is_available():
                        device = 0
                except ImportError:
                    pass

                print(f"Loading text refinement model: {self._model_name}")
                self._refinement_pipeline = pipeline(
                    "text2text-generation", model=self._model_name, device=device
                )
                self.models_loaded = True
                print("Text refinement models loaded successfully")
                return True

            except ImportError:
                print("Transformers not available, using basic text processing")
                self.models_loaded = False
                return False
            except Exception as e:
                print(f"Failed to load text refinement models: {e}")
                self.models_loaded = False
                return False

    def refine_text(self, text: str, asr_model: str = "") -> str:
        """Refine transcribed text using AI models."""
        if not text or not text.strip():
            return text

        if not self.config.get("enable_text_refinement", True):
            return text

        model_specific_config = self.config.get("text_refinement_models", {})
        if model_specific_config:
            model_enabled = model_specific_config.get(asr_model, True)
            if not model_enabled:
                return text

        if self.models_loaded or self.load_models():
            try:
                return self._ai_refine_text(text)
            except Exception as e:
                print(f"AI text refinement failed: {e}")
                return self._basic_refine_text(text)
        return self._basic_refine_text(text)

    def _ai_refine_text(self, text: str) -> str:
        """Use AI models for text refinement."""
        if not self._refinement_pipeline:
            return self._basic_refine_text(text)

        prompt = f"{self._prompt_prefix} {text.strip()}".strip()
        max_length = min(self.config.get("text_refinement_max_length", 256), 512)

        try:
            result = self._refinement_pipeline(
                prompt,
                num_beams=self.config.get("text_refinement_beams", 4),
                do_sample=False,
                max_length=max_length,
                clean_up_tokenization_spaces=True,
            )
            generated = result[0]["generated_text"].strip() if result else ""
            if not generated:
                return self._basic_refine_text(text)
            return self._basic_refine_text(generated)

        except Exception as e:
            print(f"AI refinement error: {e}")
            return self._basic_refine_text(text)

    def _basic_refine_text(self, text: str) -> str:
        """Basic text processing without AI models."""
        if not text:
            return text

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Remove filler words if enabled
        if self.config.get("remove_filler_words", True):
            text = self._remove_filler_words(text)

        # Basic capitalization (first letter of sentences)
        text = self._basic_capitalization(text)

        return text

    def _remove_filler_words(self, text: str) -> str:
        """Remove common filler words and disfluencies."""
        # Common filler words and disfluencies
        filler_words = self.config.get(
            "filler_words",
            [
                "uh",
                "um",
                "er",
                "ah",
                "like",
                "you know",
                "I mean",
                "sort of",
                "kind of",
                "right",
                "yeah",
                "yep",
                "yup",
                "hmm",
                "hmm",
                "well",
                "so",
                "anyway",
                "basically",
            ],
        )

        # Create regex pattern for filler words
        pattern = r"\b(?:" + "|".join(re.escape(word) for word in filler_words) + r")\b"

        # Remove filler words (case-insensitive)
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Clean up extra spaces
        text = re.sub(r"\s+", " ", text.strip())

        return text

    def _basic_capitalization(self, text: str) -> str:
        """Apply basic capitalization rules."""
        if not text:
            return text

        # Capitalize first letter of the text
        text = text[0].upper() + text[1:] if text else text

        # Capitalize after sentence-ending punctuation
        text = re.sub(
            r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text
        )

        return text

    def is_available(self) -> bool:
        """Check if text refinement is available."""
        return (
            self.models_loaded
            or self._refinement_pipeline is not None
            or self.config.get("enable_text_refinement", True)
        )

    def get_status(self) -> str:
        """Get current status of text refiner."""
        if self.models_loaded:
            return "AI models loaded"
        elif self.config.get("enable_text_refinement", True):
            return "Basic processing only"
        else:
            return "Disabled"
