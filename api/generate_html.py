import json
import requests
from datetime import datetime, timedelta
from flask import Flask, Response

app = Flask(__name__)

# GitHub raw URL of your chapters.json
CHAPTERS_URL = "https://raw.githubusercontent.com/jeanlouispereiramarques-web/marvel-ultimate-universe-reading-order-fan-made-list/main/chapters.json"

# Time in days before new chapters move to all chapters
NEW_CHAPTER_LIFETIME = 1  # 1 day

@app.route("/", methods=["GET"])
def generate_html():
    r = requests.get(CHAPTERS_URL)
    chapters = r.json()

    now = datetime.utcnow()

    # Separate new chapters
    new_chapters = []
    all_chapters = []

    for c in chapters:
        # parse date
        try:
            c_date = datetime.strptime(c["date"], "%d %B %Y")
        except:
            c_date = None

        # Check if it's still new
        is_new = c.get("is_new", False)
        new_time = c.get("new_timestamp", None)
        if is_new and new_time:
            new_time_dt = datetime.strptime(new_time, "%Y-%m-%dT%H:%M:%S")
            if now - new_time_dt > timedelta(days=NEW_CHAPTER_LIFETIME):
                is_new = False  # move to all chapters

        if is_new:
            new_chapters.append(c)
        else:
            all_chapters.append(c)

    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Marvel Ultimate Reading Order</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #1e1e2f; color: #f0f0f0; margin: 20px; }
            h1 { color: #ff4757; }
            h2 { color: #ffa502; margin-top: 30px; }
            ul { list-style-type: none; padding: 0; }
            li { background-color: #2f3542; margin: 5px 0; padding: 10px; border-radius: 8px; transition: background 0.3s; }
            li:hover { background-color: #57606f; }
            .date { color: #ffa502; margin-left: 10px; }
            .new-section { border: 2px solid #ff4757; padding: 10px; border-radius: 10px; background-color: #2f3542; }
        </style>
    </head>
    <body>
        <h1>Marvel Ultimate Reading Order</h1>
    """

    if new_chapters:
        html += "<div class='new-section'><h2>New Chapters</h2><ul>"
        for c in new_chapters:
            date_str = c["date"] if c["date"] != "Unknown" else "Unknown"
            html += f"<li>{c['title']} <span class='date'>– {date_str}</span></li>"
        html += "</ul></div>"

    html += "<h2>All Chapters</h2><ul>"
    for c in all_chapters:
        date_str = c["date"] if c["date"] != "Unknown" else "Unknown"
        html += f"<li>{c['title']} <span class='date'>– {date_str}</span></li>"
    html += "</ul></body></html>"

    return Response(html, mimetype="text/html")
