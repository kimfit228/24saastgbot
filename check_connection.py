#!/usr/bin/env python3
"""
Проверка связи с Telegram — БЕЗ входа в аккаунт.

Пробует подключиться к серверам Telegram двумя способами:
  1. обычный (как сейчас делает discover_channels.py)
  2. замаскированный (obfuscated) — трафик выглядит как случайные байты,
     так провайдеру сложнее его распознать и оборвать

Ничего не сохраняет на диск, код подтверждения не запрашивает.

ЗАПУСК:
  python3 check_connection.py
"""

import os
import sys

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.network import ConnectionTcpFull, ConnectionTcpObfuscated
from telethon.tl.functions.help import GetNearestDcRequest

load_dotenv()

API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")

MODES = [
    ("обычный", ConnectionTcpFull),
    ("замаскированный (obfuscated)", ConnectionTcpObfuscated),
]


def try_mode(name, connection):
    print(f"\nПробую режим: {name} ...")
    # session=None — сессия только в памяти, файл не создаётся
    client = TelegramClient(
        None, int(API_ID), API_HASH,
        connection=connection,
        timeout=10,
        connection_retries=1,
    )
    try:
        client.connect()
        dc = client(GetNearestDcRequest())
        print(f"  УСПЕХ: связь есть (страна по мнению Telegram: {dc.country}, ближайший DC: {dc.nearest_dc})")
        return True
    except Exception as e:
        print(f"  НЕ ПОЛУЧИЛОСЬ: {type(e).__name__}: {e}")
        return False
    finally:
        client.disconnect()


def main():
    if not API_ID or not API_HASH:
        print("Переменные TG_API_ID и TG_API_HASH не найдены.")
        print("Заполни их в файле .env (см. .env.example) и запусти снова.")
        sys.exit(1)

    results = {name: try_mode(name, conn) for name, conn in MODES}

    print("\nИТОГ:")
    for name, ok in results.items():
        print(f"  {name}: {'работает' if ok else 'не работает'}")


if __name__ == "__main__":
    main()
