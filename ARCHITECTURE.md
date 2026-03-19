# InsightStream Architecture

## Overview

InsightStream is an enterprise-grade RAG (Retrieval-Augmented Generation) platform built with **clean architecture** and **SOLID principles**. The system is fully decoupled, modular, and production-ready.

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  API Layer (FastAPI Routes)                                      │
│  - Request validation (Pydantic)                                 │
│  - Auth dependencies                                             │
│  - Rate limiting                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Service Layer (Business Logic)                                  │
│  - PDFService, AIService, VectorService, CacheService, etc.      │
│  - Orchestrates repositories & external APIs                     │
│  - Stateless, injectable                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Repository Layer (Data Access)                                  │
│  - UserRepository, DocumentRepository, ChunkRepository           │
│  - Abstracts database operations                                 │
│  - Single responsibility per entity                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Infrastructure (DB, Cache, Queue, Storage)                      │
│  - PostgreSQL, Redis, RabbitMQ, FAISS/S3                         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Service-Repository Pattern**: Services contain business logic; repositories handle persistence.
2. **Dependency Injection**: Services receive repositories via constructor or FastAPI `Depends()`.
3. **Abstract Interfaces**: Vector storage supports FAISS, Pinecone, Weaviate, Chroma via abstractions.
4. **Multi-Tenancy**: User-scoped namespaces for documents, vectors, and chat history.
5. **Async Processing**: Celery + RabbitMQ for PDF ingestion and heavy workloads.

## Module Independence

- **PDF Processing** → `PDFService` (PyMuPDF, LangChain splitter) - no AI/vector coupling
- **Embedding Logic** → `AIService.embed_texts()` - uses Vertex AI or mock
- **Vector Storage** → `VectorService` - FAISS default, pluggable backends
- **LLM Orchestration** → `AIService.generate_answer()` - Flash vs Pro selection
- **Caching** → `CacheService` - Redis, isolated from core logic
