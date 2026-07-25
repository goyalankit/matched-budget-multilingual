"""Lazy fastText adapter for the registered GlotLID classifier."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

# Swahili is an ISO-639-3 macrolanguage (swa) whose GlotLID members are swh
# (coastal / standard Kiswahili) and swc (Congo Swahili). MGSM Swahili traces are
# frequently coded swc; both are Swahili, so both map to `sw` (macrolanguage
# grouping; validated against blind adjudication in the §6 packet). Neighbouring
# Bantu languages (e.g. kdc, kam) are NOT Swahili and remain "other".
_ISO3_TO_STUDY_LANGUAGE = {
    "deu": "de",
    "eng": "en",
    "swh": "sw",
    "swc": "sw",
    "swa": "sw",
    "tha": "th",
}
_MODEL_ENV = "GLOTLID_MODEL_PATH"
_REPOSITORY = "cis-lmu/glotlid"
_FILENAME = "model.bin"


class _FastTextModel(Protocol):
    def predict(self, text: str, k: int = 1): ...


ModelLoader = Callable[[str], _FastTextModel]


def map_glotlid_label(label: str) -> str:
    """Map a GlotLID ISO-639-3/script label to the study language codes."""
    normalized = label.removeprefix("__label__")
    iso3 = normalized.split("_", maxsplit=1)[0]
    return _ISO3_TO_STUDY_LANGUAGE.get(iso3, "other")


def _default_model_loader(path: str) -> _FastTextModel:
    import fasttext

    return fasttext.load_model(path)


class GlotLIDClassifier:
    """Classify text with lazily loaded GlotLID fastText weights."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        model_loader: ModelLoader | None = None,
    ) -> None:
        self._configured_path = Path(model_path) if model_path is not None else None
        self._model_loader = model_loader or _default_model_loader
        self._model: _FastTextModel | None = None
        self._loaded_path: Path | None = None

    @property
    def model_path(self) -> Path | None:
        """Return the loaded model path, or an explicit configured path."""
        return self._loaded_path or self._configured_path

    def _resolve_model_path(self) -> Path:
        if self._configured_path is not None:
            return self._configured_path
        environment_path = os.environ.get(_MODEL_ENV)
        if environment_path:
            return Path(environment_path)

        from huggingface_hub import hf_hub_download

        return Path(hf_hub_download(repo_id=_REPOSITORY, filename=_FILENAME))

    def _load_model(self) -> _FastTextModel:
        if self._model is None:
            path = self._resolve_model_path()
            self._model = self._model_loader(str(path))
            self._loaded_path = path
        return self._model

    def classify(self, text: str) -> str:
        """Return a study language code for GlotLID's top prediction."""
        labels, _ = self._load_model().predict(text.replace("\n", " "), k=1)
        if not labels:
            raise RuntimeError("GlotLID returned no language prediction")
        return map_glotlid_label(str(labels[0]))
