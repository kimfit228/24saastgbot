
import csv
import os
import sys

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat

load_dotenv()

API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
SESSION_NAME = "leadgen_session"

# Ключевые слова для поиска — правь под себя, можно добавлять/убирать.
# Смешаны продуктовые термины 24SaaS, общие IT-запросы и бизнес-каналы Казахстана.
KEYWORDS = [
    "сервер аренда",
    "хостинг Казахстан",
    "IT инфраструктура",
    "VPS Казахстан",
    "дата-центр",
    "облачные технологии",
    "тендер IT",
    "IT аутсорс",
    "резервное копирование",
    "стартап Казахстан",
    "бизнес Астана",
    "бизнес Алматы",
    "предприниматели Казахстан",
]

OUTPUT_FILE = "channels_found.csv"


def search_keyword(client, keyword, limit=30):
    result = client(SearchRequest(q=keyword, limit=limit))
    found = []
    for chat in result.chats:
        if isinstance(chat, Channel):
            found.append({
                "type": "группа" if chat.megagroup else "канал",
                "id": chat.id,
                "username": chat.username or "",
                "title": chat.title,
                "participants": getattr(chat, "participants_count", "") or "",
                "keyword": keyword,
            })
        elif isinstance(chat, Chat):
            found.append({
                "type": "группа",
                "id": chat.id,
                "username": "",
                "title": chat.title,
                "participants": getattr(chat, "participants_count", "") or "",
                "keyword": keyword,
            })
    return found


def main():
    if not API_ID or not API_HASH:
        print("Переменные TG_API_ID и TG_API_HASH не найдены.")
        print("Заполни их в файле .env (см. .env.example) и запусти снова.")
        sys.exit(1)

    seen = {}
    with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
        for kw in KEYWORDS:
            print(f"Ищу: {kw} ...")
            try:
                results = search_keyword(client, kw)
            except Exception as e:
                print(f"  ошибка по запросу '{kw}': {e}")
                continue
            new_count = 0
            for r in results:
                key = r["username"] or r["id"]
                if key not in seen:
                    seen[key] = r
                    new_count += 1
            print(f"  найдено: {len(results)}, из них новых: {new_count}, всего уникальных: {len(seen)}")

    def sort_key(r):
        p = r["participants"]
        return -(p if isinstance(p, int) else 0)

    rows = sorted(seen.values(), key=sort_key)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["type", "username", "title", "participants", "keyword", "id"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nГотово. {len(rows)} уникальных каналов/чатов сохранено в {OUTPUT_FILE}")
    print("Открой файл, отметь для себя, какие реально релевантны — этот список")
    print("дальше пойдёт в мониторинг сообщений (следующий шаг).")


if __name__ == "__main__":
    main()
