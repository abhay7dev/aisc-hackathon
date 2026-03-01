# Bin Sentinel — Railway Deploy Steps

## Backend (Railway)

1. Push repo to GitHub
2. Create a new Railway project from the GitHub repo
3. Set the **root directory** to `/backend`
4. Set these **environment variables** in Railway:
   - `PERPLEXITY_API_KEY` — your Perplexity API key
   - `CHROMA_PERSIST_DIR` — set to `./chroma_db`
   - `DATABASE_URL` — set to `sqlite:///./bin_sentinel.db`
5. After first deploy, run `ingest.py` once to populate ChromaDB (if using RAG):
   ```
   railway run python ingest.py
   ```
   This must complete before `/scan` can return verdicts (when using RAG pipeline).

## Frontend (Vercel)

1. Import the GitHub repo in Vercel
2. Set the **root directory** to `/frontend`
3. Set the **environment variable**:
   - `VITE_API_URL` — your Railway backend URL (e.g. `https://bin-sentinel-production.up.railway.app`)
4. Vercel auto-detects Vite and builds with `npm run build`
5. The `vercel.json` rewrite rule handles SPA routing
