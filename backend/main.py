from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from utils.pdf_utils import extract_text_from_pdf, chunk_text
from utils.rag_utils import embed_chunks, build_faiss_index


app = FastAPI(title="AI PDF Assistant Backend")

# Allow the Vite dev server (and optionally other local tools) to call this API.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UploadResponse(BaseModel):
    filename: str
    num_pages: int
    extracted_text: str
    chunks: List[str]


class QARequest(BaseModel):
    question: str
    context: Optional[str] = None


class QAResponse(BaseModel):
    answer: str
    details: Optional[str] = None


# In a real app, you would persist these objects somewhere (database, disk, etc.).
# For this simple demo, we just keep a single in-memory example.
LAST_CHUNKS: List[str] = []
LAST_FAISS_INDEX = None


@app.get("/")
def read_root():
    """
    Simple health-check endpoint.
    """
    return {"message": "AI PDF Assistant backend is running."}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Receive a PDF file, extract text using PyMuPDF, chunk it,
    and (optionally) prepare dummy embeddings and a FAISS index.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        file_bytes = await file.read()
        extracted_text, num_pages = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {e}")

    chunks = chunk_text(extracted_text)

    # Prepare dummy embeddings and a FAISS index, just to show how it would work.
    embeddings = embed_chunks(chunks)
    global LAST_CHUNKS, LAST_FAISS_INDEX
    LAST_CHUNKS = chunks
    LAST_FAISS_INDEX = build_faiss_index(embeddings)

    return UploadResponse(
        filename=file.filename,
        num_pages=num_pages,
        extracted_text=extracted_text,
        chunks=chunks,
    )


@app.post("/chunk")
def chunk_endpoint(text: str, max_chars: int = 500) -> List[str]:
    """
    Simple helper endpoint to see how the chunking works.
    """
    return chunk_text(text, max_chars=max_chars)


@app.post("/qa", response_model=QAResponse)
def qa_endpoint(payload: QARequest):
    """
    Placeholder QA endpoint.

    In a real RAG system, you would:
    - Embed the question
    - Search similar chunks in the FAISS index
    - Pass the retrieved context + question to an LLM
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    used_context = payload.context if payload.context else "No context provided."

    answer_text = (
        "This is a placeholder answer. "
        "RAG with real embeddings and a language model is not implemented yet."
    )

    details_text = (
        "You sent the question: "
        f"'{payload.question}'.\n\n"
        "Context length (characters): "
        f"{len(used_context)}."
    )

    return QAResponse(answer=answer_text, details=details_text)


if __name__ == "__main__":
    # This allows: python main.py
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

