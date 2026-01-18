# Signup Error Fix Plan

## Problem Analysis
The error "Network error: Server returned non-JSON response: . Please check your connection and try again." occurs because:
1. The JavaScript expects JSON responses from `/signup` POST endpoint
2. Server errors (500) return HTML instead of JSON
3. No terms checkbox validation before form submission

## Information Gathered
- `app.py` signup route handles GET/POST requests
- `static/auth.js` handles form submission with fetch API
- `templates/signup.html` contains the signup form with terms checkbox
- The error message suggests server is returning non-JSON response

## Plan

### 1. Fix app.py - Ensure all responses are JSON
**File**: `/Users/lakkireddyvenkatamadhavareddy/Downloads/price-alerter-main/app.py`

Changes needed:
- Add error handler for 500 errors to return JSON
- Ensure all signup error cases return JSON
- Add proper JSON content-type headers

### 2. Fix static/auth.js - Add proper error handling
**File**: `/Users/lakkireddyvenkatamadhavareddy/Downloads/price-alerter-main/static/auth.js`

Changes needed:
- Add terms checkbox validation
- Improve error handling to handle HTML responses gracefully
- Add retry logic for transient errors
- Better user feedback for different error types

### 3. Optional: Add terms acceptance logging
Track when users accept terms for analytics

## Dependent Files to be Edited
1. `app.py` - Backend signup route
2. `static/auth.js` - Frontend form handling

## Followup Steps
1. Test signup flow with valid/invalid data
2. Test terms checkbox validation
3. Verify JSON responses for all error cases

