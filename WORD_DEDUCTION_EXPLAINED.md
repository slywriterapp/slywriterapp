# Word Deduction System - Complete Explanation

## 📊 When Are Words Deducted?

Words are deducted **when you call the tracking endpoint** after typing is complete.

---

## 🔄 The Flow

### Desktop App (Typical Flow)

```
1. User types text with SlyWriter
2. Typing session completes
3. App calculates word count
4. App calls: POST /api/usage/track?user_id={id}&words={count}
5. Backend deducts words from user's quota
```

### Web App (Browser)

```
1. User generates/types text
2. Frontend calculates word count
3. Frontend calls: POST /api/usage/track?user_id={id}&words={count}
4. Backend deducts words from user's quota
```

---

## 🎯 The Tracking Endpoint

### Endpoint: `POST /api/usage/track`

**Location**: `slywriter-ui/backend/main.py:929`

**Parameters**:
- `user_id` (query param) - User ID or email
- `words` (query param) - Number of words to deduct

**Example**:
```bash
POST /api/usage/track?user_id=12&words=150
```

**Response**:
```json
{
  "status": "tracked",
  "usage": 150
}
```

---

## 💡 How Words Are Deducted

### The Logic (database.py:368-381)

```python
def track_word_usage(db: Session, user: User, words: int):
    """Track word usage - consumes bonus words first, then weekly allowance"""

    # Always increment lifetime total
    user.total_words_typed += words

    # Step 1: Use bonus words first (from referrals)
    if user.referral_bonus and user.referral_bonus > 0:
        if words <= user.referral_bonus:
            # All words covered by bonus
            user.referral_bonus -= words
        else:
            # Use all bonus, remainder goes to weekly quota
            remaining_words = words - user.referral_bonus
            user.referral_bonus = 0
            user.words_used_this_week += remaining_words
    else:
        # No bonus - deduct from weekly allowance
        user.words_used_this_week += words

    db.commit()
    return user
```

### Example Scenarios

#### Scenario 1: No Bonus Words
```
User Plan: Free (500 words/week)
Words Used This Week: 100
Referral Bonus: 0

User types 50 words:
- words_used_this_week: 100 → 150
- referral_bonus: 0 → 0
- Words remaining: 350
```

#### Scenario 2: With Bonus Words
```
User Plan: Free (500 words/week)
Words Used This Week: 100
Referral Bonus: 1000

User types 50 words:
- words_used_this_week: 100 → 100 (unchanged!)
- referral_bonus: 1000 → 950
- Words remaining: 950 bonus + 400 weekly = 1350
```

#### Scenario 3: Bonus Runs Out Mid-Session
```
User Plan: Free (500 words/week)
Words Used This Week: 100
Referral Bonus: 30

User types 50 words:
- First 30 words: Use bonus (bonus: 30 → 0)
- Remaining 20 words: Use weekly (used: 100 → 120)
- Words remaining: 0 bonus + 380 weekly = 380
```

---

## 📅 Weekly Reset System

### When Does It Reset?

**NOT on Mondays!** Resets are based on **user's signup date**.

### Reset Logic (database.py:294-317)

```python
def check_weekly_reset(db: Session, user: User):
    """Reset weekly limits 7 days after last reset"""

    # Check if 7+ days have passed
    days_since_week_start = (datetime.utcnow() - user.week_start_date).days

    if days_since_week_start >= 7:
        # Add exactly 7 days to maintain same day
        user.week_start_date = user.week_start_date + timedelta(days=7)

        # Reset weekly counters
        user.words_used_this_week = 0
        user.ai_gen_used_this_week = 0
        user.humanizer_used_this_week = 0

        # NOTE: referral_bonus is NOT reset!

        db.commit()
        return True
```

### Reset Example

```
User signed up: October 1, 2025 (Tuesday)
Week start date: October 1
Reset happens: October 8 (7 days later)
Next reset: October 15
Pattern: Resets every Tuesday at signup time
```

---

## 📈 Word Limit Calculation

### Plan Limits (database.py:321-325)

```python
PLAN_LIMITS = {
    "Free": {"words": 500, "ai_gen": 3, "humanizer": 0},
    "Pro": {"words": 5000, "ai_gen": -1, "humanizer": 3},
    "Premium": {"words": -1, "ai_gen": -1, "humanizer": -1}
}
```

**Note**: `-1` means unlimited

### Available Words Calculation (database.py:339-347)

```python
# Bonus words consumed FIRST, then weekly allowance
bonus_words = user.referral_bonus or 0
weekly_remaining = max(0, base_words - user.words_used_this_week)
total_words_available = bonus_words + weekly_remaining
```

### Example Displays

**Free User with No Bonus**:
```
"500/500 words this week"
```

**Free User with Bonus**:
```
"1000 bonus + 500/500 weekly = 1500 total"
```

**Pro User**:
```
"5000/5000 words this week"
```

**Premium User**:
```
"Unlimited"
```

---

## 🎁 Referral Bonus Words

### How Bonus Words Work

1. **Earned from referrals**: Users invite friends
2. **Never expire**: Permanent bonus (not reset weekly)
3. **Consumed first**: Always used before weekly allowance
4. **Separate counter**: `user.referral_bonus` field

### Earning Bonus Words

From referral tier rewards (main.py:1020-1032):

