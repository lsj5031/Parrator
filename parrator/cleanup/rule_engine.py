"""
Rule-based text cleanup engine.

Provides fast, offline text cleaning using regex patterns and heuristics.
"""

import re
import time
from typing import Dict, Any, List, Set, Pattern

from .engine_base import CleanupEngineBase


class RuleEngine(CleanupEngineBase):
    """Rule-based text cleanup engine."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        # Filler words pattern
        filler_words = self.config.get(
            "filler_words",
            [
                "um",
                "uh",
                "er",
                "ah",
                "like",
                "you know",
                "i mean",
                "sort of",
                "kind of",
                "right",
                "yeah",
                "yep",
                "yup",
                "hmm",
                "well",
                # "so",  # Removed - can be legitimate transition word
                "anyway",
                "basically",
            ],
        )
        self.filler_pattern = re.compile(
            r"\b(?:" + "|".join(re.escape(word) for word in filler_words) + r")\b",
            flags=re.IGNORECASE,
        )

        # Patterns to preserve
        self.url_pattern = re.compile(r"https?://[^\s]+")
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.code_pattern = re.compile(r"`[^`]+`")
        self.hashtag_pattern = re.compile(r"#[A-Za-z0-9_]+")
        self.emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]"
        )

        # Text cleaning patterns
        self.whitespace_pattern = re.compile(r"\s+")
        self.repeated_words_pattern = re.compile(
            r"\b(\w+)(?:\s+\1)+\b", flags=re.IGNORECASE
        )
        self.repeated_letters_pattern = re.compile(r"([a-zA-Z])\1{2,}")
        self.punctuation_spacing_pattern = re.compile(r"\s*([,.!?;:])\s*")
        self.sentence_boundary_pattern = re.compile(r"([.!?]+)\s*([a-z])")

        # Grammar patterns
        self.i_pattern = re.compile(r"\bi\b", flags=re.IGNORECASE)
        self.a_an_pattern = re.compile(r"\b(a)\s+([aeiou])", flags=re.IGNORECASE)
        self.an_consonant_pattern = re.compile(
            r"\b(an)\s+([bcdfghjklmnpqrstvwxyz])", flags=re.IGNORECASE
        )

    def clean(self, text: str, mode: str = "standard") -> str:
        """Clean text using rule-based patterns."""
        if not text or not text.strip():
            return ""

        start_time = time.time()
        original_length = len(text)

        # Step 1: Pre-clean (always applied)
        text = self._pre_clean(text)

        # Step 2: Mode-specific processing
        if mode == "conservative":
            text = self._conservative_clean(text)
        elif mode == "standard":
            text = self._standard_clean(text)
        elif mode == "rewrite":
            text = self._rewrite_clean(text)

        # Step 3: Final cleanup
        text = self._final_clean(text)

        # Performance tracking
        processing_time = (time.time() - start_time) * 1000
        chars_saved = original_length - len(text)

        if chars_saved > 0:
            print(
                f"Cleaned: {original_length} → {len(text)} chars • {processing_time:.0f}ms"
            )

        return text.strip()

    def _pre_clean(self, text: str) -> str:
        """Apply basic pre-cleaning that's always needed."""
        if not text or not text.strip():
            return ""

        # Store preserved segments with placeholders
        preserved_segments = []
        placeholder_map = {}
        placeholder_counter = 0

        # Find all segments to preserve in order of appearance
        all_matches = []
        for pattern in [
            self.url_pattern,
            self.email_pattern,
            self.code_pattern,
            self.hashtag_pattern,
            self.emoji_pattern,
        ]:
            for match in pattern.finditer(text):
                all_matches.append((match.start(), match.end(), match.group(), pattern))

        # Sort by start position and process from right to left to avoid position shifts
        all_matches.sort(key=lambda x: x[0], reverse=True)

        for start, end, segment, pattern in all_matches:
            placeholder = f"__PRESERVED_{placeholder_counter}__"
            placeholder_map[placeholder] = segment
            text = text[:start] + placeholder + text[end:]
            placeholder_counter += 1

        # Normalize whitespace (but be careful with placeholders)
        text = self.whitespace_pattern.sub(" ", text.strip())

        # Fix punctuation spacing (but be careful with placeholders)
        text = self.punctuation_spacing_pattern.sub(r" \1 ", text)
        text = self.whitespace_pattern.sub(" ", text)

        # Remove repeated words (e.g., "the the")
        text = self.repeated_words_pattern.sub(r"\1", text)

        # Fix repeated letters (e.g., "sooo" -> "so")
        text = self.repeated_letters_pattern.sub(r"\1\1", text)

        # Restore preserved segments from placeholders
        for placeholder, original in placeholder_map.items():
            text = text.replace(placeholder, original)

        return text

    def _conservative_clean(self, text: str) -> str:
        """Conservative mode: basic grammar and punctuation only."""
        # Capitalize "I"
        text = self.i_pattern.sub("I", text)

        # Fix a/an errors (basic)
        text = self.a_an_pattern.sub(r"an \2", text)
        text = self.an_consonant_pattern.sub(r"a \2", text)

        # Basic sentence capitalization
        text = self._sentence_capitalization(text)

        return text

    def _standard_clean(self, text: str) -> str:
        """Standard mode: conservative + filler removal + minor tightening."""
        # Apply conservative cleaning first
        text = self._conservative_clean(text)

        # Remove filler words (with context awareness)
        text = self._remove_filler_words_safe(text)

        # Remove redundant phrases
        text = self._remove_redundant_phrases(text)

        # Re-apply sentence capitalization after phrase removal
        text = self._sentence_capitalization(text)

        return text

    def _rewrite_clean(self, text: str) -> str:
        """Rewrite mode: standard + more aggressive tightening."""
        # Apply standard cleaning first
        text = self._standard_clean(text)

        # More aggressive phrase tightening
        text = self._aggressive_tightening(text)

        # Improve flow and conciseness
        text = self._improve_flow(text)

        return text

    def _final_clean(self, text: str) -> str:
        """Apply final cleanup to all modes."""
        if not text:
            return text

        # Store preserved segments with placeholders to avoid modifying them
        preserved_segments = []
        placeholder_map = {}
        placeholder_counter = 0

        # Add missing punctuation for better readability BEFORE preserving URLs
        # Add colon after "link" when followed by URL
        text = re.sub(r"\blink\s+(https?://)", r"link: \1", text, flags=re.IGNORECASE)

        # Add sentence boundaries where appropriate
        # Add period before sentences that start with capital letters but lack punctuation
        text = re.sub(r"([a-z])\s+([A-Z][a-z]+)", r"\1. \2", text)

        # Capitalize standalone "thanks" at the end of sentences (without period - final cleanup will add it)
        text = re.sub(r"\bthanks\b\.?$", "Thanks", text)

        # Find all segments to preserve
        all_matches = []
        for pattern in [self.url_pattern, self.email_pattern, self.code_pattern]:
            for match in pattern.finditer(text):
                all_matches.append((match.start(), match.end(), match.group()))

        # Sort by start position and process from right to left
        all_matches.sort(key=lambda x: x[0], reverse=True)

        for start, end, segment in all_matches:
            placeholder = f"__FINAL_PRESERVED_{placeholder_counter}__"
            placeholder_map[placeholder] = segment
            text = text[:start] + placeholder + text[end:]
            placeholder_counter += 1

        # Final whitespace cleanup
        text = self.whitespace_pattern.sub(" ", text.strip())

        # Fix double punctuation and spaces
        text = re.sub(r",+", ",", text)  # Fix double commas
        text = re.sub(r"\s+", " ", text)  # Fix multiple spaces
        text = re.sub(r"\s*,\s*", ", ", text)  # Fix comma spacing
        text = re.sub(r"\s*\.\s*", ". ", text)  # Fix period spacing

        # Remove space before punctuation
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)

        # Ensure space after punctuation (except when at end)
        text = re.sub(r"([,.!?;:])(?=[^\s])", r"\1 ", text)

        # Clean up any remaining double spaces
        text = re.sub(r"\s+", " ", text).strip()

        # Add missing punctuation for better readability
        # Add colon after "link" when followed by URL
        text = re.sub(r"\blink\s+(https?://)", r"link: \1", text, flags=re.IGNORECASE)

        # Add sentence boundaries where appropriate
        # Add period before sentences that start with capital letters but lack punctuation
        text = re.sub(r"([a-z])\s+([A-Z][a-z]+)", r"\1. \2", text)

        # Restore preserved segments
        for placeholder, original in placeholder_map.items():
            text = text.replace(placeholder, original)

        # Add period at end if missing and text doesn't end with punctuation
        if text and text[-1] not in ".!?;:":
            # Only avoid periods for code blocks (not URLs or emails)
            ends_with_code = any(
                text.endswith(match.group())
                for match in self.code_pattern.finditer(text)
            )
            if not ends_with_code:
                text += "."

        return text.strip()

    def _remove_filler_words_safe(self, text: str) -> str:
        """Remove filler words while preserving important content."""
        # Get text segments to preserve
        preserved_segments = set()

        # Find and preserve URLs, emails, code, hashtags
        for pattern in [
            self.url_pattern,
            self.email_pattern,
            self.code_pattern,
            self.hashtag_pattern,
            self.emoji_pattern,
        ]:
            for match in pattern.finditer(text):
                preserved_segments.add((match.start(), match.end()))

        # Remove filler words with word boundary awareness
        def replace_filler(match):
            word_start = match.start()
            word_end = match.end()

            # Check if this filler word is within a preserved segment
            is_preserved = any(
                start <= word_start and word_end <= end
                for start, end in preserved_segments
            )

            if is_preserved:
                return match.group()  # Keep it
            else:
                return ""  # Remove it

        # Apply filler removal with preservation check
        filler_pattern_with_flags = re.compile(
            r"\b(?:"
            + "|".join(re.escape(word) for word in self.config.get("filler_words", []))
            + r")\b",
            flags=re.IGNORECASE,
        )
        text = filler_pattern_with_flags.sub(replace_filler, text)

        # Clean up extra spaces and fix sentence boundaries after filler removal
        text = self.whitespace_pattern.sub(" ", text.strip())

        # Fix sentence boundaries where filler words were removed between sentences
        # Example: "email. um thanks" -> "email. Thanks"
        text = re.sub(
            r"([.!?])\s+([a-z])", lambda m: m.group(1) + " " + m.group(2).upper(), text
        )

        # Add period before words like "thanks" that follow filler removal and should be new sentences
        # Common words that start new sentences after filler removal
        sentence_starters = [
            "thanks",
            "thank",
            "please",
            "sorry",
            "excuse",
            "hey",
            "hi",
            "hello",
        ]
        pattern = r"([a-z])\s+(" + "|".join(sentence_starters) + r")\b"
        text = re.sub(
            pattern,
            lambda m: m.group(1) + ". " + m.group(2).capitalize(),
            text,
            flags=re.IGNORECASE,
        )

        return text

    def _remove_redundant_phrases(self, text: str) -> str:
        """Remove redundant phrases and tighten wording."""
        redundant_patterns = [
            (r"\bi think\b", ""),  # Remove "I think" for more direct statements
            (r"\bi feel like\b", ""),  # Remove "I feel like"
            (r"\bit seems like\b", ""),  # Remove "it seems like"
            (r"\bwhat i mean is\b", ""),  # Remove "what I mean is"
            (r"\bthe thing is\b", ""),  # Remove "the thing is"
            (r"\bkind of\b", ""),  # Remove "kind of"
            (r"\bsort of\b", ""),  # Remove "sort of"
        ]

        for pattern, replacement in redundant_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Clean up any mess left by phrase removal
        text = re.sub(r"\s+", " ", text)  # Fix multiple spaces
        text = re.sub(r"\s*,\s*,\s*", ", ", text)  # Fix double commas
        text = re.sub(r",\s*,", ",", text)  # Fix consecutive commas

        return text

    def _aggressive_tightening(self, text: str) -> str:
        """More aggressive phrase tightening for rewrite mode."""
        tightening_patterns = [
            (r"\bin order to\b", "to"),
            (r"\bdue to the fact that\b", "because"),
            (r"\bat this point in time\b", "now"),
            (r"\bfor the purpose of\b", "for"),
            (r"\bon the basis of\b", "based on"),
            (r"\bwith regard to\b", "about"),
            (r"\bin the event that\b", "if"),
        ]

        for pattern, replacement in tightening_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _improve_flow(self, text: str) -> str:
        """Improve text flow and conciseness."""
        # Convert passive to active where simple
        text = re.sub(r"\bis\b\s+(\w+)\s+\bby\b", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\bare\b\s+(\w+)\s+\bby\b", r"\1", text, flags=re.IGNORECASE)

        # Remove unnecessary qualifiers
        qualifier_patterns = [
            r"\bvery\b",
            r"\breally\b",
            r"\bquite\b",
            r"\bpretty\b",
            r"\bsomewhat\b",
        ]

        for pattern in qualifier_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    def _sentence_capitalization(self, text: str) -> str:
        """Apply proper sentence capitalization."""
        # Find preserved segments to avoid capitalizing within them
        preserved_ranges = []
        for pattern in [self.url_pattern, self.email_pattern, self.code_pattern]:
            for match in pattern.finditer(text):
                preserved_ranges.append((match.start(), match.end()))

        def capitalize_safely(pos):
            """Check if position is safe to capitalize."""
            return not any(start <= pos < end for start, end in preserved_ranges)

        # Capitalize first letter if it's not in a preserved segment
        if text and capitalize_safely(0):
            text = text[0].upper() + text[1:]

        # Capitalize after sentence boundaries, avoiding preserved segments
        def capitalize_match(m):
            boundary = m.group(1)
            next_char = m.group(2)
            next_pos = m.start(2)

            if capitalize_safely(next_pos):
                return boundary + " " + next_char.upper()
            else:
                return m.group(0)  # Return unchanged

        text = self.sentence_boundary_pattern.sub(capitalize_match, text)

        return text

    def is_available(self) -> bool:
        """Rule engine is always available."""
        return True

    def get_status(self) -> str:
        """Get rule engine status."""
        return "Rule-based engine (always available)"
