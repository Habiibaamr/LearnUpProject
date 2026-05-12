# Backend Deploy Notes

This backend can now run as a standalone FastAPI service on Render.

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

## Render setup

The repo root now includes `render.yaml` with:

- `rootDir: backend`
- build command: `pip install -r requirements.txt`
- start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- health check: `/health`

## Important limitation

Student profile images still save to the local filesystem by default. That is fine for local development, but production should move uploads to persistent storage such as Cloudinary, Supabase Storage, or a mounted Render disk.
