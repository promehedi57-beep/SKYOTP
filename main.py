import asyncio
import logging
import re
from collections import deque
from typing import Optional

import aiohttp
from telegram import Bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================== কনফিগারেশন ========================
TELEGRAM_TOKEN = "8671692396:AAGzZfZPNfC5ZRmSnRxaFQcbAjT3s3X_nug"
TELEGRAM_CHAT_ID = "-1003860008126"

API_BASE_URL = "http://2.58.82.137:5000/api/v1"
API_KEY = "nxa_99f2f67b13e0e02bca175b1cbc40d57128958702"

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

# ======================== দেশের কোড ও পতাকা ========================
COUNTRY_CODES = {
    "+93": ("🇦🇫", "AF"), "+355": ("🇦🇱", "AL"), "+213": ("🇩🇿", "DZ"), "+376": ("🇦🇩", "AD"),
    "+244": ("🇦🇴", "AO"), "+54": ("🇦🇷", "AR"), "+374": ("🇦🇲", "AM"), "+61": ("🇦🇺", "AU"),
    "+43": ("🇦🇹", "AT"), "+994": ("🇦🇿", "AZ"), "+973": ("🇧🇭", "BH"), "+880": ("🇧🇩", "BD"),
    "+375": ("🇧🇾", "BY"), "+32": ("🇧🇪", "BE"), "+501": ("🇧🇿", "BZ"), "+229": ("🇧🇯", "BJ"),
    "+975": ("🇧🇹", "BT"), "+591": ("🇧🇴", "BO"), "+387": ("🇧🇦", "BA"), "+267": ("🇧🇼", "BW"),
    "+55": ("🇧🇷", "BR"), "+673": ("🇧🇳", "BN"), "+359": ("🇧🇬", "BG"), "+226": ("🇧🇫", "BF"),
    "+257": ("🇧🇮", "BI"), "+855": ("🇰🇭", "KH"), "+237": ("🇨🇲", "CM"), "+1": ("🇺🇸/🇨🇦", "US/CA"),
    "+238": ("🇨🇻", "CV"), "+236": ("🇨🇫", "CF"), "+235": ("🇹🇩", "TD"), "+56": ("🇨🇱", "CL"),
    "+86": ("🇨🇳", "CN"), "+57": ("🇨🇴", "CO"), "+269": ("🇰🇲", "KM"), "+242": ("🇨🇬", "CG"),
    "+243": ("🇨🇩", "CD"), "+506": ("🇨🇷", "CR"), "+385": ("🇭🇷", "HR"), "+53": ("🇨🇺", "CU"),
    "+357": ("🇨🇾", "CY"), "+420": ("🇨🇿", "CZ"), "+45": ("🇩🇰", "DK"), "+253": ("🇩🇯", "DJ"),
    "+593": ("🇪🇨", "EC"), "+20": ("🇪🇬", "EG"), "+503": ("🇸🇻", "SV"), "+240": ("🇬🇶", "GQ"),
    "+291": ("🇪🇷", "ER"), "+372": ("🇪🇪", "EE"), "+251": ("🇪🇹", "ET"), "+679": ("🇫🇯", "FJ"),
    "+358": ("🇫🇮", "FI"), "+33": ("🇫🇷", "FR"), "+241": ("🇬🇦", "GA"), "+220": ("🇬🇲", "GM"),
    "+995": ("🇬🇪", "GE"), "+49": ("🇩🇪", "DE"), "+233": ("🇬🇭", "GH"), "+30": ("🇬🇷", "GR"),
    "+502": ("🇬🇹", "GT"), "+224": ("🇬🇳", "GN"), "+245": ("🇬🇼", "GW"), "+592": ("🇬🇾", "GY"),
    "+509": ("🇭🇹", "HT"), "+504": ("🇭🇳", "HN"), "+36": ("🇭🇺", "HU"), "+354": ("🇮🇸", "IS"),
    "+91": ("🇮🇳", "IN"), "+62": ("🇮🇩", "ID"), "+98": ("🇮🇷", "IR"), "+964": ("🇮🇶", "IQ"),
    "+353": ("🇮🇪", "IE"), "+972": ("🇮🇱", "IL"), "+39": ("🇮🇹", "IT"), "+225": ("🇨🇮", "CI"),
    "+81": ("🇯🇵", "JP"), "+962": ("🇯🇴", "JO"), "+7": ("🇷🇺/🇰🇿", "RU/KZ"), "+254": ("🇰🇪", "KE"),
    "+686": ("🇰🇮", "KI"), "+383": ("🇽🇰", "XK"), "+965": ("🇰🇼", "KW"), "+996": ("🇰🇬", "KG"),
    "+856": ("🇱🇦", "LA"), "+371": ("🇱🇻", "LV"), "+961": ("🇱🇧", "LB"), "+266": ("🇱🇸", "LS"),
    "+231": ("🇱🇷", "LR"), "+218": ("🇱🇾", "LY"), "+423": ("🇱🇮", "LI"), "+370": ("🇱🇹", "LT"),
    "+352": ("🇱🇺", "LU"), "+261": ("🇲🇬", "MG"), "+265": ("🇲🇼", "MW"), "+60": ("🇲🇾", "MY"),
    "+960": ("🇲🇻", "MV"), "+223": ("🇲🇱", "ML"), "+356": ("🇲🇹", "MT"), "+222": ("🇲🇷", "MR"),
    "+230": ("🇲🇺", "MU"), "+52": ("🇲🇽", "MX"), "+691": ("🇫🇲", "FM"), "+373": ("🇲🇩", "MD"),
    "+377": ("🇲🇨", "MC"), "+976": ("🇲🇳", "MN"), "+382": ("🇲🇪", "ME"), "+212": ("🇲🇦", "MA"),
    "+258": ("🇲🇿", "MZ"), "+95": ("🇲🇲", "MM"), "+264": ("🇳🇦", "NA"), "+674": ("🇳🇷", "NR"),
    "+977": ("🇳🇵", "NP"), "+31": ("🇳🇱", "NL"), "+64": ("🇳🇿", "NZ"), "+505": ("🇳🇮", "NI"),
    "+227": ("🇳🇪", "NE"), "+234": ("🇳🇬", "NG"), "+850": ("🇰🇵", "KP"), "+389": ("🇲🇰", "MK"),
    "+47": ("🇳🇴", "NO"), "+968": ("🇴🇲", "OM"), "+92": ("🇵🇰", "PK"), "+680": ("🇵🇼", "PW"),
    "+970": ("🇵🇸", "PS"), "+507": ("🇵🇦", "PA"), "+675": ("🇵🇬", "PG"), "+595": ("🇵🇾", "PY"),
    "+51": ("🇵🇪", "PE"), "+63": ("🇵🇭", "PH"), "+48": ("🇵🇱", "PL"), "+351": ("🇵🇹", "PT"),
    "+974": ("🇶🇦", "QA"), "+40": ("🇷🇴", "RO"), "+250": ("🇷🇼", "RW"), "+966": ("🇸🇦", "SA"),
    "+221": ("🇸🇳", "SN"), "+381": ("🇷🇸", "RS"), "+248": ("🇸🇨", "SC"), "+232": ("🇸🇱", "SL"),
    "+65": ("🇸🇬", "SG"), "+421": ("🇸🇰", "SK"), "+386": ("🇸🇮", "SI"), "+677": ("🇸🇧", "SB"),
    "+252": ("🇸🇴", "SO"), "+27": ("🇿🇦", "ZA"), "+82": ("🇰🇷", "KR"), "+211": ("🇸🇸", "SS"),
    "+34": ("🇪🇸", "ES"), "+94": ("🇱🇰", "LK"), "+249": ("🇸🇩", "SD"), "+597": ("🇸🇷", "SR"),
    "+268": ("🇸🇿", "SZ"), "+46": ("🇸🇪", "SE"), "+41": ("🇨🇭", "CH"), "+963": ("🇸🇾", "SY"),
    "+886": ("🇹🇼", "TW"), "+992": ("🇹🇯", "TJ"), "+255": ("🇹🇿", "TZ"), "+66": ("🇹🇭", "TH"),
    "+228": ("🇹🇬", "TG"), "+676": ("🇹🇴", "TO"), "+216": ("🇹🇳", "TN"), "+90": ("🇹🇷", "TR"),
    "+993": ("🇹🇲", "TM"), "+688": ("🇹🇻", "TV"), "+256": ("🇺🇬", "UG"), "+380": ("🇺🇦", "UA"),
    "+971": ("🇦🇪", "AE"), "+44": ("🇬🇧", "GB"), "+598": ("🇺🇾", "UY"), "+998": ("🇺🇿", "UZ"),
    "+678": ("🇻🇺", "VU"), "+379": ("🇻🇦", "VA"), "+58": ("🇻🇪", "VE"), "+84": ("🇻🇳", "VN"),
    "+967": ("🇾🇪", "YE"), "+260": ("🇿🇲", "ZM"), "+263": ("🇿🇼", "ZW")
}

