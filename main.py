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
    image_url: Optional[HttpUrl] = Field(None, description="Public URL to the input image")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image (data URL or raw base64)")
    prompt: str = Field(..., description="Generation prompt")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")
    duration: Optional[float] = Field(3.0, description="Duration in seconds (typ. 2-5s)")
    motion_strength: Optional[float] = Field(0.7, ge=0, le=1, description="Motion intensity 0..1")
    seed: Optional[int] = Field(None, description="Random seed (optional)")
    nsfw: Optional[bool] = Field(True, description="Allow NSFW")
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pass-through vendor params")

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
            try:
                _, data = payload.image_base64.split(",", 1)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid data URL for image_base64")
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
        try:
            resp = await client.post(vendor_url, headers=headers, json=vendor_payload)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Vendor request error: {e!s}")

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        raise HTTPException(status_code=resp.status_code, detail={"vendor_error": data})

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