```python
TIER_REQUIREMENTS = [
    {"tier": 1, "referrals": 1, "reward": "1000 words"},
    {"tier": 2, "referrals": 2, "reward": "2500 words"},
    {"tier": 4, "referrals": 5, "reward": "5000 words"},
    {"tier": 6, "referrals": 10, "reward": "10000 words"},
    {"tier": 8, "referrals": 20, "reward": "25000 words"},
]
```

### Claiming Bonus

```bash
POST /api/referrals/claim-reward
{
  "tier": 1,
  "email": "user@example.com"
}
```

**Result**: `user.referral_bonus += 1000`

---

## 🔍 Checking Usage

### Endpoint: `GET /api/auth/user/{user_id}`

**Response** (main.py:912-926):
```json
{
  "id": 12,
  "email": "user@example.com",
  "plan": "Free",
  "usage": 150,
  "word_limit": 500,
  "words_remaining": 350,
  "total_words_available": 350,
  "bonus_words": 0,
  "word_limit_display": "350/500 words this week"
}
```

### Endpoint: `GET /auth/profile` (JWT required)

Same data as above, requires Authorization header.

### Endpoint: `GET /api/user-dashboard` (JWT required)

Full dashboard with usage stats (main.py:1742-1763):
```json
{
  "plan": {
    "name": "free",
    "words_limit": 500,
    "words_used": 150,
    "words_remaining": 350,
    "usage_percentage": 30.0
  }
}
```

---

## ⚙️ Implementation in Your App

### When to Call Tracking

**Option 1: After Each Session** (Recommended)
```python
# After typing completes
word_count = count_words(typed_text)
response = requests.post(
    f"{API_URL}/api/usage/track",
    params={"user_id": user_id, "words": word_count}
)
```

**Option 2: Real-time Tracking**
```python
# Track every N words
if typed_words % 100 == 0:
    track_usage(user_id, 100)
```

**Option 3: Batch Tracking**
```python
# Track at end of day
total_words = get_daily_words()
track_usage(user_id, total_words)
```

### Before Typing Session

```python
# Check if user has words available
user = get_user(user_id)
if user["words_remaining"] <= 0:
    show_upgrade_prompt()
    return

# Start typing session
start_typing()
```

### After Typing Session

```python
# Count words typed
words = count_words(text)

# Track usage
track_usage(user_id, words)

# Update UI
refresh_word_count()
```

---

## 🚨 Important Notes

### 1. No Automatic Deduction

Words are **NOT** deducted automatically. Your app must call the tracking endpoint.

### 2. Client-Side Responsibility

The **frontend/desktop app** is responsible for:
- Counting words accurately
- Calling the tracking endpoint
- Handling errors

### 3. No Rollback

Once tracked, words **cannot be refunded** through the API. You'd need to:
- Manually adjust in database, OR
- Add bonus words via referral system

### 4. Bonus Words First

**Always** consume bonus words before weekly allowance. This is automatic in the backend.

### 5. Weekly Reset Is Per-User

Each user resets on their own schedule (7 days from signup), not on a global Monday.

---

## 🧪 Testing Word Deduction

### Test Script

```python
import requests

API_URL = "https://slywriterapp.onrender.com"
USER_ID = 12

# Check current usage
response = requests.get(f"{API_URL}/api/auth/user/{USER_ID}")
before = response.json()
print(f"Before: {before['usage']} words used")
print(f"Remaining: {before['words_remaining']}")

# Track 50 words
response = requests.post(
    f"{API_URL}/api/usage/track",
    params={"user_id": USER_ID, "words": 50}
)
print(f"Tracked: {response.json()}")

# Check usage again
response = requests.get(f"{API_URL}/api/auth/user/{USER_ID}")
after = response.json()
print(f"After: {after['usage']} words used")
print(f"Remaining: {after['words_remaining']}")
```

---

## 📊 Database Schema

### User Table Fields

```python
# Weekly tracking (resets every 7 days)
words_used_this_week = Column(Integer, default=0)
week_start_date = Column(DateTime, default=datetime.utcnow)

# Lifetime totals (never reset)
total_words_typed = Column(Integer, default=0)

# Bonus words (never reset, consumed first)
referral_bonus = Column(Integer, default=0)

# Plan
plan = Column(String, default="Free")  # Free, Pro, Premium
```

---

## 🎯 Summary

**Words are deducted when**:
1. Your app calls `POST /api/usage/track?user_id={id}&words={count}`
2. Backend checks bonus words first
3. Remaining words deducted from weekly allowance
4. Database updated with new usage

**Words reset when**:
1. 7 days pass since `week_start_date`
2. `words_used_this_week` set to 0
3. New week starts (maintains same weekday)

**Bonus words**:
1. Earned from referrals
2. Never expire
3. Consumed before weekly allowance
4. Separate from weekly quota

---

## 🔗 Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/usage/track` | Deduct words |
| `POST /api/usage/check-reset` | Check/trigger weekly reset |
| `GET /api/auth/user/{id}` | Check current usage |
| `GET /auth/profile` | Get profile with usage (JWT) |
| `GET /api/user-dashboard` | Full dashboard (JWT) |
| `POST /api/referrals/claim-reward` | Add bonus words |

---

**Questions?** Check the test suite: `python test_render_endpoints.py`
