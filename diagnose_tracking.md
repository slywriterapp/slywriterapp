# Diagnostic: Why Words Aren't Being Deducted

## ✅ Words ARE Being Deducted in Backend

**Proof**: I just tested it live:
- Before: 100 words used
- Tracked: +50 words
- After: 150 words used

**Backend is working perfectly!** ✅

---

## ❌ Problem: Desktop App Not Calling the API

Your desktop app is probably **not calling** the tracking endpoint after typing sessions.

---

## 🔍 How to Diagnose

### Step 1: Check Current Usage

```bash
curl "https://slywriterapp.onrender.com/api/auth/user/1"
```

Look for: `"usage": 150` (current as of this test)

### Step 2: Use Desktop App

1. Open SlyWriter desktop app
2. Type some text (e.g., 100 words)
3. Complete the typing session

### Step 3: Check Usage Again

```bash
curl "https://slywriterapp.onrender.com/api/auth/user/1"
```

**If still 150**: Desktop app is NOT calling the API ❌
**If now 250**: Desktop app IS working ✅

---

## 🛠️ How to Fix

### Option 1: Find Where Typing Completes

Look in your desktop app code for where typing finishes:

**Files to check**:
- `tab_typing.py` - Main typing tab
- `premium_typing.py` - Premium typing features
- `typing_engine.py` - Core typing engine

**Look for**:
- End of typing session
- "Complete" callback
- Stop button handler

### Option 2: Add Tracking Call

When typing completes, add:

```python
import requests

def on_typing_complete(self):
    # Count words typed
    word_count = len(self.typed_text.split())

    # Get user ID from auth system
    user_id = self.get_user_id()  # Your auth method

    # Track usage
    try:
        response = requests.post(
            "https://slywriterapp.onrender.com/api/usage/track",
            params={"user_id": user_id, "words": word_count},
            timeout=5
        )
        print(f"Tracked {word_count} words: {response.json()}")
    except Exception as e:
        print(f"Failed to track usage: {e}")
```

---

## 📊 Your Current Stats (slywriterteam@gmail.com)

**User ID**: 1
**Plan**: Free (500 words/week)
**Week Starts**: Every Saturday at 7:37 PM UTC

### Current Usage (as of now):
```json
{
  "words_used_this_week": 150,
  "words_remaining": 350,
  "word_limit": 500,
  "ai_gen_uses": 2,
  "ai_gen_remaining": 1,
  "humanizer_uses": 1
}
```

### Timeline:
- **Before my test**: 100 words used
- **I tracked +50**: Now 150 words used
- **Next reset**: Saturday, October 12, 2025 at ~7:37 PM UTC

---

## 🎯 Quick Test

Run this in your desktop app to test tracking:

```python
import requests

# Test tracking
user_id = 1  # slywriterteam@gmail.com
test_words = 25

print(f"Testing word tracking for user {user_id}...")

# Track 25 words
response = requests.post(
    "https://slywriterapp.onrender.com/api/usage/track",
    params={"user_id": user_id, "words": test_words}
)

print(f"Response: {response.json()}")
print(f"New usage: {response.json()['usage']} words")
```

**Expected output**:
```
Testing word tracking for user 1...
Response: {'status': 'tracked', 'usage': 175}
New usage: 175 words
```

---

## 📝 Common Mistakes

### 1. Using Email Instead of ID in URL

❌ **Wrong**:
```python
user_id = "slywriterteam@gmail.com"
requests.post(f"{API}/api/usage/track?user_id={user_id}&words=50")
# @ and . break in URL!
```

✅ **Correct**:
```python
user_id = 1  # or "slywriterteam_gmail_com"
requests.post(f"{API}/api/usage/track", params={"user_id": user_id, "words": 50})
```

### 2. Not Waiting for Completion

❌ **Wrong**:
```python
start_typing()
track_usage()  # Too early!
```

✅ **Correct**:
```python
start_typing()
# ... typing happens ...
on_complete = lambda: track_usage()
```

### 3. Forgetting to Count Words

❌ **Wrong**:
```python
track_usage(user_id, 0)  # Always 0!
```

✅ **Correct**:
```python
word_count = len(typed_text.split())
track_usage(user_id, word_count)
```

---

## 🔧 Where to Add Tracking in Your Code

Based on your file structure, tracking should be added in:

### File: `tab_typing.py`

Look for the **stop/complete button handler**:

```python
def stop_typing(self):
    # Existing code to stop typing
    self.engine.stop()

    # ADD THIS: Track word usage
    if hasattr(self, 'typed_text') and self.typed_text:
        word_count = len(self.typed_text.split())
        self.track_word_usage(word_count)

    # Update UI
    self.update_status("Stopped")
```

Add tracking method:

```python
def track_word_usage(self, word_count):
    """Track word usage with backend"""
    if not hasattr(self.app, 'user_id') or not self.app.user_id:
        print("No user logged in, skipping tracking")
        return

    try:
        import requests
        response = requests.post(
            "https://slywriterapp.onrender.com/api/usage/track",
            params={"user_id": self.app.user_id, "words": word_count},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Tracked {word_count} words. Total: {data['usage']}")
            # Update UI with new usage
            if hasattr(self.app, 'update_word_count'):
                self.app.update_word_count(data['usage'])
        else:
            print(f"✗ Failed to track: {response.status_code}")

    except Exception as e:
        print(f"✗ Error tracking usage: {e}")
```

---

## 📞 Need Help?

1. **Check if tracking is being called**: Add `print("Tracking...")` statements
2. **Check network**: Verify desktop app can reach Render
3. **Check auth**: Make sure user_id is set after login
4. **Check response**: Print the API response to see errors

---

## ✅ Verification Checklist

After adding tracking code:

- [ ] Desktop app has tracking code in completion handler
- [ ] User ID is correctly passed (numeric 1, not email with @)
- [ ] Words are counted before tracking
- [ ] Network request succeeds (check response)
- [ ] Backend usage increases after typing
- [ ] UI updates to show new usage

---

**Bottom Line**: Backend works perfectly. Desktop app needs to call the API! 🎯
