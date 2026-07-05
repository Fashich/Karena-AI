"""In-memory job tracking for async document ingestion."""
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IngestionJob:
    job_id: str
    filename: str
    status: str = "pending"      # pending | processing | done | error
    stage: str = ""              # detect | reading | ocr | embedding | indexing
    current_page: int = 0
    total_pages: int = 0
    message: str = "Starting..."
    chunks_indexed: int = 0
    error: str = ""
    created_at: float = field(default_factory=time.time)

    @property
    def pct(self) -> int:
        if self.total_pages == 0:
            return 0
        return min(99, int(self.current_page / self.total_pages * 100))

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status,
            "stage": self.stage,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "pct": self.pct if self.status != "done" else 100,
            "message": self.message,
            "chunks_indexed": self.chunks_indexed,
            "error": self.error,
        }


_jobs: dict[str, IngestionJob] = {}


def create_job(filename: str) -> IngestionJob:
    job_id = str(uuid.uuid4())
    job = IngestionJob(job_id=job_id, filename=filename)
    _jobs[job_id] = job
    # Keep only last 100 jobs
    if len(_jobs) > 100:
        oldest = sorted(_jobs.keys(), key=lambda k: _jobs[k].created_at)[:10]
        for k in oldest:
            del _jobs[k]
    return job


def get_job(job_id: str) -> Optional[IngestionJob]:
    return _jobs.get(job_id)
