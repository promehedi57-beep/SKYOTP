import asyncio
import logging
import re
from collections import deque
from datetime import datetime

import aiohttp
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# (CopyTextButton শুধু python-telegram-bot v20.8+ এ সাপোর্ট করে)
try:
    from telegram import CopyTextButton
except ImportError:
    CopyTextButton = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================== কনফিগারেশন ========================
TELEGRAM_TOKEN = "8647348457:AAEi5Kre2Df4Xeig80aZzsd_7zR9MFO739Y"
TELEGRAM_CHAT_ID = "-1003860008126"

# --- New Panel (MNIT Network) ---
API_BASE_URL = "https://x.mnitnetwork.com/mapi/v1"
API_KEY = "M_A4UFFVM8R"

HEADERS = {
    "mapikey": API_KEY,
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
        return "🌍", "GLOBAL"
    
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

# রেজেক্স আপডেট করা হয়েছে যাতে স্পেস ছাড়াই যে কোনো ডিজিট ক্যাচ করতে পারে
OTP_REGEX = re.compile(r'\d{4,10}')

def extract_otp(text: str) -> str | None:
    if not text:
        return None
    match = OTP_REGEX.search(str(text))
    return match.group(0) if match else None

def generate_skypro_number(phone: str) -> str:
    """সামনে ৩টা + SKYPRO + পেছনে ৩টা সংখ্যা"""
    p = str(phone).strip().replace("+", "")
    if len(p) >= 6:
        return f"{p[:3]}SKYPRO{p[-3:]}"
    else:
        return f"SKYPRO{p}"

def format_telegram_message(otp_code: str, phone: str, category: str) -> str:
    flag, country_short = get_country_info(phone)
    skypro_number = generate_skypro_number(phone)
    
    cat_upper = category.upper()
    short_forms = {
        "FACEBOOK": "FB", "WHATSAPP": "WS", "TELEGRAM": "TG", "INSTAGRAM": "IG",
        "GOOGLE": "GO", "TWITTER": "TW", "TIKTOK": "TT", "SNAPCHAT": "SC",
        "DISCORD": "DC", "LINKEDIN": "LI", "MICROSOFT": "MS", "AMAZON": "AM",
        "APPLE": "AP", "VIBER": "VB", "LINE": "LN", "WECHAT": "WC", "IMO": "IM",
        "TINDER": "TN", "YAHOO": "YH", "NETFLIX": "NF"
    }
    
    cat_short = short_forms.get(cat_upper, cat_upper[:2])

    inner_text = f"{flag} {country_short}➔{cat_short}➔[{skypro_number}]"
    
    top_line = "┏━━━━━━━━━━━━━━━━━━━━━━━┓"
    mid_line = f"┃ {inner_text} ┃"
    bot_line = "┗━━━━━━━━━━━━━━━━━━━━━━━┛"
    
    return (
        f"{top_line}\n"
        f"{mid_line}\n"
        f"{bot_line}\n\n"
        f"🕋 **𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 [𝐒𝐊𝐘](https://t.me/SKYSMSOWNER)** 🕋"
    )

def create_buttons(otp_code: str) -> InlineKeyboardMarkup:
    # CopyTextButton সাপোর্ট না করলে নরমাল বাটন ব্যবহার করবে
    if CopyTextButton:
        btn = InlineKeyboardButton(f" {otp_code}", copy_text=CopyTextButton(text=otp_code))
    else:
        btn = InlineKeyboardButton(f" {otp_code} (Click to copy)", callback_data=f"copy_{otp_code}")
        
    keyboard = [
        [btn],
        [
            InlineKeyboardButton("‼️ 𝑷𝑨𝑵𝑬𝑳", url="https://t.me/SKYSMSPRO_BOT"),
            InlineKeyboardButton("📞 𝑪𝑯𝑨𝑵𝑵𝑬𝑳", url="https://t.me/SKYOFFICIALCHANNEL1")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_telegram_otp(otp_code: str, phone: str, category: str):
    text = format_telegram_message(otp_code, phone, category)
    reply_markup = create_buttons(otp_code)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"✅ OTP পাঠানো হয়েছে: {otp_code} | {category}")
    except Exception as e:
        logger.error(f"❌ টেলিগ্রামে পাঠাতে ব্যর্থ: {e}")

async def fetch_console_logs(session: aiohttp.ClientSession) -> list:
    url = f"{API_BASE_URL}/public/numsuccess/info"
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as resp:
            if resp.status == 200:
                # content_type=None দেওয়া হয়েছে যাতে JSON বা HTML যাই আসুক এরর না খায়
                data = await resp.json(content_type=None) 
                
                if isinstance(data, dict):
                    # স্ট্রিং হিসেবে চেক করা হচ্ছে
                    meta_code = str(data.get("meta", {}).get("code", ""))
                    if meta_code == "200":
                        data_obj = data.get("data", {})
                        if isinstance(data_obj, dict):
                            return data_obj.get("otps", [])
                        
            elif resp.status == 401:
                logger.error("❌ API Key ভুল বা Unauthorized!")
            else:
                logger.error(f"❌ HTTP Error: {resp.status}")
                
    except Exception as e:
        logger.error(f"❌ API থেকে ডেটা আনতে ব্যর্থ: {e}")
    return []

async def monitor_loop():
    logger.info("🚀 SKY OTP ফরওয়ার্ড বট চালু হয়েছে")
    
    # প্রথমবার চালু হলে আগের ২০ টা মেসেজ চ্যানেলে ফ্লাড করা বন্ধ করার জন্য
    is_first_run = True 
    
    # SSL এরর ইগনোর করার সঠিক নিয়ম
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            logs = await fetch_console_logs(session)
            if logs:
                for log in reversed(logs):
                    msg_id = log.get("nid")
                    if msg_id and msg_id not in processed_ids:
                        
                        if not is_first_run:
                            sms_text = str(log.get("otp", ""))
                            phone = str(log.get("number", ""))
                            raw_category = log.get("operator")
                            
                            if not raw_category or str(raw_category).strip().lower() in ["null", "none", "", "other"]:
                                category = "FACEBOOK"
                            else:
                                category = str(raw_category).strip()
                            
                            otp = extract_otp(sms_text)
                            if otp:
                                await send_telegram_otp(otp, phone, category)
                            else:
                                logger.warning(f"⚠️ OTP খুঁজে পাওয়া যায়নি: {sms_text}")
                                
                        # ID সেভ করে রাখছে যাতে ডাবল না যায়
                        processed_ids.append(msg_id)
            
            is_first_run = False
            await asyncio.sleep(2) # ২ সেকেন্ড পর পর চেক করবে

async def main():
    print("="*50)
    print("☁️ SKY OTP মনিটরিং শুরু হচ্ছে...")
    print("="*50)
    await monitor_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 বট বন্ধ করা হয়েছে।")
