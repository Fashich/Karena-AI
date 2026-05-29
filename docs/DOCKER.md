# Menjalankan Karena AI dengan Docker saja

Tidak perlu `npm run dev` atau `python run.py` di host.

## Dari folder root project

```powershell
cd C:\laragon\www\Project.Self\KarenaAI
docker compose up --build
```

Build backend ~**5–10 menit** (PyTorch CPU + model embedding). Dockerfile **tidak memakai `apt-get`** — menghindari error `deb.debian.org` / `build-essential` / GCC.

Jika Docker build tetap gagal (jaringan), jalankan stack lokal:

```powershell
docker compose up -d qdrant redis
cd backend
.\.venv\Scripts\activate
python run.py
cd ..\app
npm run dev
```

Buka http://localhost:3000/chat

## Seed knowledge (sekali)

Terminal baru:

```powershell
cd C:\laragon\www\Project.Self\KarenaAI
docker compose run --rm seed
```

## Buka aplikasi

| URL | Keterangan |
|-----|------------|
| http://localhost:3000/chat | Chat UI |
| http://localhost:8080/docs | API Swagger |
| http://localhost:6333/dashboard | Qdrant UI |

## Qdrant image

Gunakan **`qdrant/qdrant:v1.12.5`** — tag `v1.18.5` tidak ada di Docker Hub.

Client Python dipasangkan: `qdrant-client>=1.12.0,<1.13.0`

## Stop

```powershell
docker compose down
```

## Hanya infrastruktur (dev lokal Python)

```powershell
docker compose up -d qdrant redis
# lalu python run.py di backend
```
