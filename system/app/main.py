"""
Entry point aplikasi FastAPI — IT Helpdesk Assistant (Optimized Implementation).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.router import handle_query
from app.rag import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup event: Inisialisasi/memuat index FAISS dari cache disk saat server start."""
    print("[FastAPI] Memulai server IT Helpdesk Assistant...")
    try:
        build_index()
        print("[FastAPI] FAISS Index berhasil dimuat. Server siap.")
    except Exception as e:
        print(f"[FastAPI] Peringatan: Gagal memuat index pada startup: {e}")
    yield
    print("[FastAPI] Server dimatikan.")


app = FastAPI(
    title="IT Helpdesk Assistant API (Optimized)",
    description="Sistem IT Helpdesk cerdas dengan RAG teroptimasi, Tool Calling, dan Lapisan Safety Guardrails.",
    version="2.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    query: str = Field(..., description="Pertanyaan atau permintaan dari pengguna", example="berapa jatah cuti tahunan saya?")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if v is None:
            raise ValueError("Query tidak boleh null.")
        return v


class AskResponse(BaseModel):
    status: str = Field(..., description="Status hasil ('success', 'error', atau 'blocked')")
    intent: str = Field(..., description="Intent yang terdeteksi ('faq', 'ticket_status', 'mixed_faq_and_ticket', atau guardrail tag)")
    data: str = Field(..., description="Konten jawaban atau respons sistem")


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "2.0.0", "guardrails": "active"}


@app.post("/ask", response_model=AskResponse, tags=["Assistant"])
async def ask(request: AskRequest):
    """
    Endpoint utama asisten IT Helpdesk.
    Menerima query pengguna, memproses melalui lapisan Guardrail, Router, RAG, atau Tool Call.
    """
    try:
        result = await handle_query(request.query)
        return AskResponse(
            status=result.get("status", "success"),
            intent=result.get("intent", "faq"),
            data=result.get("data", ""),
        )
    except Exception as e:
        return AskResponse(
            status="error",
            intent="unknown",
            data=f"Terjadi kendala pada sistem. Silakan coba beberapa saat lagi. ({type(e).__name__})",
        )
