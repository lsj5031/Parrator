"""
AI-powered text refinement for transcribed speech.
"""

import re
import threading

from .config import Config


class TextRefiner:
    """Handles AI-powered text refinement for transcriptions."""

    def __init__(self, config: Config):
        self.config = config
        self.punctuation_model = None
        self.normalization_model = None
        self.models_loaded = False
        self.load_lock = threading.Lock()

    def load_models(self) -> bool:
        """Load text processing models in background."""
        with self.load_lock:
            if self.models_loaded:
                return True

            try:
                # Try to import NeMo NLP models
                from nemo.collections.nlp.models import PunctuationCapitalizationModel

                # Load punctuation and capitalization model
                model_name = "punctuation_en_distilbert"
                print(f"Loading text refinement model: {model_name}")

                self.punctuation_model = PunctuationCapitalizationModel.from_pretrained(
                    model_name
                )
                self.models_loaded = True
                print("Text refinement models loaded successfully")
                return True

            except ImportError:
                print("NeMo NLP not available, using basic text processing")
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

        # Check if text refinement is enabled
        if not self.config.get("enable_text_refinement", True):
            return text

        # Check if this ASR model should use refinement
        model_specific_config = self.config.get("text_refinement_models", {})
        if model_specific_config:
            # Check if current model is in the configuration
            model_enabled = model_specific_config.get(asr_model, True)
            if not model_enabled:
                return text

        # Try AI refinement first
        if self.models_loaded or self.load_models():
            try:
                return self._ai_refine_text(text)
            except Exception as e:
                print(f"AI text refinement failed: {e}")
                # Fall back to basic processing
                return self._basic_refine_text(text)
        else:
            # Use basic text processing
            return self._basic_refine_text(text)

    def _ai_refine_text(self, text: str) -> str:
        """Use AI models for text refinement."""
        if not self.punctuation_model:
            return self._basic_refine_text(text)

        try:
            # Add punctuation and capitalization
            refined_text = self.punctuation_model.add_punctuation_capitalization(
                [text]
            )[0]

            # Apply basic cleanup
            return self._basic_refine_text(refined_text)

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
        return self.models_loaded or self.config.get("enable_text_refinement", True)

    def get_status(self) -> str:
        """Get current status of text refiner."""
        if self.models_loaded:
            return "AI models loaded"
        elif self.config.get("enable_text_refinement", True):
            return "Basic processing only"
        else:
            return "Disabled"
