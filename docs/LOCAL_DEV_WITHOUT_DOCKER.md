# Local development without Docker

If `docker compose` fails with DNS errors like:

```
lookup auth.docker.io: getaddrinfow
```

your machine cannot reach Docker Hub. You can still run Karena AI locally.

## Quick start (no Docker)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env already sets VECTOR_STORE=memory

mkdir data -Force
python scripts\seed_knowledge.py
python run.py
```

In another terminal:

```powershell
cd app
npm run dev
```

Open http://localhost:3000/chat

## What runs without Docker

| Service | Without Docker |
|---------|----------------|
| Vector DB | In-memory store (`VECTOR_STORE=memory`) |
| Redis cache | In-process fallback (automatic) |
| SQLite memory | Local file `backend/data/karena.db` |
| Embeddings | Downloaded once via `sentence-transformers` |

## When Docker works again

1. Fix DNS (see below)
2. Set in `backend/.env`: `VECTOR_STORE=qdrant`
3. Run: `docker compose up -d qdrant redis`
4. Re-seed: `python scripts\seed_knowledge.py`

## Fix Docker Hub DNS (Windows)

1. **Docker Desktop** → Settings → **Docker Engine**
2. Add DNS servers:

```json
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
}
```

3. Apply & Restart Docker Desktop
4. Retry: `docker compose pull` then `docker compose up -d qdrant redis`

### Other checks

- Disable VPN or configure Docker Desktop proxy (Settings → Resources → Proxies)
- Test: `nslookup auth.docker.io` in PowerShell
- Corporate network: ask IT to allow `docker.io` and `auth.docker.io`
- Use mobile hotspot briefly to rule out firewall issues

## Optional: Qdrant without Docker Hub

Download the Windows binary from [Qdrant releases](https://github.com/qdrant/qdrant/releases), run `qdrant.exe`, then set `VECTOR_STORE=qdrant` in `.env`.