def get_country_info(phone: str) -> tuple:
    if not phone:
        return "🌍", "FACEBOOK"
    phone_str = str(phone).strip()
    if not phone_str.startswith("+"):
        phone_str = "+" + phone_str
    for code, (flag, short_name) in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if phone_str.startswith(code):
            return flag, short_name
    return "🌍", "GLOBAL"

# ট্র্যাকিং
processed_ids = deque(maxlen=500)
bot = Bot(token=TELEGRAM_TOKEN)

# OTP রেজেক্স
OTP_REGEX = re.compile(r'\b\d{4,10}\b')

def extract_otp(text: str) -> Optional[str]:
    match = OTP_REGEX.search(text)
    return match.group(0) if match else None

def generate_skypro_number(phone: str) -> str:
    """সামনে ৩টা + SKYPRO + পেছনে ৩টা সংখ্যা"""
    p = str(phone).strip().replace("+", "")
    if len(p) >= 6:
        return f"{p[:3]}SKYPRO{p[-3:]}"
    else:
        return f"SKYPRO{p}"

def format_telegram_message(otp_code: str, phone: str, category: str = "FACEBOOK") -> str:
    flag, country_short = get_country_info(phone)
    skypro_number = generate_skypro_number(phone)
    
    return (
        f"🔐 {flag} **{country_short} | {category}**\n\n"
        f"`{skypro_number}`\n\n"
        f" **POWERED BY [𝐒𝐊𝐘](https://t.me/SKYSMSOWNER)**"
    )

