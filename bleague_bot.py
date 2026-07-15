import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urlparse

# === 設定部分 ===
# GitHubの「金庫（Secrets）」からURLを読み込む
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NOTIFIED_FILE = "notified_urls.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TEAMS = [
    {"name": "千葉ジェッツ", "url": "https://chibajets.jp/news", "selector": ".p-news__text", "keywords": ["選手契約締結"]},
    {"name": "宇都宮ブレックス", "url": "https://www.utsunomiyabrex.com/news", "selector": ".p-news__text", "keywords": ["新規契約"]},
    {"name": "アルバルク東京", "url": "https://www.alvark-tokyo.jp/news", "selector": ".p-news__text", "keywords": ["契約", "加入"]},
    {"name": "群馬クレインサンダーズ", "url": "https://g-crane-thunders.jp/news", "selector": ".p-news__text", "keywords": ["契約", "加入"]}
]

def load_notified_urls():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    return []

def save_notified_url(url):
    with open(NOTIFIED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def check_and_notify():
    if not WEBHOOK_URL:
        print("エラー: Webhook URLが設定されていません。")
        return

    print("ニュースを確認中...")
    notified_urls = load_notified_urls()
    
    for team in TEAMS:
        try:
            print(f"▶ {team['name']} を確認しています...")
            response = requests.get(team["url"], headers=HEADERS)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            news_elements = soup.select(team["selector"])
            
            for element in news_elements:
                parent_a = element.find_parent("a")
                if not parent_a:
                    continue
                
                link = parent_a.get("href")
                if link.startswith("/"):
                    parsed_url = urlparse(team["url"])
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    link = base_url + link
                    
                h3_tag = element.find("h3")
                title = h3_tag.text.strip() if h3_tag else ""
                
                time_tag = element.find("time")
                date_text = time_tag.text.strip() if time_tag else ""
                
                if any(keyword in title for keyword in team["keywords"]):
                    if link not in notified_urls:
                        message = f"🏀 **新着移籍情報！**\n{team['name']}\n{date_text} | {title}\n{link}"
                        send_discord_notification(message)
                        save_notified_url(link)
                        print(f"【通知完了】{team['name']}: {title}")
                        time.sleep(1)
        except Exception as e:
            print(f"エラーが発生しました ({team['name']}): {e}")

def send_discord_notification(message):
    data = {"content": message}
    requests.post(WEBHOOK_URL, json=data)

# === メイン処理 ===
if __name__ == "__main__":
    check_and_notify()