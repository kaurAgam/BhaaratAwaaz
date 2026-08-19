from __future__ import annotations

from pathlib import Path

import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
)

from IndicTransToolkit.processor import IndicProcessor

from shared.config import Config
from shared.logging import setup_logging


logger = setup_logging()


class TranslationError(Exception):
    """Base exception for translation-related errors."""


class Translator:
    """
    Offline IndicTrans2 translation module.

    Supported:
        English ↔ Hindi
        English ↔ Marathi
        Hindi ↔ Marathi

    Translation is performed in batches to avoid
    running the model separately for every ASR segment.
    """

    MODEL_DIRS = {
        "en-indic": "indictrans2-en-indic-dist-200M",
        "indic-en": "indictrans2-indic-en-dist-200M",
        "indic-indic": "indictrans2-indic-indic-dist-320M",
    }

    LANGUAGES = {
        "en": "eng_Latn",
        "hi": "hin_Deva",
        "mr": "mar_Deva",
    }

    def __init__(
        self,
        model_root: str | Path = Config.TRANSLATION_MODEL_DIR,
        device: str = Config.TRANSLATION_DEVICE,
        batch_size: int = Config.TRANSLATION_BATCH_SIZE,
        num_beams: int = Config.TRANSLATION_NUM_BEAMS,
        max_new_tokens: int = Config.TRANSLATION_MAX_NEW_TOKENS,
    ):
        self.model_root = Path(model_root)
        self.device = device

        self.batch_size = batch_size
        self.num_beams = num_beams
        self.max_new_tokens = max_new_tokens

        # Models are loaded lazily.
        #
        # Once loaded, they stay in memory and are reused
        # for subsequent requests.
        self._models = {}
        self._tokenizers = {}
        self._processors = {}

    # ========================================================
    # Model selection
    # ========================================================

    def _get_model_type(
        self,
        source_language: str,
        target_language: str,
    ) -> str:

        source_is_english = source_language == "en"
        target_is_english = target_language == "en"

        if source_is_english and not target_is_english:
            return "en-indic"

        if not source_is_english and target_is_english:
            return "indic-en"

        if not source_is_english and not target_is_english:
            return "indic-indic"

        raise TranslationError(
            "English → English translation is not supported."
        )

    # ========================================================
    # Load model
    # ========================================================

    def _load_model(self, model_type: str):

        if model_type in self._models:

            return (
                self._tokenizers[model_type],
                self._models[model_type],
                self._processors[model_type],
            )

        model_name = self.MODEL_DIRS[model_type]

        model_path = self.model_root / model_name

        if not model_path.exists():
            raise FileNotFoundError(
                f"IndicTrans2 model not found: {model_path}"
            )

        logger.info(
            "Loading translation model: %s",
            model_path,
        )

        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path),
            trust_remote_code=True,
            local_files_only=True,
        )

        if self.device == "cuda":
            dtype = torch.float16
        else:
            dtype = torch.float32

        model = AutoModelForSeq2SeqLM.from_pretrained(
            str(model_path),
            trust_remote_code=True,
            torch_dtype=dtype,
            local_files_only=True,
        ).to(self.device)

        model.eval()

        processor = IndicProcessor(
            inference=True
        )

        self._tokenizers[model_type] = tokenizer
        self._models[model_type] = model
        self._processors[model_type] = processor

        logger.info(
            "Translation model loaded | type=%s | device=%s",
            model_type,
            self.device,
        )

        return (
            tokenizer,
            model,
            processor,
        )

    # ========================================================
    # Single text
    # ========================================================

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:

        if not text or not text.strip():
            return ""

        results = self.translate_batch(
            texts=[text],
            source_language=source_language,
            target_language=target_language,
        )

        return results[0]

    # ========================================================
    # Batch translation
    # ========================================================

    def translate_batch(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> list[str]:

        if source_language not in self.LANGUAGES:
            raise TranslationError(
                f"Unsupported source language: "
                f"{source_language}"
            )

        if target_language not in self.LANGUAGES:
            raise TranslationError(
                f"Unsupported target language: "
                f"{target_language}"
            )

        if not texts:
            return []

        # No translation required.
        if source_language == target_language:
            return texts

        model_type = self._get_model_type(
            source_language,
            target_language,
        )

        tokenizer, model, processor = self._load_model(
            model_type
        )

        src_lang = self.LANGUAGES[source_language]
        tgt_lang = self.LANGUAGES[target_language]

        all_translations = []

        # ----------------------------------------------------
        # Process in controlled batches
        # ----------------------------------------------------

        total = len(texts)

        for start in range(0, total, self.batch_size):

            end = min(
                start + self.batch_size,
                total,
            )

            batch_texts = texts[start:end]

            logger.info(
                "Translation batch | segments=%d-%d/%d",
                start + 1,
                end,
                total,
            )

            # ------------------------------------------------
            # IndicTrans preprocessing
            # ------------------------------------------------

            processed_batch = processor.preprocess_batch(
                batch_texts,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
            )

            inputs = tokenizer(
                processed_batch,
                truncation=True,
                padding=True,
                return_tensors="pt",
                return_attention_mask=True,
            )

            inputs = {
                key: value.to(self.device)
                for key, value in inputs.items()
            }

            # ------------------------------------------------
            # Translation
            # ------------------------------------------------

            with torch.inference_mode():

                generated_tokens = model.generate(
                    **inputs,
                    use_cache=True,

                    # Maximum number of tokens generated
                    # for each translated segment.
                    max_new_tokens=self.max_new_tokens,

                    # Beam search.
                    num_beams=self.num_beams,

                    num_return_sequences=1,
                )

            # ------------------------------------------------
            # Decode
            # ------------------------------------------------

            generated_text = tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )

            translations = processor.postprocess_batch(
                generated_text,
                lang=tgt_lang,
            )

            all_translations.extend(translations)

        return all_translations

    # ========================================================
    # Segment translation
    # ========================================================

    def translate_segments(
        self,
        segments: list[dict],
        source_language: str,
        target_language: str,
    ) -> list[dict]:

        if not segments:
            return []

        source_texts = [
            segment["text"]
            for segment in segments
        ]

        logger.info(
            "Translating %d segments | %s -> %s | batch_size=%d",
            len(source_texts),
            source_language,
            target_language,
            self.batch_size,
        )

        translated_texts = self.translate_batch(
            texts=source_texts,
            source_language=source_language,
            target_language=target_language,
        )

        if len(translated_texts) != len(segments):
            raise TranslationError(
                "Translation output count does not match "
                "the number of input segments."
            )

        results = []

        for segment, translated_text in zip(
            segments,
            translated_texts,
        ):

            results.append(
                {
                    "id": segment["id"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "source_text": segment["text"],
                    "translated_text": translated_text,
                }
            )

        return results