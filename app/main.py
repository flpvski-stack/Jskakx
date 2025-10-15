from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any
import os
import httpx

NOVITA_API_KEY = os.getenv("NOVITA_API_KEY")

app = FastAPI(
    title="MotionMuse-like Image-to-Video API",
    version="1.0.0",
    description="Simple proxy API for NSFW-friendly image-to-video generation using Novita AI."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Img2VideoRequest(BaseModel):
    image_url: Optional[HttpUrl] = None
    image_base64: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    duration: Optional[float] = 3.0
    motion_strength: Optional[float] = 0.7
    seed: Optional[int] = None
    nsfw: Optional[bool] = True
    extra: Optional[Dict[str, Any]] = {}

class GenericTaskResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    result_url: Optional[str] = None
    vendor_raw: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/v1/img2video", response_model=GenericTaskResponse)
async def img2video(payload: Img2VideoRequest = Body(...)):
    if not NOVITA_API_KEY:
        raise HTTPException(status_code=500, detail="NOVITA_API_KEY not configured")

    image_url = payload.image_url
    image_b64 = None
    if not image_url and payload.image_base64:
        if payload.image_base64.startswith("data:"):
            _, data = payload.image_base64.split(",", 1)
            image_b64 = data
        else:
            image_b64 = payload.image_base64

    vendor_url = "https://api.novita.ai/v1/img2video"
    headers = {
        "Authorization": f"Bearer {NOVITA_API_KEY}",
        "Content-Type": "application/json",
    }
    vendor_payload = {
        "prompt": payload.prompt,
        "negative_prompt": payload.negative_prompt or "",
        "duration": payload.duration,
        "motion_strength": payload.motion_strength,
        "seed": payload.seed,
        "nsfw": payload.nsfw,
    }

    if image_url:
        vendor_payload["image_url"] = str(image_url)
    elif image_b64:
        vendor_payload["image_base64"] = image_b64
    else:
        raise HTTPException(status_code=400, detail="Provide image_url or image_base64")

    if payload.extra:
        vendor_payload.update(payload.extra)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(vendor_url, headers=headers, json=vendor_payload)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    result_url = data.get("video_url") or data.get("result") or data.get("url")
    task_id = data.get("task_id") or data.get("id")
    status = "succeeded" if result_url else ("queued" if task_id else "unknown")

    return GenericTaskResponse(
        status=status,
        task_id=task_id,
        result_url=result_url,
        vendor_raw=data
    )