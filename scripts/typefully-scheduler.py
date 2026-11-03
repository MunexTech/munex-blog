#!/usr/bin/env python3
"""
LinkedIn Post Scheduler (Typefully API)
Watches linkedin-posts/ folder and schedules posts via Typefully.

Setup:
1. Create Typefully account: https://typefully.com
2. Connect your LinkedIn profile
3. Get API key: Settings → Integrations → API → Generate Key
4. Set: export TYPEFULLY_API_KEY="your_key"

Usage:
  python typefully-scheduler.py              # Schedule all unposted .txt files
  python typefully-scheduler.py --watch      # Watch folder for new files
  python typefully-scheduler.py --preview    # Preview without scheduling
  python typefully-scheduler.py --now        # Post immediately (not scheduled)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
POSTS_DIR = Path("/Users/badal/Public/Projects/munex-blog/linkedin-posts")
POSTED_LOG = POSTS_DIR / ".posted_files.json"
TYPEFULLY_API_URL = "https://api.typefully.com/v1"

def get_api_key():
    """Get Typefully API key from environment."""
    key = os.environ.get("TYPEFULLY_API_KEY")
    if not key:
        print("Error: TYPEFULLY_API_KEY not set.")
        print("\nSetup steps:")
        print("1. Go to https://typefully.com")
        print("2. Sign up/login and connect LinkedIn")
        print("3. Go to Settings → Integrations → API")
        print("4. Generate an API key")
        print("5. Run: export TYPEFULLY_API_KEY='your_key'")
        sys.exit(1)
    return key

def extract_post_content(file_path):
    """Extract content between the COPY markers."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    start_marker = "COPY EVERYTHING BELOW THIS LINE FOR LINKEDIN:"
    end_marker = "STOP COPYING HERE"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print(f"  Warning: Could not find markers in {file_path.name}")
        return None
    
    # Skip marker lines
    start_idx = content.find('\n', start_idx) + 1
    start_idx = content.find('\n', start_idx) + 1
    
    end_idx = content.rfind('\n', 0, end_idx)
    end_idx = content.rfind('\n', 0, end_idx)
    
    post_content = content[start_idx:end_idx].strip()
    return post_content

def get_posted_files():
    """Load list of already-posted files."""
    if POSTED_LOG.exists():
        with open(POSTED_LOG, 'r') as f:
            return json.load(f)
    return {}

def save_posted_file(file_path, draft_id):
    """Mark a file as posted."""
    posted = get_posted_files()
    posted[str(file_path)] = {
        "posted_at": datetime.now().isoformat(),
        "typefully_draft_id": draft_id
    }
    with open(POSTED_LOG, 'w') as f:
        json.dump(posted, f, indent=2)

def get_optimal_post_time():
    """Calculate next optimal posting time (weekday 9 AM IST)."""
    now = datetime.now()
    
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now.hour >= 9:
        target += timedelta(days=1)
    
    # Skip weekends
    while target.weekday() >= 5:
        target += timedelta(days=1)
    
    return target

def create_draft(content, schedule_date=None, post_now=False):
    """Create a draft in Typefully and optionally schedule it."""
    api_key = get_api_key()
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    
    # Typefully uses "threads" - each post is a thread with one tweet/post
    payload = {
        "content": content,
        "threadify": False,  # Don't split into multiple posts
        "share": True,       # Share to connected accounts (LinkedIn)
    }
    
    if schedule_date:
        # ISO format with timezone
        payload["schedule-date"] = schedule_date.strftime("%Y-%m-%dT%H:%M:%S+05:30")
    
    if post_now:
        payload["auto-plug"] = False
    
    response = requests.post(
        f"{TYPEFULLY_API_URL}/drafts/",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200 or response.status_code == 201:
        return {"success": True, "data": response.json()}
    else:
        return {"success": False, "error": response.text, "status": response.status_code}

def process_new_files(schedule=True, post_now=False):
    """Find and schedule new post files."""
    posted = get_posted_files()
    txt_files = sorted(POSTS_DIR.glob("*.txt"))
    
    new_files = [f for f in txt_files if str(f) not in posted]
    
    if not new_files:
        print("No new posts to schedule.")
        return
    
    print(f"Found {len(new_files)} new post(s):\n")
    
    for file_path in new_files:
        print(f"Processing: {file_path.name}")
        
        content = extract_post_content(file_path)
        if not content:
            continue
        
        print(f"  Content length: {len(content)} chars")
        
        if schedule:
            if post_now:
                print(f"  Posting immediately...")
                result = create_draft(content, post_now=True)
            else:
                post_time = get_optimal_post_time()
                print(f"  Scheduling for: {post_time.strftime('%Y-%m-%d %H:%M')} IST")
                result = create_draft(content, schedule_date=post_time)
            
            if result.get("success"):
                draft_id = result.get("data", {}).get("id", "unknown")
                save_posted_file(file_path, draft_id)
                print(f"  ✓ {'Posted' if post_now else 'Scheduled'}! Draft ID: {draft_id}")
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                print(f"    Status: {result.get('status')}")
        else:
            print(f"  Preview (first 150 chars):")
            print(f"    {content[:150]}...")
        
        print()

def watch_folder():
    """Watch folder for new files and schedule them."""
    print(f"Watching {POSTS_DIR} for new .txt files...")
    print("Press Ctrl+C to stop.\n")
    
    known_files = set(POSTS_DIR.glob("*.txt"))
    
    try:
        while True:
            current_files = set(POSTS_DIR.glob("*.txt"))
            new_files = current_files - known_files
            
            if new_files:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New file(s) detected!")
                process_new_files()
                known_files = current_files
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped watching.")

def test_connection():
    """Test API connection."""
    api_key = get_api_key()
    
    headers = {"X-API-KEY": api_key}
    
    # Try to list drafts to test connection
    response = requests.get(
        f"{TYPEFULLY_API_URL}/drafts/",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Typefully API connection successful!")
        print(f"  Found {len(response.json())} existing drafts")
        return True
    else:
        print(f"✗ Connection failed: {response.status_code}")
        print(f"  {response.text}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--watch":
            watch_folder()
        elif arg == "--preview":
            process_new_files(schedule=False)
        elif arg == "--now":
            process_new_files(post_now=True)
        elif arg == "--test":
            test_connection()
        elif arg == "--help":
            print(__doc__)
        else:
            print(f"Unknown option: {arg}")
            print("Use --help for usage.")
    else:
        process_new_files()
