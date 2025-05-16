from fastapi import Request, HTTPException
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEYS = os.getenv("API_KEYS", "supersecretkey").split(",")

async def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Unauthorized")