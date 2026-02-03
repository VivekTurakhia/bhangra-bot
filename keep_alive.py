from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    """Simple health check endpoint for UptimePing."""
    return "Bot is alive!"

def run():
    """Run Flask server on port 8080."""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start Flask server in a separate thread."""
    t = Thread(target=run)
    t.daemon = True
    t.start()
