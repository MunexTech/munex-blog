# LinkedIn Post Automation Setup

## Overview

Full automation flow:
```
New blog → @adsense-optimizer → @linkedin-marketer → linkedin-posts/*.txt → Scheduler → LinkedIn
```

## Option 1: Buffer (Free tier: 10 scheduled posts)

### Setup Steps

1. **Create Buffer account**
   - Go to https://buffer.com
   - Sign up (free tier works)
   - Connect your LinkedIn personal profile

2. **Get API Access Token**
   - Go to https://buffer.com/developers/api
   - Create an app or get your access token
   - Copy the token

3. **Configure Environment**
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   export BUFFER_ACCESS_TOKEN="your_token_here"
   ```

4. **Get your LinkedIn Profile ID**
   ```bash
   cd /Users/badal/Public/Projects/munex-blog/scripts
   python linkedin-scheduler.py --list
   ```
   This will show your Buffer profile ID. Then:
   ```bash
   export BUFFER_PROFILE_ID="your_profile_id"
   ```

5. **Test it**
   ```bash
   # Preview posts without scheduling
   python linkedin-scheduler.py --preview
   
   # Actually schedule posts
   python linkedin-scheduler.py
   ```

### Automation Options

**Manual trigger** (run after creating posts):
```bash
python /Users/badal/Public/Projects/munex-blog/scripts/linkedin-scheduler.py
```

**Watch mode** (run in background):
```bash
python /Users/badal/Public/Projects/munex-blog/scripts/linkedin-scheduler.py --watch &
```

**Cron job** (check every hour):
```bash
# Add to crontab (crontab -e)
0 * * * * cd /Users/badal/Public/Projects/munex-blog/scripts && /usr/bin/python3 linkedin-scheduler.py >> /tmp/linkedin-scheduler.log 2>&1
```

---

## Option 2: Typefully (Better for LinkedIn, 1 free profile)

Typefully is purpose-built for social scheduling with better LinkedIn support.

### Setup Steps

1. **Create Typefully account**
   - Go to https://typefully.com
   - Sign up and connect LinkedIn

2. **Get API Key**
   - Go to Settings → API
   - Generate API key

3. **Use the Typefully script** (see typefully-scheduler.py)

---

## Option 3: Direct LinkedIn API (Most control, complex setup)

For full control without third-party tools:

1. Create LinkedIn App at https://developer.linkedin.com
2. Request Marketing Developer Platform access (can take weeks)
3. Implement OAuth flow
4. Use Share API to post

This is overkill for personal use - Buffer/Typefully is easier.

---

## Recommended Setup

1. **Use Buffer** (simplest, free tier is enough)
2. **Add cron job** to auto-schedule new posts every hour
3. Posts queue up and go live at optimal times (weekday 9 AM)

## Files

- `linkedin-scheduler.py` - Buffer integration script
- `linkedin-posts/*.txt` - Ready-to-post content (I create these)
- `linkedin-posts/.posted_files.json` - Tracks what's been scheduled (auto-created)
