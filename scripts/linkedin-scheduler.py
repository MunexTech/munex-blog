#!/usr/bin/env python3
"""
LinkedIn Post Scheduler
Watches linkedin-posts/ folder and schedules new posts via Buffer API.

Setup:
1. Create Buffer account: https://buffer.com
2. Connect your LinkedIn profile in Buffer
3. Get API token: https://buffer.com/developers/api
4. Set environment variable: export BUFFER_ACCESS_TOKEN="your_token"
5. Get your LinkedIn profile ID from Buffer API and set: export BUFFER_PROFILE_ID="your_profile_id"

Usage:
  python linkedin-scheduler.py              # Schedule all unposted .txt files
  python linkedin-scheduler.py --watch      # Watch folder for new files
  python linkedin-scheduler.py --list       # List Buffer profiles to get ID
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
POSTS_DIR = Path("/Users/badal/Public/Projects/munex-blog/linkedin-posts")
POSTED_LOG = POSTS_DIR / ".posted_files.json"
BUFFER_API_URL = "https://api.bufferapp.com/1"

def get_env_or_exit(var_name):
    """Get environment variable or exit with instructions."""
    value = os.environ.get(var_name)
    if not value:
        print(f"Error: {var_name} not set.")
        print(f"\nTo set it: export {var_name}='your_value'")
        if var_name == "BUFFER_ACCESS_TOKEN":
            print("Get your token at: https://buffer.com/developers/api")
        elif var_name == "BUFFER_PROFILE_ID":
            print("Run: python linkedin-scheduler.py --list")
        sys.exit(1)
    return value

def list_buffer_profiles():
    """List all Buffer profiles to find LinkedIn profile ID."""
    token = get_env_or_exit("BUFFER_ACCESS_TOKEN")
    
    response = requests.get(
        f"{BUFFER_API_URL}/profiles.json",
        params={"access_token": token}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    profiles = response.json()
    print("\nYour Buffer Profiles:")
    print("-" * 60)
    for p in profiles:
        print(f"  Service: {p.get('service', 'unknown')}")
        print(f"  Name: {p.get('formatted_username', 'unknown')}")
        print(f"  ID: {p.get('id')}")
        print("-" * 60)
    
    linkedin_profiles = [p for p in profiles if p.get('service') == 'linkedin']
    if linkedin_profiles:
        print(f"\n✓ LinkedIn Profile ID: {linkedin_profiles[0]['id']}")
        print(f"\nSet it with: export BUFFER_PROFILE_ID='{linkedin_profiles[0]['id']}'")
    else:
        print("\n⚠ No LinkedIn profile found. Connect LinkedIn in Buffer first.")

def extract_post_content(file_path):
    """Extract content between the COPY markers."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find content between markers
    start_marker = "COPY EVERYTHING BELOW THIS LINE FOR LINKEDIN:"
    end_marker = "STOP COPYING HERE"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print(f"  Warning: Could not find markers in {file_path.name}")
        return None
    
    # Extract and clean
    start_idx = content.find('\n', start_idx) + 1  # Skip the marker line
    start_idx = content.find('\n', start_idx) + 1  # Skip the === line
    
    end_idx = content.rfind('\n', 0, end_idx)  # Go back to before === line
    end_idx = content.rfind('\n', 0, end_idx)  # Go back one more line
    
    post_content = content[start_idx:end_idx].strip()
    return post_content

def get_posted_files():
    """Load list of already-posted files."""
    if POSTED_LOG.exists():
        with open(POSTED_LOG, 'r') as f:
            return json.load(f)
    return {}

def save_posted_file(file_path, post_id):
    """Mark a file as posted."""
    posted = get_posted_files()
    posted[str(file_path)] = {
        "posted_at": datetime.now().isoformat(),
        "buffer_post_id": post_id
    }
    with open(POSTED_LOG, 'w') as f:
        json.dump(posted, f, indent=2)

def get_optimal_post_time():
    """Calculate next optimal posting time (weekday 9 AM IST)."""
    now = datetime.now()
    
    # Next 9 AM
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now.hour >= 9:
        target += timedelta(days=1)
    
    # Skip to Monday if weekend
    while target.weekday() >= 5:  # Saturday=5, Sunday=6
        target += timedelta(days=1)
    
    return target

def schedule_post(content, profile_id, token, scheduled_at=None):
    """Schedule a post via Buffer API."""
    data = {
        "access_token": token,
        "profile_ids[]": profile_id,
        "text": content,
    }
    
    if scheduled_at:
        data["scheduled_at"] = int(scheduled_at.timestamp())
    else:
        data["now"] = "true"  # Post immediately if no time specified
    
    response = requests.post(
        f"{BUFFER_API_URL}/updates/create.json",
        data=data
    )
    
    return response.json()

def process_new_files(schedule=True):
    """Find and schedule new post files."""
    token = get_env_or_exit("BUFFER_ACCESS_TOKEN")
    profile_id = get_env_or_exit("BUFFER_PROFILE_ID")
    
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
            post_time = get_optimal_post_time()
            print(f"  Scheduling for: {post_time.strftime('%Y-%m-%d %H:%M')}")
            
            result = schedule_post(content, profile_id, token, post_time)
            
            if result.get("success"):
                post_id = result.get("updates", [{}])[0].get("id", "unknown")
                save_posted_file(file_path, post_id)
                print(f"  ✓ Scheduled! Buffer ID: {post_id}")
            else:
                print(f"  ✗ Failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"  Preview (first 100 chars): {content[:100]}...")
        
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
                print(f"\nNew file(s) detected!")
                process_new_files()
                known_files = current_files
            
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        print("\nStopped watching.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_buffer_profiles()
        elif sys.argv[1] == "--watch":
            watch_folder()
        elif sys.argv[1] == "--preview":
            process_new_files(schedule=False)
        elif sys.argv[1] == "--help":
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage.")
    else:
        process_new_files()
