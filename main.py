import time
import requests
import pycountry
import re
import os
from datetime import datetime
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv
from neonize.proto.Neonize_pb2 import MessageServerID
from neonize.utils.enum import ReceiptType
from apscheduler.schedulers.background import BackgroundScheduler
from settings import CONFIG

# --- فنکشن: کنٹری فلیگ لاجک ---
def get_emoji_flag(country_code):
    if not country_code: return "🌐"
    offset = 127397
    return "".join(chr(ord(c.upper()) + offset) for c in country_code)

def get_country_info(raw_country_str):
    country_name = raw_country_str.split(' ')[0]
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        iso_code = country.alpha_2
        f = get_emoji_flag(iso_code)
        return f, f"{f} {country_name}"
    except:
        return "🌐", f"🌐 {country_name}"

def extract_otp(message):
    match = re.search(r'\b\d{3,4}[-\s]?\d{3,4}\b|\b\d{4,8}\b', message)
    return match.group(0) if match else "N/A"

def mask_number(number):
    if not number: return "N/A"
    return f"{number[:5]}XXXX{number[-2:]}"

last_processed_ids = set()

# --- OTP بھیجنے کا فنکشن (بٹنز کے ساتھ) ---
def send_otp_with_buttons(client: NewClient, chat_id, body, otp_text):
    # یہاں ہم واٹس ایپ کے بٹنز (Native Flow) استعمال کر رہے ہیں
    # نوٹ: بٹنز کچھ واٹس ایپ ورژن پر شو نہیں ہوتے، اس لیے لنک ٹیکسٹ میں بھی موجود ہے
    buttons = [
        {"name": "cta_copy", "buttonParamsJson": '{"display_text":"Copy OTP","id":"123","copy_code":"' + otp_text + '"}'},
        {"name": "cta_url", "buttonParamsJson": '{"display_text":"Join Group","url":"https://chat.whatsapp.com/EbaJKbt5J2T6pgENIeFFht"}'}
    ]
    client.send_message(chat_id, body) # فی الحال سادہ میسج بھیج رہا ہوں کیونکہ نان بزنس پر بٹنز بلاک ہو رہے ہیں

# --- OTP مانیٹرنگ لوپ ---
def check_otp_apis(client: NewClient):
    global last_processed_ids
    for url in CONFIG['otp_api_urls']:
        try:
            api_name = "API 1" if "railway" in url else "API 2"
            response = requests.get(url, timeout=10)
            data = response.json()
            records = data.get('aaData', [])
            for row in records:
                if len(row) < 5: continue
                msg_id = f"{row[2]}_{row[0]}" 
                if msg_id not in last_processed_ids:
                    raw_time, country_info, phone_number, service_name, full_msg = row[0], row[1], row[2], row[3], row[4]
                    c_flag, country_with_flag = get_country_info(country_info)
                    masked_num = mask_number(phone_number)
                    otp_code = extract_otp(full_msg)
                    
                    otp_message_body = f"""
✨ *{c_flag} | {service_name.upper()} New Message Received {api_name}*⚡

> ⏰   *`Time`   •   _{raw_time}_*

> 🌍   *`Country`  ✓   _{country_with_flag}_*

  📞   *`Number`  √   _{masked_num}_*

> ⚙️   *`Service`  ©   _{service_name}_*

  🔑   *`OTP`  ~   _{otp_code}_*
  
> 📋   *`Join For Numbers`*
  
> https://chat.whatsapp.com/EbaJKbt5J2T6pgENIeFFht

> 📩   `Full Message`

> `{full_msg}`

> Developed by Nothing Is Impossible

> `🙂MR~Bunny🙂` `💔Um@R💔` `👑Mohsin~King👑` 
> `😎SK~SuFyAn😎` `😈SUDAIS~Ahmed👿`
                    """.strip()

                    for channel in CONFIG['otp_channel_ids']:
                        client.send_message(channel, otp_message_body)
                    
                    last_processed_ids.add(msg_id)
                    if len(last_processed_ids) > 500: last_processed_ids.clear()
        except Exception as e:
            print(f"❌ API Error: {e}")

# --- ایونٹ ہینڈلرز (Corrected Syntax) ---
client = NewClient("kami_session.db")

@client.event(ConnectedEv)
def on_connected(_: NewClient, __: ConnectedEv):
    print(f"✅ {CONFIG['bot_name']} Connected Successfully!")
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_otp_apis, 'interval', seconds=CONFIG['monitor_interval'], args=[client])
    scheduler.start()

@client.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    msg_text = message.Message.conversation or message.Message.extendedTextMessage.text
    chat_id = message.Info.MessageSource.Chat
    
    # 1. .id کمانڈ
    if msg_text == ".id":
        client.reply_message(message, f"📍 *Chat ID:* `{chat_id}`")

    # 2. .chk کمانڈ (بٹنز ٹیسٹنگ)
    elif msg_text == ".chk" or msg_text == ".check":
        test_body = "🧪 *Testing WhatsApp Buttons Styles* ⚡"
        # ہم یہاں ٹیکسٹ کے ساتھ لنکس بھیج رہے ہیں کیونکہ واٹس ایپ کے نئے رولز میں بٹنز صرف بزنس پیغامات میں مستحکم ہیں
        client.reply_message(message, test_body + "\n\n1. Copy OTP: `123456` (Click to copy)\n2. Group: https://chat.whatsapp.com/EbaJKbt5J2T6pgENIeFFht")

def start_bot():
    if not client.is_registered():
        print(f"⏳ Pairing for: {CONFIG['owner_number']}")
        time.sleep(5)
        code = client.pair_code(CONFIG['owner_number'])
        print(f"\n🔑 PAIRING CODE: \033[1;32m{code}\033[0m\n")
    client.connect()

if __name__ == "__main__":
    start_bot()