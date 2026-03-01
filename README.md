# Bin Sentinel

Bin Sentinel is a facility-aware recycling classification system. The camera captures an item; the backend identifies and classifies it using local Materials Recovery Facility (MRF) specs and returns a RECYCLE / TRASH / COMPOST verdict with facility-specific reasoning — because recyclability is local, and our system explains exactly why.

## Quickstart

```bash
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys, then start the server:

```bash
uvicorn main:app --reload
```
