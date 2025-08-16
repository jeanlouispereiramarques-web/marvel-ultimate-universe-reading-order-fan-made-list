import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from plyer import notification
import subprocess  # for git commands

# === Sites de comics ===
comic_urls = [
    "https://readcomicsonline.ru/comic/ultimate-spiderman-2024",
    "https://readcomicsonline.ru/comic/the-ultimates-2024",
    "https://readcomicsonline.ru/comic/ultimate-black-panther-2024",
    "https://readcomicsonline.ru/comic/ultimate-xmen-2024",
    "https://readcomicsonline.ru/comic/ultimate-spiderman-incursion-2025",
    "https://readcomicsonline.ru/comic/ultimate-wolverine-2025"
]

json_file = "chapters.json"
html_file = "comic_chapters.html"

# === GitHub repo settings ===
git_repo_path = "C:/Users/Elève/Desktop/ComicTracker"  # replace with your local repo path
git_commit_msg = "Auto-update comic chapters"

# === Récupérer chapitres avec dates ===
def fetch_chapters(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    title_tag = soup.find("h1") or soup.find("h2")
    series_name = title_tag.get_text(strip=True) if title_tag else "Unknown Series"
    chapters = []
    chap_titles = soup.select("h5.chapter-title-rtl a")
    chap_dates = soup.select("div.date-chapter-title-rtl")
    for title_elem, date_elem in zip(chap_titles, chap_dates):
        chap_title = title_elem.get_text(strip=True)
        link = title_elem.get("href")
        date_str = date_elem.get_text(strip=True)
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d %b. %Y").date()
        except:
            date_obj = None
        chapters.append({
            "title": chap_title,
            "link": link,
            "date_obj": date_obj,
            "is_new": False
        })
    return chapters

# === Charger les chapitres existants ===
def load_previous():
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                try:
                    item["date_obj"] = datetime.datetime.strptime(item["date"], "%d %B %Y").date()
                except:
                    item["date_obj"] = None
                item["is_new"] = False
            return data
    return []

# === Sauvegarder chapitres ===
def save_chapters(chapters):
    to_save = [{"title": c["title"], "link": c["link"],
                "date": c["date_obj"].strftime("%d %B %Y") if c["date_obj"] else "Unknown",
                "is_new": c.get("is_new", False)}
               for c in chapters]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)

# === Générer HTML cliquable avec style ===
def generate_html(chapters):
    new_chapters = [c for c in chapters if c.get("is_new", False)]
    all_chapters = [c for c in chapters if not c.get("is_new", False)]
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
            a { color: #70a1ff; text-decoration: none; }
            a:hover { text-decoration: underline; }
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
            date_str = c["date_obj"].strftime("%d %B %Y") if c["date_obj"] else "Unknown"
            html += f'<li>{c["title"]} <span class="date">– {date_str}</span> - <a href="{c["link"]}" target="_blank">Lire</a></li>'
        html += "</ul></div>"
    html += "<h2>All Chapters</h2><ul>"
    for c in all_chapters:
        date_str = c["date_obj"].strftime("%d %B %Y") if c["date_obj"] else "Unknown"
        html += f'<li>{c["title"]} <span class="date">– {date_str}</span> - <a href="{c["link"]}" target="_blank">Lire</a></li>'
    html += "</ul></body></html>"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

# === Pousser les changements sur GitHub ===
def push_to_github():
    try:
        subprocess.run(["git", "-C", git_repo_path, "add", "."], check=True)
        subprocess.run(["git", "-C", git_repo_path, "commit", "-m", git_commit_msg], check=True)
        subprocess.run(["git", "-C", git_repo_path, "push"], check=True)
        print("✅ Changes pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")

# === Vérifier les nouveaux chapitres et notifier ===
def main():
    all_chapters = []
    for url in comic_urls:
        try:
            chaps = fetch_chapters(url)
            all_chapters.extend(chaps)
        except Exception as e:
            print(f"Erreur sur {url}: {e}")

    prev_chapters = load_previous()
    prev_titles = {c["title"] for c in prev_chapters}

    # Marquer les nouveaux chapitres
    new_chapters = []
    for c in all_chapters:
        if c["title"] not in prev_titles:
            c["is_new"] = True
            new_chapters.append(c)

    # Notification pour le premier nouveau chapitre seulement
    if new_chapters:
        first = new_chapters[0]
        notification.notify(
            title="Nouveau chapitre !",
            message=f"{first['title']} – {first['date_obj'].strftime('%d %B %Y') if first['date_obj'] else 'Unknown'}",
            timeout=10
        )

    # Fusionner anciens et nouveaux, garder les dates connues
    combined = prev_chapters + new_chapters
    combined = [c for c in combined if c["date_obj"] is not None]

    # Tri par date (du plus ancien au plus récent)
    combined.sort(key=lambda x: x["date_obj"])

    save_chapters(combined)
    generate_html(combined)
    push_to_github()  # push automatically

    print(f"✅ {len(new_chapters)} nouveaux chapitres ajoutés. Vérifie {html_file} !")

if __name__ == "__main__":
    main()
