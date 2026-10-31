#!/usr/bin/env python3
"""
Munex Content Pipeline - Automated Blog Content Generation
Runs daily to find trending topics and create humanized content
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
BLOG_DIR = Path("/Users/badal/Public/Projects/munex-blog")
CONTENT_DIR = BLOG_DIR / "src/content/blog"

# Top RSS feeds to check for trending content
RSS_FEEDS = [
    # AI
    "https://openai.com/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/technology/ai/rss/",
    
    # SaaS
    "https://www.notion.so/blog/rss.xml",
    "https://zapier.com/blog/feeds/latest/",
    
    # Dev Tools
    "https://github.blog/feed/",
    "https://vercel.com/atom",
    "https://blog.cloudflare.com/rss/",
    
    # Business
    "https://stripe.com/blog/feed.rss",
    "https://ahrefs.com/blog/feed/",
]

# High-CPC topic patterns to prioritize
HIGH_CPC_PATTERNS = [
    "AI", "ChatGPT", "Claude", "GPT-4", "LLM",
    "CRM", "email marketing", "automation",
    "project management", "productivity",
    "SaaS", "software", "tools", "best",
    "vs", "comparison", "alternative",
    "pricing", "review", "guide"
]

def get_existing_posts():
    """Get list of existing post slugs to avoid duplicates"""
    posts = []
    for f in CONTENT_DIR.glob("*.md"):
        posts.append(f.stem.lower())
    return posts

def main():
    existing = get_existing_posts()
    print(f"Pipeline started at {datetime.now().isoformat()}")
    print(f"Existing posts: {len(existing)}")
    print(f"RSS feeds to check: {len(RSS_FEEDS)}")
    print(f"High-CPC patterns: {len(HIGH_CPC_PATTERNS)}")
    print("\n--- Ready for agent to process ---")
    print(json.dumps({
        "existing_posts": existing,
        "feeds": RSS_FEEDS,
        "patterns": HIGH_CPC_PATTERNS,
        "target_posts": "2-5",
        "content_dir": str(CONTENT_DIR)
    }, indent=2))

if __name__ == "__main__":
    main()
