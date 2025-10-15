import requests, os, json

API = os.getenv("API_URL", "http://localhost:8000/v1/img2video")

payload = {
    "image_url": "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d",
    "prompt": "cinematic portrait turning head, 4k, film look",
    "duration": 3,
    "motion_strength": 0.7,
    "nsfw": True
}

r = requests.post(API, json=payload, timeout=120)
print("Status:", r.status_code)
print(json.dumps(r.json(), indent=2))
