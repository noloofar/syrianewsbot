import sqlite3
import time
import logging
from telegram import Bot
from telegram.error import TelegramError

# إعدادات البوت
TOKEN = '7917608803:AAEW9seeNKKBWoMNVM9f9JFyAqb7iGvBQhs'
CHANNEL_ID = '@syrianewsbyMalek'

# قاعدة البيانات
DB_FILE = 'syria_articles.db'

# إعداد البوت
bot = Bot(token=TOKEN)

# إعداد اللوجات
logging.basicConfig(level=logging.INFO)

# وظيفة لجلب المقالات غير المرسلة
def get_unsent_articles():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, link FROM articles WHERE sent = 0")
    articles = cursor.fetchall()
    conn.close()
    return articles

# وظيفة تحديث حالة الإرسال
def mark_article_as_sent(article_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE articles SET sent = 1 WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()

# الوظيفة الرئيسية
def send_articles():
    articles = get_unsent_articles()
    for article_id, link in articles:
        try:
            message = f"🔗 رابط الخبر:\n{link}"
            bot.send_message(chat_id=CHANNEL_ID, text=message)
            mark_article_as_sent(article_id)
            logging.info(f"تم إرسال الرابط بنجاح: {link}")
            time.sleep(5)
        except TelegramError as e:
            logging.error(f"خطأ أثناء الإرسال: {e}")
            continue

# تشغيل البوت
if __name__ == "__main__":
    while True:
        send_articles()
        time.sleep(60)
