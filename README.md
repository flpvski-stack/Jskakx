# MotionMuse-like Img2Video API (NSFW-friendly)

FastAPI proxy to an NSFW-permissive image-to-video backend (Novita AI).
Intended to mimic a subset of motionmuse.ai behavior.

IMPORTANT: You must comply with laws and provider ToS. Use responsibly.

## Quick start (local)

    git clone <your-repo-url>
    cd motionmuse-clone-api
    cp .env.example .env
    # set NOVITA_API_KEY in .env
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Open: http://localhost:8000/docs

## Docker

    docker build -t motionmuse-clone-api .
    docker run -e NOVITA_API_KEY=your_key -p 8000:8000 motionmuse-clone-api

## Endpoint

POST /v1/img2video

Request JSON:
    {
      "image_url": "https://example.com/input.jpg",
      "prompt": "cinematic portrait turning head, soft light",
      "negative_prompt": "blurry, low quality",
      "duration": 3.0,
      "motion_strength": 0.7,
      "nsfw": true
    }

Or with base64:
    {
      "image_base64": "data:image/png;base64,iVBORw0KGgo...",
      "prompt": "artistic nude, cinematic lighting",
      "nsfw": true
    }

Response JSON:
    {
      "status": "succeeded | queued | unknown",
      "task_id": "optional",
      "result_url": "https://.../video.mp4",
      "vendor_raw": {}
    }

Notes:
- Some vendors return a task_id first; others return video_url immediately.
- Use "extra" in request to pass vendor-specific params:
    {
      "image_url": "...",
      "prompt": "...",
      "nsfw": true,
      "extra": { "fps": 24, "motion_scale": 1.2 }
    }

## Deploy

Docker to any VPS:
    docker build -t motionmuse-clone-api .
    docker run -d --restart unless-stopped -e NOVITA_API_KEY=your_key -p 80:8000 --name motionmuse motionmuse-clone-api

Add Nginx or Caddy reverse proxy + SSL.

## Security

- Add auth (API keys/JWT).
- Rate-limit per IP.
- Log audit events.
- You can later swap Novita for a local AnimateDiff stack keeping the same JSON schema.