def create_buttons(otp_code: str) -> dict:
    keyboard = [
        [{"text": f" {otp_code}", "copy_text": {"text": otp_code}}],
        [
            {"text": "‼️ 𝑷𝑨𝑵𝑬𝑳", "url": "https://t.me/SKYSMSPRO_BOT"},
            {"text": "📞 𝑪𝑯𝑨𝑵𝑵𝑬𝑳", "url": "https://t.me/SKYOFFICIALCHANNEL1"}
        ]
    ]
    return {"inline_keyboard": keyboard}

async def send_telegram_otp(otp_code: str, phone: str, category: str = "Unknown"):
    text = format_telegram_message(otp_code, phone, category)
    reply_markup = create_buttons(otp_code)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"✅ OTP পাঠানো হয়েছে: {otp_code} | {category}")
    except Exception as e:
        logger.error(f"❌ টেলিগ্রামে পাঠাতে ব্যর্থ: {e}")

async def fetch_console_logs(session: aiohttp.ClientSession) -> list:
    url = f"{API_BASE_URL}/console/logs?limit=10"
    try:
        # দ্রুত রেসপন্স পাওয়ার জন্য টাইমআউট কমানো হয়েছে
        async with session.get(url, headers=HEADERS, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success") and "data" in data:
                    return data["data"]
            elif resp.status == 401:
                logger.error("❌ API Key ভুল!")
    except Exception as e:
        pass # দ্রুত লুপ চালানোর জন্য এরর লগিং স্কিপ করা হচ্ছে
    return []

async def monitor_loop():
    logger.info("🚀 SKY OTP ফরওয়ার্ড বট সুপারফাস্ট মোডে চালু হয়েছে")
    # TCP Connector কনফিগার করা হয়েছে যাতে রিকোয়েস্ট আরও ফাস্ট হয়
    connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=60)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            logs = await fetch_console_logs(session)
            if logs:
                for log in reversed(logs):
                    msg_id = log.get("id")
                    if msg_id and msg_id not in processed_ids:
                        sms_text = log.get("sms", "")
                        phone = log.get("phone", log.get("number", ""))
                        category = log.get("service") or log.get("app") or log.get("service_name") or "Unknown"
                        otp = extract_otp(sms_text)
                        if otp:
                            # ব্যাকগ্রাউন্ড টাস্ক হিসেবে পাঠানো হচ্ছে যাতে লুপ না থামে
                            asyncio.create_task(send_telegram_otp(otp, phone, category))
                            processed_ids.append(msg_id)
            
            # 🔥 এখানে ১ সেকেন্ডের জায়গায় ০.২ সেকেন্ড (২০০ মিলি-সেকেন্ড) করা হয়েছে!
            await asyncio.sleep(0.2) 

async def main():
    print("="*50)
    print("⚡ SKY OTP সুপারফাস্ট মনিটরিং শুরু হচ্ছে...")
    print("="*50)
    await monitor_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 বট বন্ধ করা হয়েছে।")
