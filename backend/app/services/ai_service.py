"""AI service: embeddings (Vertex) and LLM (Gemini Flash/Pro) with streaming."""

from typing import AsyncIterator, Iterator, List

import numpy as np

from app.core.config import settings
from app.core.exceptions import EmbeddingError, RAGError
from app.core.logging_config import get_logger
from app.models.chat_models import RAGMode

logger = get_logger(__name__)


def _get_vertex_embedding() -> "Any":
    """Lazy load Vertex AI embedding model."""
    try:
        from vertexai.language_models import TextEmbeddingModel
        import vertexai
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        return TextEmbeddingModel.from_pretrained(settings.vertex_text_embedding_model)
    except Exception as e:
        logger.debug("Vertex AI embedding not available: %s", e)
        return None


def _get_gemini_model(use_pro: bool = False) -> "Any":
    """Lazy load Gemini model. use_pro=True for deep_dive."""
    try:
        from vertexai.generative_models import GenerativeModel
        import vertexai
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        model_name = settings.vertex_pro_model if use_pro else settings.vertex_flash_model
        return GenerativeModel(model_name)
    except Exception as e:
        logger.debug("Vertex AI Gemini not available: %s", e)
        return None


class AIService:
    """
    AI orchestration: embeddings (Vertex) and LLM (Gemini Flash/Pro).
    Falls back to placeholder when GCP credentials unavailable.
    """

    def __init__(self) -> None:
        self._embedding_model = None
        self._flash_model = None
        self._pro_model = None

    def _embed_model(self):
        if self._embedding_model is None:
            self._embedding_model = _get_vertex_embedding()
        return self._embedding_model

    def _gemini(self, use_pro: bool = False):
        if use_pro:
            if self._pro_model is None:
                self._pro_model = _get_gemini_model(use_pro=True)
            return self._pro_model
        if self._flash_model is None:
            self._flash_model = _get_gemini_model(use_pro=False)
        return self._flash_model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings. Falls back to deterministic dummy vectors if Vertex unavailable."""
        if not texts:
            raise EmbeddingError("No texts to embed.")

        # Free-key mode: API-key varsa (GOOGLE_API_KEY set) sadece API-key ile embedding al.
        # Bu şekilde Vertex/ADC (Application Default Credentials) aramasına hiç düşmeyiz.
        if settings.google_api_key:
            try:
                import google.genai as genai

                client = genai.Client(api_key=settings.google_api_key)
                resp = client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=texts,
                )
                embeddings = getattr(resp, "embeddings", None) or resp.model_dump().get("embeddings")  # type: ignore[union-attr]
                if embeddings:
                    vectors = [
                        (e.values if hasattr(e, "values") else e.get("values"))  # type: ignore[attr-defined]
                        for e in embeddings
                    ]
                    return np.array(vectors, dtype="float32")
                logger.warning("Gemini API-key embedding returned empty embeddings, using fallback.")
            except Exception as e:
                logger.warning("Gemini API-key embedding failed (free-key-only mode): %s", e)

            # Free-key-only mode: Vertex/ADC'e geri dönme, deterministic fallback dön.
            dim = 768
            rng = np.random.default_rng(seed=42)
            return rng.normal(size=(len(texts), dim)).astype("float32")

        # Prefer API-key embeddings when available.
        # This avoids needing Vertex/ADC credentials for local/dev usage.
        model = self._embed_model()
        if model:
            try:
                embeddings = model.get_embeddings(texts)
                vectors = [e.values for e in embeddings]
                return np.array(vectors, dtype="float32")
            except Exception as e:
                logger.warning("Vertex embedding failed, using fallback: %s", e)

        dim = 768
        rng = np.random.default_rng(seed=42)
        return rng.normal(size=(len(texts), dim)).astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])

    def _build_prompt(self, mode: RAGMode, question: str, context: str) -> str:
        if mode == "summary":
            system = "You are InsightStream, a concise summarization assistant."
        elif mode == "deep_dive":
            system = "You are InsightStream, an in-depth analysis assistant."
        else:
            system = (
                "You are InsightStream, explain complex ideas in very simple "
                "language suitable for a 10-year-old."
            )
        return (
            f"{system}\n\n"
            "Use the provided context. If you don't know the answer, say so.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n"
        )

    def _use_pro_model(self, mode: RAGMode) -> bool:
        """Use Pro for deep_dive, Flash for summary and explain_to_kid."""
        return mode == "deep_dive"

    def generate_answer(
        self,
        mode: RAGMode,
        question: str,
        retrieved_chunks: List[str],
    ) -> str:
        """Generate answer (non-streaming)."""
        if not retrieved_chunks:
            raise RAGError("No context chunks retrieved for RAG.")
        context = "\n\n".join(retrieved_chunks)
        prompt = self._build_prompt(mode, question, context)
        use_pro = self._use_pro_model(mode)

        # Free-key mode: API-key varsa Vertex/ADC'ye hiç düşme.
        if settings.google_api_key:
            try:
                import google.genai as genai

                client = genai.Client(api_key=settings.google_api_key)
                model_name = settings.vertex_pro_model if use_pro else settings.vertex_flash_model
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                # google.genai responses usually expose `.text` for convenience.
                text = getattr(response, "text", None)
                if text:
                    return text
            except Exception as e:
                logger.warning("Gemini API-key generate failed (free-key-only mode): %s", e)

            return (
                "Gemini API-key ile yanıt üretilemedi. "
                "Ücretsiz kota/tahsis tükenmiş olabilir. "
                "Lütfen API key için Gemini kullanımını kontrol edip tekrar deneyin."
            )

        model = self._gemini(use_pro=use_pro)

        if model:
            try:
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning("Gemini generate failed: %s", e)

        return (
            "This is a placeholder answer. "
            "Configure GCP credentials for Vertex AI Gemini to get real responses."
        )

    def generate_answer_stream(
        self,
        mode: RAGMode,
        question: str,
        retrieved_chunks: List[str],
    ) -> Iterator[str]:
        """
        Stream answer token-by-token.
        Yields text chunks for SSE.
        """
        if not retrieved_chunks:
            raise RAGError("No context chunks retrieved for RAG.")
        context = "\n\n".join(retrieved_chunks)
        prompt = self._build_prompt(mode, question, context)
        use_pro = self._use_pro_model(mode)

        # Free-key mode: API-key varsa Vertex/ADC'ye hiç düşme.
        if settings.google_api_key:
            try:
                import google.genai as genai

                client = genai.Client(api_key=settings.google_api_key)
                model_name = settings.vertex_pro_model if use_pro else settings.vertex_flash_model

                for chunk in client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt,
                ):
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
                return
            except Exception as e:
                logger.warning("Gemini API-key stream failed (free-key-only mode): %s", e)
                yield (
                    "Gemini API-key ile streaming yanıt alınamadı. "
                    "Ücretsiz kota/tahsis tükenmiş olabilir. Lütfen tekrar deneyin."
                )
                return

        model = self._gemini(use_pro=use_pro)
        if model:
            try:
                responses = model.generate_content(prompt, stream=True)
                for response in responses:
                    if response.text:
                        yield response.text
                return
            except Exception as e:
                logger.warning("Gemini stream failed: %s", e)

        yield "Configure GCP credentials for Vertex AI Gemini to get streaming responses."
