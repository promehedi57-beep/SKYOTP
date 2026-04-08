import requests
import json
import time
import re
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
import logging
from datetime import datetime

# লগিং কনফিগারেশন
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OTPMonitorBot:
    def __init__(self, telegram_token, group_chat_id, session_cookie, target_url):
        self.telegram_token = telegram_token
        self.group_chat_id = group_chat_id
        self.session_cookie = session_cookie
        self.target_url = target_url
        self.processed_otps = set()
        self.start_time = datetime.now()
        self.total_otps_sent = 0
        self.last_otp_time = None
        self.is_monitoring = True
        
        # OTP প্যাটার্ন ডিটেকশন
        self.otp_patterns = [
            r'\b\d{3}-\d{3}\b',  # 123-456 ফরম্যাট
            r'\b\d{5}\b',        # 5 ডিজিট কোড
            r'code\s*\d+',       # "code 12345"
            r'code:\s*\d+',      # "code: 12345"
            r'কোড\s*\d+',        # বাংলা "কোড 12345"
            r'\b\d{6}\b',        # 6 ডিজিট কোড
            r'\b\d{4}\b',        # 4 ডিজিট কোড
            r'Your WhatsApp code \d+-\d+',
            r'WhatsApp code \d+-\d+',
            r'Telegram code \d+',
        ]
    
    def hide_phone_number(self, phone_number):
        """ফোন নাম্বার হাইড করুন (মাঝখানে SKYPRO)"""
        if len(phone_number) >= 8:
            # প্রথম ৪টি এবং শেষের ৩টি ডিজিট রেখে মাঝখানে SKYPRO বসাবে
            return phone_number[:4] + 'SKYPRO' + phone_number[-3:]
        return phone_number
    
    def extract_operator_name(self, operator):
        """অপারেটর থেকে শুধু দেশের নাম এক্সট্র্যাক্ট করুন"""
        parts = operator.split()
        if parts:
            return parts[0]
        return operator

    def get_country_info(self, phone_number):
        """ফোন নাম্বার থেকে দেশের নাম ও পতাকা বের করার লজিক"""
        num = str(phone_number).lstrip('+')
        
        # ডায়াল কোড অনুযায়ী দেশের পতাকা ও শর্ট নেমের বিশাল লিস্ট (আপনার দেওয়া)
        country_data = {
            '1268': ('🇦🇬', 'AG'), '1242': ('🇧🇸', 'BS'), '1246': ('🇧🇧', 'BB'), '1869': ('🇰🇳', 'KN'),
            '1758': ('🇱🇨', 'LC'), '1784': ('🇻🇨', 'VC'), '1868': ('🇹🇹', 'TT'), '1876': ('🇯🇲', 'JM'),
            '1473': ('🇬🇩', 'GD'), '1767': ('🇩🇲', 'DM'), '1809': ('🇩🇴', 'DO'), '1829': ('🇩🇴', 'DO'),
            '1849': ('🇩🇴', 'DO'),
            '994': ('🇦🇿', 'AZ'), '973': ('🇧🇭', 'BH'), '880': ('🇧🇩', 'BD'), '975': ('🇧🇹', 'BT'),
            '591': ('🇧🇴', 'BO'), '387': ('🇧🇦', 'BA'), '267': ('🇧🇼', 'BW'), '673': ('🇧🇳', 'BN'),
            '359': ('🇧🇬', 'BG'), '226': ('🇧🇫', 'BF'), '257': ('🇧🇮', 'BI'), '855': ('🇰🇭', 'KH'),
            '237': ('🇨🇲', 'CM'), '238': ('🇨🇻', 'CV'), '236': ('🇨🇫', 'CF'), '235': ('🇹🇩', 'TD'),
            '269': ('🇰🇲', 'KM'), '242': ('🇨🇬', 'CG'), '506': ('🇨🇷', 'CR'), '385': ('🇭🇷', 'HR'),
            '357': ('🇨🇾', 'CY'), '420': ('🇨🇿', 'CZ'), '253': ('🇩🇯', 'DJ'), '593': ('🇪🇨', 'EC'),
            '503': ('🇸🇻', 'SV'), '240': ('🇬🇶', 'GQ'), '291': ('🇪🇷', 'ER'), '372': ('🇪🇪', 'EE'),
            '268': ('🇸🇿', 'SZ'), '251': ('🇪🇹', 'ET'), '679': ('🇫🇯', 'FJ'), '241': ('🇬🇦', 'GA'),
            '220': ('🇬🇲', 'GM'), '995': ('🇬🇪', 'GE'), '233': ('🇬🇭', 'GH'), '502': ('🇬🇹', 'GT'),
            '224': ('🇬🇳', 'GN'), '245': ('🇬🇼', 'GW'), '592': ('🇬🇾', 'GY'), '504': ('🇭🇳', 'HN'),
            '354': ('🇮🇸', 'IS'), '972': ('🇮🇱', 'IL'), '962': ('🇯🇴', 'JO'), '254': ('🇰🇪', 'KE'),
            '686': ('🇰🇮', 'KI'), '965': ('🇰🇼', 'KW'), '996': ('🇰🇬', 'KG'), '856': ('🇱🇦', 'LA'),
            '371': ('🇱🇻', 'LV'), '961': ('🇱🇧', 'LB'), '266': ('🇱🇸', 'LS'), '231': ('🇱🇷', 'LR'),
            '218': ('🇱🇾', 'LY'), '423': ('🇱🇮', 'LI'), '370': ('🇱🇹', 'LT'), '352': ('🇱🇺', 'LU'),
            '261': ('🇲🇬', 'MG'), '265': ('🇲🇼', 'MW'), '960': ('🇲🇻', 'MV'), '223': ('🇲🇱', 'ML'),
            '356': ('🇲🇹', 'MT'), '692': ('🇲🇭', 'MH'), '222': ('🇲🇷', 'MR'), '230': ('🇲🇺', 'MU'),
            '691': ('🇫🇲', 'FM'), '373': ('🇲🇩', 'MD'), '377': ('🇲🇨', 'MC'), '976': ('🇲🇳', 'MN'),
            '382': ('🇲🇪', 'ME'), '212': ('🇲🇦', 'MA'), '258': ('🇲🇿', 'MZ'), '264': ('🇳🇦', 'NA'),
            '674': ('🇳🇷', 'NR'), '977': ('🇳🇵', 'NP'), '505': ('🇳🇮', 'NI'), '227': ('🇳🇪', 'NE'),
            '234': ('🇳🇬', 'NG'), '850': ('🇰🇵', 'KP'), '389': ('🇲🇰', 'MK'), '968': ('🇴🇲', 'OM'),
            '680': ('🇵🇼', 'PW'), '507': ('🇵🇦', 'PA'), '675': ('🇵🇬', 'PG'), '595': ('🇵🇾', 'PY'),
            '974': ('🇶🇦', 'QA'), '250': ('🇷🇼', 'RW'), '685': ('🇼🇸', 'WS'), '378': ('🇸🇲', 'SM'),
            '239': ('🇸🇹', 'ST'), '966': ('🇸🇦', 'SA'), '221': ('🇸🇳', 'SN'), '381': ('🇷🇸', 'RS'),
            '248': ('🇸🇨', 'SC'), '232': ('🇸🇱', 'SL'), '421': ('🇸🇰', 'SK'), '386': ('🇸🇮', 'SI'),
            '677': ('🇸🇧', 'SB'), '252': ('🇸🇴', 'SO'), '211': ('🇸🇸', 'SS'), '249': ('🇸🇩', 'SD'),
            '597': ('🇸🇷', 'SR'), '963': ('🇸🇾', 'SY'), '886': ('🇹🇼', 'TW'), '992': ('🇹🇯', 'TJ'),
            '255': ('🇹🇿', 'TZ'), '670': ('🇹🇱', 'TL'), '228': ('🇹🇬', 'TG'), '676': ('🇹🇴', 'TO'),
            '216': ('🇹🇳', 'TN'), '993': ('🇹🇲', 'TM'), '688': ('🇹🇻', 'TV'), '256': ('🇺🇬', 'UG'),
            '380': ('🇺🇦', 'UA'), '971': ('🇦🇪', 'AE'), '598': ('🇺🇾', 'UY'), '998': ('🇺🇿', 'UZ'),
            '678': ('🇻🇺', 'VU'), '379': ('🇻🇦', 'VA'), '967': ('🇾🇪', 'YE'), '260': ('🇿🇲', 'ZM'),
            '263': ('🇿🇼', 'ZW'), '355': ('🇦🇱', 'AL'), '213': ('🇩🇿', 'DZ'), '376': ('🇦🇩', 'AD'),
            '244': ('🇦🇴', 'AO'), '374': ('🇦🇲', 'AM'), '375': ('🇧🇾', 'BY'), '501': ('🇧🇿', 'BZ'),
            '229': ('🇧🇯', 'BJ'), '353': ('🇮🇪', 'IE'), '358': ('🇫🇮', 'FI'), '350': ('🇬🇮', 'GI'),
            '964': ('🇮🇶', 'IQ'), '95': ('🇲🇲', 'MM'), '77': ('🇰🇿', 'KZ'), '93': ('🇦🇫', 'AF'), 
            '54': ('🇦🇷', 'AR'), '61': ('🇦🇺', 'AU'), '43': ('🇦🇹', 'AT'), '32': ('🇧🇪', 'BE'), 
            '55': ('🇧🇷', 'BR'), '56': ('🇨🇱', 'CL'), '86': ('🇨🇳', 'CN'), '57': ('🇨🇴', 'CO'), 
            '53': ('🇨🇺', 'CU'), '45': ('🇩🇰', 'DK'), '20': ('🇪🇬', 'EG'), '33': ('🇫🇷', 'FR'), 
            '49': ('🇩🇪', 'DE'), '30': ('🇬🇷', 'GR'), '509': ('🇭🇹', 'HT'), '36': ('🇭🇺', 'HU'), 
            '91': ('🇮🇳', 'IN'), '62': ('🇮🇩', 'ID'), '98': ('🇮🇷', 'IR'), '90': ('🇹🇷', 'TR'), 
            '92': ('🇵🇰', 'PK'), '81': ('🇯🇵', 'JP'), '82': ('🇰🇷', 'KR'), '39': ('🇮🇹', 'IT'), 
            '27': ('🇿🇦', 'ZA'), '34': ('🇪🇸', 'ES'), '46': ('🇸🇪', 'SE'), '44': ('🇬🇧', 'GB'), 
            '47': ('🇳🇴', 'NO'), '31': ('🇳🇱', 'NL'), '64': ('🇳🇿', 'NZ'), '60': ('🇲🇾', 'MY'), 
            '65': ('🇸🇬', 'SG'), '66': ('🇹🇭', 'TH'), '52': ('🇲🇽', 'MX'), '51': ('🇵🇪', 'PE'), 
            '63': ('🇵🇭', 'PH'), '48': ('🇵🇱', 'PL'), '351': ('🇵🇹', 'PT'), '40': ('🇷🇴', 'RO'), 
            '94': ('🇱🇰', 'LK'), '41': ('🇨🇭', 'CH'), '58': ('🇻🇪', 'VE'), '84': ('🇻🇳', 'VN'), 
            '7': ('🇷🇺', 'RU'), '1': ('🇺🇸', 'US'), '225': ('🇨🇮', 'CI')
        }

        # যাতে বড় কোড (যেমন 1242) আগে চেক হয় আর ছোট কোড (যেমন 1) এর সাথে কনফ্লিক্ট না করে
        for code in sorted(country_data.keys(), key=len, reverse=True):
            if num.startswith(code):
                return country_data[code]
        
        return "🌐", "GLOBAL"

    def get_app_info(self, message):
        """মেসেজ স্ক্যান করে অ্যাপের নাম ও লোগো বের করার লজিক"""
        msg_lower = message.lower()
        if 'instagram' in msg_lower or 'ig' in msg_lower: return "📸", "Instagram"
        if 'facebook' in msg_lower or 'fb' in msg_lower: return "📘", "Facebook"
        if 'whatsapp' in msg_lower: return "💬", "WhatsApp"
        if 'telegram' in msg_lower: return "✈️", "Telegram"
        if 'google' in msg_lower or 'g-' in msg_lower: return "🇬", "Google"
        if 'tiktok' in msg_lower: return "🎵", "TikTok"
        if 'snapchat' in msg_lower: return "👻", "Snapchat"
        if 'microsoft' in msg_lower: return "🪟", "Microsoft"
        if 'apple' in msg_lower: return "🍎", "Apple"
        if 'amazon' in msg_lower: return "🛒", "Amazon"
        if 'netflix' in msg_lower: return "🎬", "Netflix"
        if 'paypal' in msg_lower: return "💳", "PayPal"
        if 'discord' in msg_lower: return "👾", "Discord"
        if 'twitter' in msg_lower or ' x ' in msg_lower: return "🐦", "X/Twitter"
        if 'tinder' in msg_lower: return "🔥", "Tinder"
        return "📱", "App"
    
    async def send_telegram_message(self, message, chat_id=None, reply_markup=None):
        """টেলিগ্রামে মেসেজ সেন্ড করুন"""
        if chat_id is None:
            chat_id = self.group_chat_id
            
        try:
            bot = Bot(token=self.telegram_token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            logger.error(f"❌ Telegram Error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Send Message Error: {e}")
            return False
    
    async def send_startup_message(self):
        """বট শুরু হলে স্টার্টআপ মেসেজ সেন্ড করুন"""
        startup_msg = f"""
🚀 **𝐎𝐓𝐏 𝐌𝐨𝐧𝐢𝐭𝐨𝐫 𝐁𝐨𝐭 𝐀𝐜𝐭𝐢𝐯𝐚𝐭𝐞𝐝** 🚀
➖➖➖➖➖➖➖➖➖➖➖

✅ **𝐒𝐭𝐚𝐭𝐮𝐬:** `𝐋𝐈𝐕𝐄 & 𝐌𝐎𝐍𝐈𝐓𝐨𝐑𝐈𝐍𝐆`
⚡ **𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:** `𝐈𝐌𝐌𝐄𝐃𝐈𝐀𝐓𝐄`
📡 **𝐌𝐨𝐝𝐞:** `𝐑𝐄𝐀𝐋-𝐓𝐈𝐌𝐄`

🎯 **𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:**
• First OTP Only
• Live Monitoring
• Auto Detection

⏰ **𝐒𝐭𝐚𝐫𝐭 𝐓𝐢𝐦𝐞:** `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`

🔔 **𝐍𝐨𝐭𝐞:** Only the FIRST OTP will be forwarded!

➖➖➖➖➖➖➖➖➖➖➖
🤖 **𝐎𝐓𝐏 𝐌𝐨𝐧𝐢𝐭𝐨𝐫 𝐁𝐨𝐭**
        """
        
        keyboard = [
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ONLYALLSUPPORT")],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/SKYOFFICIALCHANNEL1")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        success = await self.send_telegram_message(startup_msg, reply_markup=reply_markup)
        if success:
            logger.info("✅ Startup message sent to group")
        return success
    
    def extract_otp(self, message):
        """মেসেজ থেকে OTP এক্সট্র্যাক্ট করুন"""
        for pattern in self.otp_patterns:
            matches = re.findall(pattern, message)
            if matches:
                return matches[0]
        return None
    
    def create_otp_id(self, timestamp, phone_number, message):
        """ইউনিক OTP ID তৈরি করুন"""
        return f"{timestamp}_{phone_number}"  # শুধু টাইমস্ট্যাম্প এবং ফোন নম্বর
    
    def format_message(self, sms_data, otp_code, message_text):
        """স্ক্রিনশটের মত করে SMS ডেটা প্রফেশনালভাবে ফরম্যাট করুন"""
        raw_phone_number = sms_data[2]
        
        # নাম্বারটি হাইড করা হচ্ছে (মাঝখানে SKYPRO বসবে)
        hidden_phone_number = self.hide_phone_number(raw_phone_number)
        
        # দেশ এবং অ্যাপের ইনফরমেশন বের করা
        country_flag, country_code = self.get_country_info(raw_phone_number)
        app_logo, app_name = self.get_app_info(message_text)
        
        # নতুন প্রফেশনাল ডিজাইন (হাইড করা নাম্বার ও আপডেট করা লিংক)
        # ট্যাপ টু কপি টেক্সট সরিয়ে শুধু OTP রাখা হয়েছে যাতে ট্যাপ করলেই কপি হয়
        formatted_msg = f"{country_flag} #{country_code} {app_logo} **{app_name}** ┇ `{hidden_phone_number}`\n\n🦇 𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈  [𝐒𝐊𝐘](https://t.me/ONLYALLSUPPORT) 🥷\n\n`{otp_code}`"
        return formatted_msg
    
    def create_response_buttons(self, otp_code):
        """স্ক্রিনশটের মত করে রেস্পন্স বাটন তৈরি করুন"""
        keyboard = [
            [
                # OTP বাটন (ক্লিক করলে কপি হবে)
                InlineKeyboardButton(f" {otp_code}", copy_text=CopyTextButton(text=otp_code))
            ],
            [
                # চ্যানেল, প্যানেল বাটন
                InlineKeyboardButton("📞 𝑪𝑯𝑨𝑵𝑵𝑬𝑳", url="https://t.me/SKYOFFICIALCHANNEL1"),
                InlineKeyboardButton("​⚙️𝑷𝑨𝑵𝑬𝑳", url="https://t.me/SKYSMSPRO_BOT")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def fetch_sms_data(self):
        """ওয়েবসাইট থেকে SMS ডেটা ফেচ করুন"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; V2333 Build/AP3A.240905.015.A2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.177 Mobile Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://139.99.208.63/ints/client/SMSCDRStats',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': f'PHPSESSID={self.session_cookie}',
            'Connection': 'keep-alive'
        }
        
        current_date = time.strftime("%Y-%m-%d")
        params = {
            'fdate1': f'{current_date} 00:00:00',
            'fdate2': f'{current_date} 23:59:59',
            'frange': '',
            'fnum': '',
            'fcli': '',
            'fgdate': '',
            'fgmonth': '',
            'fgrange': '',
            'fgnumber': '',
            'fgcli': '',
            'fg': '0',
            'sEcho': '1',
            'iColumns': '7',
            'sColumns': ',,,,,,',
            'iDisplayStart': '0',
            'iDisplayLength': '25',
            'mDataProp_0': '0',
            'sSearch_0': '',
            'bRegex_0': 'false',
            'bSearchable_0': 'true',
            'bSortable_0': 'true',
            'mDataProp_1': '1',
            'sSearch_1': '',
            'bRegex_1': 'false',
            'bSearchable_1': 'true',
            'bSortable_1': 'true',
            'mDataProp_2': '2',
            'sSearch_2': '',
            'bRegex_2': 'false',
            'bSearchable_2': 'true',
            'bSortable_2': 'true',
            'mDataProp_3': '3',
            'sSearch_3': '',
            'bRegex_3': 'false',
            'bSearchable_3': 'true',
            'bSortable_3': 'true',
            'mDataProp_4': '4',
            'sSearch_4': '',
            'bRegex_4': 'false',
            'bSearchable_4': 'true',
            'bSortable_4': 'true',
            'mDataProp_5': '5',
            'sSearch_5': '',
            'bRegex_5': 'false',
            'bSearchable_5': 'true',
            'bSortable_5': 'true',
            'mDataProp_6': '6',
            'sSearch_6': '',
            'bRegex_6': 'false',
            'bSearchable_6': 'true',
            'bSortable_6': 'true',
            'sSearch': '',
            'bRegex': 'false',
            'iSortCol_0': '0',
            'sSortDir_0': 'desc',
            'iSortingCols': '1',
            '_': str(int(time.time() * 1000))
        }
        
        try:
            response = requests.get(
                self.target_url,
                headers=headers,
                params=params,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                if response.text.strip():
                    try:
                        data = response.json()
                        return data
                    except json.JSONDecodeError:
                        return None
                else:
                    return None
            else:
                return None
                
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None
    
    async def monitor_loop(self):
        """মেইন মনিটরিং লুপ - শুধু প্রথম OTP এবং 0.50 সেকেন্ড ইন্টারভাল"""
        logger.info("🚀 OTP Monitoring Started - FIRST OTP ONLY")
        await self.send_startup_message()
        
        check_count = 0
        
        while self.is_monitoring:
            try:
                check_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                
                logger.info(f"🔍 Check #{check_count} at {current_time}")
                
                # API কল
                data = self.fetch_sms_data()
                
                if data and 'aaData' in data:
                    sms_list = data['aaData']
                    
                    # বৈধ SMS ফিল্টার করুন
                    valid_sms = [sms for sms in sms_list if len(sms) >= 8 and isinstance(sms[0], str) and ':' in sms[0]]
                    
                    if valid_sms:
                        # ✅ শুধু প্রথম SMS নিন
                        first_sms = valid_sms[0]
                        timestamp = first_sms[0]
                        phone_number = first_sms[2]
                        message_text = first_sms[5]
                        
                        # OTP ID তৈরি করুন
                        otp_id = self.create_otp_id(timestamp, phone_number, message_text)
                        
                        # ✅ শুধুমাত্র নতুন প্রথম OTP চেক করুন
                        if otp_id not in self.processed_otps:
                            logger.info(f"🚨 FIRST OTP DETECTED: {timestamp}")
                            
                            otp_code = self.extract_otp(message_text)
                            if otp_code:
                                logger.info(f"🔢 OTP Code: {otp_code}")
                                
                                # মেসেজ এবং বাটন তৈরি করুন (মেসেজ টেক্সট পাস করা হলো অ্যাপ ডিটেকশনের জন্য)
                                formatted_msg = self.format_message(first_sms, otp_code, message_text)
                                reply_markup = self.create_response_buttons(otp_code)
                                
                                success = await self.send_telegram_message(
                                    formatted_msg, 
                                    reply_markup=reply_markup
                                )
                                
                                if success:
                                    # ✅ প্রসেসড লিস্টে এড করুন
                                    self.processed_otps.add(otp_id)
                                    self.total_otps_sent += 1
                                    self.last_otp_time = current_time
                                    
                                    logger.info(f"✅ FIRST OTP SENT: {timestamp} - Total: {self.total_otps_sent}")
                                else:
                                    logger.error(f"❌ Failed to send OTP: {timestamp}")
                        else:
                            logger.debug(f"⏩ First OTP Already Processed: {timestamp}")
                    else:
                        logger.info("ℹ️ No valid SMS records found")
                
                else:
                    logger.warning("⚠️ No data from API")
                
                # প্রতি 20 চেকে স্ট্যাটাস
                if check_count % 20 == 0:
                    logger.info(f"📊 Status - Total First OTPs: {self.total_otps_sent}")
                
                # ✅ 0.50 সেকেন্ড অপেক্ষা
                await asyncio.sleep(0.50)
                
            except Exception as e:
                logger.error(f"❌ Monitor Loop Error: {e}")
                await asyncio.sleep(1)

async def main():
    # কনফিগারেশন
    TELEGRAM_BOT_TOKEN = "8671692396:AAFAdypLyd1SRqwD1smNok5bw8JmixORzuw"
    GROUP_CHAT_ID = "-1003860008126"
    SESSION_COOKIE = "dd73e30a2d1aabb0d0dfe8970919c397"
    TARGET_URL = "http://139.99.208.63/ints/client/res/data_smscdr.php"
    
    print("=" * 50)
    print("🤖 OTP MONITOR BOT - PROFESSIONAL MODE")
    print("=" * 50)
    print("⚡ Mode: FIRST OTP ONLY")
    print("⏰ Check Interval: 0.50 SECONDS")
    print("📱 Group ID:", GROUP_CHAT_ID)
    print("🎯 Feature: App & Country Auto Detection")
    print("🚀 Starting bot...")
    
    # OTP মনিটর বট তৈরি করুন
    otp_bot = OTPMonitorBot(
        telegram_token=TELEGRAM_BOT_TOKEN,
        group_chat_id=GROUP_CHAT_ID,
        session_cookie=SESSION_COOKIE,
        target_url=TARGET_URL
    )
    
    print("✅ BOT STARTED SUCCESSFULLY!")
    print("🎯 Monitoring: ACTIVE")
    print("🚀 Mode: FIRST OTP ONLY")
    print("⏰ Check Speed: 0.50 seconds")
    print("📊 Each first OTP sent ONLY ONCE")
    print("-" * 50)
    print("🛑 Press Ctrl+C to stop the bot")
    print("=" * 50)
    
    # মনিটরিং শুরু করুন
    try:
        await otp_bot.monitor_loop()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user!")
        otp_bot.is_monitoring = False
        print(f"📊 Final Stats - Total OTPs Sent: {otp_bot.total_otps_sent}")
        print("👋 Goodbye!")

if __name__ == "__main__":
    # SSL warning disable
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # এসিঙ্ক্রোনাস মেইন ফাংশন রান করুন
    asyncio.run(main())
