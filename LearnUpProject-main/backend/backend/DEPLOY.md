# Backend Deploy Notes

This backend can now run as a standalone FastAPI service on Render or Vercel.

## Minimum environment variables

- `DATABASE_URL` or `NEON_URL`
- `OPENAI_API_KEY`
- `JWT_SECRET`

## Optional environment variables

- `CORS_ORIGINS`
  Comma-separated list of allowed frontend origins.
- `FRONTEND_URL`
  Single frontend URL to append to the allow-list.
- `UPLOADS_DIR`
  Absolute path for uploaded files if you attach persistent storage.
- `CHATBOT_DATA_DIR`
  Optional override for the knowledge-base folder used by the chatbot.

## Vercel setup

Use a separate Vercel project for the backend and set the project's Root Directory to `backend`.

- Vercel will detect [server.py](./server.py) as the FastAPI entrypoint with zero configuration
- The chatbot files now live under `backend/Chatbot`, so they are available from the backend root directory without extra Vercel config

Important:

- The repo root [vercel.json](../vercel.json) uses Vercel Services, which is currently in Private Beta
- For now, backend-only deployment on Vercel should point to the `backend` folder, not the repo root

## Render setup

The repo root now includes `render.yaml` with:

- `rootDir: backend`
- build command: `pip install -r requirements.txt`
- start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- health check: `/health`

## Important limitation

Student profile images still save to the local filesystem by default. That is fine for local development, but production should move uploads to persistent storage such as Cloudinary, Supabase Storage, or a mounted Render disk.
