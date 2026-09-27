import os
import sys

from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
PHONE = sys.argv[1] if len(sys.argv) > 1 else input("Phone: ")

client = TelegramClient(None, API_ID, API_HASH)
client.connect()
try:
    sent = client.send_code_request(PHONE)
    print("1-й запрос -> type:", sent.type, "| next_type:", sent.next_type, "| timeout:", sent.timeout)

    print("\nПробую принудительно через SMS...")
    sent2 = client.send_code_request(PHONE, force_sms=True)
    print("2-й запрос (force_sms) -> type:", sent2.type, "| next_type:", sent2.next_type, "| timeout:", sent2.timeout)
except Exception as e:
    print(f"ОШИБКА: {type(e).__name__}: {e}")
finally:
    client.disconnect()
