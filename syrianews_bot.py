import feedparser
import requests
from bs4 import BeautifulSoup
import re
import time
import sqlite3
from datetime import datetime
from telegram import Bot
from transformers import pipeline

# إعدادات تلغرام
TELEGRAM_TOKEN = '7917608803:AAEW9seeNKKBWoMNVM9f9JFyAqb7iGvBQhs'
TELEGRAM_CHAT_ID = -1002631343729  # الرقم الذي أعطيتني إياه

bot = Bot(token=TELEGRAM_TOKEN)

# إعداد قاعدة بيانات SQLite لتخزين الروابط المرسلة
conn = sqlite3.connect('sent_articles.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS sent_articles (
        url TEXT PRIMARY KEY
    )
''')
conn.commit()

# الكلمات المفتاحية التي نبحث عنها داخل المتن
keywords = [
    "Syria", "Syrian", "Damascus", "Assad", "Aleppo", "Idlib", "Kurds", "Kurdish", "HTS",
    "Iran in Syria", "Russian airstrikes", "SDF", "YPG", "refugee crisis", "Syrian economy"
]

# المواقع التي نتابعها
rss_feeds = [
    "https://foreignpolicy.com/feed/",
    "https://foreignaffairs.com/rss.xml",
    "https://thehill.com/feed",
    "https://www.al-monitor.com/rss.xml",
    "https://www.atlanticcouncil.org/feed/",
    "https://www.brookings.edu/feed/",
    "https://www.csis.org/rss.xml",
    "https://www.rand.org/rss.xml",
    "https://www.washingtoninstitute.org/rss.xml",
    "https://www.mei.edu/rss.xml",
    "https://www.haaretz.com/misc/rss/all-news",
    "https://www.debka.com/feed/",
    "https://www.axios.com/rss"
]

# تجهيز الموديل الخاص بالتلخيص
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# وظيفة استخراج نص المقال كاملاً
def extract_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text.strip()
    except Exception as e:
        print(f"خطأ أثناء تحميل المقال: {e}")
        return None

# وظيفة تلخيص النص
def summarize_text(text):
    try:
        if len(text) > 1024:
            text = text[:1024]
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"خطأ أثناء التلخيص: {e}")
        return None

# وظيفة البحث عن مقالات جديدة
def fetch_and_send_articles():
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            url = entry.link

            # التحقق هل سبق إرسال هذا الرابط
            c.execute('SELECT 1 FROM sent_articles WHERE url = ?', (url,))
            if c.fetchone():
                continue

            # استخراج نص المقال
            article_text = extract_article_content(url)
            if article_text is None:
                continue

            # البحث عن الكلمات المفتاحية
            if not any(re.search(r'\b' + re.escape(keyword) + r'\b', article_text, re.IGNORECASE) for keyword in keywords):
                continue

            # تلخيص المقال
            summary = summarize_text(article_text)
            if summary is None:
                continue

            # إرسال التلخيص مع الرابط
            message = f"📰 *عنوان المقال:* {entry.title}\n\n✏️ *ملخص:* {summary}\n\n🔗 [قراءة المقال كاملاً]({url})"
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown', disable_web_page_preview=False)
                print(f"تم إرسال: {entry.title}")

                # تسجيل الرابط في قاعدة البيانات
                c.execute('INSERT INTO sent_articles (url) VALUES (?)', (url,))
                conn.commit()

                time.sleep(5)  # الانتظار قليلاً بين كل إرسال لتجنب الحظر
            except Exception as e:
                print(f"خطأ أثناء إرسال المقال: {e}")

# حلقة التشغيل الدائمة
if __name__ == "__main__":
    while True:
        print(f"🕓 فحص التحديثات... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fetch_and_send_articles()
        print("⌛ الانتظار ساعة...")
        time.sleep(3600)  # انتظر ساعة كاملة قبل الفحص التالي
