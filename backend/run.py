"""Development server entry point."""

import os

import uvicorn

from karena.config import get_settings

if __name__ == "__main__":
  settings = get_settings()
  port = int(os.environ.get("PORT", settings.api_port))
  host = os.environ.get("HOST", settings.api_host)

  print(f"Starting Karena AI API at http://{host}:{port}")
  print(f"Docs: http://{host}:{port}/docs")

  uvicorn.run(
    "karena.main:app",
    host=host,
    port=port,
    reload=True,
  )
