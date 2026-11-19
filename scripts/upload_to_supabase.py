import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lihoygvdnnfqodjjxqnz.supabase.co").rstrip("/")
# Prefer service_role_key if available, fallback to anon key
API_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_ANON_KEY", "sb_publishable_xknRF_gqAzQqznqNvSONRg_j6GkQdrS").strip()

BUCKET_NAME = "email-assets"
IMAGES_DIR = r"c:\Users\raynz\Desktop\project\node_backent\app\static\email_images"

headers = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
}

def upload_all():
    print(f"Connecting to Supabase Storage at: {SUPABASE_URL}")
    print(f"Target Bucket: {BUCKET_NAME}")
    
    # 1. Try to create bucket if using service role key
    try:
        b_res = httpx.post(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers=headers,
            json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": True},
            timeout=10.0,
        )
        if b_res.status_code in (200, 201):
            print(f"✓ Created bucket '{BUCKET_NAME}' successfully.")
        elif b_res.status_code == 400 and "already exists" in b_res.text:
            print(f"Bucket '{BUCKET_NAME}' already exists.")
    except Exception as e:
        print(f"Note on bucket creation: {e}")

    # 2. Upload each compressed image
    results = {}
    files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    
    with httpx.Client(timeout=30.0) as client:
        for file_name in files:
            file_path = os.path.join(IMAGES_DIR, file_name)
            with open(file_path, "rb") as f:
                content = f.read()

            upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}"
            req_headers = {
                **headers,
                "Content-Type": "image/jpeg",
                "x-upsert": "true",
            }

            res = client.post(upload_url, headers=req_headers, content=content)
            
            if res.status_code in (200, 201):
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
                results[file_name] = public_url
                print(f"✓ Uploaded {file_name} -> {public_url}")
            else:
                print(f"✗ Failed {file_name} (HTTP {res.status_code}): {res.text}")

    print("\n--- Summary of Image Public URLs ---")
    for name, url in results.items():
        print(f"{name}: {url}")
    return results

if __name__ == "__main__":
    upload_all()

