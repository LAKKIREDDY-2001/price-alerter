# TODO: Fix Missing pending_signups Table

## Steps to Complete:
1. [x] Add pending_signups table creation to init_db() function
2. [x] Remove dynamic table creation from /signup POST route
3. [x] Delete old database file
4. [x] Restart server to reinitialize database
5. [x] Test the fix by accessing the signup page

## Notes:
- The pending_signups table should be created during init_db() like other tables
- This will ensure the table exists when database is recreated

## Changes Made:
- Added `pending_signups` table to `init_db()` function with columns: id, signup_token, username, email, password, phone, email_otp, email_otp_expiry, phone_otp, phone_otp_expiry, created_at
- Removed duplicate `CREATE TABLE` statement from `/signup` POST route (lines 796-815)
- The table is now properly initialized when the database is created

