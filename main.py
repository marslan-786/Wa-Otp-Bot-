import time
import requests
import pycountry
import re
from datetime import datetime
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv
from apscheduler.schedulers.background import BackgroundScheduler
from settings import CONFIG

# --- فنکشن: کنٹری کوڈ کو ایموجی جھنڈے میں بدلنے کے لیے (بغیر کسی اضافی لائبریری کے) ---
def get_emoji_flag(country_code):
    if not country_code: return "🌐"
    # Regional Indicator Symbols کی بنیاد پر جھنڈا بنانا
    offset = 127397
    return "".join(chr(ord(c.upper()) + offset) for c in country_code)

# --- کنٹری فلیگ لاجک (صرف pycountry استعمال کرتے ہوئے) ---
def get_country_info(raw_country_str):
    country_name = raw_country_str.split(' ')[0]
    try:
        # ملک کے نام سے ڈیٹا تلاش کرنا
        country = pycountry.countries.search_fuzzy(country_name)[0]
        iso_code = country.alpha_2 # جیسے PK, US, VN
        f = get_emoji_flag(iso_code)
        return f, f"{f} {country_name}"
    except:
        return "🌐", f"🌐 {country_name}"

# --- باقی کوڈ وہی ہے ---
def extract_otp(message):
    match = re.search(r'\b\d{3,4}[-\s]?\d{3,4}\b|\b\d{4,8}\b', message)
    return match.group(0) if match else "N/A"

def mask_number(number):
    if not number: return "N/A"
    return f"{number[:5]}XXXX{number[-2:]}"

last_processed_ids = set()

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
                    raw_time = row[0]
                    country_info = row[1]
                    phone_number = row[2]
                    service_name = row[3]
                    full_msg = row[4]
                    
                    c_flag, country_with_flag = get_country_info(country_info)
                    masked_num = mask_number(phone_number)
                    otp_code = extract_otp(full_msg)
                    service_title = service_name.upper()

                    # 🔥 آپ کی سیم ٹو سیم میسج باڈی
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

                    for channel in CONFIG['otp_channel_ids']:
                        client.send_message(channel, otp_message_body)
                    
                    last_processed_ids.add(msg_id)
                    if len(last_processed_ids) > 500: last_processed_ids.clear()
        except Exception as e:
            print(f"❌ API Error: {e}")

def on_connected(client: NewClient, _: ConnectedEv):
    print(f"✅ {CONFIG['bot_name']} Active!")
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_otp_apis, 'interval', seconds=15, args=[client])
    scheduler.start()

def on_message(client: NewClient, message: MessageEv):
    msg_text = message.Message.conversation or message.Message.extendedTextMessage.text
    if msg_text == ".id":
        client.reply_message(message, f"Chat ID: {message.Info.MessageSource.Chat}")

def start_bot():
    client = NewClient("kami_session.db")
    client.event_handler(ConnectedEv)(on_connected)
    client.event_handler(MessageEv)(on_message)

    if not client.is_registered():
        print(f"⏳ Code for: {CONFIG['owner_number']}")
        time.sleep(4)
        code = client.pair_code(CONFIG['owner_number'])
        print(f"\n🔑 PAIRING CODE: \033[1;32m{code}\033[0m\n")

    client.connect()

if __name__ == "__main__":
    start_bot()
