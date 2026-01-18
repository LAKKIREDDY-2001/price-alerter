# Signup Error Fix - TODO

## Phase 1: Fix app.py Backend
- [x] Add JSON error handler for 500 errors
- [x] Ensure all signup routes return JSON responses
- [x] Add proper exception handling

## Phase 2: Fix static/auth.js Frontend  
- [x] Add terms checkbox validation
- [x] Improve error handling for HTML responses
- [x] Add better user feedback for network errors

## Phase 3: Testing
- [ ] Test signup with valid data
- [ ] Test signup with invalid data
- [ ] Verify JSON responses for all error cases
- [ ] Test terms checkbox validation

---
## Completed Changes Summary

### app.py Changes:
- Added @app.errorhandler(400) - returns JSON for bad request
- Added @app.errorhandler(404) - returns JSON for not found
- Added @app.errorhandler(500) - returns JSON for server errors

### static/auth.js Changes:
- Added terms checkbox validation before form submission
- Improved error message for non-JSON responses
- Simplified network error message for better UX

