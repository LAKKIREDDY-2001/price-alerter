# AI Shopping Price Alert Assistant

The project is now set up with a separate HTML, CSS, and JavaScript file.

To run your full-stack price alert application, please follow these steps in your terminal:

**1. Install Backend Dependencies:**
You have already installed 'requests' and 'beautifulsoup4'. You also need 'Flask' and 'Flask-Cors'. Run this command:
```bash
pip install Flask Flask-Cors
```

**2. Start the Backend Server:**
In your terminal, run the following command. This will start the Python web server on port 5000.
```bash
python3 app.py
```
Keep this terminal window open.

**3. Open the Frontend:**
Open the `index.html` file in your web browser. You can do this by right-clicking the file in your file explorer and selecting 'Open with' your preferred browser, or by using the VS Code 'Live Server' extension.

**4. Test the Application:**
- Paste an Amazon product URL into the input field.
- Click the 'Start AI Tracking' button.
- The frontend will send the URL to your Python backend.
- The backend will scrape the price, and the frontend will show an alert with the price it found.
- You can then enter a target price and simulate setting an alert.

Your real-time price tracker is now ready to go!
