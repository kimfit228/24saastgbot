
import asyncio
import csv
import getpass
import os
import sys

import qrcode
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.errors import PasswordHashInvalidError, SessionPasswordNeededError
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat
from telethon.tl.types.auth import LoginTokenSuccess

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


async def authorize_with_qr(client, max_qr_attempts=3):
    """Authorize an unauthenticated Telethon client using a terminal QR code."""
    if await client.is_user_authorized():
        return

    for attempt in range(1, max_qr_attempts + 1):
        qr_login = await client.qr_login()

        # Telethon may return an already accepted token if it was scanned
        # just before the previous wait started.
        if isinstance(qr_login._resp, LoginTokenSuccess):
            await client._on_login(qr_login._resp.authorization.user)
            break

        qr = qrcode.QRCode(border=2)
        qr.add_data(qr_login.url)
        qr.make(fit=True)

        wait_task = asyncio.create_task(qr_login.wait())
        await asyncio.sleep(0)

        print("\nTelegram → Settings → Devices → Link Desktop Device")
        print("Отсканируй QR-код в Telegram:")
        qr.print_ascii(tty=sys.stdout.isatty(), invert=True)

        try:
            await wait_task
        except asyncio.TimeoutError:
            if attempt == max_qr_attempts:
                raise RuntimeError(
                    "Не удалось авторизоваться: время ожидания QR-кода истекло. "
                    "Запусти программу снова, чтобы повторить попытку."
                )
            print(f"QR-код истёк. Создаю новый ({attempt + 1}/{max_qr_attempts})...")
            continue
        except SessionPasswordNeededError:
            while True:
                password = getpass.getpass("Введи пароль двухфакторной аутентификации Telegram: ")
                if not password:
                    print("Пароль не может быть пустым.")
                    continue
                try:
                    await client.sign_in(password=password)
                    break
                except PasswordHashInvalidError:
                    print("Неверный пароль. Попробуй ещё раз.")

        if await client.is_user_authorized():
            break

    if not await client.is_user_authorized():
        raise RuntimeError("Telegram authorization did not complete.")

    print("Telegram authorization successful. Session saved.")


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

    client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
    client.connect()
    client.loop.run_until_complete(authorize_with_qr(client))

    seen = {}
    try:
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
    finally:
        client.disconnect()

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
