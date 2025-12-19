import time
import requests
import pycountry
import re
import os
from datetime import datetime
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv
from apscheduler.schedulers.background import BackgroundScheduler
from settings import CONFIG

# --- فنکشن: کنٹری کوڈ کو ایموجی جھنڈے میں بدلنے کے لیے ---
def get_emoji_flag(country_code):
    if not country_code: return "🌐"
    offset = 127397
    return "".join(chr(ord(c.upper()) + offset) for c in country_code)

# --- کنٹری فلیگ لاجک (pycountry استعمال کرتے ہوئے) ---
def get_country_info(raw_country_str):
    country_name = raw_country_str.split(' ')[0]
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        iso_code = country.alpha_2
        f = get_emoji_flag(iso_code)
        return f, f"{f} {country_name}"
    except:
        return "🌐", f"🌐 {country_name}"

# --- او ٹی پی نکالنے کا فنکشن ---
def extract_otp(message):
    # میسج میں سے ہندسے (جیسے 625-266 یا 454381) تلاش کریں
    match = re.search(r'\b\d{3,4}[-\s]?\d{3,4}\b|\b\d{4,8}\b', message)
    return match.group(0) if match else "N/A"

# --- نمبر ماسک کرنے کا فنکشن ---
def mask_number(number):
    if not number: return "N/A"
    return f"{number[:5]}XXXX{number[-2:]}"

last_processed_ids = set()

# --- OTP مانیٹرنگ کی مین لاجک ---
def check_otp_apis(client: NewClient):
    global last_processed_ids
    
    for url in CONFIG['otp_api_urls']:
        try:
            api_name = "API 1" if "railway" in url else "API 2"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # API کے 'aaData' کو پراسیس کرنا
            records = data.get('aaData', [])
            
            for row in records:
                if len(row) < 5: continue
                
                # یونیک آئی ڈی (نمبر + وقت) تاکہ پرانا میسج دوبارہ نہ جائے
                msg_id = f"{row[2]}_{row[0]}" 
                
                if msg_id not in last_processed_ids:
                    raw_time = row[0]
                    country_info = row[1]
                    phone_number = row[2]
                    service_name = row[3]
                    full_msg = row[4]
                    
                    c_flag, country_with_flag = get_country_info(country_info)
                    masked_num = mask_number(phone_number)
                    otp_code = extract_otp(full_msg)
                    service_title = service_name.upper()

                    # 🔥 آپ کی بتائی ہوئی "سیم ٹو سیم" باڈی
                    otp_message_body = f"""
✨ *{c_flag} | {service_title} New Message Received {api_name}*⚡

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

                    # تمام چینلز پر میسج بھیجنا
                    for channel in CONFIG['otp_channel_ids']:
                        try:
                            client.send_message(channel, otp_message_body)
                        except Exception as e:
                            print(f"Failed to send to {channel}: {e}")
                    
                    last_processed_ids.add(msg_id)
                    # میموری بچانے کے لیے پرانا ڈیٹا صاف کریں
                    if len(last_processed_ids) > 500: last_processed_ids.clear()
                    
        except Exception as e:
            print(f"❌ API Error ({url}): {e}")

# --- بوٹ ایونٹ ہینڈلرز ---
def on_connected(client: NewClient, _: ConnectedEv):
    print(f"✅ {CONFIG['bot_name']} is Connected!")
    # شیڈولر شروع کریں
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_otp_apis, 'interval', seconds=CONFIG['monitor_interval'], args=[client])
    scheduler.start()

def on_message(client: NewClient, message: MessageEv):
    msg_text = message.Message.conversation or message.Message.extendedTextMessage.text
    if msg_text == ".id":
        client.reply_message(message, f"Chat ID: {message.Info.MessageSource.Chat}")

# --- مین اسٹارٹ اپ ---
def start_bot():
    # سیشن فائل کا نام
    client = NewClient("kami_otp_session.db")
    
    client.event_handler(ConnectedEv)(on_connected)
    client.event_handler(MessageEv)(on_message)

    # اگر پہلے سے لاگ ان نہیں ہے تو پیرنگ کوڈ مانگے
    if not client.is_registered():
        print(f"\n⏳ Requesting Pairing Code for: {CONFIG['owner_number']}")
        time.sleep(5)
        try:
            code = client.pair_code(CONFIG['owner_number'])
            print(f"\n================================")
            print(f"✅ YOUR PAIRING CODE: \033[1;32m{code}\033[0m")
            print(f"================================\n")
        except Exception as e:
            print(f"Pairing Error: {e}")

    client.connect()

if __name__ == "__main__":
    start_bot()