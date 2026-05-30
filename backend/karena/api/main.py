from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from karena.api.routes import chat, documents, admin, users, escalation
from karena.config import get_settings
from karena.observability.metrics import setup_metrics
from karena.observability.tracing import setup_tracing
import logging

settings = get_settings()
app = FastAPI(
    title="Karena AI Enterprise",
    description="Enterprise RAG Knowledge Intelligence Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability
setup_metrics(app)
setup_tracing(app)

# Routes
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(escalation.router, prefix="/api/v1/escalation", tags=["Escalation"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
