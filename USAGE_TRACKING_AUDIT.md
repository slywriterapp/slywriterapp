# Usage Tracking Audit - Critical Issues Found

## Summary

**Date**: October 9, 2025
**Status**: 🔴 **CRITICAL ISSUES FOUND**

The desktop app is NOT properly tracking AI generation and Humanizer usage with the backend.

---

## Issues Found

### 1. ❌ AI Generation NOT Tracked Properly

**File**: `ai_text_generator.py` (Line 564-571)

**Current Code**:
```python
requests.post(
    "https://slywriterapp.onrender.com/update_usage",  # ❌ OLD ENDPOINT!
    json={"user_id": user_id, "words": word_count},
    timeout=10
)
```

**Problems**:
1. Uses `/update_usage` (old endpoint that doesn't exist)
2. Only tracks word count, not AI generation usage
3. Doesn't track with proper endpoint `/api/usage/track`
4. Doesn't call `/api/usage/ai-generation` to track AI gen usage

**Impact**: Users can spam AI generation infinitely without being charged!

---

###2. ❌ Humanizer NOT Tracked At All

**File**: `ai_text_generator.py` (Line 312-351)

**Current Code**:
```python
def _call_humanizer(self, text):
    # ... makes API call to /ai_humanize_text ...
    # ❌ NO USAGE TRACKING!
    return result.get('humanized_text')
```

**Problems**:
1. Calls humanizer API but never tracks usage
2. Doesn't call `/api/usage/humanizer` endpoint
3. Users can use humanizer infinitely for free

**Impact**: You're paying for humanizer API calls but users aren't being charged!

---

### 3. ❌ Premium AI Filler NOT Tracked

**File**: `premium_typing.py` (Line 46-149)

**Current Code**:
```python
def generate_filler(goal_text, ...):
    response = requests.post(FILLER_SERVER_URL, ...)
    # ❌ NO USAGE TRACKING!
    return filler
```

**Problems**:
1. Generates AI filler text but never tracks usage
2. Doesn't track with `/api/usage/ai-generation`
3. Premium users get infinite AI filler for free

**Impact**: Burning OpenAI credits without charging users!

---

### 4. ✅ Word Tracking - FIXED (But Needs Verification)

**File**: `typing_engine.py` (Lines 441-475)

**Status**: Recently fixed, but needs testing

**What Works**:
- Calls `/api/usage/track` after typing sessions
- Properly tracks word count
- Has error handling

**Needs Verification**:
- Test with actual typing session
- Verify server updates correctly

---

## Backend API Endpoints (from main.py)

### Word Tracking ✅
```python
POST /api/usage/track?user_id={id}&words={count}
Response: {"status": "tracked", "usage": 150}
```

### AI Generation Tracking ❌ NOT CALLED
```python
POST /api/usage/ai-generation?user_id={id}
Response: {"status": "tracked", "usage": 2}
```

### Humanizer Tracking ❌ NOT CALLED
```python
POST /api/usage/humanizer?user_id={id}
Response: {"status": "tracked", "usage": 1}
```

---

## Critical Fixes Needed

### Fix 1: AI Generation Usage Tracking

**File**: `ai_text_generator.py`

**Current** (Line 160-161):
```python
# Update word usage tracking
self._update_usage_tracking(generated_text)
```

**Should Be**:
```python
# Track AI generation usage (CRITICAL!)
self._track_ai_generation_usage()

# Track word usage
self._update_usage_tracking(generated_text)
```

**New Method Needed**:
```python
def _track_ai_generation_usage(self):
    """Track AI generation usage with backend"""
    try:
        user_id = getattr(self.app, 'user_id', None) or (self.app.user.get('id') if self.app.user else None)

        if not user_id:
            print("[AI GEN] No user_id, skipping AI gen tracking")
            return

        response = requests.post(
            "https://slywriterapp.onrender.com/api/usage/ai-generation",
            params={"user_id": user_id},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[BACKEND] Tracked AI generation. Total uses: {data['usage']}")
        else:
            print(f"[BACKEND] AI gen tracking failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] AI gen tracking error: {e}")
```

---

### Fix 2: Humanizer Usage Tracking

**File**: `ai_text_generator.py`

**Current** (Line 339-342):
```python
if result.get('success'):
    return result.get('humanized_text')
```

**Should Be**:
```python
if result.get('success'):
    # Track humanizer usage (CRITICAL!)
    self._track_humanizer_usage()
    return result.get('humanized_text')
```

**New Method Needed**:
```python
def _track_humanizer_usage(self):
    """Track humanizer usage with backend"""
    try:
        user_id = getattr(self.app, 'user_id', None) or (self.app.user.get('id') if self.app.user else None)

        if not user_id:
            print("[HUMANIZER] No user_id, skipping humanizer tracking")
            return

        response = requests.post(
            "https://slywriterapp.onrender.com/api/usage/humanizer",
            params={"user_id": user_id},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[BACKEND] Tracked humanizer. Total uses: {data['usage']}")
        else:
            print(f"[BACKEND] Humanizer tracking failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Humanizer tracking error: {e}")
```

---

### Fix 3: Update Word Tracking Method

**File**: `ai_text_generator.py`

**Current** (Line 565-568):
```python
requests.post(
    "https://slywriterapp.onrender.com/update_usage",  # ❌ WRONG!
    json={"user_id": user_id, "words": word_count},
    timeout=10
)
```

**Should Be**:
```python
response = requests.post(
    "https://slywriterapp.onrender.com/api/usage/track",  # ✅ CORRECT!
    params={"user_id": user_id, "words": word_count},  # ✅ Use params, not json
    timeout=5
)

if response.status_code == 200:
    data = response.json()
    print(f"[BACKEND] Tracked {word_count} words. Total: {data['usage']}")
else:
    print(f"[BACKEND] Word tracking failed: {response.status_code}")
```

---

### Fix 4: Premium AI Filler Tracking

**File**: `premium_typing.py`

**Current** (Line 91-122):
```python
if response.status_code == 200:
    # ... process filler ...
    return processed_filler
```

**Should Be**:
```python
if response.status_code == 200:
    # ... process filler ...

    # Track AI filler generation (CRITICAL!)
    _track_ai_filler_usage()

    return processed_filler
```

**New Function Needed**:
```python
def _track_ai_filler_usage():
    """Track AI filler generation usage"""
    try:
        # Get user_id from account tab
        import typing_engine
        user_id = None

        if typing_engine._account_tab and hasattr(typing_engine._account_tab, 'app'):
            if typing_engine._account_tab.app.user:
                user_id = typing_engine._account_tab.app.user.get('id')

        if not user_id:
            print("[AI FILLER] No user_id, skipping tracking")
            return

        response = requests.post(
            "https://slywriterapp.onrender.com/api/usage/ai-generation",
            params={"user_id": user_id},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[BACKEND] Tracked AI filler. Total uses: {data['usage']}")
        else:
            print(f"[BACKEND] AI filler tracking failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] AI filler tracking error: {e}")
```

---

## Testing Plan

### Test 1: AI Generation Usage
```bash
# Before test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "ai_gen_usage": 2

# Use AI generation hotkey (Ctrl+Alt+G)
# Should see in console: "[BACKEND] Tracked AI generation. Total uses: 3"

# After test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "ai_gen_usage": 3 ✅
```

### Test 2: Humanizer Usage
```bash
# Before test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "humanizer_usage": 1

# Use AI generation with humanizer enabled
# Should see: "[BACKEND] Tracked humanizer. Total uses: 2"

# After test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "humanizer_usage": 2 ✅
```

### Test 3: Word Usage (Already Fixed)
```bash
# Before test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "usage": 175

# Type 50 words
# Should see: "[BACKEND] Tracked 50 words. Total: 225"

# After test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "usage": 225 ✅
```

### Test 4: Premium AI Filler
```bash
# Before test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "ai_gen_usage": 2

# Use premium typing with AI filler
# Filler triggers ~3 times per session
# Should see: "[BACKEND] Tracked AI filler. Total uses: 5"

# After test
curl "https://slywriterapp.onrender.com/api/auth/user/1"
# Check: "ai_gen_usage": 5 ✅
```

---

## Priority

🔴 **CRITICAL - MUST FIX IMMEDIATELY**

**Financial Impact**:
- You're paying for OpenAI API calls
- You're paying for AIUndetect API calls
- Users are using these for FREE
- This is costing you money right now!

**Estimated Cost**:
- AI Generation: $0.002 per request (GPT-4)
- Humanizer: $0.01-0.05 per request (AIUndetect)
- If 100 users spam AI gen 10x each = $20/day loss
- If 50 users spam humanizer 5x each = $12.50/day loss
- **Estimated loss: $32.50+/day**

---

## Implementation Order

1. ✅ **Word tracking** - Already fixed (needs testing)
2. 🔴 **AI generation tracking** - Fix immediately
3. 🔴 **Humanizer tracking** - Fix immediately
4. 🔴 **Premium AI filler tracking** - Fix immediately
5. ✅ **Test all endpoints** - Verify fixes work

---

## Files That Need Changes

### Critical:
1. `ai_text_generator.py` - Add AI gen + humanizer tracking
2. `premium_typing.py` - Add AI filler tracking

### Nice to Have:
3. `typing_engine.py` - Already fixed, just verify

---

## Summary

**Current State**: 🔴 **BROKEN**
- Word tracking: ✅ Fixed
- AI generation tracking: ❌ Missing
- Humanizer tracking: ❌ Missing
- Premium filler tracking: ❌ Missing

**After Fixes**: ✅ **WORKING**
- Word tracking: ✅ Working
- AI generation tracking: ✅ Working
- Humanizer tracking: ✅ Working
- Premium filler tracking: ✅ Working

**Estimated Time**:
- Fixes: 30 minutes
- Testing: 20 minutes
- Total: 50 minutes

---

**MUST FIX BEFORE USERS DISCOVER THIS!**

If users realize they can spam AI generation/humanizer for free, you'll have:
1. Massive OpenAI bills
2. Massive AIUndetect bills
3. Server overload
4. Financial loss

**Fix this NOW!**
