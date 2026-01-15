# Signup Error Fix - TODO List

## Phase 1: Fix Email Validation Regex

### Step 1.1: Fix static/auth.js ✅ DONE
- [x] Update email regex from `^[\w\.-]+@[\w\.-]+\.\w+$` to `^[^\s@]+@[^\s@]+\.[^\s@]+$`
- [x] Add better error logging

### Step 1.2: Fix app.py ✅ DONE
- [x] Update email regex from `r'^[\w\.-]+@[\w\.-]+\.\w+$'` to `r'^[^\s@]+@[^\s@]+\.[^\s@]+$'`

## Phase 2: Remove Browser Validation Conflict

### Step 2.1: Fix templates/signup.html ✅ DONE
- [x] Change `type="email"` to `type="text"` for email input
- [x] Add `pattern` attribute with new regex for HTML5 validation

## Phase 3: Test the Fix

### Step 3.1: Manual Testing
- [ ] Test with standard email (user@gmail.com)
- [ ] Test with multi-level TLD (user@company.co.uk)
- [ ] Test with numbers in domain (user123@domain123.com)
- [ ] Verify no browser validation errors appear
- [ ] Verify server-side validation still works

### Step 3.2: Check Logs
- [ ] Check browser console for signup logs
- [ ] Check Flask terminal output for `[SIGNUP]` logs

## How to Verify

1. Restart the Flask server:
   ```bash
   python app.py
   ```

2. Clear browser cache and cookies

3. Try signing up with various email formats

4. Check the network tab in browser dev tools for response details

