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
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    client.disconnect()
