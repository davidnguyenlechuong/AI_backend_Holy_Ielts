import os
import uuid
import logging
import httpx
import anyio
from src.core.config import settings

logger = logging.getLogger("storage")

async def upload_file_to_storage(file_bytes: bytes, filename: str, mime_type: str) -> str:
    """
    Uploads a file to Supabase Storage if configured (using httpx).
    Otherwise, falls back to storing the file on the local disk.
    
    Returns the public URL (or relative static URL path if using local storage fallback).
    """
    # Extract extension and generate a clean unique filename
    _, ext = os.path.splitext(filename)
    # Default to .png if ext is empty
    if not ext:
        ext = ".png"
    unique_filename = f"{uuid.uuid4()}{ext.lower()}"

    # Supabase credentials check
    if settings.SUPABASE_URL and settings.SUPABASE_KEY and settings.SUPABASE_URL != "https://your-project-ref.supabase.co":
        try:
            return await upload_to_supabase(file_bytes, unique_filename, mime_type)
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}. Falling back to local storage.")
            # Fallback to local storage
            
    return await save_to_local(file_bytes, unique_filename)

async def upload_to_supabase(file_bytes: bytes, unique_filename: str, mime_type: str) -> str:
    """
    Directly uploads file to Supabase Storage endpoint using HTTP POST.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be fully configured.")
        
    # Sanitize base URL
    base_url = settings.SUPABASE_URL.rstrip("/")
    supabase_key = settings.SUPABASE_KEY
    bucket = settings.SUPABASE_BUCKET
    
    # Supabase upload endpoint: /storage/v1/object/bucket/file_path
    upload_url = f"{base_url}/storage/v1/object/{bucket}/{unique_filename}"
    
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "ApiKey": supabase_key,
        "Content-Type": mime_type
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(upload_url, content=file_bytes, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Supabase response status {response.status_code}: {response.text}")
            
    # Return the clean public URL: /storage/v1/object/public/bucket/file_path
    return f"{base_url}/storage/v1/object/public/{bucket}/{unique_filename}"

async def save_to_local(file_bytes: bytes, unique_filename: str) -> str:
    """
    Saves a file to the local directory (fallback default).
    """
    upload_dir = settings.UPLOAD_DIR
    path = anyio.Path(upload_dir)
    
    # Ensure directory exists async
    if not await path.exists():
        await path.mkdir(parents=True, exist_ok=True)
        
    destination_file = path / unique_filename
    await destination_file.write_bytes(file_bytes)
    
    # Return path relative to mount point
    return f"/static/uploads/{unique_filename}"
