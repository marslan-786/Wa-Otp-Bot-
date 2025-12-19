# settings.py
CONFIG = {
    'owner_number': '923027665767',  # آپ کا واٹس ایپ نمبر (بغیر + کے)
    'bot_name': "Kami OTP Monitor",
    'otp_channel_ids': [
        '120363423562861659@newsletter', 
        '120363421646654726@newsletter'
    ],
    'otp_api_urls': [
        'https://web-production-b717.up.railway.app/api?type=sms',
        'https://www.kamibroken.pw/api/sms1?type=sms',
    ],
    'monitor_interval':3  # کتنا وقفہ ہو (سیکنڈز میں)
}