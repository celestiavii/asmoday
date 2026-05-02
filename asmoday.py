import json
import asyncio
import re
import html
import os
import urllib.request
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path
from itertools import combinations

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InputTextMessageContent,
    MessageEntity,
    BotCommand,
    MenuButtonCommands,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from telegram.error import Forbidden
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
    ApplicationHandlerStop,
)

try:
    import chess
    import chess.engine
    CHESS_LIB_AVAILABLE = True
except Exception:
    chess = None
    CHESS_LIB_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    CHESS_IMAGE_AVAILABLE = True
    IDCARD_IMAGE_AVAILABLE = True
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None
    CHESS_IMAGE_AVAILABLE = False
    IDCARD_IMAGE_AVAILABLE = False


# =========================================================
# KONFIG
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN tidak ditemukan. Pastikan sudah diset di environment hosting.")

OWNER_USERNAME = "deittee"

OWNER_USER_IDS = set()
OXANA_INFO_URL = "https://deivern.carrd.co"

FORWARD_PUBLIC_CHAT_ID = -1003742691663
FORWARD_STAFFTALK_CHAT_ID = -1003742691663

FORNEUS_UID = 8065791665
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
IDC_DIR = ASSETS_DIR / "idc"
FONT_DIR = ASSETS_DIR / "fonts"

STOCKFISH_PATH = str(BASE_DIR / "stockfish_engine")
if not os.path.exists(STOCKFISH_PATH):
    print("Downloading Stockfish...")
    url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2"
    urllib.request.urlretrieve(url, STOCKFISH_PATH)
    os.chmod(STOCKFISH_PATH, 0o755)

CHESS_ASSET_DIR = str(ASSETS_DIR / "Chess")
CHESS_BOARD_MARGIN = 37
CHESS_PIECE_SCALE = 0.85
# Ukuran grid asli design: fullboard 512px, area kotak 437.6466px.
CHESS_BOARD_GRID_SIZE = 437.6466

STATE_FILE = "oxana_state.json"
ACCOUNTS_FILE = "oxana_accounts.json"
PENDING_FILE = "oxana_pending.json"
STARTED_USERS_FILE = "oxana_started_users.json"
MENU_FILE = "oxana_menu.json"
ROOM_FILE = "oxana_room.json"
ANGEL_FILE = "oxana_angel.json"
PAYMENT_FILE = "oxana_payment.json"
SHIFT_FILE = "oxana_shift.json"
STAFF_INTERVIEW_FILE = "oxana_staff_interview.json"
CURATED_DINING_FILE = "oxana_curated_dining.json"
CUSTOM_COMMAND_FILE = "oxana_custom_commands.json"


IDCARD_ASSET_DIR = str(IDC_DIR)
IDCARD_FONT_DIR = str(FONT_DIR)
IDCARD_TEMPLATE_FILE = "staff_idc.png"
IDCARD_MEMBER_DIR = "."
IDCARD_MEMBER_VIP_FILE = "idc-mem-vip.png"
IDCARD_MEMBER_REG_FILE = "idc-mem-reg.png"
IDCARD_BASE_W = 1024
IDCARD_BASE_H = 554
IDCARD_PHOTO_SLOT_X = 82
IDCARD_PHOTO_SLOT_Y = 160
IDCARD_PHOTO_SLOT_W = 277
IDCARD_PHOTO_SLOT_H = 333
MAX_CODENAME_TEXT = "Julien Vaalsarova"
MAX_CODENAME_LEN = len(MAX_CODENAME_TEXT)



BOT_SHORT_DESCRIPTION = "ⓘ .. OXANA DESVANTRA ┊ talking ... asmoday—the withered mind forger"

INITIAL_MEMBER_BALANCE = {
    "regular": 2_500_000,
    "vip": 7_500_000,
}

ALLOWED_STAFF_ROLES = {
    "currathor": "Currathor",
    "server": "Server",
    "dj": "DJ",
    "disc jockey": "DJ",
    "disc_jockey": "DJ",
    "bartender": "Bartender",
    "angel": "Angel",
    "strip dancer": "Strip Dancer",
    "strip_dancer": "Strip Dancer",
    "stripdancer": "Strip Dancer",
    "general staff": "General Staff",
    "general_staff": "General Staff",
    "generalstaff": "General Staff",
    "chef": "Chef",
    "performer": "Performer",
}
STAFF_ROLE_KEYS = [
    ("currathor", "Currathor"),
    ("server", "Server"),
    ("dj", "DJ"),
    ("bartender", "Bartender"),
    ("angel", "Angel"),
    ("stripdancer", "Strip Dancer"),
    ("generalstaff", "General Staff"),
    ("chef", "Chef"),
    ("performer", "Performer"),
]

MENU_CATEGORY_LABELS = {
    "basic": "Basic Menu 🍷",
    "standard_cocktail": "Standard Cocktail 🍷",
    "signature": "Signature Cocktail 🍷",
    "themed": "Themed Drink 🍷",
    "exclusive": "Exclusive Menu 🍷",
    "vip": "VIP Only 🍷",
    "limited": "Limited Edition Drink 🍷",
}
MENU_CATEGORY_ORDER = ["basic", "standard_cocktail", "signature", "themed", "exclusive", "vip", "limited"]
MENU_CATEGORY_CREATE_ROWS = [
    [("basic", "Basic Menu"), ("standard_cocktail", "Standard Cocktail")],
    [("signature", "Signature Cocktail"), ("themed", "Themed Drink")],
    [("exclusive", "Exclusive Menu"), ("vip", "VIP Only")],
    [("limited", "Limited Edition Drink")],
]

# =========================================================
# DATA
# =========================================================
admin_ids = set()
talk_map = {}
approval_map = {}

ACCOUNTS = {}
ACCOUNT_INDEX = {}
FREED_NUMBERS = []

PENDING_MEMBERSHIP = {}
STARTED_USERS = {}

CHOICE_POKER_ROOMS = {}
POKER_ROOMS = {}
THIRTYONE_ROOMS = {}
BLACKJACK_ROOMS = {}
BOORAY_ROOMS = {}
DICE_POKER_ROOMS = {}
CHESS_ROOMS = {}
BACCARAT_ROOMS = {}
JUGEMENT_ROOMS = {}
ALLURING_ROOMS = {}

MENU_ITEMS = []
ROLLED_MENU = {}
ROOM_ITEMS = []
ROOM_BOOKINGS = []
ANGEL_PROFILES = {}
PENDING_BILLS = {}
SHIFT_SESSIONS = {}
OPEN_BAR_PENDING = {}
STAFF_INTERVIEW_DATA = {}
CURATED_DININGS = []
CUSTOM_COMMANDS = {}

SHIFT_ROLE_LABELS = {
    "dj": "Disc Jockey",
    "bartender": "Bartender",
    "strip_dancer": "Strip Dancer",
    "server": "Server",
    "angel": "Angel",
    "chef": "Chef",
    "performer": "Performer",
}
SHIFT_SLOT_LIMITS = {
    "dj": 1,
    "bartender": 2,
    "strip_dancer": 2,
    "server": 4,
    "angel": 5,
    "chef": 2,
    "performer": 2,
}
SHIFT_MODE_CONFIG = {
    "bar": {
        "label": "Bar",
        "roles": ["dj", "bartender", "strip_dancer", "server"],
    },
    "resort": {
        "label": "Resort",
        "roles": ["chef", "performer", "server"],
    },
}
SHIFT_SALARY_BY_ROLE = {
    "dj": 950000,
    "bartender": 950000,
    "strip_dancer": 950000,
    "server": 950000,
    "chef": 950000,
    "performer": 950000,
}

# =========================================================
# BASIC HELPERS
# =========================================================
def _now():
    return datetime.now()


def _parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _fmt_dt(dt_str):
    return dt_str if dt_str else "-"


def _tm_key(chat_id: int, message_id: int) -> str:
    return f"{chat_id}:{message_id}"


def _tm_parse(key: str):
    c, m = key.split(":", 1)
    return int(c), int(m)


def _is_owner(user) -> bool:
    if not user:
        return False

    try:
        if int(getattr(user, "id", 0)) in OWNER_USER_IDS:
            return True
    except Exception:
        pass

    username = (getattr(user, "username", None) or "").strip().lstrip("@").lower()
    owner_username = (OWNER_USERNAME or "").strip().lstrip("@").lower()
    if username and owner_username and username == owner_username:
        return True

    try:
        rec = ACCOUNTS.get(str(user.id))
        if rec and (rec.get("account_type") == "owner" or rec.get("owner_override")):
            return True
    except Exception:
        pass

    return False

def _is_admin(user) -> bool:
    return bool(user and (_is_owner(user) or (user.id in admin_ids)))


def _is_currathor(user) -> bool:
    if not user:
        return False
    if _is_owner(user):
        return True
    rec = _get_existing_account(user.id)
    role = (rec.get("staff_role") or "").strip().lower() if rec else ""
    return bool(rec and rec.get("account_type") == "staff" and role == "currathor")


def _can_manage_staff(user) -> bool:
    return _is_currathor(user)


def _membership_days(package: str) -> int:
    return 30 if (package or "").lower() == "vip" else 14


def _initial_member_balance(package: str) -> int:
    return int(INITIAL_MEMBER_BALANCE.get((package or "Regular").strip().lower(), INITIAL_MEMBER_BALANCE["regular"]))


def _registration_label(kind: str) -> str:
    mapping = {
        "membership": "Membership",
        "pengurus": "Staff Registration",
        "media_partner": "Media Partner",
        "sponsorship": "Sponsorship",
        "renewal": "Membership Renewal",
        "upgrade_vip": "Upgrade Plan VIP",
    }
    return mapping.get(kind, kind)


def _normalize_staff_role(role_text: str):
    if not role_text:
        return None
    key = role_text.strip().lower()
    return ALLOWED_STAFF_ROLES.get(key)


async def _sync_private_commands_for_user(context, user):
    try:
        rec = _get_existing_account(user.id)
        await context.bot.set_my_commands(
            _build_commands_for_user(user, rec),
            scope=BotCommandScopeChat(chat_id=user.id),
        )
    except Exception as e:
        print(f"[_sync_private_commands_for_user] error: {e}")


# =========================================================
# SEMI APP UI HELPERS
# =========================================================
def _safe_username(rec):
    username = (rec or {}).get("username") or "-"
    return f"@{username}" if username != "-" else "-"


def _account_status_text(user, rec):
    if not rec:
        return "No Account"
    if rec.get("account_type") == "owner":
        return "Owner"
    if rec.get("account_type") == "staff":
        return rec.get("staff_role") or "Staff"
    _refresh_membership_status(rec)
    mem_type = rec.get("membership_type") or "No Package"
    mem_status = (rec.get("membership_status") or "deactive").title()
    return f"{mem_type} — {mem_status}" if mem_type != "No Package" else mem_status


def _home_dashboard_text(user, rec):
    acc_no = rec.get("acc_no", "-") if rec else "-"
    codename = rec.get("name", "-") if rec else "-"
    balance = _format_balance((rec or {}).get("balance", 0))
    status = _account_status_text(user, rec)
    expires = ((rec or {}).get("membership_expires_at") or "-").split(" ")[0]
    return f"""𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐇𝐎𝐌𝐄

Account Number : {acc_no}
Codename : {codename}
Username : {_safe_username(rec or {})}
Status : {status}
Expired Date : {expires}
Balance : {balance} ✦𝕷

Pilih section di bawah untuk membuka fitur Lethéa."""
def _home_dashboard_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("My Account", callback_data="nav:account"),
            InlineKeyboardButton("Membership", callback_data="nav:membership"),
        ],
        [
            InlineKeyboardButton("Lethéa", callback_data="nav:lethea"),
            InlineKeyboardButton("Support", callback_data="nav:support"),
        ],
        [InlineKeyboardButton("Help", callback_data="nav:help")],
    ])


def _account_screen_text(user, rec):
    if not rec:
        return "Belum ada jejak account atas namamu di tatanan ini."
    _refresh_membership_status(rec)
    if rec.get("account_type") in ("owner", "staff"):
        status_text = "Owner" if rec.get("account_type") == "owner" else (rec.get("staff_role") or "Staff")
        return f"""𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓

Account Number : {rec.get('acc_no', '-')}
Username : {_safe_username(rec)}
Codename : {rec.get('name', '-')}
Role : {status_text}
Balance : {_format_balance(rec.get('balance', 0))} ✦𝕷"""
    return f"""𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓

Account Number : {rec.get('acc_no', '-')}
Username : {_safe_username(rec)}
Codename : {rec.get('name', '-')}
Membership : {rec.get('membership_type') or '-'}
Status : {(rec.get('membership_status') or '-').title()}
Expired Date : {(rec.get('membership_expires_at') or '-').split(' ')[0]}
Balance : {_format_balance(rec.get('balance', 0))} ✦𝕷"""
def _account_screen_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Change Codename", callback_data="nav:account:codename")],
        [InlineKeyboardButton("Refresh", callback_data="nav:account"), InlineKeyboardButton("Home", callback_data="nav:home")],
    ])


def _membership_screen_text(user, rec):
    status = _account_status_text(user, rec)
    expires = ((rec or {}).get("membership_expires_at") or "-").split(" ")[0]
    return f"""𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐌𝐄𝐌𝐁𝐄𝐑𝐒𝐇𝐈𝐏

VIP : masa aktif 30 hari
Regular : masa aktif 14 hari

Current Status : {status}
Expired Date : {expires}

Pilih action membership yang ingin kamu gunakan."""
def _membership_screen_keyboard(rec):
    rows = [
        [InlineKeyboardButton("Registration", callback_data="navaction:registration")],
        [InlineKeyboardButton("Renewal", callback_data="navaction:renewal")],
    ]
    if rec and rec.get("account_type") == "member" and rec.get("membership_type") == "Regular":
        rows.append([InlineKeyboardButton("Upgrade VIP", callback_data="navaction:upgradevip")])
    rows.append([InlineKeyboardButton("Home", callback_data="nav:home")])
    return InlineKeyboardMarkup(rows)


def _lethea_screen_text(user, rec):
    vip_access = "Yes" if _can_rent_angel(user, rec) else "No"
    gamble_access = "Yes" if _has_gamble_access(rec) else "No"
    return f"""𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐋𝐄𝐓𝐇É𝐀

Akses cepat menuju fitur utama Lethéa.

Rent Angel Access : {vip_access}
Game Access : {gamble_access}

Gunakan tombol di bawah untuk membuka menu, room game, atau panel Angel."""
def _lethea_screen_keyboard(user, rec):
    rows = [
        [InlineKeyboardButton("The Menu", callback_data="navaction:letheamenu"), InlineKeyboardButton("Choice Poker", callback_data="navaction:choicepoker")],
    ]
    if _can_rent_angel(user, rec):
        rows.append([InlineKeyboardButton("Rent Angel", callback_data="navaction:rentangel")])
    rows.append([InlineKeyboardButton("Home", callback_data="nav:home")])
    return InlineKeyboardMarkup(rows)


def _support_screen_text():
    return """𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐒𝐔𝐏𝐏𝐎𝐑𝐓

Kirim masukan, pesan anonim, atau hubungi admin langsung dari panel ini.

Kritik dan Saran : sampaikan feedback
Anonymous Message : kirim pesan tanpa nama
Panggil Asmoday : untuk berbicara langsung dengan pengurus"""
def _support_screen_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Kritik & Saran", callback_data="navaction:kritik"), InlineKeyboardButton("Anonymous", callback_data="navaction:menfess")],
        [InlineKeyboardButton("Panggil Asmoday", callback_data="navaction:talk")],
        [InlineKeyboardButton("Home", callback_data="nav:home")],
    ])


def _help_screen_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Home", callback_data="nav:home")]])


# =========================================================
# STORAGE
# =========================================================
def save_state():
    try:
        data = {
            "admin_ids": list(admin_ids),
            "talk_map": {_tm_key(c, m): int(uid) for (c, m), uid in talk_map.items()},
            "approval_map": {_tm_key(c, m): info for (c, m), info in approval_map.items()},
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_state failed: {e}")


def load_state():
    global admin_ids, talk_map, approval_map
    try:
        p = Path(STATE_FILE)
        if not p.exists():
            return

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        admin_ids.clear()
        for x in data.get("admin_ids", []):
            try:
                admin_ids.add(int(x))
            except Exception:
                pass

        talk_map.clear()
        for k, uid in data.get("talk_map", {}).items():
            try:
                chat_id, msg_id = _tm_parse(k)
                talk_map[(chat_id, msg_id)] = int(uid)
            except Exception:
                pass

        approval_map.clear()
        for k, info in data.get("approval_map", {}).items():
            try:
                chat_id, msg_id = _tm_parse(k)
                approval_map[(chat_id, msg_id)] = info
            except Exception:
                pass
    except Exception as e:
        print(f"[WARN] load_state failed: {e}")


def save_accounts():
    try:
        data = {
            "accounts": ACCOUNTS,
            "index": ACCOUNT_INDEX,
            "freed": FREED_NUMBERS,
        }
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_accounts failed: {e}")


def load_accounts():
    global ACCOUNTS, ACCOUNT_INDEX, FREED_NUMBERS
    try:
        p = Path(ACCOUNTS_FILE)
        if not p.exists():
            return

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        ACCOUNTS = data.get("accounts", {})
        ACCOUNT_INDEX = data.get("index", {})
        FREED_NUMBERS = data.get("freed", [])

        changed = False
        for uid_str, rec in list(ACCOUNTS.items()):
            before = dict(rec)
            ACCOUNTS[uid_str] = _normalize_account_record(int(uid_str), rec)
            if before != ACCOUNTS[uid_str]:
                changed = True

            acc_no = str(ACCOUNTS[uid_str]["acc_no"])
            if acc_no not in ACCOUNT_INDEX:
                ACCOUNT_INDEX[acc_no] = uid_str
                changed = True

        if changed:
            save_accounts()

    except Exception as e:
        print(f"[WARN] load_accounts failed: {e}")


def save_pending():
    try:
        data = {"membership": PENDING_MEMBERSHIP}
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_pending failed: {e}")


def load_pending():
    global PENDING_MEMBERSHIP
    try:
        p = Path(PENDING_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        PENDING_MEMBERSHIP = data.get("membership", {})
    except Exception as e:
        print(f"[WARN] load_pending failed: {e}")

def save_started_users():
    try:
        with open(STARTED_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(STARTED_USERS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_started_users failed: {e}")


def load_started_users():
    global STARTED_USERS
    try:
        p = Path(STARTED_USERS_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        STARTED_USERS = data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[WARN] load_started_users failed: {e}")
        STARTED_USERS = {}


def __old_save_menu_data_1():
    try:
        data = {
            "items": MENU_ITEMS,
            "rolled_menu": ROLLED_MENU,
        }
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_menu_data failed: {e}")


def __old_load_menu_data_1():
    global MENU_ITEMS, ROLLED_MENU
    try:
        p = Path(MENU_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        MENU_ITEMS = data.get("items", [])
        ROLLED_MENU = data.get("rolled_menu", {})
        if not isinstance(MENU_ITEMS, list):
            MENU_ITEMS = []
        if not isinstance(ROLLED_MENU, dict):
            ROLLED_MENU = {}
    except Exception as e:
        print(f"[WARN] load_menu_data failed: {e}")
        MENU_ITEMS = []
        ROLLED_MENU = {}


def save_angel_data():
    try:
        data = {
            "profiles": ANGEL_PROFILES,
        }
        with open(ANGEL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_angel_data failed: {e}")


def load_angel_data():
    global ANGEL_PROFILES
    try:
        p = Path(ANGEL_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ANGEL_PROFILES = data.get("profiles", {})
        if not isinstance(ANGEL_PROFILES, dict):
            ANGEL_PROFILES = {}
    except Exception as e:
        print(f"[WARN] load_angel_data failed: {e}")
        ANGEL_PROFILES = {}


def save_payment_data():
    try:
        with open(PAYMENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"pending_bills": PENDING_BILLS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_payment_data failed: {e}")


def load_payment_data():
    global PENDING_BILLS
    try:
        p = Path(PAYMENT_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        PENDING_BILLS = data.get("pending_bills", {})
        if not isinstance(PENDING_BILLS, dict):
            PENDING_BILLS = {}
    except Exception as e:
        print(f"[WARN] load_payment_data failed: {e}")
        PENDING_BILLS = {}


def save_shift_data():
    try:
        with open(SHIFT_FILE, "w", encoding="utf-8") as f:
            json.dump({"shift_sessions": SHIFT_SESSIONS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_shift_data failed: {e}")


def load_shift_data():
    global SHIFT_SESSIONS
    try:
        p = Path(SHIFT_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        SHIFT_SESSIONS = data.get("shift_sessions", {})
        if not isinstance(SHIFT_SESSIONS, dict):
            SHIFT_SESSIONS = {}
    except Exception as e:
        print(f"[WARN] load_shift_data failed: {e}")
        SHIFT_SESSIONS = {}



# =========================================================
# CUSTOM COMMAND STORAGE
# =========================================================
def save_custom_command_data():
    try:
        with open(CUSTOM_COMMAND_FILE, "w", encoding="utf-8") as f:
            json.dump({"commands": CUSTOM_COMMANDS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_custom_command_data failed: {e}")


def load_custom_command_data():
    global CUSTOM_COMMANDS
    try:
        p = Path(CUSTOM_COMMAND_FILE)
        if not p.exists():
            CUSTOM_COMMANDS = {}
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        commands = data.get("commands", {}) if isinstance(data, dict) else {}
        CUSTOM_COMMANDS = commands if isinstance(commands, dict) else {}
    except Exception as e:
        print(f"[WARN] load_custom_command_data failed: {e}")
        CUSTOM_COMMANDS = {}

# =========================================================
# STAFF REGISTRATION INTERVIEW SCHEDULE
# =========================================================
def save_staff_interview_data():
    try:
        with open(STAFF_INTERVIEW_FILE, "w", encoding="utf-8") as f:
            json.dump(STAFF_INTERVIEW_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_staff_interview_data failed: {e}")


def load_staff_interview_data():
    global STAFF_INTERVIEW_DATA
    try:
        p = Path(STAFF_INTERVIEW_FILE)
        if not p.exists():
            STAFF_INTERVIEW_DATA = {}
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        STAFF_INTERVIEW_DATA = data if isinstance(data, dict) else {}
        STAFF_INTERVIEW_DATA.setdefault("open", None)
        STAFF_INTERVIEW_DATA.setdefault("bookings", {})
    except Exception as e:
        print(f"[WARN] load_staff_interview_data failed: {e}")
        STAFF_INTERVIEW_DATA = {"open": None, "bookings": {}}


def _staff_interview_slots():
    return [
        ("12-13", "12.00–13.00"),
        ("17-18", "17.00–18.00"),
        ("18-19", "18.00–19.00"),
        ("19-20", "19.00–20.00"),
        ("20-21", "20.00–21.00"),
        ("21-22", "21.00–22.00"),
    ]


def _parse_staff_oprec_date(text: str):
    try:
        return datetime.strptime((text or "").strip(), "%d-%m-%Y").date()
    except Exception:
        return None


def _fmt_staff_oprec_date(d):
    if isinstance(d, str):
        d = _parse_staff_oprec_date(d) or d
    if hasattr(d, "strftime"):
        return d.strftime("%d-%m-%Y")
    return str(d)


def _active_staff_oprec_dates():
    data = STAFF_INTERVIEW_DATA.get("open") or {}
    start = _parse_staff_oprec_date(data.get("start"))
    end = _parse_staff_oprec_date(data.get("end"))
    if not start or not end:
        return []
    today = _now().date()
    cur = max(start, today)
    out = []
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def _staff_oprec_closed_text() -> str:
    return (
        "ⓘ Jadwal wawancara staff belum dibuka. "
        "Minta Currathor/Owner membuka jadwal dengan /oprecstaff dd-mm-yyyy - dd-mm-yyyy."
    )


def _is_staff_oprec_open() -> bool:
    return bool(_active_staff_oprec_dates())


def _staff_date_key(date_text: str) -> str:
    d = _parse_staff_oprec_date(date_text)
    return d.strftime("%d-%m-%Y") if d else str(date_text or "")


def _staff_slot_label(slot_key: str) -> str:
    return dict(_staff_interview_slots()).get(slot_key, slot_key)


def _staff_booking_for(date_key: str, slot_key: str):
    return (STAFF_INTERVIEW_DATA.get("bookings") or {}).get(date_key, {}).get(slot_key)


def _is_staff_slot_available(date_key: str, slot_key: str) -> bool:
    return not bool(_staff_booking_for(date_key, slot_key))


def _staff_interview_date_keyboard():
    rows = []
    for d in _active_staff_oprec_dates():
        date_key = d.strftime("%d-%m-%Y")
        available = sum(1 for slot_key, _ in _staff_interview_slots() if _is_staff_slot_available(date_key, slot_key))
        if available > 0:
            rows.append([InlineKeyboardButton(f"{date_key} · {available} slot", callback_data=f"staffiv:date:{date_key}")])
    rows.append([InlineKeyboardButton("Batalkan", callback_data="staffiv:cancel")])
    return InlineKeyboardMarkup(rows)


def _staff_interview_slot_keyboard(date_key: str):
    rows = []
    for slot_key, label in _staff_interview_slots():
        if _is_staff_slot_available(date_key, slot_key):
            rows.append([InlineKeyboardButton(label, callback_data=f"staffiv:slot:{date_key}:{slot_key}")])
    rows.append([InlineKeyboardButton("← Pilih tanggal lain", callback_data="staffiv:backdates")])
    rows.append([InlineKeyboardButton("Batalkan", callback_data="staffiv:cancel")])
    return InlineKeyboardMarkup(rows)


def _staff_interview_booking_text(date_key: str, slot_key: str) -> str:
    return f"{date_key} | {_staff_slot_label(slot_key)}"


def _release_staff_interview_booking(flow: dict, uid: int | None = None):
    if not flow:
        return
    date_key = flow.get("interview_date")
    slot_key = flow.get("interview_slot")
    if not date_key or not slot_key:
        return
    bookings = STAFF_INTERVIEW_DATA.setdefault("bookings", {})
    day = bookings.setdefault(date_key, {})
    current = day.get(slot_key)
    if current and (uid is None or int(current.get("uid", 0)) == int(uid)):
        day.pop(slot_key, None)
        if not day:
            bookings.pop(date_key, None)
        flow.pop("interview_date", None)
        flow.pop("interview_slot", None)
        flow.pop("interview_label", None)
        save_staff_interview_data()


async def oprec_staff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Titah ini hanya dapat dibuka oleh Owner atau Currathor.")
        return

    raw = (update.effective_message.text or "").split(maxsplit=1)
    arg_text = raw[1].strip() if len(raw) > 1 else ""
    m = re.match(r"^(\d{2}-\d{2}-\d{4})\s*-\s*(\d{2}-\d{2}-\d{4})$", arg_text)
    if not m:
        await update.message.reply_text("Format titah: /oprecstaff dd-mm-yyyy - dd-mm-yyyy")
        return

    start = _parse_staff_oprec_date(m.group(1))
    end = _parse_staff_oprec_date(m.group(2))
    if not start or not end:
        await update.message.reply_text("Tanggal itu tidak terbaca oleh catatanku. Contoh: /oprecstaff 26-04-2026 - 30-04-2026")
        return
    if end < start:
        await update.message.reply_text("Akhir masa tidak dapat mendahului awalnya.")
        return

    STAFF_INTERVIEW_DATA["open"] = {
        "start": start.strftime("%d-%m-%Y"),
        "end": end.strftime("%d-%m-%Y"),
        "opened_by": int(update.effective_user.id),
        "opened_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    STAFF_INTERVIEW_DATA.setdefault("bookings", {})
    save_staff_interview_data()

    await update.message.reply_text(
        "／  ⟢ › STAFF INTERVIEW OPEN .. !\n"
        "───\n"
        f"Rentang wawancara: {start.strftime('%d-%m-%Y')} sampai {end.strftime('%d-%m-%Y')}\n\n"
        "Calon staff yang mengisi form akan diminta memilih tanggal dan jam wawancara yang masih tersedia."
    )


async def staff_interview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    flow = context.user_data.get("registration_flow")
    if not flow or flow.get("flow_type") != "staff_form":
        await query.answer("Sesi registration staff tidak ditemukan.", show_alert=True)
        return

    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "cancel":
        _release_staff_interview_booking(flow, query.from_user.id)
        context.user_data.pop("registration_flow", None)
        await query.edit_message_text("Sesi registration staff telah kugugurkan dari catatan.")
        return

    if action == "backdates":
        await query.edit_message_text(
            "Pilih tanggal wawancara staff yang tersedia.",
            reply_markup=_staff_interview_date_keyboard()
        )
        return

    if action == "date" and len(parts) >= 3:
        date_key = _staff_date_key(parts[2])
        if date_key not in [d.strftime("%d-%m-%Y") for d in _active_staff_oprec_dates()]:
            await query.answer("Tanggal ini sudah tidak tersedia.", show_alert=True)
            return
        if not any(_is_staff_slot_available(date_key, slot_key) for slot_key, _ in _staff_interview_slots()):
            await query.answer("Slot di tanggal ini sudah penuh.", show_alert=True)
            return
        flow["step"] = "choose_interview_slot"
        flow["interview_date"] = date_key
        await query.edit_message_text(
            f"Tanggal dipilih: {date_key}\n\nPilih jam wawancara yang masih tersedia.",
            reply_markup=_staff_interview_slot_keyboard(date_key)
        )
        return

    if action == "slot" and len(parts) >= 4:
        date_key = _staff_date_key(parts[2])
        slot_key = parts[3]
        if slot_key not in dict(_staff_interview_slots()):
            await query.answer("Slot tidak valid.", show_alert=True)
            return
        if not _is_staff_slot_available(date_key, slot_key):
            await query.answer("Slot ini sudah diambil. Pilih jam lain.", show_alert=True)
            await query.edit_message_text(
                f"Tanggal dipilih: {date_key}\n\nPilih jam wawancara yang masih tersedia.",
                reply_markup=_staff_interview_slot_keyboard(date_key)
            )
            return

        _release_staff_interview_booking(flow, query.from_user.id)
        STAFF_INTERVIEW_DATA.setdefault("bookings", {}).setdefault(date_key, {})[slot_key] = {
            "uid": int(query.from_user.id),
            "username": query.from_user.username or "-",
            "name": query.from_user.full_name or "-",
            "booked_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_staff_interview_data()
        label = _staff_interview_booking_text(date_key, slot_key)
        flow["step"] = "confirm"
        flow["interview_date"] = date_key
        flow["interview_slot"] = slot_key
        flow["interview_label"] = label
        keyboard = [
            [InlineKeyboardButton("☑ Sudah benar", callback_data="regconfirm:yes")],
            [InlineKeyboardButton("☒ Masih ada yang salah", callback_data="regconfirm:no")],
        ]
        await query.edit_message_text(
            "Apakah data berikut sudah benar?\n\n"
            f"{flow.get('form_data', '-')}\n\n"
            f"Jadwal Wawancara : {label}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

def _remember_started_user(user):
    if not user:
        return

    username_clean = (user.username or "").strip().lstrip("@").lower()

    STARTED_USERS[str(user.id)] = {
        "id": user.id,
        "username": username_clean,
        "full_name": user.full_name or user.first_name or f"User {user.id}",
        "started_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_started_users()


def _get_started_user_by_username(username: str):
    if not username:
        return None

    lookup = username.strip().lstrip("@").lower()
    if not lookup:
        return None

    for uid, data in STARTED_USERS.items():
        stored_username = (data.get("username") or "").strip().lstrip("@").lower()
        if stored_username == lookup:
            return data

    return None


# =========================================================
# ACCOUNT HELPERS
# =========================================================
def _next_account_number() -> int:
    if FREED_NUMBERS:
        FREED_NUMBERS.sort()
        return FREED_NUMBERS.pop(0)

    used = [int(k) for k in ACCOUNT_INDEX.keys()] if ACCOUNT_INDEX else []
    return (max(used) + 1) if used else 1


def _ensure_owner_account(user):
    if not _is_owner(user):
        return None

    rec = _get_existing_account(user.id)
    if rec:
        changed = False
        # Owner tetap dikenali sebagai owner walau account_type/staff_role-nya sedang Server, Currathor, dll.
        # Ini tidak mengubah role display/staff_role, hanya memberi akses owner permanen pada akun ini.
        if not rec.get("owner_override"):
            rec["owner_override"] = True
            changed = True
        if rec.get("balance") is None:
            rec["balance"] = 0
            changed = True
        if changed:
            save_accounts()
        return rec

    rec = _create_account(user.id, user, account_type="owner")
    rec["owner_override"] = True
    rec["balance"] = 0
    save_accounts()
    return rec

def _get_existing_account(uid: int):
    rec = ACCOUNTS.get(str(uid))
    if not rec:
        return None
    return _normalize_account_record(uid, rec)


def _refresh_membership_status(rec):
    if "membership_status" not in rec:
        rec["membership_status"] = "deactive"

    expires_at = _parse_dt(rec.get("membership_expires_at"))
    if expires_at and expires_at <= _now():
        rec["membership_status"] = "deactive"

    return rec.get("membership_status", "deactive")


def _is_active_member(rec) -> bool:
    if not rec:
        return False
    _refresh_membership_status(rec)
    return rec.get("membership_status") == "active"


def _has_gamble_access(rec) -> bool:
    if not rec:
        return False
    acc_no = rec.get("acc_no")
    return acc_no not in (None, "", "-")


def _can_use_locked_features(user, rec) -> bool:
    if _is_admin(user):
        return True
    if not rec:
        return False
    if rec.get("account_type") in ("staff", "owner"):
        return True
    return _is_active_member(rec)


def _get_account_by_acc_no(acc_no: str):
    uid = ACCOUNT_INDEX.get(str(acc_no))
    if not uid:
        return None, None
    rec = ACCOUNTS.get(str(uid))
    if not rec:
        return uid, None
    return uid, _normalize_account_record(int(uid), rec)


def _get_account_by_username(username: str):
    if not username:
        return None, None
    lookup = username.lower().lstrip('@')
    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        if (rec.get("username") or "").lower().lstrip('@') == lookup:
            return uid_str, rec
    return None, None


def _is_banned_record(rec) -> bool:
    return bool(rec and rec.get("banned"))


def _format_balance(amount) -> str:
    try:
        return f"{int(amount):,}"
    except Exception:
        return str(amount)


def _get_raw_target_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    text = (getattr(msg, "text", None) or getattr(msg, "caption", None) or "").strip()
    raw = None

    if context.args:
        raw = (context.args[0] or "").strip()

    if not raw and text:
        parts = text.split(maxsplit=1)
        if len(parts) >= 2:
            raw = parts[1].strip().split()[0]

    if not raw:
        return None

    raw = raw.strip().rstrip(",.;:)")
    return raw or None


def _make_dummy_user(uid, username=None, full_name=None):
    class DummyUser:
        pass

    u = DummyUser()
    u.id = int(uid)
    u.username = username
    u.full_name = full_name or username or f"User {uid}"
    u.is_bot = False
    return u


def _extract_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user

    raw = _get_raw_target_token(update, context)
    if not raw:
        return None

    if raw.isdigit():
        uid, rec = _get_account_by_acc_no(raw)
        if not rec:
            return None
        return _make_dummy_user(uid, rec.get("username"), rec.get("name") or rec.get("username") or f"Account {raw}")

    if raw.startswith('@'):
        uname = raw[1:].strip().lower()
        if not uname:
            return None
        started = _get_started_user_by_username(uname)
        if started and started.get("id"):
            return _make_dummy_user(started.get("id"), started.get("username"), started.get("full_name") or started.get("username") or uname)
        uid, rec = _get_account_by_username(uname)
        if rec:
            return _make_dummy_user(uid, rec.get("username"), rec.get("name") or rec.get("username") or uname)
        return None

    return None


def _get_target_account_from_acc_no_arg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = _get_raw_target_token(update, context)
    if not raw:
        return None, None, "ⓘ .. Format: gunakan account number. Contoh: /delstaff 2"

    acc_no = raw.strip()
    if not acc_no.isdigit():
        return None, None, "ⓘ .. Gunakan account number yang berupa angka. Contoh: /editrole 2"

    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        return None, None, "ⓘ .. Account number tidak ditemukan."

    return int(uid), rec, None


async def _resolve_staff_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return None, "ⓘ .. Pesan tidak ditemukan."

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
        if getattr(target, "is_bot", False):
            return None, "ⓘ .. Tidak bisa memilih Asmoday sebagai target staff."
        return target, None

    text = (getattr(msg, "text", None) or getattr(msg, "caption", None) or "")
    entities = list(getattr(msg, "entities", None) or [])
    entities += list(getattr(msg, "caption_entities", None) or [])

    for ent in entities:
        ent_type = getattr(ent, "type", None)

        if ent_type == "text_mention" and getattr(ent, "user", None):
            target = ent.user
            if getattr(target, "is_bot", False):
                return None, "ⓘ .. Tidak bisa memilih Asmoday sebagai target staff."
            return target, None

        if ent_type == "mention":
            try:
                mention_text = text[ent.offset: ent.offset + ent.length]
            except Exception:
                mention_text = None
            if mention_text:
                mention_text = mention_text.strip()
                if mention_text.startswith('@'):
                    started = _get_started_user_by_username(mention_text)
                    if started and started.get("id"):
                        return _make_dummy_user(started.get("id"), started.get("username"), started.get("full_name") or started.get("username") or mention_text), None

                    uid, rec = _get_account_by_username(mention_text)
                    if rec:
                        return _make_dummy_user(uid, rec.get("username"), rec.get("name") or rec.get("username") or mention_text), None

    raw_target = _get_raw_target_token(update, context)
    target = _extract_target_user(update, context)
    if target and getattr(target, "id", None):
        if getattr(target, "is_bot", False):
            return None, "ⓘ .. Tidak bisa memilih Asmoday sebagai target staff."

        if raw_target and raw_target.startswith('@'):
            requested_username = raw_target.lstrip('@').strip().lower()
            actor_username = (getattr(update.effective_user, 'username', None) or '').strip().lstrip('@').lower()
            resolved_username = (getattr(target, 'username', None) or '').strip().lstrip('@').lower()

            if requested_username != resolved_username:
                if requested_username == actor_username:
                    return target, None
                return None, (
                    f"Username @{requested_username} tidak cocok dengan data target yang terbaca. "
                    "Pastikan username benar dan user target sudah /start Asmoday."
                )

        return target, None

    return None, (
        "ⓘ .. Target tidak ditemukan. Reply pesan usernya, dan pastikan si user sudah /start."
    )
async def _ensure_not_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return True
    rec = _get_existing_account(user.id)
    if not _is_banned_record(rec):
        return True
    text = "ⓘ .. Kamu sedang diban. Tidak bisa akses fitur ku."
    if update.callback_query:
        try:
            await update.callback_query.answer(text, show_alert=True)
        except Exception:
            pass
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
    elif update.effective_message:
        try:
            await update.effective_message.reply_text(text)
        except Exception:
            pass
    return False


def _extend_membership_from_current(rec, package: str):
    now = _now()
    current_expiry = _parse_dt(rec.get("membership_expires_at"))

    if current_expiry and current_expiry > now:
        start_base = current_expiry
    else:
        start_base = now

    new_expiry = start_base + timedelta(days=_membership_days(package))

    rec["membership_type"] = package
    rec["membership_status"] = "active"
    if not rec.get("membership_started_at"):
        rec["membership_started_at"] = now.strftime("%Y-%m-%d | %H:%M")
    rec["membership_expires_at"] = new_expiry.strftime("%Y-%m-%d %H:%M")
    rec["last_expiry_notified_at"] = None


def _can_manage_menu(user) -> bool:
    return _is_currathor(user)

def _can_rent_angel(user, rec=None) -> bool:
    if not user:
        return False

    rec = rec or _get_existing_account(user.id)

    if _is_owner(user):
        return True

    if rec:
        account_type = (rec.get("account_type") or "").strip().lower()
        staff_role = (rec.get("staff_role") or "").strip().lower()

        if account_type == "owner":
            return True
        if account_type == "staff" and staff_role == "currathor":
            return True

        _refresh_membership_status(rec)
        return (
            account_type == "member"
            and rec.get("membership_type") == "VIP"
            and rec.get("membership_status") == "active"
        )

    return False


def _is_staff_like(user, rec=None) -> bool:
    if _is_owner(user):
        return True
    rec = rec or (_get_existing_account(user.id) if user else None)
    return bool(rec and rec.get("account_type") == "staff")


def _angel_staff_records():
    items = []
    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        if rec.get("account_type") == "staff" and (rec.get("staff_role") or "").lower() == "angel":
            items.append((int(uid_str), rec))
    items.sort(key=lambda x: int(x[1].get("acc_no", 0) or 0))
    return items


def _angel_popularity_info(total_orders: int):
    total_orders = int(total_orders or 0)
    if total_orders <= 5:
        return "Rising", 1500000
    if total_orders <= 12:
        return "Favorite", 2500000
    if total_orders <= 25:
        return "Star", 4000000
    if total_orders <= 45:
        return "Iconic", 6500000
    return "Legendary", 10000000


def _angel_current_price(rec, profile=None):
    profile = profile or _ensure_angel_profile(int(rec.get("acc_no") and ACCOUNT_INDEX.get(str(rec.get("acc_no"))) or 0) or 0)
    return _angel_popularity_info(int((profile or {}).get("total_orders", 0) or 0))


def _angel_display_name(rec):
    return rec.get("name") or (f"@{rec.get('username')}" if rec.get("username") and rec.get("username") != "-" else f"Angel {rec.get('acc_no', '-')}")


def _currathor_uids():
    uids = []
    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        if rec.get("account_type") == "staff" and (rec.get("staff_role") or "").lower() == "currathor":
            uids.append(int(uid_str))
    uids.sort()
    return uids


def _split_evenly(total: int, uids):
    total = int(total or 0)
    uids = list(uids or [])
    if total <= 0 or not uids:
        return {}
    base = total // len(uids)
    rem = total % len(uids)
    result = {}
    for i, uid in enumerate(uids):
        result[int(uid)] = base + (1 if i < rem else 0)
    return result


async def _notify_income_dm(context, uid: int, amount: int, source_text: str):
    if int(amount or 0) <= 0:
        return
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "💸 Pemasukan Baru\n\n"
                f"Nominal : {_normalize_price_text(amount)} ✦𝕷\n"
                f"Sumber : {source_text}"
            )
        )
    except Exception as e:
        print(f"[_notify_income_dm] failed uid={uid}: {e}")


async def _credit_currathors(context, total_amount: int, source_text: str):
    payouts = _split_evenly(int(total_amount or 0), _currathor_uids())
    if not payouts:
        return {}
    for uid, amount in payouts.items():
        rec = _get_existing_account(int(uid))
        if not rec:
            continue
        rec["balance"] = int(rec.get("balance", 0)) + int(amount)
        await _notify_income_dm(context, int(uid), int(amount), source_text)
    save_accounts()
    return payouts


async def _credit_angel_income(context, angel_uid: int, amount: int, source_text: str):
    if int(amount or 0) <= 0:
        return False
    rec = _get_existing_account(int(angel_uid))
    if not rec:
        return False
    rec["balance"] = int(rec.get("balance", 0)) + int(amount)
    save_accounts()
    await _notify_income_dm(context, int(angel_uid), int(amount), source_text)
    return True

async def _grant_angel_rent_cnit(context, angel_uid: int, source_text: str, amount: int = 1000):
    try:
        amount = int(amount or 0)
        if amount <= 0:
            return False
        rec = _get_existing_account(int(angel_uid))
        if not rec:
            return False
        rec["cnit_pending"] = int(rec.get("cnit_pending", 0) or 0) + amount
        try:
            _push_cnit_claim_history(rec, amount, "earned", source_text)
        except Exception:
            pass
        save_accounts()
        try:
            await context.bot.send_message(
                chat_id=int(angel_uid),
                text=(
                    "💠 CNIT Rent Angel Masuk\n\n"
                    f"Jumlah : {amount} CNIT\n"
                    f"Sumber : {source_text}\n"
                    f"Balance CNIT : {int(rec.get('cnit_pending', 0) or 0)}"
                ),
            )
        except Exception as e:
            print(f"[angel rent cnit notify] failed uid={angel_uid}: {e}")
        return True
    except Exception as e:
        print(f"[_grant_angel_rent_cnit] failed uid={angel_uid}: {e}")
        return False


def _new_bill_id():
    return f"bill_{int(_now().timestamp() * 1000)}_{len(PENDING_BILLS)+1}"


def _normalize_price_text(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


def _normalize_menu_block_text(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _format_menu_info_text(item: dict) -> str:
    ingredients = _normalize_menu_block_text(item.get("ingredients") or "")
    how_to_make = _normalize_menu_block_text(item.get("how_to_make") or "")

    lines = [
        f"࣪ ˖ ੭ .. : {item.get('name', '-')}",
        ingredients or "› -",
        "",
        "———— ╱╱ How to make :",
        how_to_make or "› -",
    ]
    return "\n".join(lines)


def _next_menu_number() -> int:
    used = [int(item.get("no", 0)) for item in MENU_ITEMS if str(item.get("no", "")).isdigit()]
    return (max(used) + 1) if used else 1


def _sorted_menu_items():
    out = []
    for item in MENU_ITEMS:
        try:
            sort_no = int(item.get("no", 0))
        except Exception:
            sort_no = 999999999
        out.append((sort_no, item))
    out.sort(key=lambda x: x[0])
    return [item for _, item in out]


def _group_menu_items_by_category(items):
    grouped = {key: [] for key in MENU_CATEGORY_ORDER}
    for item in items:
        cat = item.get("category")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item)
    return grouped


def _roll_count_for_category(category: str, item_count: int) -> int:
    if item_count <= 0:
        return 0

    import random

    if category == "limited":
        # condong tidak muncul
        if random.random() < 0.75:
            return 0
        return 1

    ranges = {
        "basic": (4, 7),
        "standard_cocktail": (3, 5),
        "signature": (3, 5),
        "themed": (2, 3),
        "exclusive": (1, 2),
        "vip": (1, 2),
    }

    min_count, max_count = ranges.get(category, (1, item_count))
    if item_count < min_count:
        return item_count
    return random.randint(min_count, min(max_count, item_count))


def _format_rolled_menu_text():
    lines = [
        "ㅤ",
        "𖠷 ╱ .. 𝐋𝐄𝐓𝐇É𝐀: 𝐓𝐇𝐄 𝐌𝐄𝐍𝐔 ",
        "───────────────`",
    ]
    has_any = False
    for category in MENU_CATEGORY_ORDER:
        items = ROLLED_MENU.get(category) or []
        if not items:
            continue
        has_any = True
        lines.extend([
            f"࣪ ˖ ੭ .. : {_menu_category_label(category)}",
        ])
        for item in items:
            lines.append(f"› {item.get('name', '-')} — {_normalize_price_text(item.get('price', 0))}")
        lines.append("")
    if not has_any:
        return "ⓘ .. Belum ada hasil roll menu. Gunakan /rollmenu dulu."
    return "\n".join(lines).strip()


def _format_full_menu_list_text():
    items = _sorted_menu_items()
    if not items:
        return "ⓘ .. Belum ada menu tersimpan."
    lines = ["Lethéa Menu List:", ""]
    grouped = _group_menu_items_by_category(items)
    for category in MENU_CATEGORY_ORDER:
        cat_items = grouped.get(category) or []
        if not cat_items:
            continue
        lines.append(f"[{_menu_category_label(category)}]")
        for item in cat_items:
            lines.append(f"{item.get('no')}. {item.get('name')} | {_normalize_price_text(item.get('price', 0))}")
        lines.append("")
    return "\n".join(lines).strip()


def _eligible_openbar_members():
    recipients = []
    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        if rec.get("account_type") != "member":
            continue
        _refresh_membership_status(rec)
        if rec.get("membership_status") != "active":
            continue
        recipients.append((int(uid_str), rec))
    recipients.sort(key=lambda x: int(x[1].get("acc_no", 0) or 0))
    return recipients


def _eligible_openresort_members():
    recipients = []
    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        if rec.get("account_type") != "member":
            continue
        _refresh_membership_status(rec)
        if rec.get("membership_status") != "active":
            continue
        if (rec.get("membership_type") or "").strip().lower() != "vip":
            continue
        recipients.append((int(uid_str), rec))
    recipients.sort(key=lambda x: int(x[1].get("acc_no", 0) or 0))
    return recipients


def _openwarung_label(kind: str) -> str:
    return "RESORT" if (kind or "").strip().lower() == "resort" else "BAR"


def _openwarung_recipients(kind: str):
    return _eligible_openresort_members() if (kind or "").strip().lower() == "resort" else _eligible_openbar_members()


def _openwarung_dm_text(kind: str, link: str) -> str:
    label = _openwarung_label(kind)
    return (
        f"⚠︎ — NOTIFIED! LETHÉA {label} //\n"
        "…\n"
        f"❯ Status : Open\n"
        f"❯ Gate : {link}\n\n"
        "Sentuh pranala yang telah dihaturkan guna menapaki salah satu mahligai surga kami."
    )


def _openwarung_done_text(kind: str, sent_count: int, fail_count: int) -> str:
    label = _openwarung_label(kind)
    target = "member VIP aktif" if label == "RESORT" else "member aktif"
    return f"{label} telah dibuka. Notifikasi terkirim ke {sent_count} {target}. Gagal DM: {fail_count}."


def _openwarung_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Open Bar", callback_data="openwarung:choose:bar")],
        [InlineKeyboardButton("Open Resort", callback_data="openwarung:choose:resort")],
        [InlineKeyboardButton("Batalkan", callback_data="openwarung:cancel")],
    ])


def _shift_role_key_from_record(rec):
    role = (rec.get("staff_role") or "").strip().lower()
    if role in ("dj", "disc jockey", "disc_jockey"):
        return "dj"
    if role == "bartender":
        return "bartender"
    if role in ("strip dancer", "strip_dancer", "stripdancer"):
        return "strip_dancer"
    if role == "server":
        return "server"
    if role == "angel":
        return "angel"
    if role == "chef":
        return "chef"
    if role == "performer":
        return "performer"
    return None


def _shift_display_name(rec):
    username = rec.get("username")
    if username and username != "-":
        return f"@{username}"
    return rec.get("name") or f"Account {rec.get('acc_no', '-')}"


def _shift_session_key(chat_id: int) -> str:
    return str(chat_id)


def _shift_mode_label(session: dict) -> str:
    mode = (session or {}).get("mode") or "bar"
    return SHIFT_MODE_CONFIG.get(mode, {}).get("label", "Bar")


def _shift_allowed_roles(session: dict):
    roles = list((session or {}).get("allowed_roles") or [])
    if roles:
        return roles
    mode = (session or {}).get("mode") or "bar"
    return list(SHIFT_MODE_CONFIG.get(mode, {}).get("roles", []))


def _find_shift_member_role(session: dict, uid: int):
    uid = int(uid)
    for role_key, members in (session.get("attendees") or {}).items():
        if uid in [int(x) for x in members]:
            return role_key
    return None


def _shift_panel_keyboard(chat_id: int, is_open: bool = True):
    if not is_open:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join", callback_data=f"shiftjoin:{chat_id}")]])


async def _notify_shift_salary(context, uid: int, amount: int, role_key: str):
    if int(amount or 0) <= 0:
        return
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "💸 Salary Shift Masuk\n\n"
                f"Role : {SHIFT_ROLE_LABELS.get(role_key, role_key)}\n"
                f"Nominal : {_normalize_price_text(amount)} ✦𝕷"
            )
        )
    except Exception as e:
        print(f"[_notify_shift_salary] failed uid={uid}: {e}")


# =========================================================
# CHOICE POKER HELPERS
# =========================================================
CARD_SUITS = ["♠", "♥", "♦", "♣"]
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUE = {r: i + 2 for i, r in enumerate(CARD_RANKS)}
HAND_LABELS = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card",
}


def _choice_poker_room_key(chat_id: int) -> str:
    return str(chat_id)


def _new_deck():
    return [f"{r}{s}" for s in CARD_SUITS for r in CARD_RANKS]


def _card_rank(card: str) -> int:
    rank = card[:-1]
    return RANK_VALUE[rank]


def _format_cards(cards):
    return " ".join(cards)


def _card_to_text(card: str) -> str:
    return card


def _draw_cards(room: dict, n: int):
    deck = room.setdefault("deck", _new_deck())
    out = []
    for _ in range(n):
        if not deck:
            deck[:] = _new_deck()
        out.append(deck.pop(0))
    return out


def _choice_poker_shuffle_deck(room: dict):
    import random
    deck = _new_deck()
    random.shuffle(deck)
    room["deck"] = deck


def _evaluate_poker_hand(cards):
    values = sorted((_card_rank(c) for c in cards), reverse=True)
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    ordered = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    is_flush = len({c[-1] for c in cards}) == 1
    uniq = sorted(set(values), reverse=True)
    is_straight = False
    straight_high = max(values)
    if len(uniq) == 5 and uniq[0] - uniq[-1] == 4:
        is_straight = True
        straight_high = uniq[0]
    elif uniq == [14, 5, 4, 3, 2]:
        is_straight = True
        straight_high = 5

    if is_straight and is_flush:
        return (8, [straight_high])
    if ordered[0][1] == 4:
        four = ordered[0][0]
        kicker = max(v for v in values if v != four)
        return (7, [four, kicker])
    if ordered[0][1] == 3 and ordered[1][1] == 2:
        return (6, [ordered[0][0], ordered[1][0]])
    if is_flush:
        return (5, values)
    if is_straight:
        return (4, [straight_high])
    if ordered[0][1] == 3:
        trip = ordered[0][0]
        kickers = sorted((v for v in values if v != trip), reverse=True)
        return (3, [trip] + kickers)
    if ordered[0][1] == 2 and ordered[1][1] == 2:
        pair_hi = max(ordered[0][0], ordered[1][0])
        pair_lo = min(ordered[0][0], ordered[1][0])
        kicker = max(v for v in values if v not in (pair_hi, pair_lo))
        return (2, [pair_hi, pair_lo, kicker])
    if ordered[0][1] == 2:
        pair = ordered[0][0]
        kickers = sorted((v for v in values if v != pair), reverse=True)
        return (1, [pair] + kickers)
    return (0, values)


def _choice_poker_compare(player_cards, dealer_cards):
    player_score = _evaluate_poker_hand(player_cards)
    dealer_score = _evaluate_poker_hand(dealer_cards)
    if player_score > dealer_score:
        return 1, player_score, dealer_score
    if player_score < dealer_score:
        return -1, player_score, dealer_score
    return 0, player_score, dealer_score


def _choice_poker_turn_uid(room: dict):
    order = room.get("turn_order") or []
    if not order:
        return None
    idx = int(room.get("turn_index", 0)) % len(order)
    return order[idx]


def _choice_poker_next_turn(room: dict):
    order = room.get("turn_order") or []
    if order:
        room["turn_index"] = (int(room.get("turn_index", 0)) + 1) % len(order)


def _choice_poker_outstanding(room: dict, uid: str) -> int:
    p = room.get("players", {}).get(str(uid)) or {}
    return max(0, int(room.get("current_bet", 0)) - int(p.get("committed", 0)))


def _choice_poker_status_text(room):
    players = room.get("players", {})
    status = room.get('status', 'waiting').upper()
    lines = [
        "🔻… [ Choice Poker ]",
        "",
        f"• [] Status : {status}",
        f"• [] Host : {room.get('host_name', '-')}",
        "",
        "———— ╱╱ Player List :",
    ]

    if not players:
        lines.append("› -")
    else:
        for uid, p in players.items():
            result = p.get('result_label') or '-'
            lines.append(f"› {p.get('name', 'Player')} | {result}")

    if room.get('status') == 'waiting':
        lines.extend([
            "",
            "———— ╱╱ The Game Flow :",
            "O1. Pertandingan berlangsung 1 vs 1 antar pemain, dengan Asmoday sebagai dealer yang mengatur jalannya permainan.",
            "O2. Kedua pemain memasang taruhan awal menggunakan angka biasa sebagai open bet.",
            "O3. Asmoday kemudian membagikan 5 kartu secara tertutup kepada masing-masing pemain.",
            "O4. Asmoday kemudian membagikan 5 kartu secara tertutup kepada masing-masing pemain.",
            "O5. Besaran total taruhan menentukan pilihan arah permainan: Stronger atau Weaker.",
            "O6. Stronger mengikuti urutan ranking kartu normal, sedangkan Weaker membalik sistem tersebut — tangan dengan nilai terendah akan menjadi pemenang.",
        ])
    else:
        if room.get('choice_mode'):
            lines.extend(["", f"• [] Mode : {room.get('choice_mode').title()}"])
        turn_uid = _choice_poker_turn_uid(room)
        if room.get('status') == 'action' and turn_uid and str(turn_uid) in players:
            lines.extend(["", f"• [] Turn : {players[str(turn_uid)].get('name', 'Player')}"])
        if room.get('pending_raise_uid') and str(room.get('pending_raise_uid')) in players:
            lines.extend(["", f"• [] Awaiting Raise : {players[str(room.get('pending_raise_uid'))].get('name', 'Player')}"])
    return "\n".join(lines)

def _choice_poker_waiting_keyboard(host_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Join", callback_data="choicepoker:join"),
            InlineKeyboardButton("Leave", callback_data="choicepoker:leave"),
        ],
        [InlineKeyboardButton("Cancel", callback_data="choicepoker:cancel")],
    ])


def _choice_poker_swap_keyboard(room_chat_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data=f"choicepokerswap:{room_chat_id}:0"),
            InlineKeyboardButton("2", callback_data=f"choicepokerswap:{room_chat_id}:1"),
            InlineKeyboardButton("3", callback_data=f"choicepokerswap:{room_chat_id}:2"),
            InlineKeyboardButton("4", callback_data=f"choicepokerswap:{room_chat_id}:3"),
            InlineKeyboardButton("5", callback_data=f"choicepokerswap:{room_chat_id}:4"),
        ],
        [InlineKeyboardButton("🩸 Keep Hand", callback_data=f"choicepokerswap:{room_chat_id}:keep")],
    ])


def _choice_poker_action_keyboard(room_chat_id: int, room: dict, uid: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Raise", callback_data=f"choicepokeract:{room_chat_id}:raise"),
            InlineKeyboardButton("All-in", callback_data=f"choicepokeract:{room_chat_id}:allin"),
        ],
        [InlineKeyboardButton("Lock Bet", callback_data=f"choicepokeract:{room_chat_id}:lock")],
    ])
async def _choice_poker_send_room_message(context, room: dict, text: str, *, reply_to_room: bool = True, reply_markup=None):
    kwargs = {"chat_id": room.get("chat_id"), "text": text}
    thread_id = room.get("thread_id")
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    if reply_to_room and room.get("message_id"):
        kwargs["reply_to_message_id"] = room.get("message_id")
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    return await context.bot.send_message(**kwargs)


async def _choice_poker_refresh_message(context, chat_id: int, room: dict):
    message_id = room.get("message_id")
    if not message_id:
        return

    reply_markup = None
    if room.get("status") == "waiting":
        reply_markup = _choice_poker_waiting_keyboard(room.get("host_id"))
    elif room.get("status") == "action":
        turn_uid = _choice_poker_turn_uid(room)
        if turn_uid:
            reply_markup = _choice_poker_action_keyboard(chat_id, room, str(turn_uid))

    text_value = _choice_poker_status_text(room)
    markup_value = reply_markup.to_dict() if reply_markup else None
    if room.get("_last_render_text") == text_value and room.get("_last_render_markup") == markup_value:
        return

    kwargs = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text_value,
        "reply_markup": reply_markup,
    }

    try:
        await context.bot.edit_message_text(**kwargs)
        room["_last_render_text"] = text_value
        room["_last_render_markup"] = markup_value
    except Exception as e:
        if "message is not modified" in str(e).lower():
            room["_last_render_text"] = text_value
            room["_last_render_markup"] = markup_value
            return
        print(f"[_choice_poker_refresh_message] error: {e}")


async def _choice_poker_begin_action_phase(context, chat_id: int, room: dict):
    room['status'] = 'action'
    players = room.get('players', {})
    order = list(players.keys())
    order.sort(key=lambda x: int(x) != int(room.get('host_id')))
    room['turn_order'] = order
    room['turn_index'] = 0
    room['pending_raise_uid'] = None
    room['chooser_uid'] = None
    room['choice_mode'] = None
    for p in players.values():
        p['locked'] = False
    await _choice_poker_refresh_message(context, chat_id, room)
    turn_uid = _choice_poker_turn_uid(room)
    if turn_uid and turn_uid in players:
        await _choice_poker_send_room_message(
            context,
            room,
            f"🎭 Fase taruhan dimulai. Giliran {players[turn_uid].get('name')}: raise, all-in, atau lock taruhan.",
            reply_markup=_choice_poker_action_keyboard(chat_id, room, turn_uid),
        )
async def _choice_poker_finish(context, chat_id: int, room: dict):
    players = room.get('players', {})
    order = list(players.keys())
    lines = ["🃏 — Showdown Choice Poker", ""]
    if room.get('choice_mode'):
        lines.append(f"Mode: {room.get('choice_mode').title()}")
        lines.append("")
    for uid in order:
        p = players[uid]
        result = p.get("result")
        if not result:
            continue
        lines.append(
            f"• {p.get('name')}\n"
            f"  Open bet : {p.get('bet', 0)}\n"
            f"  Total bet : {p.get('committed', 0)}\n"
            f"  Kartu : {_format_cards(result['player_cards'])} ({result['player_label']})\n"
            f"  Hasil : {result['outcome']}\n"
            f"  Saldo sekarang : {p.get('balance_after', 0)}"
        )
        lines.append("")

    room['status'] = 'resolved'
    await _choice_poker_refresh_message(context, chat_id, room)
    await _choice_poker_send_room_message(context, room, "\n".join(lines).strip())
    CHOICE_POKER_ROOMS.pop(_choice_poker_room_key(chat_id), None)
async def _choice_poker_finish_fold(context, chat_id: int, room: dict, winner_uid: str, loser_uid: str):
    return
async def _choice_poker_resolve_showdown(context, chat_id: int, room: dict):
    players = room.get('players', {})
    order = list(players.keys())
    if len(order) != 2:
        return
    a_uid, b_uid = order[0], order[1]
    a = players[a_uid]
    b = players[b_uid]
    cmp_result, a_score, b_score = _choice_poker_compare(a.get('player_cards') or [], b.get('player_cards') or [])
    mode = (room.get('choice_mode') or 'stronger').lower()
    if mode == 'weaker':
        cmp_result = -cmp_result

    a_rec = _get_existing_account(int(a_uid))
    b_rec = _get_existing_account(int(b_uid))
    a_comm = int(a.get('committed', 0))
    b_comm = int(b.get('committed', 0))
    pot = a_comm + b_comm

    # Gunakan saldo awal ronde agar hasil akhir konsisten dengan logika "pot".
    # Jadi winner menerima seluruh pot, loser kehilangan total committed miliknya.
    a_start = int(a.get('stack_total', a_rec.get('balance', 0) if a_rec else 0))
    b_start = int(b.get('stack_total', b_rec.get('balance', 0) if b_rec else 0))

    if cmp_result == 0:
        a_final = a_start
        b_final = b_start
        a_outcome = f'Seri — pot {pot} dikembalikan'
        b_outcome = f'Seri — pot {pot} dikembalikan'
    elif cmp_result > 0:
        a_final = a_start - a_comm + pot
        b_final = b_start - b_comm
        a_outcome = f"Menang pot {pot} (net +{pot - a_comm})"
        b_outcome = f"Kalah -{b_comm}"
    else:
        a_final = a_start - a_comm
        b_final = b_start - b_comm + pot
        a_outcome = f"Kalah -{a_comm}"
        b_outcome = f"Menang pot {pot} (net +{pot - b_comm})"

    if a_rec:
        a_rec['balance'] = max(0, a_final)
        a['balance_after'] = a_rec['balance']
    else:
        a['balance_after'] = max(0, a_final)

    if b_rec:
        b_rec['balance'] = max(0, b_final)
        b['balance_after'] = b_rec['balance']
    else:
        b['balance_after'] = max(0, b_final)

    a['result'] = {
        'player_cards': a.get('player_cards') or [],
        'player_label': HAND_LABELS[a_score[0]],
        'outcome': a_outcome,
    }
    b['result'] = {
        'player_cards': b.get('player_cards') or [],
        'player_label': HAND_LABELS[b_score[0]],
        'outcome': b_outcome,
    }
    save_accounts()
    await _choice_poker_finish(context, chat_id, room)

def _choice_poker_choice_keyboard(room_chat_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Stronger", callback_data=f"choicepokerchoice:{room_chat_id}:stronger"),
            InlineKeyboardButton("Weaker", callback_data=f"choicepokerchoice:{room_chat_id}:weaker"),
        ]
    ])


async def _choice_poker_begin_choice_phase(context, chat_id: int, room: dict):
    players = room.get('players', {})
    order = list(players.keys())
    if len(order) != 2:
        return
    a_uid, b_uid = order[0], order[1]
    a_comm = int(players[a_uid].get('committed', 0))
    b_comm = int(players[b_uid].get('committed', 0))
    room['status'] = 'choice'
    room['pending_raise_uid'] = None
    if a_comm > b_comm:
        chooser_uid = a_uid
    elif b_comm > a_comm:
        chooser_uid = b_uid
    else:
        chooser_uid = None
    room['chooser_uid'] = chooser_uid
    room['choice_mode'] = None
    await _choice_poker_refresh_message(context, chat_id, room)
    if chooser_uid:
        chooser = players[chooser_uid]
        await _choice_poker_send_room_message(context, room, f"🃏 Total taruhan lebih besar milik {chooser.get('name')}. Dia berhak memilih Stronger atau Weaker.")
        try:
            await context.bot.send_message(
                chat_id=int(chooser_uid),
                text=(
                    f"⌜ Choice Poker — Final Choice ⌟\n"
                    f"Total taruhanmu: {players[chooser_uid].get('committed', 0)}\n"
                    f"Lawan: {players[b_uid if chooser_uid == a_uid else a_uid].get('name')}\n\n"
                    "Pilih mode ronde: Stronger atau Weaker."
                ),
                reply_markup=_choice_poker_choice_keyboard(chat_id),
            )
        except Exception:
            await _choice_poker_send_room_message(context, room, f"⚠️ DM ke {chooser.get('name')} gagal. Pilih langsung dari tombol berikut.", reply_markup=_choice_poker_choice_keyboard(chat_id))
    else:
        room['choice_mode'] = 'stronger'
        await _choice_poker_send_room_message(context, room, 'Jumlah taruhan kedua pihak seimbang. Tanpa adanya keunggulan taruhan, ronde akan ditentukan dengan sistem Stronger secara otomatis.')
        await _choice_poker_resolve_showdown(context, chat_id, room)

# =========================================================
# PROOF HELPERS
# =========================================================
def _proof_label(flow):
    flow_type = flow.get("flow_type")

    if flow_type == "renewal":
        return "Membership Renewal"
    if flow_type == "upgrade_vip":
        return "Upgrade Plan VIP"
    if flow.get("kind") == "membership":
        return "Membership Registration"
    if flow.get("kind") == "media_partner":
        return "Media Partner"
    if flow.get("kind") == "sponsorship":
        return "Sponsorship"
    if flow.get("kind") == "pengurus":
        return "Staff Registration"
    return "Submission"


def _build_proof_keyboard(flow):
    proof_items = flow.get("proof_items", [])
    keyboard = []

    for i in range(len(proof_items)):
        keyboard.append([
            InlineKeyboardButton(f"Ubah Bukti {i + 1}", callback_data=f"proofedit:replace:{i}"),
            InlineKeyboardButton(f"Hapus Bukti {i + 1}", callback_data=f"proofedit:delete:{i}"),
        ])

    keyboard.append([
        InlineKeyboardButton("Tambah Bukti", callback_data="proofedit:add")
    ])

    if proof_items:
        keyboard.append([
            InlineKeyboardButton("Kirim Pengajuan", callback_data="proofdone:yes")
        ])

    return InlineKeyboardMarkup(keyboard)


def _build_proof_summary_text(flow):
    proof_items = flow.get("proof_items", [])
    replace_index = flow.get("replace_index")

    lines = [
        f"⌜{_proof_label(flow)}⌟",
        "",
        "Bukti pembayaranmu, kelolalah ia pada ruang yang tersaji di bawah ini.",
        "Tambahkan, perbarui, atau hapuslah semaumu, sebelum ia dihaturkan kepada Currathor.",
        "",
    ]

    if replace_index is not None:
        lines.append(f"Mode kini: penggantian Bukti {replace_index + 1}")
        lines.append("Haturkan satu citra, entah rupa atau berkas bergambar, sebagai pengganti bagi bukti tersebut.")
        lines.append("")

    if not proof_items:
        lines.append("Belum jua ada bukti yang tersampaikan.")
    else:
        lines.append("Jejak bukti yang tersimpan:")
        for i in range(len(proof_items)):
            lines.append(f"• Bukti {i + 1} telah tersedia.")

    lines.append("")
    lines.append("Tentukan pilihanmu melalui titah yang terhampar di bawah ini.")

    return "\n".join(lines)


async def _refresh_proof_summary_message(context, chat_id: int, flow: dict):
    summary_message_id = flow.get("proof_summary_message_id")
    text = _build_proof_summary_text(flow)
    reply_markup = _build_proof_keyboard(flow)

    if summary_message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=summary_message_id,
                text=text,
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass

    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )
    flow["proof_summary_message_id"] = sent.message_id


async def _start_proof_upload_flow(context, chat_id: int, flow: dict):
    flow["step"] = "upload_proof"
    flow.setdefault("proof_items", [])
    flow["replace_index"] = None
    await _refresh_proof_summary_message(context, chat_id, flow)


# =========================================================
# SEND HELPERS
# =========================================================
async def send_public_safe(context: ContextTypes.DEFAULT_TYPE, text: str, reply_to=None):
    try:
        sent = await context.bot.send_message(chat_id=FORWARD_PUBLIC_CHAT_ID, text=text)
        return sent
    except Exception as e:
        print(f"[PUBLIC SEND ERROR] {e}")
        if reply_to:
            try:
                await reply_to.reply_text(
                    "Pesan gagal menyeberang menuju ruang Currathor/publik.\n"
                    "Pastikan Asmoday berada di sana dan diberi hak untuk mengirimkan pesan."
                )
            except Exception:
                pass
        return None


# =========================================================
# EXPIRE WATCHER
# =========================================================
async def membership_expiry_watcher(context: ContextTypes.DEFAULT_TYPE):
    changed = False

    for uid_str, rec in ACCOUNTS.items():
        _normalize_account_record(int(uid_str), rec)

        if rec.get("account_type") in ("staff", "owner"):
            continue

        prev_status = rec.get("membership_status", "deactive")
        _refresh_membership_status(rec)
        new_status = rec.get("membership_status", "deactive")

        expires_at = _parse_dt(rec.get("membership_expires_at"))
        notified_at = rec.get("last_expiry_notified_at")

        if expires_at and expires_at <= _now() and new_status == "deactive":
            if not notified_at:
                try:
                    await context.bot.send_message(
                        chat_id=int(uid_str),
                        text=(
                            "⌜ Membership Notice ⌟\n"
                            "Masa keanggotaanmu telah usai.\n\n"
                            f"Package : {rec.get('membership_type') or '-'}\n"
                            f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
                            "Perbaruilah keanggotaanmu melalui menu yang tersedia pada ku, agar ikatan itu kembali terjaga."
                        )
                    )
                    rec["last_expiry_notified_at"] = _now().strftime("%Y-%m-%d | %H:%M")
                    changed = True
                except Exception as e:
                    print(f"[expiry notify failed] uid={uid_str} error={e}")

        if prev_status != new_status:
            changed = True

    if changed:
        save_accounts()


# =========================================================
# BOT UI SETUP
# =========================================================
async def post_init(application):
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "Open menu"),
            BotCommand("menu", "Open menu"),
            BotCommand("registration", "Open registration menu"),
            BotCommand("registrationstaff", "Send staff application form"),
            BotCommand("oprecstaff", "Open staff interview schedule"),
            BotCommand("renewal", "Renew current plan"),
            BotCommand("upgradevip", "Upgrade Regular plan to VIP"),
            BotCommand("myacc", "Show Lethéa ID card"),
            BotCommand("changeidcphoto", "Change IDC photo"),
            BotCommand("changepict", "Change IDC photo"),
            BotCommand("changefullname", "Change IDC full name"),
            BotCommand("mybalance", "Check Luxen balance"),
            BotCommand("mystafflog", "Check CNIT and shift log"),
            BotCommand("setnitroid", "Set NitroSeen ID"),
            BotCommand("claimcnit", "Claim CNIT payout"),
            BotCommand("changecodename", "Change your codename"),
            BotCommand("cancel", "Cancel current session"),
            BotCommand("help", "Show help"),
            BotCommand("choicepoker", "Create Choice Poker room"),
            BotCommand("poker", "Create Texas Hold'em room"),
            BotCommand("blackjack", "Create Blackjack table"),
            BotCommand("booray", "Create Booray table"),
            BotCommand("dicepoker", "Create Dice Poker table"),
            BotCommand("symphony", "Create The Alluring Symphony room"),
            BotCommand("chess", "Create Chess room"),
            BotCommand("joinchess", "Join Chess room"),
            BotCommand("chessstart", "Start Chess match"),
            BotCommand("chessclose", "Close Chess room"),
            BotCommand("letheamenu", "Show rolled Lethéa menu"),
            BotCommand("openwarung", "Open Bar/Resort and DM members"),
            BotCommand("broadcast", "Broadcast to started users"),
            BotCommand("openbar", "Open bar and DM active members"),
            BotCommand("openresort", "Open resort and DM VIP members"),
            BotCommand("opencurated", "Open curated dining"),
            BotCommand("listcurated", "List curated dining"),
            BotCommand("closecurated", "Close curated dining"),
            BotCommand("delcurated", "Delete curated dining"),
            BotCommand("addcmd", "Add custom command"),
            BotCommand("listcmd", "List custom commands"),
            BotCommand("delcmd", "Delete custom command by number"),
            BotCommand("rentangel", "Browse and rent Angel"),
            BotCommand("tagall", "Tag all started users in group"),
            BotCommand("tagmember", "Tag members in group"),
            BotCommand("tagvip", "Tag active VIP members in group"),
            BotCommand("tagregular", "Tag active Regular members in group"),
            BotCommand("tagstaff", "Tag staff in group"),
            BotCommand("tagcurrathor", "Tag Currathors in group"),
            BotCommand("tagserver", "Tag Servers in group"),
            BotCommand("tagdj", "Tag DJs in group"),
            BotCommand("tagbartender", "Tag Bartenders in group"),
            BotCommand("tagangel", "Tag Angels in group"),
            BotCommand("tagstripdancer", "Tag Strip Dancers in group"),
            BotCommand("tagchef", "Tag Chefs in group"),
            BotCommand("tagperformer", "Tag Performers in group"),
            BotCommand("topup", "Top up Luxen reward"),
            BotCommand("openevent", "Open internal event reward"),
            BotCommand("closeevent", "Close internal event reward"),
        ], scope=BotCommandScopeDefault())
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        await application.bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
    except Exception as e:
        print(f"[post_init] error: {e}")
    except Exception as e:
        print(f"[post_init] error: {e}")

# =========================================================
# FEATURE: START / MAIN MENU
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    _remember_started_user(update.effective_user)
    _ensure_owner_account(update.effective_user)
    await _sync_private_commands_for_user(context, update.effective_user)
    await menu(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    _ensure_owner_account(update.effective_user)
    await _sync_private_commands_for_user(context, update.effective_user)

    keyboard = [
        [
            InlineKeyboardButton("Perihal Lethéa", url=OXANA_INFO_URL),
            InlineKeyboardButton("Kritik dan Saran", callback_data="menu:kritik"),
        ],
        [
            InlineKeyboardButton("Bisikan tanpa nama", callback_data="menu:menfess"),
            InlineKeyboardButton("Panggil Asmoday", callback_data="menu:talk"),
        ],
        [
            InlineKeyboardButton("Registration", callback_data="menu:registration"),
            InlineKeyboardButton("Renewal", callback_data="menu:renewal"),
        ],
        [
            InlineKeyboardButton("Upgrade Plan VIP", callback_data="menu:upgradevip"),
        ],
    ]

    text = (
        "𖠷 ╱ .. Tentukanlah pilihan di hadapanmu, sebab tiap jalur menyimpan makna tersendiri.\n\n"
        "：！𝐏𝐞𝐫𝐢𝐡𝐚𝐥 𝐋𝐞𝐭𝐡𝐞́𝐚 : selayang pandang tentang Lethéa\n"
        "：！𝐊𝐫𝐢𝐭𝐢𝐤 𝐝𝐚𝐧 𝐒𝐚𝐫𝐚𝐧 : titipkan suara dan rasa\n"
        "：！𝐁𝐢𝐬𝐢𝐤𝐚𝐧 𝐭𝐚𝐧𝐩𝐚 𝐧𝐚𝐦𝐚 : utarakan pesan tanpa jejak\n"
        "：！𝐏𝐚𝐧𝐠𝐠𝐢𝐥 𝐀𝐬𝐦𝐨𝐝𝐚𝐲 : sampaikan pesan kepada penguasa\n"
        "：！𝐑𝐞𝐠𝐢𝐬𝐭𝐫𝐚𝐭𝐢𝐨𝐧 : mulai ikatan sebagai member / pengurus / mitra\n"
        "：！𝐑𝐞𝐧𝐞𝐰𝐚𝐥 : lanjutkan masa yang kau miliki\n"
        "：！𝐔𝐩𝐠𝐫𝐚𝐝𝐞 𝐏𝐥𝐚𝐧 𝐕𝐈𝐏 : naikkan derajat menuju VIP"
    )

    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# FEATURE: SEMI APP NAVIGATION
# =========================================================
async def semi_app_nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    user = query.from_user
    _ensure_owner_account(user)
    await _sync_private_commands_for_user(context, user)
    rec = _get_existing_account(user.id)
    data = query.data or ""

    if data == "nav:home":
        await query.edit_message_text(_home_dashboard_text(user, rec), reply_markup=_home_dashboard_keyboard())
        return
    if data == "nav:account":
        await query.edit_message_text(_account_screen_text(user, rec), reply_markup=_account_screen_keyboard())
        return
    if data == "nav:membership":
        await query.edit_message_text(_membership_screen_text(user, rec), reply_markup=_membership_screen_keyboard(rec))
        return
    if data == "nav:lethea":
        await query.edit_message_text(_lethea_screen_text(user, rec), reply_markup=_lethea_screen_keyboard(user, rec))
        return
    if data == "nav:support":
        await query.edit_message_text(_support_screen_text(), reply_markup=_support_screen_keyboard())
        return
    if data == "nav:help":
        await query.edit_message_text(_help_screen_text(user), reply_markup=_help_screen_keyboard())
        return
    if data == "nav:account:codename":
        await query.answer("Ucapkan titah /changecodename NamaBaru di ruang ini, agar namamu beralih rupa.", show_alert=True)
        return


async def semi_app_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    user = query.from_user
    _ensure_owner_account(user)
    await _sync_private_commands_for_user(context, user)
    rec = _get_existing_account(user.id)
    data = (query.data or "").split(":", 1)
    if len(data) != 2:
        return
    action = data[1]

    if action == "registration":
        keyboard = [
            [InlineKeyboardButton("Membership", callback_data="reg:choose:membership")],
            [InlineKeyboardButton("Staff Registration", callback_data="reg:choose:pengurus")],
            [InlineKeyboardButton("Media Partner", callback_data="reg:choose:media_partner")],
            [InlineKeyboardButton("Sponsorship", callback_data="reg:choose:sponsorship")],
            [InlineKeyboardButton("← Back", callback_data="nav:membership")],
        ]
        await query.edit_message_text(
            "𖠷 ╱ .. Lethéa Registration\n\nTentukanlah ikatan yang hendak kau rajut di ambang Lethéa.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if action == "renewal":
        if not rec or rec.get("account_type") != "member" or not rec.get("membership_type"):
            await query.answer("Tiada keanggotaan yang tersemat padamu untuk diperpanjang.", show_alert=True)
            return
        info = (
            f"𖠷 ╱ .. Membership Renewal\n\n"
            f"Perpanjangan ini menapak pada ikatan yang telah kau genggam. Ia dapat kau pilih, bahkan sebelum batas waktunya luruh.\n\n"
            f"Account Number : {rec.get('acc_no', '-')}\n"
            f"Current Package : {rec.get('membership_type')}\n"
            f"Current Status : {_refresh_membership_status(rec)}\n"
            f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
            "Sentuhlah pilihan di bawah untuk melanjutkan perpanjangan."
        )
        await query.edit_message_text(
            info,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Perpanjang {rec.get('membership_type')}", callback_data="renew:start")],
                [InlineKeyboardButton("Kembali", callback_data="nav:membership")],
            ]),
        )
        return

    if action == "upgradevip":
        if not rec or rec.get("account_type") != "member" or rec.get("membership_type") != "Regular":
            await query.answer("Peningkatan menuju VIP hanya diperuntukkan bagi mereka yang bernaung dalam keanggotaan Regular.", show_alert=True)
            return
        info = (
            f"𖠷 ╱ .. Upgrade Plan VIP\n\n"
            f"Di sinilah langkahmu beralih, dari Regular menuju derajat VIP.\n"
            f"Waktu yang kau genggam akan bertambah, seiring durasi dalam naungan barunya.\n\n"
            f"Account Number : {rec.get('acc_no', '-')}\n"
            f"Current Package : {rec.get('membership_type')}\n"
            f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
            "Raih pilihan di bawah untuk menapaki kenaikan ini."
        )
        await query.edit_message_text(
            info,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Beralih ke VIP", callback_data="upgrade:start")],
                [InlineKeyboardButton("Kembali", callback_data="nav:membership")],
            ]),
        )
        return

    if action == "letheamenu":
        await query.edit_message_text(
            _format_rolled_menu_text(),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="nav:lethea")]]),
        )
        return

    if action == "choicepoker":
        await query.answer("Ucapkan /choicepoker di ruang ini, agar gelanggang permainan terbuka.", show_alert=True)
        return

    if action == "rentangel":
        if not _can_rent_angel(user, rec):
            await query.answer("Hanya mereka yang berstatus VIP aktif atau menyandang gelar Currathor yang diperkenankan.", show_alert=True)
            return
        angels = _angel_staff_records()
        if not angels:
            await query.answer("Tiada Angel yang tersedia saat ini.", show_alert=True)
            return
        await query.edit_message_text(
            "𖠷 ╱ .. 𝐋𝐄𝐓𝐇𝐄́𝐀: 𝐑𝐄𝐍𝐓 𝐀𝐍𝐆𝐄𝐋\n\nPilihlah Angel dari rupa yang akan segera tersingkap di hadapanmu.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kembali", callback_data="nav:lethea")]]),
        )
        sent_any = False
        for uid, angel_rec in angels:
            profile = _ensure_angel_profile(uid)
            if not profile.get("image_file_id"):
                continue
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=profile.get("image_file_id"),
                    caption=_angel_display_name(angel_rec),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Detail", callback_data=f"angelview:detail:{uid}")]]),
                )
                sent_any = True
            except Exception as e:
                print(f"[semi rent angel] send photo error: {e}")
        if not sent_any:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Belum ada rupa Angel yang lengkap untuk kutampilkan.")
        return

    if action == "kritik":
        context.user_data["menu_mode"] = "kritik"
        await query.edit_message_text("𖠷 ╱ .. Titipkan suara dan kesanmu di sini.\nJika ingin mengurungkan niat, gunakan /cancel")
        return

    if action == "menfess":
        context.user_data["menu_mode"] = "menfess"
        await query.edit_message_text(
            "𖠷 ╱ .. Titipkan rasa yang enggan terucap, biarlah aku yang menyampaikan pada yang kau tuju .♡\n\n"
            "Format\n"
            "• Dari: (boleh kosong/anonim)\n"
            "• Kepada: (nama/username)\n"
            "• Pesan: …"
        )
        return

    if action == "talk":
        context.user_data["talk_mode"] = True
        await query.edit_message_text(
            "𖠷 ╱ .. Asmoday telah terpanggil. Bisikan apa yang tersimpan di benakmu. Gunakan /stoptalk untuk mengakhiri."
        )
        return
# =========================================================
# FEATURE: REGISTRATION / RENEWAL / UPGRADE
# =========================================================
async def registration_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    keyboard = [
        [InlineKeyboardButton("Membership", callback_data="reg:choose:membership")],
        [InlineKeyboardButton("Staff Registration", callback_data="reg:choose:pengurus")],
        [InlineKeyboardButton("Media Partner", callback_data="reg:choose:media_partner")],
        [InlineKeyboardButton("Sponsorship", callback_data="reg:choose:sponsorship")],
    ]
    await update.message.reply_text(
        "𖠷 ╱ .. Lethéa Registration\n\nTentukanlah ikatan yang hendak kau pintal dalam naungan Lethéa.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def registration_staff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _is_staff_oprec_open():
        await update.message.reply_text(_staff_oprec_closed_text())
        return
    context.user_data["registration_flow"] = {
        "flow_type": "staff_form",
        "kind": "pengurus",
        "package": None,
        "step": "fill_form",
        "needs_proof": False,
        "proof_items": [],
        "proof_summary_message_id": None,
        "form_data": "",
        "replace_index": None,
    }

    text = (
        "<b>／  ⟢ › STAFF REGISTRATION .. !</b>\n"
        "───\n"
        "Sila isi perihal data diri yang tersedia, lalu titipkan kembali padaku.\n\n"
        "<pre>\n"
        "› Nama Lengkap :\n"
        "› Username :\n"
        "› Pilihan Jabatan : (diperbolehkan dua)\n"
        "</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def renewal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    rec = _get_existing_account(user.id)

    if not rec or rec.get("account_type") != "member":
        await update.message.reply_text("ⓘ Tiada ikatan aktif yang tersandang atas namamu dalam lingkup ini.")
        return

    package = rec.get("membership_type")
    if not package:
        await update.message.reply_text("ⓘ Tiada masa yang dapat kau lanjutkan, sebab ikatan itu belum pernah ada.")
        return

    info = (
        "𖠷 ╱ .. Membership Renewal\n\n"
        "Perpanjangan ini menapak pada ikatan yang telah kau genggam. Ia dapat kau pilih, bahkan sebelum batas waktunya luruh.\n\n"
        f"Account Number : {rec.get('acc_no', '-')}\n"
        f"Current Package : {package}\n"
        f"Current Status : {_refresh_membership_status(rec)}\n"
        f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
        "Sentuhlah pilihan di bawah untuk melanjutkan perpanjangan."
    )

    keyboard = [
        [InlineKeyboardButton(f"Renew {package}", callback_data="renew:start")],
    ]
    await update.message.reply_text(info, reply_markup=InlineKeyboardMarkup(keyboard))


async def upgrade_vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    rec = _get_existing_account(user.id)

    if not rec or rec.get("account_type") != "member":
        await update.message.reply_text("ⓘ Namamu belum terdaftar dalam lingkup ikatan sistem ini.")
        return

    current_package = rec.get("membership_type")
    if current_package != "Regular":
        await update.message.reply_text("ⓘ VIP tak terbuka selain bagi pengemban ikatan Regular.")
        return

    info = (
        "𖠷 ╱ .. Upgrade Plan VIP\n\n"
        "Di sinilah langkahmu beralih, dari Regular menuju derajat VIP.\n"
        "Waktu yang kau genggam akan bertambah, seiring durasi dalam naungan barunya.\n\n"
        f"Account Number : {rec.get('acc_no', '-')}\n"
        f"Current Package : {current_package}\n"
        f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
        "Sentuhlah pilihan di bawah untuk menapaki kenaikan ini."
    )

    keyboard = [
        [InlineKeyboardButton("Upgrade to VIP", callback_data="upgrade:start")],
    ]
    await update.message.reply_text(info, reply_markup=InlineKeyboardMarkup(keyboard))


def _approval_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ACC", callback_data="approve:acc"),
            InlineKeyboardButton("Reject", callback_data="approve:reject"),
        ]
    ])


# =========================================================
# MENU CALLBACK
# =========================================================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()

    _, kind = query.data.split(":", 1)

    user = query.from_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)

    context.user_data.pop("menu_mode", None)
    context.user_data.pop("registration_flow", None)

    if kind == "kritik":
        context.user_data["menu_mode"] = "kritik"
        await query.edit_message_text(
            "𖠷 ╱ .. Titipkan kritik dan saranmu di sini.\n"
            "Kalau ingin batal, gunakan /cancel"
        )
        return

    if kind == "menfess":
        context.user_data["menu_mode"] = "menfess"
        await query.edit_message_text(
            "Titipkan pesan anonim yang ingin kamu sampaikan.\n\n"
            "Format bebas, atau bisa pakai contoh ini:\n"
            "• Dari: Anonim\n"
            "• Kepada: Nama/Username\n"
            "• Pesan: ...\n\n"
            "Kalau ingin batal, gunakan /cancel"
        )
        return

    if kind == "talk":
        context.user_data["talk_mode"] = True
        await query.edit_message_text(
            "𐂗 ``Asmoday hadir.\n"
            "Segala ucapan akan ia dengar dan jawab. Jika usai, gunakan /stoptalk.``\n\n"
        )
        return

    if kind == "registration":
        keyboard = [
            [InlineKeyboardButton("Membership", callback_data="reg:choose:membership")],
            [InlineKeyboardButton("Staff Registration", callback_data="reg:choose:pengurus")],
            [InlineKeyboardButton("Media Partner", callback_data="reg:choose:media_partner")],
            [InlineKeyboardButton("Sponsorship", callback_data="reg:choose:sponsorship")],
        ]
        await query.edit_message_text(
            "𖠷╱ .. Lethéa Registration\n\nSila dipilih jenis pendaftaran.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if kind == "renewal":
        if not rec or rec.get("account_type") != "member":
            await query.edit_message_text("Belum ada jejak account member atas namamu di tatanan ini.")
            return

        package = rec.get("membership_type")
        if not package:
            await query.edit_message_text("ⓘ Belum ada package membership yang dapat kau lanjutkan.")
            return

        info = (
            "𖠷 ╱ .. Membership Renewal\n\n"
            "Renewal mengikuti package yang kamu miliki saat ini.\n"
            "Renewal bisa dilakukan meskipun membership belum expired.\n\n"
            f"Account Number : {rec.get('acc_no', '-')}\n"
            f"Current Package : {package}\n"
            f"Current Status : {_refresh_membership_status(rec)}\n"
            f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
            "Tekan tombol di bawah untuk lanjut renewal."
        )
        keyboard = [
            [InlineKeyboardButton(f"Renew {package}", callback_data="renew:start")],
        ]
        await query.edit_message_text(info, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if kind == "upgradevip":
        if not rec or rec.get("account_type") != "member":
            await query.edit_message_text("❌ Belum ada jejak account member atas namamu di tatanan ini.")
            return

        current_package = rec.get("membership_type")
        if current_package != "Regular":
            await query.edit_message_text("ⓘ Jalan menuju VIP hanya terbuka bagi pemegang Regular.")
            return

        info = (
            "𖠷 ╱ .. Upgrade Plan VIP\n\n"
            "Fitur ini digunakan untuk pindah package dari Regular ke VIP.\n"
            "Masa aktif akan ditambahkan sesuai durasi VIP.\n\n"
            f"Account Number : {rec.get('acc_no', '-')}\n"
            f"Current Package : {current_package}\n"
            f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}\n\n"
            "Tekan tombol di bawah untuk lanjut upgrade."
        )
        keyboard = [
            [InlineKeyboardButton("Upgrade to VIP", callback_data="upgrade:start")],
        ]
        await query.edit_message_text(info, reply_markup=InlineKeyboardMarkup(keyboard))
        return


# =========================================================
# REGISTRATION / RENEWAL / UPGRADE CALLBACK
# =========================================================
async def registration_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()

    user = query.from_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)
    data = query.data or ""

    if data.startswith("reg:choose:"):
        kind = data.split(":")[2]

        if kind == "membership":
            text = (
                "<b>／  ⟢ › MEMBER REGISTRATION .. !</b>\n"
                "───\n"
                "🔻Perihal Membership:\n\n"
                "<pre>\n"
                "› VIP : Masa berlaku selama 30 hari\n"
                "› Regular : Masa berlaku selama 14 hari\n"
                "</pre>\n"
                "<i>﴾ …. ﴿ :</i>\n"
                "<i>Selagi masa itu belum luruh, tiada kewajiban upeti atas akses yang tersaji. "
                "Sila dipilih membership yang hendak kau emban:</i>"
            )
            keyboard = [
                [InlineKeyboardButton("VIP", callback_data="reg:pkg:VIP")],
                [InlineKeyboardButton("Regular", callback_data="reg:pkg:Regular")],
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            return

        if kind == "pengurus":
            if not _is_staff_oprec_open():
                await query.edit_message_text(_staff_oprec_closed_text())
                return
            context.user_data["registration_flow"] = {
                "flow_type": "staff_form",
                "kind": "pengurus",
                "package": None,
                "step": "fill_form",
                "needs_proof": False,
                "proof_items": [],
                "proof_summary_message_id": None,
                "form_data": "",
                "replace_index": None,
            }
            text = (
                "<b>／  ⟢ › STAFF REGISTRATION .. !</b>\n"
                "───\n"
                "Sila isi perihal data diri yang tersedia, lalu titipkan kembali padaku.\n\n"
                "<pre>\n"
                "› Nama Lengkap :\n"
                "› Username :\n"
                "› Pilihan Jabatan : (diperbolehkan dua)\n"
                "</pre>"
            )
            await query.edit_message_text(text, parse_mode="HTML")
            return

        if kind == "media_partner":
            context.user_data["registration_flow"] = {
                "flow_type": "registration",
                "kind": "media_partner",
                "package": None,
                "step": "fill_form",
                "needs_proof": False,
                "proof_items": [],
                "proof_summary_message_id": None,
                "form_data": "",
                "replace_index": None,
            }
            form = (
                "<b>／  ⟢ › MEDIA PARTNER REGISTRATION .. !</b>\n"
                "───\n"
                "Sila isi perihal data diri yang tersedia, lalu titipkan kembali padaku.\n\n"
                "<pre>\n"
                "› Nama Instansi :\n"
                "› Link Channel/Fanpage :\n"
                "› Perwakilan :\n"
                "  ①. Nama + Username\n"
                "  ②. Nama + Username\n"
                "</pre>"
            )
            await query.edit_message_text(form, parse_mode="HTML")
            return

        if kind == "sponsorship":
            context.user_data["registration_flow"] = {
                "flow_type": "registration",
                "kind": "sponsorship",
                "package": None,
                "step": "fill_form",
                "needs_proof": False,
                "proof_items": [],
                "proof_summary_message_id": None,
                "form_data": "",
                "replace_index": None,
            }
            form = (
                "<b>／  ⟢ › SPONSORSHIP REGISTRATION .. !</b>\n"
                "───\n"
                "Sila isi perihal data diri yang tersedia, lalu titipkan kembali padaku.\n\n"
                "<pre>\n"
                "› Nama Instansi :\n"
                "› Link Channel/Fanpage :\n"
                "› Pilihan Sponsorship :\n"
                "› Perwakilan :\n"
                "  ①. Nama + Username\n"
                "  ②. Nama + Username\n"
                "</pre>"
            )
            await query.edit_message_text(form, parse_mode="HTML")
            return

    if data.startswith("reg:pkg:"):
        package = data.split(":")[2]

        if rec and rec.get("account_type") == "member":
            await query.edit_message_text(
                "ⓘ Ikatan telah tersandang atas namamu. Untuk melanjutkan, gunakan Renewal atau tempuh Upgrade Plan VIP untuk beranjak."
            )
            return

        context.user_data["registration_flow"] = {
            "flow_type": "registration",
            "kind": "membership",
            "package": package,
            "step": "fill_form",
            "needs_proof": True,
            "proof_items": [],
            "proof_summary_message_id": None,
            "form_data": "",
            "replace_index": None,
        }
        form = (
            "Sila isi perihal data diri yang tersedia, lalu titipkan kembali padaku.\n\n"
            "⌜Membership Registration⌟\n\n"
            f"▸ Package : {package}\n"
            "▸ Nama Lengkap :\n"
            "▸ Username :\n"
            "▸ Contact :\n"
            "▸ Catatan Tambahan :"
        )
        await query.edit_message_text(form)
        return

    if data == "renew:start":
        if not rec or rec.get("account_type") != "member":
            await query.edit_message_text("ⓘ Namamu belum terukir dalam tatanan ini.")
            return

        package = rec.get("membership_type")
        if not package:
            await query.edit_message_text("ⓘ Tiada jejak membership yang dapat dikenali.")
            return

        context.user_data["registration_flow"] = {
            "flow_type": "renewal",
            "kind": "renewal",
            "package": package,
            "step": "upload_proof",
            "needs_proof": True,
            "form_data": "",
            "proof_items": [],
            "proof_summary_message_id": None,
            "replace_index": None,
        }

        await query.edit_message_text(
            "ⓘ Renewal dimulai.\n"
            "Kini, persembahkan bukti pembayaranmu."
        )

        await _start_proof_upload_flow(
            context,
            query.message.chat_id,
            context.user_data["registration_flow"]
        )
        return

    if data == "upgrade:start":
        if not rec or rec.get("account_type") != "member":
            await query.edit_message_text("ⓘ Namamu belum terukir dalam tatanan ini.")
            return

        if rec.get("membership_type") != "Regular":
            await query.edit_message_text("ⓘ Upgrade Plan VIP hanya tersedia untuk member dengan package Regular.")
            return

        context.user_data["registration_flow"] = {
            "flow_type": "upgrade_vip",
            "kind": "upgrade_vip",
            "package": "VIP",
            "step": "upload_proof",
            "needs_proof": True,
            "form_data": "",
            "proof_items": [],
            "proof_summary_message_id": None,
            "replace_index": None,
        }

        await query.edit_message_text(
            "ⓘ Upgrade Plan VIP dimulai.\n"
            "Kini, persembahkan bukti pembayaranmu."
        )

        await _start_proof_upload_flow(
            context,
            query.message.chat_id,
            context.user_data["registration_flow"]
        )
        return

    if data == "proofdone:yes":
        flow = context.user_data.get("registration_flow")
        if not flow:
            await query.edit_message_text("Aku tidak menemukan sesi yang sedang berjalan.")
            return

        if flow.get("replace_index") is not None:
            await query.answer("Tuntaskan dahulu perubahan rupa yang kini masih terjalin.", show_alert=True)
            return

        if not flow.get("proof_items"):
            await query.answer("Setidaknya, persembahkan satu bukti terlebih dahulu.", show_alert=True)
            return

        flow_type = flow.get("flow_type")

        if flow_type in ("renewal", "upgrade_vip"):
            ok = await _submit_pending_to_admin(context, query.from_user, flow)
            if ok:
                await query.edit_message_text(
                    "ⓘ Data kamu telah kami terima.\n"
                    "Silakan menunggu proses selanjutnya."
                )
            else:
                await query.edit_message_text("ⓘ Data itu belum berhasil mencapai hadapan para pengurus.")
            context.user_data.pop("registration_flow", None)
            return

        flow["step"] = "confirm"
        keyboard = [
            [InlineKeyboardButton("☑ Sudah benar", callback_data="regconfirm:yes")],
            [InlineKeyboardButton("☒ Masih ada yang salah", callback_data="regconfirm:no")],
        ]
        await query.edit_message_text(
            f"Total bukti diterima: {len(flow.get('proof_items', []))}\n\n"
            "Kalau semuanya sudah benar, tekan konfirmasi.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "regconfirm:yes":
        flow = context.user_data.get("registration_flow")
        if not flow:
            await query.edit_message_text("Aku tidak menemukan sesi yang sedang berjalan.")
            return

        if flow.get("needs_proof") and not flow.get("proof_items"):
            await query.edit_message_text("ⓘ Bukti belum dikirim.")
            return

        ok = await _submit_pending_to_admin(context, query.from_user, flow)
        if ok:
            await query.edit_message_text(
                "ⓘ Data kamu telah kami terima.\n"
                "Silakan menunggu proses selanjutnya."
            )
        else:
            await query.edit_message_text("ⓘ Data itu belum berhasil mencapai hadapan para pengurus.")
        context.user_data.pop("registration_flow", None)
        return

    if data == "regconfirm:no":
        flow = context.user_data.get("registration_flow")
        if not flow:
            await query.edit_message_text("Aku tidak menemukan sesi yang sedang berjalan.")
            return

        if flow.get("flow_type") == "staff_form":
            _release_staff_interview_booking(flow, query.from_user.id)

        flow["step"] = "fill_form"
        flow["proof_items"] = []
        flow["proof_summary_message_id"] = None
        flow["replace_index"] = None
        await query.edit_message_text("ⓘ Jejakmu terhapus, isi kembali agar tercatat.")
        return


# =========================================================
# PROOF EDIT CALLBACK
# =========================================================
# =========================================================
# FEATURE: PROOF BUBBLE / TRANSACTION MEDIA EDITOR
# =========================================================
async def proof_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()

    flow = context.user_data.get("registration_flow")
    if not flow:
        await query.edit_message_text("Aku tidak menemukan sesi yang sedang berjalan.")
        return

    data = query.data or ""
    parts = data.split(":")

    if len(parts) < 2:
        return

    action = parts[1]

    if action == "add":
        flow["replace_index"] = None
        await query.answer("Kirim gambar baru untuk ditambahkan.", show_alert=True)
        await _refresh_proof_summary_message(context, query.message.chat_id, flow)
        return

    if len(parts) < 3:
        return

    try:
        idx = int(parts[2])
    except Exception:
        await query.answer("Index bukti tidak valid.", show_alert=True)
        return

    proof_items = flow.setdefault("proof_items", [])

    if action == "replace":
        if not (0 <= idx < len(proof_items)):
            await query.answer("Bukti tidak ditemukan.", show_alert=True)
            return

        flow["replace_index"] = idx
        await query.answer(f"Kirim gambar baru untuk mengganti Bukti {idx + 1}.", show_alert=True)
        await _refresh_proof_summary_message(context, query.message.chat_id, flow)
        return

    if action == "delete":
        if not (0 <= idx < len(proof_items)):
            await query.answer("Bukti tidak ditemukan.", show_alert=True)
            return

        proof_items.pop(idx)

        if flow.get("replace_index") is not None:
            if flow["replace_index"] == idx:
                flow["replace_index"] = None
            elif flow["replace_index"] > idx:
                flow["replace_index"] -= 1

        await query.answer(f"Bukti {idx + 1} dihapus.")
        await _refresh_proof_summary_message(context, query.message.chat_id, flow)
        return


# =========================================================
# SUBMIT TO ADMIN GROUP
# =========================================================
async def _submit_pending_to_admin(context, user, flow):
    uid = user.id
    uid_str = str(uid)
    rec = _get_existing_account(uid)

    flow_type = flow.get("flow_type")
    kind = flow.get("kind")
    package = flow.get("package")
    form_data = flow.get("form_data", "")

    label = _registration_label(kind if kind != "renewal" else "renewal")

    header_lines = [
        f"ⓘ ► {label}",
        "",
        f"UID : {uid}",
        f"Username : @{user.username or user.id}",
    ]

    if rec:
        header_lines.append(f"Account Number : {rec.get('acc_no', '-')}")

    if package:
        header_lines.append(f"Package : {package}")

    if flow_type == "staff_form" and flow.get("interview_label"):
        header_lines.append(f"Jadwal Wawancara : {flow.get('interview_label')}")

    if flow_type in ("renewal", "upgrade_vip") and rec:
        header_lines.append(f"Current Package : {rec.get('membership_type') or '-'}")
        header_lines.append(f"Current Status : {_refresh_membership_status(rec)}")
        header_lines.append(f"Expired At : {_fmt_dt(rec.get('membership_expires_at'))}")

    if form_data:
        header_text = "\n".join(header_lines) + f"\n\n{form_data}"
    else:
        header_text = "\n".join(header_lines)

    try:
        hdr = await context.bot.send_message(
            chat_id=FORWARD_PUBLIC_CHAT_ID,
            text=header_text,
            reply_markup=None if (flow_type in ("staff_form",) or kind in ("media_partner", "sponsorship")) else _approval_keyboard()
        )

        if flow_type in ("staff_form",) or kind in ("media_partner", "sponsorship"):
            return True

        approve_kind = kind if flow_type not in ("renewal", "upgrade_vip") else flow_type

        approval_map[(FORWARD_PUBLIC_CHAT_ID, hdr.message_id)] = {
            "uid": uid,
            "kind": approve_kind,
        }

        proof_items = flow.get("proof_items", [])
        for item in proof_items:
            copied = await context.bot.copy_message(
                chat_id=FORWARD_PUBLIC_CHAT_ID,
                from_chat_id=item["chat_id"],
                message_id=item["message_id"]
            )
            approval_map[(FORWARD_PUBLIC_CHAT_ID, copied.message_id)] = {
                "uid": uid,
                "kind": approve_kind,
            }

        if flow_type == "registration" and kind == "membership":
            PENDING_MEMBERSHIP[uid_str] = {
                "package": package,
                "form_data": form_data,
                "submitted_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "proof_count": len(proof_items),
                "username": user.username or "-",
                "name": user.full_name or "-",
            }
            save_pending()

        elif flow_type == "renewal" and rec:
            rec["renewal_pending"] = {
                "package": package,
                "form_data": form_data,
                "submitted_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "proof_count": len(proof_items),
            }
            save_accounts()

        elif flow_type == "upgrade_vip" and rec:
            rec["upgrade_pending"] = {
                "package": "VIP",
                "form_data": form_data,
                "submitted_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "proof_count": len(proof_items),
            }
            save_accounts()

        save_state()
        return True

    except Exception as e:
        print(f"[_submit_pending_to_admin] error: {e}")
        return False


# =========================================================
# REGISTRATION ROUTERS
# =========================================================
async def registration_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    flow = context.user_data.get("registration_flow")
    if not flow:
        return

    if flow.get("step") != "fill_form":
        return

    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Form tidak dapat kuhaturkan dalam keadaan hampa.")
        return

    flow["form_data"] = text

    if flow.get("flow_type") == "staff_form":
        dates = _active_staff_oprec_dates()
        if not dates:
            context.user_data.pop("registration_flow", None)
            await update.message.reply_text(_staff_oprec_closed_text())
            return
        flow["step"] = "choose_interview_date"
        await update.message.reply_text(
            "Form staff telah kuterima. Sekarang pilih tanggal wawancara yang tersedia.",
            reply_markup=_staff_interview_date_keyboard()
        )
        return

    if flow.get("needs_proof"):
        flow["step"] = "upload_proof"
        flow["proof_items"] = []
        flow["replace_index"] = None
        flow["proof_summary_message_id"] = None
        await _start_proof_upload_flow(context, update.message.chat_id, flow)
        return

    flow["step"] = "confirm"
    keyboard = [
        [InlineKeyboardButton("☑ Sudah benar", callback_data="regconfirm:yes")],
        [InlineKeyboardButton("☒ Masih ada yang salah", callback_data="regconfirm:no")],
    ]
    await update.message.reply_text(
        f"Apakah data berikut sudah benar?\n\n{text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def registration_proof_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    # Prioritaskan flow /changepict supaya foto IDC tidak ikut diambil router bukti pembayaran.
    if context.user_data.get("idcard_waiting_photo"):
        return
    flow = context.user_data.get("registration_flow")
    if not flow:
        return

    if flow.get("step") != "upload_proof":
        return

    msg = update.effective_message

    has_photo = bool(msg.photo)
    has_image_doc = bool(msg.document and (msg.document.mime_type or "").startswith("image/"))

    if not has_photo and not has_image_doc:
        await msg.reply_text("Bukti perlu hadir sebagai foto atau berkas gambar.")
        return

    proof_items = flow.setdefault("proof_items", [])
    replace_index = flow.get("replace_index")

    item = {
        "chat_id": msg.chat_id,
        "message_id": msg.message_id,
    }

    if replace_index is not None:
        if 0 <= replace_index < len(proof_items):
            proof_items[replace_index] = item
            flow["replace_index"] = None
        else:
            flow["replace_index"] = None
            proof_items.append(item)
    else:
        proof_items.append(item)

    await _refresh_proof_summary_message(context, msg.chat_id, flow)


# =========================================================
# MENU TEXT ROUTER
# =========================================================
# =========================================================
# FEATURE: MENU TEXT FLOWS
# =========================================================
async def menu_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    mode = context.user_data.get("menu_mode")
    if not mode:
        return

    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Pesanmu masih hampa; belum ada yang dapat kusampaikan.")
        return

    if mode == "kritik":
        payload = (
            "𝙉𝙊𝙏𝙄𝙁𝙄𝘾𝘼𝙏𝙄𝙊𝙉 𝙃𝘼𝙎 𝘼𝙍𝙍𝙄𝙑𝙀𝘿 ! Kritik dan Saran.\n\n"
            f"{text}\n\n"
            f"Dari: @{update.effective_user.username or update.effective_user.id}"
        )
        sent = await send_public_safe(context, payload, reply_to=update.message)
        if sent:
            await update.message.reply_text("Terima kasih. Suaramu telah kuteruskan ke ruang yang semestinya.")
            context.user_data.pop("menu_mode", None)
        return

    if mode == "menfess":
        payload = (
            "𝙉𝙊𝙏𝙄𝙁𝙄𝘾𝘼𝙏𝙄𝙊𝙉 𝙃𝘼𝙎 𝘼𝙍𝙍𝙄𝙑𝙀𝘿 ! MENFESS.\n\n"
            f"{text}\n\n"
            "Dari bot: anonim"
        )
        sent = await send_public_safe(context, payload, reply_to=update.message)
        if sent:
            await update.message.reply_text("Bisikan anonim itu telah kulepaskan menuju tujuannya.")
            context.user_data.pop("menu_mode", None)
        return


# =========================================================
# ASMODAY TALK
# =========================================================
# =========================================================
# FEATURE: ASMODAY TALK
# =========================================================
async def starttalk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    rec = _get_existing_account(user.id)

    context.user_data["talk_mode"] = True
    context.user_data["talk_notified_once"] = False
    await update.message.reply_text(
        "𐂗 ``Asmoday hadir.\n"
        "Segala ucapan akan ia dengar dan jawab. Jika usai, gunakan /stoptalk.``"
    )


async def stoptalk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    context.user_data.pop("talk_notified_once", None)
    if context.user_data.pop("talk_mode", None):
        await update.message.reply_text("Asmoday undur diri dari percakapan ini.")
    else:
        await update.message.reply_text("Asmoday undur diri dari percakapan ini.")


async def talk_user_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not context.user_data.get("talk_mode"):
        return

    msg = update.effective_message
    user = update.effective_user
    rec = _get_existing_account(user.id)

    uid = user.id
    username = f"@{user.username}" if user.username else user.first_name

    try:
        header_text = f"🗣️ From {username} (uid:{uid})"
        hdr = await context.bot.send_message(
            chat_id=FORWARD_STAFFTALK_CHAT_ID,
            text=header_text
        )
        talk_map[(FORWARD_STAFFTALK_CHAT_ID, hdr.message_id)] = uid

        copied = await context.bot.copy_message(
            chat_id=FORWARD_STAFFTALK_CHAT_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        talk_map[(FORWARD_STAFFTALK_CHAT_ID, copied.message_id)] = uid
        save_state()

        if not context.user_data.get("talk_notified_once"):
            await msg.reply_text("Pesanmu telah kuteruskan ke hadapan pengurus.")
            context.user_data["talk_notified_once"] = True
    except Exception as e:
        print(f"[talk_user_router] error: {e}")
        try:
            await msg.reply_text("Maaf, bisikanmu belum dapat mencapai Asmoday.")
        except Exception:
            pass


async def talk_admin_reply_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    sender = update.effective_user

    if chat_id != FORWARD_STAFFTALK_CHAT_ID:
        return

    if not _is_admin(sender):
        return

    if not msg or not msg.reply_to_message:
        return

    reply_src = msg.reply_to_message
    target_uid = talk_map.get((chat_id, reply_src.message_id))

    if target_uid is None:
        txt = (reply_src.text or reply_src.caption or "")
        m = re.search(r"uid\s*:\s*(\d+)", txt)
        if m:
            try:
                target_uid = int(m.group(1))
            except Exception:
                target_uid = None

    if target_uid is None:
        return

    lower_text = (msg.text or "").strip().lower()
    if lower_text in {"acc", "reject"}:
        return

    try:
        await context.bot.copy_message(
            chat_id=target_uid,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
    except Forbidden as e:
        print(f"[talk_admin_reply_router] Forbidden to DM user {target_uid}: {e}")
    except Exception as e:
        print(f"[talk_admin_reply_router] error: {e}")


# =========================================================
# APPROVAL
# =========================================================
# =========================================================
# FEATURE: ADMIN APPROVAL FLOW
# =========================================================
async def acc_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        await msg.reply_text("Balas jejak pengajuan yang hendak kau restui.")
        return

    ok, text = await _process_approval_action(
        context=context,
        actor=update.effective_user,
        chat_id=update.effective_chat.id,
        target_message=msg.reply_to_message,
        mode="acc",
        reply_message=msg,
    )
    if not ok:
        await msg.reply_text(text)


async def reject_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        await msg.reply_text("Balas jejak pengajuan yang hendak kau tolak.")
        return

    ok, text = await _process_approval_action(
        context=context,
        actor=update.effective_user,
        chat_id=update.effective_chat.id,
        target_message=msg.reply_to_message,
        mode="reject",
        reply_message=msg,
    )
    if not ok:
        await msg.reply_text(text)


async def approval_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        return

    text = (msg.text or "").strip().lower()
    if text not in {"acc", "reject"}:
        return

    mode = "acc" if text == "acc" else "reject"

    ok, result_text = await _process_approval_action(
        context=context,
        actor=update.effective_user,
        chat_id=update.effective_chat.id,
        target_message=msg.reply_to_message,
        mode=mode,
        reply_message=msg,
    )

    if not ok:
        await msg.reply_text(result_text)


async def approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data.split(":")[1]

    ok, result_text = await _process_approval_action(
        context=context,
        actor=query.from_user,
        chat_id=query.message.chat_id,
        target_message=query.message,
        mode=mode,
        reply_message=query.message,
    )

    if ok:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
    else:
        await query.answer(result_text, show_alert=True)


# =========================================================
# FEATURE: CHOICE POKER
# =========================================================
async def choice_poker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Choice Poker hanya dapat dibuka di ruang group.")
        return

    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Nomor account perlu kau miliki sebelum membuka room Choice Poker.")
        return

    room_key = _choice_poker_room_key(chat.id)
    if room_key in CHOICE_POKER_ROOMS:
        await update.message.reply_text("Masih ada room Choice Poker yang bernyawa di grup ini.")
        return

    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "host_name": user.full_name or user.username or f"User {user.id}",
        "status": "waiting",
        "players": {
            str(user.id): {
                "name": user.full_name or user.username or f"User {user.id}",
                "bet": None,
                "committed": 0,
                "choice": None,
                "hand_sent": False,
                "player_cards": None,
                "swapped": False,
                "swap_done": False,
                "swap_note": None,
                "folded": False,
                "all_in": False,
                "acted_cycle": False,
                "stack_total": int(rec.get('balance', 0)),
            }
        },
        "dealer_public_reveal": None,
        "message_id": None,
        "pot": 0,
        "current_bet": 0,
        "turn_order": [],
        "turn_index": 0,
    }
    sent = await update.message.reply_text(
        _choice_poker_status_text(room),
        reply_markup=_choice_poker_waiting_keyboard(user.id),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    await update.message.reply_text(
        "Asmoday membuka meja Choice Poker.",
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
        reply_to_message_id=sent.message_id,
    )
    room["message_id"] = sent.message_id
    CHOICE_POKER_ROOMS[room_key] = room


async def choice_poker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    room = CHOICE_POKER_ROOMS.get(_choice_poker_room_key(chat_id))
    if not room:
        await query.answer("Room tidak ditemukan atau sudah selesai.", show_alert=True)
        return

    action = (query.data or '').split(':', 1)[1]
    uid = str(user.id)

    if action == 'join':
        rec = _get_existing_account(user.id)
        if not _has_gamble_access(rec):
            await query.answer("Nomor account perlu kau miliki sebelum ikut bermain.", show_alert=True)
            return
        if uid in room['players']:
            return
        if len(room['players']) >= 2:
            await query.answer("Meja ini khusus duel 1 vs 1. Slot sudah penuh.", show_alert=True)
            return
        room['players'][uid] = {
            "name": user.full_name or user.username or f"User {user.id}",
            "bet": None,
            "committed": 0,
            "choice": None,
            "hand_sent": False,
            "player_cards": None,
            "swapped": False,
            "swap_done": False,
            "swap_note": None,
            "folded": False,
            "all_in": False,
            "acted_cycle": False,
            "stack_total": int(rec.get('balance', 0)),
        }
        room['status'] = 'betting'
        room['current_bet'] = 0
        room['pot'] = 0
        await _choice_poker_refresh_message(context, chat_id, room)
        await _choice_poker_send_room_message(
            context,
            room,
            (
                f"🎴 {room['players'][uid]['name']} duduk di meja. Karena host juga dihitung sebagai player, Choice Poker dimulai.\n\n"
                "⛃ ⛁ · Open bet dibuka. Kedua pemain kirim nominal bet dengan format angka saja di topik ini.\n"
                "Contoh: 5000\n\n"
                "Ini baru taruhan pembuka. Setelah kartu dibagi, tidak ada call atau fold — hanya raise, all-in, atau lock taruhan.\n"
                "Syarat: saldo cukup dan wajib punya account number."
            ),
        )
        return

    if action == 'leave':
        if uid == str(room.get('host_id')):
            await query.answer("Host tidak bisa leave. Cancel room kalau mau batal.", show_alert=True)
            return
        if room.get('status') != 'waiting':
            await query.answer("Duel sudah dimulai. Tidak bisa leave sekarang.", show_alert=True)
            return
        if uid in room['players']:
            room['players'].pop(uid, None)
            await _choice_poker_refresh_message(context, chat_id, room)
        return

    if action == 'cancel':
        if user.id != room.get('host_id') and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa membatalkan room.", show_alert=True)
            return
        CHOICE_POKER_ROOMS.pop(_choice_poker_room_key(chat_id), None)
        await query.edit_message_text("Room Choice Poker telah ditutup dari gelanggang.")
        return

    if action == 'start':
        if user.id != room.get('host_id') and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa mulai.", show_alert=True)
            return
        if len(room.get('players', {})) != 2:
            await query.answer("Meja ini wajib tepat 2 pemain dulu ya.", show_alert=True)
            return
        room['status'] = 'betting'
        await _choice_poker_refresh_message(context, chat_id, room)
        await _choice_poker_send_room_message(
            context,
            room,
            (
                "⛃ ⛁ · Open bet dibuka. Kedua pemain kirim nominal bet dengan format angka saja di topik ini.\n"
                "Contoh: 5000\n\n"
                "Ini baru taruhan pembuka. Setelah kartu dibagi, tidak ada call atau fold — hanya raise, all-in, atau lock taruhan.\n"
                "Syarat: saldo cukup dan wajib punya account number."
            ),
        )
        return


async def choice_poker_swap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Versi ini mengikuti Choice Poker ala Kakegurui tanpa swap kartu.", show_alert=True)
    return
async def choice_poker_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    parts = (query.data or '').split(':')
    if len(parts) != 3:
        await query.answer("Data aksi tidak valid.", show_alert=True)
        return
    _, room_chat_id_raw, action = parts
    try:
        room_chat_id = int(room_chat_id_raw)
    except Exception:
        await query.answer("Room tidak valid.", show_alert=True)
        return

    room = CHOICE_POKER_ROOMS.get(_choice_poker_room_key(room_chat_id))
    if not room or room.get('status') != 'action':
        await query.answer("Fase aksi sudah lewat.", show_alert=True)
        return

    uid = str(user.id)
    if uid != str(_choice_poker_turn_uid(room)):
        await query.answer("Bukan giliranmu.", show_alert=True)
        return

    player = room.get('players', {}).get(uid)
    others = [k for k in room.get('players', {}).keys() if k != uid]
    if not player or len(others) != 1:
        await query.answer("Room tidak valid.", show_alert=True)
        return
    opp_uid = others[0]
    opp = room['players'][opp_uid]
    total_stack = int(player.get('stack_total', 0))
    committed = int(player.get('committed', 0))
    available = max(0, total_stack - committed)

    if action == 'raise':
        if available <= 0:
            await query.answer("Chip kamu habis. Tinggal all-in sudah otomatis, atau lock taruhan.", show_alert=True)
            return
        room['pending_raise_uid'] = uid
        await _choice_poker_refresh_message(context, room_chat_id, room)
        await _choice_poker_send_room_message(context, room, f"⛃ ⛁ · {player.get('name')} menyiapkan raise. Kirim nominal TOTAL taruhan barumu dengan angka saja di topik ini. Minimal harus lebih besar dari {max(int(player.get('committed', 0)), int(opp.get('committed', 0)))}.")
        return

    if action == 'allin':
        if available <= 0:
            await query.answer("Kamu sudah tidak punya chip tersisa.", show_alert=True)
            return
        player['committed'] = total_stack
        player['all_in'] = True
        player['locked'] = True
        room['pot'] = sum(int(p.get('committed', 0)) for p in room.get('players', {}).values())
        note = f"all-in ke {player['committed']}"
    elif action == 'lock':
        player['locked'] = True
        note = f"mengunci taruhan di {player['committed']}"
    else:
        await query.answer("Aksi tidak dikenal.", show_alert=True)
        return

    await _choice_poker_send_room_message(context, room, f"🎭 {player.get('name')} {note}.")

    if all(p.get('locked') or p.get('all_in') for p in room.get('players', {}).values()):
        await _choice_poker_refresh_message(context, room_chat_id, room)
        await _choice_poker_begin_choice_phase(context, room_chat_id, room)
        return

    _choice_poker_next_turn(room)
    await _choice_poker_refresh_message(context, room_chat_id, room)
    turn_uid = _choice_poker_turn_uid(room)
    if turn_uid:
        await _choice_poker_send_room_message(context, room, f"🫀 Sekarang giliran {room['players'][turn_uid].get('name')}. Hanya raise, all-in, atau lock taruhan.", reply_markup=_choice_poker_action_keyboard(room_chat_id, room, turn_uid))
async def choice_poker_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    parts = (query.data or '').split(':')
    if len(parts) != 3:
        await query.answer("Data pilihan tidak valid.", show_alert=True)
        return
    _, room_chat_id_raw, action = parts
    try:
        room_chat_id = int(room_chat_id_raw)
    except Exception:
        await query.answer("Room tidak valid.", show_alert=True)
        return

    room = CHOICE_POKER_ROOMS.get(_choice_poker_room_key(room_chat_id))
    if not room or room.get('status') != 'choice':
        await query.answer("Fase pilihan sudah lewat.", show_alert=True)
        return
    if str(user.id) != str(room.get('chooser_uid')):
        await query.answer("Hak pilih bukan milikmu.", show_alert=True)
        return
    if action not in ('stronger', 'weaker'):
        await query.answer("Pilihan tidak valid.", show_alert=True)
        return

    room['choice_mode'] = action
    await _choice_poker_refresh_message(context, room_chat_id, room)
    await _choice_poker_send_room_message(context, room, f"🃏 {room['players'][str(user.id)].get('name')} memilih mode {action.title()}.")
    try:
        await query.edit_message_text(f"Pilihanmu dikunci: {action.title()}")
    except Exception:
        pass
    await _choice_poker_resolve_showdown(context, room_chat_id, room)


def _parse_bet_amount(text: str):
    raw = (text or "").strip().replace(",", "").replace(".", "")
    if not raw.isdigit():
        return None
    amount = int(raw)
    if amount <= 0:
        return None
    return amount


def _asmoday_bet_ack_text(player_name: str, amount: int) -> str:
    return f"Asmoday mencatat taruhan {player_name}: {_normalize_price_text(amount)}✦𝕷."


async def choice_poker_bet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == 'private' or not msg or not msg.text:
        return

    room = CHOICE_POKER_ROOMS.get(_choice_poker_room_key(chat.id))
    if not room:
        return

    uid = str(user.id)
    player = room.get('players', {}).get(uid)
    if not player:
        return

    amount = _parse_bet_amount(msg.text)
    if amount is None:
        return

    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await msg.reply_text('Akses gamble menuntut account number yang sah.')
        return

    balance = int(rec.get('balance', 0))

    if room.get('status') == 'action' and str(room.get('pending_raise_uid') or '') == uid:
        target = amount
        current_max = max(int(p.get('committed', 0)) for p in room.get('players', {}).values())
        if target <= current_max:
            await msg.reply_text(f'Raise harus lebih besar dari {current_max}.')
            return
        if target > balance:
            await msg.reply_text(f'Saldo kamu tidak cukup. Saldo sekarang: {balance}')
            return
        player['committed'] = target
        player['locked'] = True
        player['all_in'] = target == balance
        other_uid = [k for k in room.get('players', {}).keys() if k != uid][0]
        room['players'][other_uid]['locked'] = False
        room['pot'] = sum(int(p.get('committed', 0)) for p in room.get('players', {}).values())
        room['pending_raise_uid'] = None
        await msg.reply_text(f'Raise {player.get("name")} diterima: total taruhan sekarang {target}', message_thread_id=getattr(msg, 'message_thread_id', None))
        await _choice_poker_refresh_message(context, chat.id, room)
        _choice_poker_next_turn(room)
        turn_uid = _choice_poker_turn_uid(room)
        await _choice_poker_send_room_message(context, room, f"🫀 Sekarang giliran {room['players'][turn_uid].get('name')}. Naikkan taruhan lagi, all-in, atau lock.", reply_markup=_choice_poker_action_keyboard(chat.id, room, turn_uid))
        return

    if room.get('status') != 'betting':
        return

    bet = amount
    if player.get('bet') is not None:
        return
    if bet > balance:
        await msg.reply_text(f'Saldo kamu tidak cukup. Saldo sekarang: {balance}')
        return

    player['stack_total'] = balance
    player['bet'] = bet
    player['committed'] = bet
    await msg.reply_text(_asmoday_bet_ack_text(player.get('name'), bet), message_thread_id=getattr(msg, 'message_thread_id', None))
    await _choice_poker_refresh_message(context, chat.id, room)

    if len(room.get('players', {})) == 2 and all(p.get('bet') is not None for p in room.get('players', {}).values()):
        room['status'] = 'dealing'
        room['pot'] = sum(int(p.get('committed', 0)) for p in room.get('players', {}).values())
        _choice_poker_shuffle_deck(room)
        for pid, pdata in room.get('players', {}).items():
            pdata['hand_sent'] = False
            pdata['all_in'] = False
            pdata['locked'] = False
            pdata['player_cards'] = _draw_cards(room, 5)
        await _choice_poker_send_room_message(context, room, '🃏 Semua open bet sudah masuk. Oxana membagikan 5 kartu rahasia ke masing-masing pemain. Setelah ini hanya raise, all-in, atau lock taruhan.')
        await _choice_poker_refresh_message(context, chat.id, room)
        dm_failed = False
        for pid, pdata in room.get('players', {}).items():
            try:
                await context.bot.send_message(
                    chat_id=int(pid),
                    text=(
                        f"⌜ Choice Poker — Private Hand ⌟\n"
                        f"Room: {chat.title or chat.id}\n"
                        f"Open bet kamu: {pdata.get('bet')}\n"
                        f"Kartumu: {_format_cards(pdata.get('player_cards') or [])}\n\n"
                        "Sekarang masuk fase taruhan Choice Poker. Kamu hanya bisa raise, all-in, atau lock taruhan. Pihak dengan total taruhan lebih besar nanti memilih Stronger atau Weaker."
                    ),
                )
                pdata['hand_sent'] = True
            except Exception:
                dm_failed = True
                await _choice_poker_send_room_message(context, room, f"⚠️ {pdata.get('name')} belum bisa di-DM. Minta dia /start bot dulu, lalu buka room baru supaya kartu rahasianya bisa dikirim.")
        await _choice_poker_refresh_message(context, chat.id, room)
        if dm_failed:
            room['status'] = 'cancelled'
            CHOICE_POKER_ROOMS.pop(_choice_poker_room_key(chat.id), None)
            await _choice_poker_send_room_message(context, room, "Room Choice Poker dibatalkan agar kartu rahasia tidak bocor atau game tidak nyangkut. Semua pemain wajib /start bot dulu sebelum buka ulang room.")
            return
        await _choice_poker_begin_action_phase(context, chat.id, room)

# =========================================================
# FEATURE: BACCARAT
# =========================================================
def _baccarat_room_key(chat_id: int) -> str:
    return str(chat_id)

def _baccarat_new_deck():
    return [f"{r}{s}" for s in CARD_SUITS for r in CARD_RANKS]

def _baccarat_shuffle(room: dict):
    import random
    deck = _baccarat_new_deck() * 8
    random.shuffle(deck)
    room["deck"] = deck

def _baccarat_draw(room: dict):
    deck = room.setdefault("deck", [])
    if len(deck) < 10:
        _baccarat_shuffle(room)
        deck = room["deck"]
    return deck.pop()

def _baccarat_card_value(card: str) -> int:
    rank = card[:-1]
    if rank in ("10", "J", "Q", "K"):
        return 0
    if rank == "A":
        return 1
    return int(rank)

def _baccarat_total(cards) -> int:
    return sum(_baccarat_card_value(c) for c in (cards or [])) % 10

def _baccarat_should_banker_draw(banker_total: int, player_third):
    if player_third is None:
        return banker_total <= 5
    pv = _baccarat_card_value(player_third)
    if banker_total <= 2:
        return True
    if banker_total == 3:
        return pv != 8
    if banker_total == 4:
        return 2 <= pv <= 7
    if banker_total == 5:
        return 4 <= pv <= 7
    if banker_total == 6:
        return 6 <= pv <= 7
    return False

def _baccarat_waiting_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join", callback_data="baccarat:join"), InlineKeyboardButton("Leave", callback_data="baccarat:leave")],
        [InlineKeyboardButton("Start Betting", callback_data="baccarat:start"), InlineKeyboardButton("Close", callback_data="baccarat:close")],
    ])

def _baccarat_betting_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Deal", callback_data="baccarat:deal"), InlineKeyboardButton("Close", callback_data="baccarat:close")]])

def _baccarat_status_text(room: dict) -> str:
    players = room.get("players") or {}
    lines = ["⛃ ⛁ · BACCARAT", "", f"Status : {(room.get('status') or 'waiting').upper()}", f"Host : {room.get('host_name', '-')}", "", "Player List:"]
    if not players:
        lines.append("› -")
    else:
        for uid, pdata in players.items():
            bets = pdata.get("bets") or {}
            bet_text = ", ".join(f"{k}:{_normalize_price_text(v)}" for k, v in bets.items()) if bets else "belum bet"
            lines.append(f"› {pdata.get('name', 'Player')} | {bet_text}")
    if room.get("status") == "waiting":
        lines.extend(["", "Cara main:", "› Join meja, lalu host menekan Start Betting.", "› Pasang taruhan dengan /baccaratbet <player|banker|tie> <nominal>.", "› Host menekan Deal untuk membuka kartu.", "› Player/Banker menang dibayar 1:1, Tie dibayar 8:1."])
    elif room.get("status") == "betting":
        lines.extend(["", "Pasang bet: /baccaratbet player 5000 atau /baccaratbet banker 5000 atau /baccaratbet tie 5000"])
    return "\n".join(lines)

async def _baccarat_refresh_message(context, room: dict):
    message_id = room.get("message_id")
    if not message_id:
        return
    markup = _baccarat_waiting_keyboard() if room.get("status") == "waiting" else _baccarat_betting_keyboard() if room.get("status") == "betting" else None
    try:
        await context.bot.edit_message_text(chat_id=room.get("chat_id"), message_id=message_id, text=_baccarat_status_text(room), reply_markup=markup)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[_baccarat_refresh_message] error: {e}")

async def baccarat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Baccarat hanya dapat dibuka di ruang group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Nomor account perlu kau miliki sebelum membuka meja Baccarat.")
        return
    key = _baccarat_room_key(chat.id)
    if key in BACCARAT_ROOMS:
        await update.message.reply_text("Masih ada meja Baccarat yang bernyawa di grup ini.")
        return
    room = {"chat_id": chat.id, "thread_id": getattr(update.effective_message, "message_thread_id", None), "host_id": user.id, "host_name": user.full_name or user.username or f"User {user.id}", "status": "waiting", "players": {str(user.id): {"name": user.full_name or user.username or f"User {user.id}", "bets": {}}}, "message_id": None, "deck": []}
    _baccarat_shuffle(room)
    sent = await update.message.reply_text(_baccarat_status_text(room), reply_markup=_baccarat_waiting_keyboard(), message_thread_id=getattr(update.effective_message, "message_thread_id", None))
    room["message_id"] = sent.message_id
    BACCARAT_ROOMS[key] = room

async def baccarat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    room = BACCARAT_ROOMS.get(_baccarat_room_key(chat_id))
    if not room:
        await query.answer("Meja Baccarat tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    uid = str(query.from_user.id)
    if action == "join":
        if room.get("status") != "waiting":
            await query.answer("Betting sudah dimulai.", show_alert=True)
            return
        rec = _get_existing_account(query.from_user.id)
        if not _has_gamble_access(rec):
            await query.answer("Kamu harus punya account number dulu.", show_alert=True)
            return
        room.setdefault("players", {}).setdefault(uid, {"name": query.from_user.full_name or query.from_user.username or f"User {uid}", "bets": {}})
        await _baccarat_refresh_message(context, room)
        return
    if action == "leave":
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Close meja kalau batal.", show_alert=True)
            return
        if room.get("status") != "waiting":
            await query.answer("Meja sudah berjalan.", show_alert=True)
            return
        room.get("players", {}).pop(uid, None)
        await _baccarat_refresh_message(context, room)
        return
    if action == "close":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya host/admin yang bisa menutup meja.", show_alert=True)
            return
        BACCARAT_ROOMS.pop(_baccarat_room_key(chat_id), None)
        await query.edit_message_text("Meja Baccarat telah ditutup.")
        return
    if action == "start":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya host/admin yang bisa mulai betting.", show_alert=True)
            return
        room["status"] = "betting"
        await _baccarat_refresh_message(context, room)
        return
    if action == "deal":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya host/admin yang bisa deal.", show_alert=True)
            return
        await _baccarat_deal_and_resolve(context, room)

async def baccarat_bet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    msg = update.effective_message
    if chat.type == "private":
        await msg.reply_text("Taruhan Baccarat hanya dapat dicatat di ruang group.")
        return
    room = BACCARAT_ROOMS.get(_baccarat_room_key(chat.id))
    if not room or room.get("status") != "betting":
        await msg.reply_text("Belum ada fase taruhan Baccarat yang sedang terbuka.")
        return
    uid = str(update.effective_user.id)
    if uid not in room.get("players", {}):
        await msg.reply_text("Namamu belum duduk di meja Baccarat.")
        return
    if len(context.args) != 2:
        await msg.reply_text("Format titah: /baccaratbet <player|banker|tie> <nominal>")
        return
    side = (context.args[0] or "").lower()
    if side not in ("player", "banker", "tie"):
        await msg.reply_text("Pilihan hanya dapat berupa player, banker, atau tie.")
        return
    amount = _parse_bet_amount(context.args[1])
    if amount is None:
        await msg.reply_text("Nominal taruhan perlu berupa angka yang lebih dari 0.")
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or not _has_gamble_access(rec):
        await msg.reply_text("Jejak account-mu tidak kutemukan. Pastikan account number telah kau miliki.")
        return
    current_total = sum(int(v) for v in (room["players"][uid].get("bets") or {}).values())
    if current_total + amount > int(rec.get("balance", 0)):
        await msg.reply_text(f"Saldo tidak cukup. Saldo sekarang: {_normalize_price_text(rec.get('balance', 0))}")
        return
    bets = room["players"][uid].setdefault("bets", {})
    bets[side] = int(bets.get(side, 0)) + amount
    await msg.reply_text(f"Bet Baccarat dicatat: {side.title()} {_normalize_price_text(amount)} ✦𝕷.")
    await _baccarat_refresh_message(context, room)

async def _baccarat_deal_and_resolve(context, room: dict):
    if room.get("status") != "betting":
        return
    has_bets = any((p.get("bets") or {}) for p in room.get("players", {}).values())
    if not has_bets:
        await context.bot.send_message(chat_id=room.get("chat_id"), text="Belum ada taruhan Baccarat yang memasuki catatan.")
        return
    player_cards = [_baccarat_draw(room), _baccarat_draw(room)]
    banker_cards = [_baccarat_draw(room), _baccarat_draw(room)]
    pt = _baccarat_total(player_cards)
    bt = _baccarat_total(banker_cards)
    player_third = None
    if pt not in (8, 9) and bt not in (8, 9):
        if pt <= 5:
            player_third = _baccarat_draw(room)
            player_cards.append(player_third)
            pt = _baccarat_total(player_cards)
        if _baccarat_should_banker_draw(bt, player_third):
            banker_cards.append(_baccarat_draw(room))
            bt = _baccarat_total(banker_cards)
    winner = "player" if pt > bt else "banker" if bt > pt else "tie"
    lines = ["⛃ ⛁ · BACCARAT RESULT", "", f"Player : {_format_cards(player_cards)} = {pt}", f"Banker : {_format_cards(banker_cards)} = {bt}", f"Winner : {winner.title()}", "", "Settlement:"]
    for uid, pdata in list(room.get("players", {}).items()):
        rec = _get_existing_account(int(uid))
        bets = pdata.get("bets") or {}
        if not rec or not bets:
            continue
        net = 0
        details = []
        for side, amount in bets.items():
            amount = int(amount or 0)
            if winner == "tie":
                if side == "tie":
                    gain = amount * 8
                    net += gain
                    details.append(f"Tie menang +{_normalize_price_text(gain)}")
                else:
                    details.append(f"{side.title()} push")
            elif side == winner:
                net += amount
                details.append(f"{side.title()} menang +{_normalize_price_text(amount)}")
            else:
                net -= amount
                details.append(f"{side.title()} kalah -{_normalize_price_text(amount)}")
        rec["balance"] = max(0, int(rec.get("balance", 0)) + net)
        lines.append(f"› {pdata.get('name')} | {'; '.join(details)} | Saldo: {_normalize_price_text(rec.get('balance', 0))}")
    save_accounts()
    room["status"] = "resolved"
    await _baccarat_refresh_message(context, room)
    await context.bot.send_message(chat_id=room.get("chat_id"), text="\n".join(lines), reply_to_message_id=room.get("message_id"))
    BACCARAT_ROOMS.pop(_baccarat_room_key(room.get("chat_id")), None)

# =========================================================
# FEATURE: JUGEMENT DE CARDINALE
# =========================================================
JUGEMENT_CARD_VALUES = {"La Glace": 14, "L’empereur": 13, "L'impératrice": 12, "Le Chevalier": 11}
for _i in range(1, 11):
    JUGEMENT_CARD_VALUES[f"Le Pion {_i}"] = _i

def _jugement_room_key(chat_id: int) -> str:
    return str(chat_id)

def _jugement_draw(room: dict):
    import random
    deck = room.setdefault("deck", [])
    if not deck:
        base = list(JUGEMENT_CARD_VALUES.keys())
        deck.extend(base * 4)
        random.shuffle(deck)
    return deck.pop()

def _jugement_total(cards) -> int:
    return sum(JUGEMENT_CARD_VALUES.get(c, 0) for c in (cards or []))

def _jugement_distance(total: int) -> int:
    return 999 if total > 25 else abs(25 - int(total or 0))

def _jugement_waiting_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join", callback_data="jugement:join"), InlineKeyboardButton("Leave", callback_data="jugement:leave")], [InlineKeyboardButton("Asmoday Start Trial", callback_data="jugement:start"), InlineKeyboardButton("Close", callback_data="jugement:close")]])

def _jugement_after_deal_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Asmoday Mulai Pemihakan", callback_data="jugement:begin")], [InlineKeyboardButton("Close", callback_data="jugement:close")]])

def _jugement_pair_keyboard(chat_id: int, pair_id: int):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Take", callback_data=f"jugementact:{chat_id}:{pair_id}:take"), InlineKeyboardButton("Pass", callback_data=f"jugementact:{chat_id}:{pair_id}:pass")], [InlineKeyboardButton("Lock", callback_data=f"jugementact:{chat_id}:{pair_id}:lock")]])

def _jugement_status_text(room: dict) -> str:
    players = room.get("players") or {}
    lines = ["⛃ ⛁ · JUGEMENT DE CARDINALE", "", f"Status : {(room.get('status') or 'waiting').upper()}", "Hakim : Asmoday", "", "Pengunjung Persidangan:"]
    if not players:
        lines.append("› -")
    else:
        for pdata in players.values():
            lines.append(f"› {pdata.get('name', 'Player')}")
    if room.get("status") == "waiting":
        lines.extend([
        "",
        "[ 𝗛𝗢𝗪 𝗧𝗢 𝗣𝗟𝗔𝗬 . ]",
        "",
        "Permainan ini terbagi menjadi dua peran pemain: Pendosa dan Saksi.",
        "ㅤㅤ‹⚖:۰ 𝗥𝗼𝗹𝗲 𝗘𝘅𝗽𝗹𝗮𝗻𝗮𝘁𝗶𝗼𝗻",
        "ㅤㅤ— — • — • — — • — • — — • — •",
        "ㅤㅤ• 𝗦𝗶𝗻𝗻𝗲𝗿 : Pendosa yang diadili oleh Penguasa.",
        "ㅤㅤ• 𝗪𝗶𝘁𝗻𝗲𝘀𝘀 : Saksi yang membela Pendosa.",
        "ㅤㅤ— — • — • — — • — • — — • — •",
        "",
        "O2. Asmoday akan memulai persidangan otomatis.",
        "O3. Role & kartu dikirim ke DM.",
        "O4. Setiap pemain mendapat 1 kartu awal.",
        "5. Witness melakukan taruhan:",
        "ㅤㅤ!bet [amount]",
        "O6. Nilai tidak boleh > 25.",
        "O7. Aksi:",
        "ㅤㅤ!take / !pass / !lock",
        "O8. Pemenang = paling dekat ke 25.",
        "O9. >25 = kalah.",
        "1O. DRAW → +100,000 Vert",
        "",
        "---",
        "[ 𝗚𝗔𝗠𝗘 𝗣𝗛𝗔𝗦𝗘 . ]",
        "",
        "!join jugement",
        "Role dibagi",
        "Witness bet",
        "Turn berjalan",
        "Evaluasi",
        "Selesai",
        "",
        ])
    return "\n".join(lines)

async def _jugement_refresh_message(context, room: dict):
    if not room.get("message_id"):
        return
    markup = _jugement_waiting_keyboard() if room.get("status") == "waiting" else _jugement_after_deal_keyboard() if room.get("status") == "betting" else None
    try:
        await context.bot.edit_message_text(chat_id=room.get("chat_id"), message_id=room.get("message_id"), text=_jugement_status_text(room), reply_markup=markup)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[_jugement_refresh_message] error: {e}")

async def jugement_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Jugement de Cardinale hanya dapat dibuka di ruang group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Nomor account perlu kau miliki sebelum membuka persidangan.")
        return
    key = _jugement_room_key(chat.id)
    if key in JUGEMENT_ROOMS:
        await update.message.reply_text("Masih ada persidangan yang berlangsung di grup ini.")
        return
    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "judge_name": "Asmoday",
        "opened_by": user.id,
        "status": "waiting",
        "players": {},
        "pairs": [],
        "deck": [],
        "message_id": None,
    }
    sent = await update.message.reply_text(
        _jugement_status_text(room),
        reply_markup=_jugement_waiting_keyboard(),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    room["message_id"] = sent.message_id
    JUGEMENT_ROOMS[key] = room
    await update.message.reply_text(
        "Asmoday membuka pintu persidangan Jugement de Cardinale. Pemain dapat masuk dengan tombol Join atau !join jugement.",
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
        reply_to_message_id=sent.message_id,
    )

async def join_jugement_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    if chat.type == "private":
        return
    room = JUGEMENT_ROOMS.get(_jugement_room_key(chat.id))
    if not room or room.get("status") != "waiting":
        await update.message.reply_text("Tidak ada persidangan yang sedang membuka pintunya.")
        return
    await _jugement_add_player(context, room, update.effective_user, update.effective_message)

async def _jugement_add_player(context, room: dict, user, reply_msg=None):
    uid = str(user.id)
    if uid in room.get("players", {}):
        if reply_msg:
            await reply_msg.reply_text("Namamu telah tercatat di dalam persidangan.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        if reply_msg:
            await reply_msg.reply_text("Nomor account perlu kau miliki sebelum ikut bermain.")
        return
    room.setdefault("players", {})[uid] = {"name": user.full_name or user.username or f"User {user.id}"}
    if reply_msg:
        await reply_msg.reply_text("Namamu telah masuk ke lingkar persidangan.")
    await _jugement_refresh_message(context, room)

async def jugement_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    room = JUGEMENT_ROOMS.get(_jugement_room_key(chat_id))
    if not room:
        await query.answer("Persidangan tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    uid = str(query.from_user.id)
    if action == "join":
        if room.get("status") != "waiting":
            await query.answer("Pintu persidangan sudah ditutup.", show_alert=True)
            return
        await _jugement_add_player(context, room, query.from_user)
        return
    if action == "leave":
        if room.get("status") != "waiting":
            await query.answer("Persidangan sudah dimulai.", show_alert=True)
            return
        room.get("players", {}).pop(uid, None)
        await _jugement_refresh_message(context, room)
        return
    if action == "close":
        if not _is_admin(query.from_user) and not _can_manage_staff(query.from_user):
            await query.answer("Hanya admin/Currathor yang bisa menutup persidangan.", show_alert=True)
            return
        JUGEMENT_ROOMS.pop(_jugement_room_key(chat_id), None)
        await query.edit_message_text("Persidangan Jugement de Cardinale telah ditutup.")
        return
    if action == "start":
        # Hakim persidangan adalah Asmoday. Tombol ini hanya menjadi pemicu agar Asmoday mulai membagi role.
        await _jugement_start_trial(context, room)
        return
    if action == "begin":
        # Fase pemihakan juga dipimpin Asmoday; tombol ini hanya fallback jika auto-start belum terpanggil.
        await _jugement_begin_alignment(context, room)
        return

async def _jugement_start_trial(context, room: dict):
    import random
    players = list((room.get("players") or {}).items())
    if len(players) < 2:
        await context.bot.send_message(chat_id=room.get("chat_id"), text="Persidangan memerlukan sedikitnya dua jiwa untuk dimulai.")
        return
    random.shuffle(players)
    removed = None
    if len(players) % 2 == 1:
        removed = players.pop()
    pairs = []
    for idx in range(0, len(players), 2):
        a_uid, a_data = players[idx]
        b_uid, b_data = players[idx + 1]
        sinner_uid, witness_uid = (a_uid, b_uid) if random.choice([True, False]) else (b_uid, a_uid)
        pair = {"id": len(pairs), "sinner_uid": sinner_uid, "witness_uid": witness_uid, "bet": None, "round": 1, "choices": {}, "locked": False, "resolved": False}
        for uid, role in ((sinner_uid, "Sinner"), (witness_uid, "Witness")):
            pdata = room["players"][uid]
            card = _jugement_draw(room)
            pdata["role"] = role
            pdata["cards"] = [card]
        pairs.append(pair)
    if removed:
        room["players"].pop(removed[0], None)
    room["pairs"] = pairs
    room["status"] = "betting"
    await _jugement_refresh_message(context, room)
    if removed:
        await context.bot.send_message(chat_id=room.get("chat_id"), text=f"Jumlah pengunjung ganjil. {removed[1].get('name')} dikeluarkan secara acak dari persidangan.")
    for pair in pairs:
        for uid in (pair["sinner_uid"], pair["witness_uid"]):
            pdata = room["players"][uid]
            try:
                await context.bot.send_message(chat_id=int(uid), text=("⌜ Jugement de Cardinale — Private Notice ⌟\n" f"Role : {pdata.get('role')}\n" f"Kartu awal : {_format_cards(pdata.get('cards') or [])}\n" f"Total pemihakan : {_jugement_total(pdata.get('cards') or [])}\n\n" "Jangan bagikan kartu ini ke personal contact lain. Diskusi hanya di grup."))
            except Exception as e:
                print(f"[_jugement_start_trial] DM failed uid={uid}: {e}")
    await context.bot.send_message(
        chat_id=room.get("chat_id"),
        text=(
            "Asmoday telah membagikan peran dan kartu pemihakan melalui DM.\n\n"
            "Para Witness memasang taruhan dengan /bet <amount>. Setelah seluruh Witness memasang taruhan, Asmoday akan otomatis membuka fase pemihakan."
        ),
        reply_markup=_jugement_after_deal_keyboard(),
    )

async def jugement_bet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    if chat.type == "private":
        return
    room = JUGEMENT_ROOMS.get(_jugement_room_key(chat.id))
    if not room or room.get("status") != "betting":
        return
    uid = str(update.effective_user.id)
    pair = next((p for p in room.get("pairs", []) if p.get("witness_uid") == uid), None)
    if not pair:
        await update.message.reply_text("Hanya Witness yang berhak menaruh taruhan.")
        return
    if not context.args:
        await update.message.reply_text("Format titah: /bet <amount>")
        return
    amount = _parse_bet_amount(context.args[0])
    if amount is None:
        await update.message.reply_text("Nominal taruhan perlu berupa angka yang lebih dari 0.")
        return
    sinner_rec = _get_existing_account(int(pair["sinner_uid"]))
    witness_rec = _get_existing_account(int(pair["witness_uid"]))
    if not sinner_rec or not witness_rec:
        await update.message.reply_text("Jejak account pasangan tidak kutemukan.")
        return
    if amount > int(sinner_rec.get("balance", 0)) or amount > int(witness_rec.get("balance", 0)):
        await update.message.reply_text("Kepemilikan Saksi atau Pendosa belum cukup untuk taruhan ini.")
        return
    pair["bet"] = amount
    await update.message.reply_text(f"Taruhan Witness dicatat: {_normalize_price_text(amount)} ✦𝕷.")

    if room.get("status") == "betting" and all(p.get("bet") is not None for p in room.get("pairs", [])):
        await update.message.reply_text("Seluruh taruhan Witness telah tercatat. Asmoday membuka fase pemihakan.")
        await _jugement_begin_alignment(context, room)

async def _jugement_begin_alignment(context, room: dict):
    missing = []
    for pair in room.get("pairs", []):
        if pair.get("bet") is None:
            w = room.get("players", {}).get(pair.get("witness_uid"), {})
            missing.append(w.get("name", "Witness"))
    if missing:
        await context.bot.send_message(chat_id=room.get("chat_id"), text="Masih ada Witness yang belum bet: " + ", ".join(missing))
        return
    room["status"] = "alignment"
    await _jugement_refresh_message(context, room)
    await _jugement_prompt_next_pair(context, room)

async def _jugement_prompt_next_pair(context, room: dict):
    active = next((p for p in room.get("pairs", []) if not p.get("resolved") and not p.get("locked")), None)
    if not active:
        await _jugement_finish(context, room)
        return
    s = room["players"][active["sinner_uid"]]
    w = room["players"][active["witness_uid"]]
    text = ("⚖️ Giliran pemihakan.\n\n" f"Pendosa : {s.get('name')}\n" f"Saksi : {w.get('name')}\n" f"Ronde : {active.get('round', 1)}\n\n" "Masing-masing pihak pilih Take, Pass, atau Lock. Kalau salah satu Lock, analisis langsung dimulai. Kalau Take/Pass berbeda, Penguasa tidak memberi kartu tambahan.")
    await context.bot.send_message(chat_id=room.get("chat_id"), text=text, reply_markup=_jugement_pair_keyboard(room.get("chat_id"), active.get("id")))

async def jugement_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 4:
        return
    _, chat_id_raw, pair_id_raw, action = parts
    try:
        chat_id = int(chat_id_raw); pair_id = int(pair_id_raw)
    except Exception:
        await query.answer("Data persidangan tidak valid.", show_alert=True)
        return
    room = JUGEMENT_ROOMS.get(_jugement_room_key(chat_id))
    if not room or room.get("status") != "alignment":
        await query.answer("Fase pemihakan tidak aktif.", show_alert=True)
        return
    await _jugement_handle_action(context, room, query.from_user, pair_id, action, query.message)

async def _jugement_handle_action(context, room: dict, user, pair_id: int, action: str, reply_msg=None):
    pair = next((p for p in room.get("pairs", []) if int(p.get("id")) == int(pair_id)), None)
    if not pair or pair.get("resolved"):
        if reply_msg: await reply_msg.reply_text("Sesi pasangan ini telah mencapai akhirnya.")
        return
    uid = str(user.id)
    if uid not in (str(pair.get("sinner_uid")), str(pair.get("witness_uid"))):
        if reply_msg: await reply_msg.reply_text("Namamu tidak tercatat dalam pasangan persidangan ini.")
        return
    if action not in ("take", "pass", "lock"):
        return
    role = "Pendosa" if uid == str(pair.get("sinner_uid")) else "Saksi"
    if action == "lock":
        pair["locked"] = True
        pair["resolved"] = True
        await context.bot.send_message(chat_id=room.get("chat_id"), text=f"{role} {room['players'][uid].get('name')} mengumumkan kesaksian. Analisis pasangan ini dimulai.")
        await _jugement_prompt_next_pair(context, room)
        return
    pair.setdefault("choices", {})[uid] = action
    await context.bot.send_message(chat_id=room.get("chat_id"), text=f"{role} {room['players'][uid].get('name')} memilih {action.upper()}.")
    if pair.get("sinner_uid") in pair.get("choices", {}) and pair.get("witness_uid") in pair.get("choices", {}):
        c1 = pair["choices"].get(pair["sinner_uid"]); c2 = pair["choices"].get(pair["witness_uid"])
        if c1 == "take" and c2 == "take":
            for puid in (pair["sinner_uid"], pair["witness_uid"]):
                card = _jugement_draw(room)
                room["players"][puid].setdefault("cards", []).append(card)
                try:
                    await context.bot.send_message(chat_id=int(puid), text=f"Kartu tambahan: {card}\nTotal: {_jugement_total(room['players'][puid].get('cards') or [])}")
                except Exception:
                    pass
            await context.bot.send_message(chat_id=room.get("chat_id"), text="Keduanya meminta TAKE. Penguasa memberi kartu tambahan kepada kedua pihak.")
        elif c1 != c2:
            await context.bot.send_message(chat_id=room.get("chat_id"), text="Pendosa dan Saksi berbeda pendapat. Penguasa tidak memberi kartu tambahan.")
        else:
            await context.bot.send_message(chat_id=room.get("chat_id"), text="Keduanya memilih PASS. Tidak ada kartu tambahan.")
        pair["choices"] = {}
        pair["round"] = int(pair.get("round", 1)) + 1
        if pair["round"] > 5:
            pair["resolved"] = True
            await context.bot.send_message(chat_id=room.get("chat_id"), text="Batas pemihakan tercapai. Pasangan ini masuk analisis.")
        await _jugement_prompt_next_pair(context, room)

async def jugement_take_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _jugement_command_action(update, context, "take")
async def jugement_pass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _jugement_command_action(update, context, "pass")
async def jugement_lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _jugement_command_action(update, context, "lock")

async def _jugement_command_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    if chat.type == "private":
        return
    room = JUGEMENT_ROOMS.get(_jugement_room_key(chat.id))
    if not room or room.get("status") != "alignment":
        return
    uid = str(update.effective_user.id)
    pair = next((p for p in room.get("pairs", []) if uid in (str(p.get("sinner_uid")), str(p.get("witness_uid"))) and not p.get("resolved")), None)
    if not pair:
        await update.message.reply_text("Belum ada giliran pemihakan yang tertuju padamu.")
        return
    await _jugement_handle_action(context, room, update.effective_user, int(pair.get("id")), action, update.message)

async def _jugement_finish(context, room: dict):
    lines = ["⚖️ HASIL JUGEMENT DE CARDINALE", ""]
    for pair in room.get("pairs", []):
        s_uid = pair["sinner_uid"]; w_uid = pair["witness_uid"]
        s = room["players"][s_uid]; w = room["players"][w_uid]
        s_total = _jugement_total(s.get("cards") or []); w_total = _jugement_total(w.get("cards") or [])
        s_dist = _jugement_distance(s_total); w_dist = _jugement_distance(w_total)
        bet = int(pair.get("bet") or 0)
        s_rec = _get_existing_account(int(s_uid)); w_rec = _get_existing_account(int(w_uid))
        if s_dist == w_dist:
            result = "DRAW"; bonus = 100000
            if s_rec: s_rec["balance"] = int(s_rec.get("balance", 0)) + bonus
            if w_rec: w_rec["balance"] = int(w_rec.get("balance", 0)) + bonus
            settlement = f"Draw. Keduanya mendapat kompensasi {_normalize_price_text(bonus)} ✦𝕷."
        elif s_dist < w_dist:
            result = "Pendosa tidak bersalah"
            if s_rec: s_rec["balance"] = int(s_rec.get("balance", 0)) + bet
            if w_rec: w_rec["balance"] = max(0, int(w_rec.get("balance", 0)) - bet)
            settlement = f"Pendosa menerima kompensasi {_normalize_price_text(bet)} ✦✦𝕷; Saksi terkena denda."
        else:
            result = "Saksi membuktikan pembelaan"
            if w_rec: w_rec["balance"] = int(w_rec.get("balance", 0)) + bet
            if s_rec: s_rec["balance"] = max(0, int(s_rec.get("balance", 0)) - bet)
            settlement = f"Saksi menerima kompensasi {_normalize_price_text(bet)} ✦𝕷; Pendosa terkena denda."
        lines.extend([f"Pendosa : {s.get('name')} | {_format_cards(s.get('cards') or [])} = {s_total}", f"Saksi : {w.get('name')} | {_format_cards(w.get('cards') or [])} = {w_total}", f"Putusan : {result}", f"Settlement : {settlement}", ""])
    save_accounts()
    room["status"] = "resolved"
    await _jugement_refresh_message(context, room)
    await context.bot.send_message(chat_id=room.get("chat_id"), text="\n".join(lines).strip(), reply_to_message_id=room.get("message_id"))
    JUGEMENT_ROOMS.pop(_jugement_room_key(room.get("chat_id")), None)

async def bang_game_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text or not update.effective_chat or update.effective_chat.type == "private":
        return
    text = msg.text.strip(); low = text.lower()
    if low in ("!join jugement", "!join jugdment", "!join judgment"):
        room = JUGEMENT_ROOMS.get(_jugement_room_key(update.effective_chat.id))
        if room and room.get("status") == "waiting":
            await _jugement_add_player(context, room, update.effective_user, msg)
        return
    if low.startswith("!bet"):
        context.args = text.split()[1:]
        await jugement_bet_cmd(update, context)
        return
    if low in ("!take", "!pass", "!lock"):
        await _jugement_command_action(update, context, low[1:])
        return


# =========================================================
# FEATURE: THE ALLURING SYMPHONY
# =========================================================
SYMPHONY_CHORDS = ["A", "B", "C", "D", "E", "F", "G"]
SYMPHONY_INSTRUMENTS = [
    ("violin", "🔴 Violin"),
    ("piano", "🔵 Piano"),
    ("flute", "🟡 Flute"),
    ("drum", "🟣 Drum"),
    ("harp", "⚪ Harp"),
]
SYMPHONY_STAGE_SCORE = {0: 0, 1: 10, 2: 20, 3: 30, 4: 10, 5: 0, 6: -10, 7: -20, 8: -30, 9: -40}


def _symphony_room_key(chat_id: int) -> str:
    return str(chat_id)


def _symphony_new_deck():
    return [{"chord": c, "instrument": k, "label": v} for c in SYMPHONY_CHORDS for k, v in SYMPHONY_INSTRUMENTS]


def _symphony_shuffle_deck():
    import random
    deck = _symphony_new_deck()
    random.shuffle(deck)
    return deck


def _symphony_card_text(card: dict, effective: bool = False) -> str:
    if not card:
        return "-"
    chord = card.get("effective_chord") if effective and card.get("effective_chord") else card.get("chord")
    out = f"{card.get('label', card.get('instrument', '-'))} {chord}"
    if effective and card.get("effective_chord") and card.get("effective_chord") != card.get("chord"):
        out += f" (from {card.get('chord')})"
    return out


def _symphony_chord_shift(chord: str, delta: int) -> str:
    if chord not in SYMPHONY_CHORDS:
        return chord
    return SYMPHONY_CHORDS[(SYMPHONY_CHORDS.index(chord) + int(delta)) % len(SYMPHONY_CHORDS)]


def _symphony_strength(chord: str, key_chord: str) -> int:
    if chord not in SYMPHONY_CHORDS or key_chord not in SYMPHONY_CHORDS:
        return 99
    return (SYMPHONY_CHORDS.index(chord) - SYMPHONY_CHORDS.index(key_chord)) % len(SYMPHONY_CHORDS)


def _symphony_waiting_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join", callback_data="symphony:join"), InlineKeyboardButton("Leave", callback_data="symphony:leave")],
        [InlineKeyboardButton("Start", callback_data="symphony:start"), InlineKeyboardButton("Close", callback_data="symphony:close")],
    ])


def _symphony_status_text(room: dict) -> str:
    lines = [
        "⛃ ⛁ · THE ALLURING SYMPHONY",
        "",
        f"Status : {(room.get('status') or 'waiting').upper()}",
        f"Stage : {room.get('stage', 0)}/3",
        f"Key : {room.get('key_chord') or '-'}",
        f"Bet : {_normalize_price_text(room.get('bet', 0))} ✦𝕷" if int(room.get("bet", 0) or 0) > 0 else "Bet : Free play",
        "",
        "Players:",
    ]
    players = room.get("players") or {}
    if not players:
        lines.append("› -")
    else:
        for uid, p in players.items():
            stage_tricks = int((p.get("stats") or {}).get("stage_tricks", 0))
            lines.append(f"› {p.get('name', 'Player')} | Score {int(p.get('score', 0))} | Trick {stage_tricks} | Spotlight {int(p.get('spotlight', 0))}")
    if room.get("status") == "waiting":
        lines.extend([
            "",
            "[ 𝗛𝗢𝗪 𝗧𝗢 𝗣𝗟𝗔𝗬 . ]",
            "",
            "O1. Setiap pemain memainkan 1 kartu per ronde (Trick).",
            "2. Tujuan: mendapatkan skor terbaik, bukan selalu menang.",
            "O3. Setiap kartu memiliki:",
            "ㅤㅤ• Chord (A–G)",
            "ㅤㅤ• Instrument (warna)",
            "",
            "---",
            "[ 𝗜𝗡𝗦𝗧𝗥𝗨𝗠𝗘𝗡𝗧 . ]",
            "",
            "🔴 Violin → +1 poin jika menang",
            "🔵 Piano → bisa ubah nilai chord ±1",
            "🟡 Flute → bebas dari aturan warna",
            "🟣 Drum → memicu Key Change",
            "",
            "---",
            "[ 𝗚𝗔𝗠𝗘 𝗙𝗟𝗢𝗪 . ]",
            "",
            "O1. Setiap pemain mendapat 8 kartu per Stage.",
            "O2. 1 kartu dibuka sebagai Key (terkuat).",
            "O3. Leader memulai dengan memainkan 1 kartu.",
            "O4. Player lain harus mengikuti aturan:",
            "ㅤㅤ• Jika punya warna yang sama → wajib ikut",
            "ㅤㅤ• Jika tidak punya → bebas",
            "ㅤㅤ• Flute → selalu bebas",
            "O5. Setelah semua pemain bermain, Trick diselesaikan.",
            "",
            "---",
            "[ 𝗧𝗥𝗜𝗖𝗞 𝗥𝗘𝗦𝗨𝗟𝗧 . ]",
            "",
            "O1. Pemenang ditentukan dari Chord terkuat.",
            "O2. Jika sama → warna Leader menang.",
            "O3. Jika masih sama → yang main dulu menang.",
            "",
            "---",
            "[ 𝗞𝗘𝗬 𝗖𝗛𝗔𝗡𝗚𝗘 . ]",
            "",
            "Terjadi jika:",
            "ㅤㅤ• Chord yang sama muncul 2x",
            "ㅤㅤ• Drum dimainkan",
            "",
            "Efek:",
            "ㅤㅤ→ Player terakhir menjadi Leader baru",
            "",
            "---",
            "[ 𝗦𝗖𝗢𝗥𝗘 . ]",
            "",
            "0 → 0",
            "1 → 10",
            "2 → 20",
            "3 → 30",
            "4 → 10",
            "5 → 0",
            "6 → -10",
            "7 → -20",
            "8 → -30",
            "",
            "---",
            "[ 𝗥𝗨𝗟𝗘𝗦 . ]",
            "",
            "Jangan over-win (terlalu banyak menang = minus)",
            "Gunakan strategi, bukan brute force",
            "Leader menentukan flow permainan",
        ])
    elif room.get("status") == "playing":
        turn_uid = str(room.get("turn_uid") or "")
        if turn_uid in players:
            lines.extend(["", f"Turn : {players[turn_uid].get('name')}"])
    return "\n".join(lines)


async def _symphony_refresh_message(context, room: dict):
    if not room.get("message_id"):
        return
    try:
        await context.bot.edit_message_text(
            chat_id=room.get("chat_id"),
            message_id=room.get("message_id"),
            text=_symphony_status_text(room),
            reply_markup=_symphony_waiting_keyboard() if room.get("status") == "waiting" else None,
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[_symphony_refresh_message] error: {e}")


async def alluringsymphony_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("The Alluring Symphony hanya dapat dibuka di ruang group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Nomor account perlu kau miliki sebelum membuka The Alluring Symphony.")
        return
    key = _symphony_room_key(chat.id)
    if key in ALLURING_ROOMS:
        await update.message.reply_text("Masih ada room The Alluring Symphony yang bernyawa di grup ini.")
        return
    bet = 0
    if context.args:
        parsed = _parse_bet_amount(context.args[0])
        if parsed is None:
            await update.message.reply_text("Format titah: /symphony atau /symphony <nominal_bet>")
            return
        bet = int(parsed)
        if bet > int(rec.get("balance", 0)):
            await update.message.reply_text(f"Saldo kamu tidak cukup. Saldo sekarang: {_normalize_price_text(rec.get('balance', 0))} ✦𝕷")
            return
    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "host_name": user.full_name or user.username or f"User {user.id}",
        "status": "waiting",
        "bet": bet,
        "players": {str(user.id): {"name": user.full_name or user.username or f"User {user.id}", "hand": [], "score": 0, "spotlight": 0, "violin_bonus": 0, "stats": {"stage_tricks": 0}}},
        "player_order": [str(user.id)],
        "stage": 0,
        "trick_no": 0,
        "leader_uid": str(user.id),
        "turn_uid": None,
        "turn_index": 0,
        "current_trick": None,
        "message_id": None,
    }
    sent = await update.message.reply_text(
        _symphony_status_text(room),
        reply_markup=_symphony_waiting_keyboard(),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    room["message_id"] = sent.message_id
    ALLURING_ROOMS[key] = room


async def symphony_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    room = ALLURING_ROOMS.get(_symphony_room_key(chat_id))
    if not room:
        await query.answer("Room Symphony tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    uid = str(query.from_user.id)
    if action == "join":
        if room.get("status") != "waiting":
            await query.answer("Game sudah berjalan.", show_alert=True)
            return
        if uid in room.get("players", {}):
            await query.answer("Kamu sudah join.")
            return
        if len(room.get("players", {})) >= 4:
            await query.answer("Room ini khusus 4 pemain.", show_alert=True)
            return
        rec = _get_existing_account(query.from_user.id)
        if not _has_gamble_access(rec):
            await query.answer("Kamu harus punya account number dulu.", show_alert=True)
            return
        if int(room.get("bet", 0) or 0) > int(rec.get("balance", 0)):
            await query.answer("Saldo kamu tidak cukup untuk bet room ini.", show_alert=True)
            return
        room["players"][uid] = {"name": query.from_user.full_name or query.from_user.username or f"User {uid}", "hand": [], "score": 0, "spotlight": 0, "violin_bonus": 0, "stats": {"stage_tricks": 0}}
        room.setdefault("player_order", []).append(uid)
        await _symphony_refresh_message(context, room)
        return
    if action == "leave":
        if room.get("status") != "waiting":
            await query.answer("Game sudah berjalan.", show_alert=True)
            return
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Close room kalau batal.", show_alert=True)
            return
        room.get("players", {}).pop(uid, None)
        room["player_order"] = [x for x in room.get("player_order", []) if str(x) != uid]
        await _symphony_refresh_message(context, room)
        return
    if action == "close":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya pembuka room/admin yang bisa close.", show_alert=True)
            return
        ALLURING_ROOMS.pop(_symphony_room_key(chat_id), None)
        await query.edit_message_text("Room The Alluring Symphony telah ditutup.")
        return
    if action == "start":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya pembuka room/admin yang bisa mulai.", show_alert=True)
            return
        if len(room.get("players", {})) != 4:
            await query.answer("The Alluring Symphony butuh tepat 4 pemain.", show_alert=True)
            return
        for puid in room.get("player_order", []):
            rec = _get_existing_account(int(puid))
            if not rec or int(rec.get("balance", 0)) < int(room.get("bet", 0) or 0):
                await query.answer("Ada pemain yang saldonya tidak cukup / account hilang.", show_alert=True)
                return
        await _symphony_start_stage(context, room, first=True)


async def _symphony_start_stage(context, room: dict, first: bool = False):
    import random
    room["status"] = "playing"
    room["stage"] = int(room.get("stage", 0)) + 1
    room["trick_no"] = 0
    room["current_trick"] = None
    deck = _symphony_shuffle_deck()
    order = list(room.get("player_order") or room.get("players", {}).keys())
    for p in room.get("players", {}).values():
        p["hand"] = []
        p.setdefault("stats", {})["stage_tricks"] = 0
    for _ in range(8):
        for uid in order:
            room["players"][uid]["hand"].append(deck.pop())
    aside = [deck.pop(), deck.pop(), deck.pop()]
    room["aside"] = aside
    room["key_chord"] = aside[0].get("chord")
    if first or not room.get("leader_uid"):
        room["leader_uid"] = random.choice(order)
    await _symphony_refresh_message(context, room)
    await context.bot.send_message(
        chat_id=room.get("chat_id"),
        text=f"🎼 Stage {room['stage']} dimulai.\nKartu Key terbuka: {_symphony_card_text(aside[0])}\nKey terkuat: {room['key_chord']}\n\nAsmoday membagikan 8 kartu ke tiap pemain melalui DM.",
    )
    dm_failed = []
    for uid in order:
        try:
            await context.bot.send_message(chat_id=int(uid), text=_symphony_hand_text(room, uid))
        except Exception:
            dm_failed.append(room["players"][uid].get("name"))
    if dm_failed:
        await context.bot.send_message(chat_id=room.get("chat_id"), text="⚠️ DM gagal ke: " + ", ".join(dm_failed) + ". Minta mereka /start bot dulu, lalu buka ulang room.")
        ALLURING_ROOMS.pop(_symphony_room_key(room.get("chat_id")), None)
        return
    await _symphony_begin_trick(context, room)


def _symphony_hand_text(room: dict, uid: str) -> str:
    hand = room.get("players", {}).get(str(uid), {}).get("hand") or []
    lines = ["⌜ The Alluring Symphony — Hand ⌟", f"Stage : {room.get('stage')}/3", f"Key : {room.get('key_chord')}", ""]
    for i, card in enumerate(hand, start=1):
        lines.append(f"{i}. {_symphony_card_text(card)}")
    return "\n".join(lines)


def _symphony_valid_card_indexes(room: dict, uid: str):
    hand = room.get("players", {}).get(str(uid), {}).get("hand") or []
    lead = (room.get("current_trick") or {}).get("lead_instrument")
    if not lead:
        return list(range(len(hand)))
    has_lead = any(c.get("instrument") == lead for c in hand)
    if not has_lead:
        return list(range(len(hand)))
    return [i for i, c in enumerate(hand) if c.get("instrument") == lead or c.get("instrument") == "flute"]


def _symphony_play_keyboard(room: dict, uid: str):
    hand = room.get("players", {}).get(str(uid), {}).get("hand") or []
    valid = set(_symphony_valid_card_indexes(room, uid))
    rows = []
    for i, card in enumerate(hand):
        label = f"{i+1}. {_symphony_card_text(card)}"
        if i not in valid:
            label = "× " + label
        rows.append([InlineKeyboardButton(label[:40], callback_data=f"symphonyplay:{room.get('chat_id')}:{i}")])
    return InlineKeyboardMarkup(rows)


async def _symphony_begin_trick(context, room: dict):
    room["trick_no"] = int(room.get("trick_no", 0)) + 1
    leader = str(room.get("leader_uid") or (room.get("player_order") or [None])[0])
    order = list(room.get("player_order") or [])
    if leader in order:
        start = order.index(leader)
        turn_order = order[start:] + order[:start]
    else:
        turn_order = order
    room["current_trick"] = {"plays": [], "turn_order": turn_order, "lead_instrument": None, "awaiting_piano": None}
    room["turn_index"] = 0
    room["turn_uid"] = turn_order[0] if turn_order else None
    await _symphony_refresh_message(context, room)
    await context.bot.send_message(chat_id=room.get("chat_id"), text=f"🎵 Stage {room.get('stage')} Trick {room.get('trick_no')} dimulai. Leader: {room['players'][room['turn_uid']].get('name')}.")
    await _symphony_prompt_turn(context, room)


async def _symphony_prompt_turn(context, room: dict):
    uid = str(room.get("turn_uid"))
    if not uid or uid not in room.get("players", {}):
        return
    lead = (room.get("current_trick") or {}).get("lead_instrument")
    lead_text = f"Lead Color : {lead.title()}" if lead else "Kamu adalah Leader. Mainkan kartu apa saja."
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=f"⌜ The Alluring Symphony — Your Turn ⌟\nStage {room.get('stage')} Trick {room.get('trick_no')}\nKey : {room.get('key_chord')}\n{lead_text}\n\nPilih kartu yang ingin dimainkan.",
            reply_markup=_symphony_play_keyboard(room, uid),
        )
    except Exception as e:
        print(f"[_symphony_prompt_turn] DM failed: {e}")
        await context.bot.send_message(chat_id=room.get("chat_id"), text=f"⚠️ Tidak bisa DM {room['players'][uid].get('name')}. Game dibatalkan.")
        ALLURING_ROOMS.pop(_symphony_room_key(room.get("chat_id")), None)


async def symphony_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return
    try:
        chat_id = int(parts[1])
        idx = int(parts[2])
    except Exception:
        await query.answer("Data kartu tidak valid.", show_alert=True)
        return
    room = ALLURING_ROOMS.get(_symphony_room_key(chat_id))
    if not room or room.get("status") != "playing":
        await query.answer("Room Symphony tidak aktif.", show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid != str(room.get("turn_uid")):
        await query.answer("Belum giliranmu.", show_alert=True)
        return
    hand = room.get("players", {}).get(uid, {}).get("hand") or []
    if idx < 0 or idx >= len(hand):
        await query.answer("Kartu tidak ditemukan.", show_alert=True)
        return
    if idx not in _symphony_valid_card_indexes(room, uid):
        await query.answer("Kartu ini tidak boleh dimainkan karena Lead Color wajib diikuti, kecuali Flute.", show_alert=True)
        return
    card = dict(hand.pop(idx))
    card["effective_chord"] = card.get("chord")
    trick = room.get("current_trick") or {}
    if not trick.get("lead_instrument"):
        trick["lead_instrument"] = card.get("instrument")
    trick.setdefault("plays", []).append({"uid": uid, "card": card, "order": len(trick.get("plays") or [])})
    room["current_trick"] = trick
    try:
        await query.edit_message_text(f"Kamu memainkan: {_symphony_card_text(card)}")
    except Exception:
        pass
    await context.bot.send_message(chat_id=chat_id, text=f"{room['players'][uid].get('name')} memainkan {_symphony_card_text(card)}.")
    if card.get("instrument") == "piano":
        trick["awaiting_piano"] = uid
        await query.message.reply_text(
            "🔵 Piano dapat menggeser Chord kartu ini sekali.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("-1", callback_data=f"symphonypiano:{chat_id}:-1"), InlineKeyboardButton("Tetap", callback_data=f"symphonypiano:{chat_id}:0"), InlineKeyboardButton("+1", callback_data=f"symphonypiano:{chat_id}:1")]]),
        )
        return
    await _symphony_after_card_finalized(context, room)


async def symphony_piano_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return
    try:
        chat_id = int(parts[1])
        delta = int(parts[2])
    except Exception:
        await query.answer("Data Piano tidak valid.", show_alert=True)
        return
    room = ALLURING_ROOMS.get(_symphony_room_key(chat_id))
    if not room or room.get("status") != "playing":
        await query.answer("Room Symphony tidak aktif.", show_alert=True)
        return
    uid = str(query.from_user.id)
    trick = room.get("current_trick") or {}
    if str(trick.get("awaiting_piano")) != uid:
        await query.answer("Pilihan Piano ini bukan untukmu.", show_alert=True)
        return
    play = (trick.get("plays") or [])[-1]
    card = play.get("card") or {}
    old = card.get("effective_chord") or card.get("chord")
    card["effective_chord"] = _symphony_chord_shift(card.get("chord"), delta)
    card["piano_shift"] = delta
    trick["awaiting_piano"] = None
    try:
        await query.edit_message_text(f"Piano shift: {old} → {card.get('effective_chord')}")
    except Exception:
        pass
    await context.bot.send_message(chat_id=chat_id, text=f"🔵 Piano mengubah chord menjadi {card.get('effective_chord')} untuk {room['players'][uid].get('name')}.")
    await _symphony_after_card_finalized(context, room)


async def _symphony_after_card_finalized(context, room: dict):
    trick = room.get("current_trick") or {}
    turn_order = trick.get("turn_order") or []
    if len(trick.get("plays") or []) >= len(turn_order):
        await _symphony_resolve_trick(context, room)
        return
    room["turn_index"] = int(room.get("turn_index", 0)) + 1
    room["turn_uid"] = turn_order[int(room.get("turn_index", 0))]
    await _symphony_refresh_message(context, room)
    await _symphony_prompt_turn(context, room)


def _symphony_key_changer_from_trick(trick: dict):
    plays = trick.get("plays") or []
    counts = {}
    for play in plays:
        card = play.get("card") or {}
        chord = card.get("effective_chord") or card.get("chord")
        counts.setdefault(chord, []).append(play)
    repeated = {c: ps for c, ps in counts.items() if len(ps) >= 2}
    if not repeated:
        return None
    if len(repeated) >= 2 and plays:
        leader_card = plays[0].get("card") or {}
        leader_chord = leader_card.get("effective_chord") or leader_card.get("chord")
        if leader_chord in repeated:
            return repeated[leader_chord][-1].get("uid")
    for play in reversed(plays):
        card = play.get("card") or {}
        chord = card.get("effective_chord") or card.get("chord")
        if chord in repeated:
            return play.get("uid")
    return None


async def _symphony_resolve_trick(context, room: dict):
    trick = room.get("current_trick") or {}
    plays = trick.get("plays") or []
    lead = trick.get("lead_instrument")
    key = room.get("key_chord")

    def sort_key(play):
        card = play.get("card") or {}
        chord = card.get("effective_chord") or card.get("chord")
        return (_symphony_strength(chord, key), 0 if card.get("instrument") == lead else 1, int(play.get("order", 99)))

    winner_play = sorted(plays, key=sort_key)[0]
    winner_uid = str(winner_play.get("uid"))
    winner_card = winner_play.get("card") or {}
    stats = room["players"][winner_uid].setdefault("stats", {})
    stats["stage_tricks"] = int(stats.get("stage_tricks", 0)) + 1
    if (winner_card.get("effective_chord") or winner_card.get("chord")) == key:
        room["players"][winner_uid]["spotlight"] = int(room["players"][winner_uid].get("spotlight", 0)) + 1
    if winner_card.get("instrument") == "violin":
        room["players"][winner_uid]["violin_bonus"] = int(room["players"][winner_uid].get("violin_bonus", 0)) + 1
        room["players"][winner_uid]["score"] = int(room["players"][winner_uid].get("score", 0)) + 1
    key_changer_uid = _symphony_key_changer_from_trick(trick)
    room["leader_uid"] = str(key_changer_uid or winner_uid)
    lines = [f"🏆 Trick {room.get('trick_no')} selesai.", ""]
    for play in plays:
        lines.append(f"› {room['players'][str(play.get('uid'))].get('name')} : {_symphony_card_text(play.get('card'), effective=True)}")
    lines.extend(["", f"Winner : {room['players'][winner_uid].get('name')}"])
    if key_changer_uid:
        lines.append(f"Key Change Leader : {room['players'][str(key_changer_uid)].get('name')}")
    if winner_card.get("instrument") == "violin":
        lines.append("🔴 Violin bonus: +1 point.")
    await context.bot.send_message(chat_id=room.get("chat_id"), text="\n".join(lines))
    await _symphony_refresh_message(context, room)
    if all(len((p.get("hand") or [])) == 0 for p in room.get("players", {}).values()):
        await _symphony_finish_stage(context, room)
    else:
        await _symphony_begin_trick(context, room)


async def _symphony_finish_stage(context, room: dict):
    lines = [f"📊 Stage {room.get('stage')} selesai.", ""]
    for uid in room.get("player_order", []):
        pdata = room["players"][uid]
        tricks = int((pdata.get("stats") or {}).get("stage_tricks", 0))
        stage_score = int(SYMPHONY_STAGE_SCORE.get(tricks, -40))
        pdata["score"] = int(pdata.get("score", 0)) + stage_score
        lines.append(f"› {pdata.get('name')} | Tricks {tricks} = {stage_score} | Total {pdata.get('score')}")
    await context.bot.send_message(chat_id=room.get("chat_id"), text="\n".join(lines))
    if int(room.get("stage", 0)) >= 3:
        await _symphony_finish_game(context, room)
        return
    await _symphony_start_stage(context, room)


async def _symphony_finish_game(context, room: dict):
    players = room.get("players") or {}
    best = max(int(p.get("score", 0)) for p in players.values()) if players else 0
    winners = [uid for uid, p in players.items() if int(p.get("score", 0)) == best]
    bet = int(room.get("bet", 0) or 0)
    settlement = []
    if bet > 0:
        pot = bet * len(players)
        share = pot // len(winners)
        for uid in players:
            rec = _get_existing_account(int(uid))
            if rec:
                rec["balance"] = max(0, int(rec.get("balance", 0)) - bet)
        for uid in winners:
            rec = _get_existing_account(int(uid))
            if rec:
                rec["balance"] = int(rec.get("balance", 0)) + share
        save_accounts()
        settlement.append(f"Pot : {_normalize_price_text(pot)} ✦𝕷 | Winner share : {_normalize_price_text(share)} ✦ℒ")
    lines = ["🎼 THE ALLURING SYMPHONY — FINAL RESULT", ""]
    for uid in room.get("player_order", []):
        pdata = players[uid]
        lines.append(f"› {pdata.get('name')} | Score {int(pdata.get('score', 0))} | Spotlight {int(pdata.get('spotlight', 0))} | Violin Bonus {int(pdata.get('violin_bonus', 0))}")
    lines.extend(["", "Winner : " + ", ".join(players[uid].get("name") for uid in winners)])
    lines.extend(settlement)
    await context.bot.send_message(chat_id=room.get("chat_id"), text="\n".join(lines).strip(), reply_to_message_id=room.get("message_id"))
    ALLURING_ROOMS.pop(_symphony_room_key(room.get("chat_id")), None)


# =========================================================
# FEATURE: ID CARD IMAGE
# =========================================================
def _idcard_template_info(rec: dict):
    """Pilih template IDC dan warna teks sesuai jenis akun."""
    base = Path(IDCARD_ASSET_DIR)
    account_type = (rec.get("account_type") or "").strip().lower()
    membership_type = (rec.get("membership_type") or "").strip().lower()

    staff_path = base / "staff_idc.png"
    vip_path = base / IDCARD_MEMBER_DIR / IDCARD_MEMBER_VIP_FILE
    reg_path = base / IDCARD_MEMBER_DIR / IDCARD_MEMBER_REG_FILE

    if account_type in ("staff", "owner"):
        return staff_path, (209, 211, 212, 255), "staff"
    if membership_type == "vip":
        return vip_path, (209, 211, 212, 255), "vip"
    return reg_path, (0, 0, 0, 255), "regular"


def _idcard_template_path(rec: dict | None = None):
    if rec is None:
        rec = {}
    primary, _, _ = _idcard_template_info(rec)
    candidates = [
        primary,
        Path(IDCARD_ASSET_DIR) / "staff_idc.png",
        Path(IDCARD_ASSET_DIR) / IDCARD_TEMPLATE_FILE,
        Path(IDCARD_ASSET_DIR) / "Staff IDC.png",
        Path(IDCARD_ASSET_DIR) / "idcard_staff.png",
        Path.cwd() / IDCARD_TEMPLATE_FILE,
        Path(__file__).resolve().parent / IDCARD_TEMPLATE_FILE,
    ]
    for pth in candidates:
        if pth.exists():
            return pth
    return primary


def _idcard_font(names, size):
    if not IDCARD_IMAGE_AVAILABLE or ImageFont is None:
        return None
    for name in names:
        try:
            return ImageFont.truetype(name, int(round(float(size))))
        except Exception:
            pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _idcard_text_width(draw, text, font):
    try:
        box = draw.textbbox((0, 0), str(text), font=font)
        return box[2] - box[0]
    except Exception:
        return len(str(text)) * 10


def _idcard_draw_text_fit(draw, xy, text, font_names, max_width, size, fill=(226, 226, 226, 255), min_size=8, uppercase=True):
    text = str(text or "-")
    if uppercase:
        text = text.upper()
    cur_size = int(round(float(size)))
    font = _idcard_font(font_names, cur_size)
    while font and cur_size > int(min_size):
        if _idcard_text_width(draw, text, font) <= max_width:
            break
        cur_size -= 1
        font = _idcard_font(font_names, cur_size)
    draw.text(xy, text, font=font, fill=fill)
    return font


def _idcard_crop_cover(img, target_size):
    tw, th = target_size
    img = img.convert("RGBA")
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return Image.new("RGBA", target_size, (0, 0, 0, 0))
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return img.crop((left, top, left + tw, top + th))


def _idcard_photo_mask(size, radius=0):
    return Image.new("L", size, 255)


def _idcard_date_only(value):
    if not value:
        return "-"
    text = str(value).strip()
    if " " in text:
        return text.split(" ", 1)[0]
    if "|" in text:
        return text.split("|", 1)[0].strip()
    return text[:10] if len(text) >= 10 else text


def _idcard_member_status_text(rec: dict) -> str:
    account_type = (rec.get("account_type") or "").strip().lower()
    if account_type == "owner":
        return "OWNER"
    if account_type == "staff":
        return rec.get("staff_role") or "STAFF"

    membership_type = (rec.get("membership_type") or "Regular").strip()
    _refresh_membership_status(rec)
    status = (rec.get("membership_status") or "deactive").strip().lower()
    status_text = "ACTIVE MEMBER" if status == "active" else "NON ACTIVE MEMBER"
    return f"{membership_type} - {status_text}"


def _idcard_photo_cache_path(user_id) -> Path:
    cache_dir = BASE_DIR / "idc-photo-cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return cache_dir / f"{user_id}.png"


async def _telegram_get_file_with_timeout(context, file_id):
    try:
        return await context.bot.get_file(
            file_id,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
        )
    except TypeError:
        return await context.bot.get_file(file_id)


async def _telegram_download_file_to_memory(tg_file, bio: BytesIO):
    try:
        await tg_file.download_to_memory(
            out=bio,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
        )
    except TypeError:
        await tg_file.download_to_memory(out=bio)


async def _idcard_load_user_photo(context, user, rec, log_prefix="_render_idcard_png"):
    """Load IDC photo with bigger Telegram timeout + local cache fallback."""
    selected_file_id = (rec or {}).get("idcard_photo_file_id")

    if not selected_file_id:
        try:
            try:
                photos = await context.bot.get_user_profile_photos(
                    user.id,
                    limit=1,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
            except TypeError:
                photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos and photos.total_count and photos.photos:
                selected_file_id = photos.photos[0][-1].file_id
        except Exception as e:
            print(f"[{log_prefix}] profile photo lookup error: {e}")

    cache_path = _idcard_photo_cache_path(getattr(user, "id", "unknown"))

    if selected_file_id:
        for attempt in range(2):
            try:
                tg_file = await _telegram_get_file_with_timeout(context, selected_file_id)
                bio = BytesIO()
                await _telegram_download_file_to_memory(tg_file, bio)
                bio.seek(0)
                img = Image.open(bio).convert("RGBA")
                try:
                    img.save(cache_path, format="PNG")
                except Exception as cache_err:
                    print(f"[{log_prefix}] photo cache save error: {cache_err}")
                return img
            except Exception as e:
                print(f"[{log_prefix}] IDC photo download error attempt {attempt + 1}: {e}")

    if cache_path.exists():
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception as e:
            print(f"[{log_prefix}] photo cache load error: {e}")

    return None


async def _render_staff_idcard_png(context, user, rec):
    """Render IDC khusus staff/owner memakai layout staff lama (portrait, info simpel)."""
    if not IDCARD_IMAGE_AVAILABLE:
        return None, "Library Pillow belum tersedia. Install dulu dengan: pip install pillow"

    base = Path(IDCARD_ASSET_DIR)
    font_base = Path(IDCARD_FONT_DIR)
    candidates = [
        base / "staff_idc.png",
        base / "Staff IDC.png",
        base / IDCARD_TEMPLATE_FILE,
        base / "idcard_staff.png",
        Path.cwd() / IDCARD_TEMPLATE_FILE,
        Path(__file__).resolve().parent / IDCARD_TEMPLATE_FILE,
    ]
    template_path = next((x for x in candidates if x.exists()), candidates[0])
    if not template_path.exists():
        return None, f"Template IDC staff tidak ditemukan: {template_path}"

    template = Image.open(template_path).convert("RGBA")
    w, h = template.size
    staff_base_w = 984
    staff_base_h = 1536
    staff_photo_w = 670
    staff_photo_h = 906
    sx = w / staff_base_w
    sy = h / staff_base_h

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    profile_img = await _idcard_load_user_photo(context, user, rec, "_render_staff_idcard_png")
    if profile_img is not None:
        photo_box = (
            int(157 * sx),
            int(424 * sy),
            int(staff_photo_w * sx),
            int(staff_photo_h * sy),
        )
        fitted = _idcard_crop_cover(profile_img, (photo_box[2], photo_box[3]))
        mask = Image.new("L", (photo_box[2], photo_box[3]), 0)
        d = ImageDraw.Draw(mask)
        radius = int(335 * sx)
        d.rounded_rectangle((0, 0, photo_box[2], photo_box[3]), radius=radius, fill=255)
        d.rectangle((0, radius, photo_box[2], photo_box[3]), fill=255)
        canvas.paste(fitted, (photo_box[0], photo_box[1]), mask)

    canvas.alpha_composite(template)
    draw = ImageDraw.Draw(canvas)

    codename = rec.get("name") or user.full_name or user.username or "-"
    role = "Owner" if rec.get("account_type") == "owner" else (rec.get("staff_role") or "Staff")
    acc_no = str(rec.get("acc_no", "-"))

    left = int(67.9204 * sx)
    right = int(w - (67.9204 * sx))
    name_y = int(221 * sy)
    role_y = int(292 * sy)
    num_y = int(221 * sy)

    name_font_names = [
        str(font_base / "PlayfairDisplaySC-Bold.ttf"),
        str(font_base / "PlayfairDisplay-Bold.ttf"),
        "PlayfairDisplaySC-Bold.ttf", "PlayfairDisplay-Bold.ttf",
        "Times New Roman Bold.ttf", "Times New Roman.ttf", "Times New Roman",
        "Times New Roman Bold", "/Library/Fonts/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "Georgia Bold.ttf", "DejaVuSerif-Bold.ttf",
    ]
    role_font_names = [
        str(font_base / "dm-sans-9pt-regular.ttf"),
        str(font_base / "DMSans-Regular.ttf"),
        str(font_base / "DMSans_18pt-ExtraBold.ttf"),
        "dm-sans-9pt-regular.ttf", "DM Sans.ttf", "DMSans-Regular.ttf",
        "/Library/Fonts/DM Sans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf",
    ]

    text_fill = (226, 226, 226, 255)
    number_font = _idcard_font(name_font_names, 72.6889 * sx)
    try:
        nb = draw.textbbox((0, 0), acc_no, font=number_font)
        number_w = nb[2] - nb[0]
    except Exception:
        number_w = len(acc_no) * int(72.6889 * sx)

    _idcard_draw_text_fit(
        draw,
        (left, name_y),
        codename,
        name_font_names,
        max_width=max(10, right - left - number_w - int(40 * sx)),
        size=72.6889 * sx,
        fill=text_fill,
        min_size=32 * sx,
        uppercase=True,
    )
    draw.text((right - number_w, num_y), acc_no, font=number_font, fill=text_fill)

    role_font = _idcard_font(role_font_names, 38.988 * sx)
    draw.text((left, role_y), str(role), font=role_font, fill=text_fill)

    out = BytesIO()
    out.name = f"lethea_staff_idcard_{rec.get('acc_no', user.id)}.png"
    canvas.save(out, format="PNG")
    out.seek(0)
    return out, None


async def _render_member_idcard_png(context, user, rec):
    """Render IDC khusus member VIP/Regular memakai layout member detail."""
    if not IDCARD_IMAGE_AVAILABLE:
        return None, "Library Pillow belum tersedia. Install dulu dengan: pip install pillow"

    template_path, text_fill, template_kind = _idcard_template_info(rec)
    if not template_path.exists():
        fallback = _idcard_template_path(rec)
        if fallback.exists():
            template_path = fallback
        else:
            return None, f"Template IDC member tidak ditemukan: {template_path}"

    template = Image.open(template_path).convert("RGBA")
    w, h = template.size
    sx = w / IDCARD_BASE_W
    sy = h / IDCARD_BASE_H

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    profile_img = await _idcard_load_user_photo(context, user, rec, "_render_member_idcard_png")
    if profile_img is not None:
        photo_box = (
            int(IDCARD_PHOTO_SLOT_X * sx),
            int(IDCARD_PHOTO_SLOT_Y * sy),
            int(IDCARD_PHOTO_SLOT_W * sx),
            int(IDCARD_PHOTO_SLOT_H * sy),
        )
        fitted = _idcard_crop_cover(profile_img, (photo_box[2], photo_box[3]))
        mask = _idcard_photo_mask((photo_box[2], photo_box[3]))
        canvas.paste(fitted, (photo_box[0], photo_box[1]), mask)

    canvas.alpha_composite(template)
    draw = ImageDraw.Draw(canvas)

    username = rec.get("username") or getattr(user, "username", None) or "-"
    username = f"@{str(username).lstrip('@')}" if username != "-" else "-"
    full_name = rec.get("full_name") or getattr(user, "full_name", None) or rec.get("name") or "-"
    codename = rec.get("name") or getattr(user, "full_name", None) or getattr(user, "username", None) or "-"
    status = _idcard_member_status_text(rec)
    expired_date = _idcard_date_only(rec.get("membership_expires_at"))
    member_since = _idcard_date_only(rec.get("membership_started_at") or rec.get("created_at"))
    acc_no = str(rec.get("acc_no", "-"))

    dm_sans_extra = [
        str(Path(IDCARD_FONT_DIR) / "DMSans-ExtraBold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "DM Sans ExtraBold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "dm-sans-9pt-extrabold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "DMSans_18pt-ExtraBold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "DMSans-Bold.ttf"),
        "DMSans-ExtraBold.ttf", "DM Sans ExtraBold.ttf", "DMSans-Bold.ttf",
        "Arial Bold.ttf", "Arial.ttf", "Helvetica Bold.ttf", "DejaVuSans-Bold.ttf",
    ]
    playfair = [
        str(Path(IDCARD_FONT_DIR) / "PlayfairDisplay-Bold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "PlayfairDisplaySC-Bold.ttf"),
        str(Path(IDCARD_FONT_DIR) / "PlayfairDisplay-Black.ttf"),
        "PlayfairDisplay-Bold.ttf", "PlayfairDisplaySC-Bold.ttf",
        "Times New Roman Bold.ttf", "Georgia Bold.ttf", "DejaVuSerif-Bold.ttf",
    ]

    x_value = 596.4261 * sx
    y_username = 215.6992 * sy
    y_fullname = 266.0 * sy
    y_codename = 316.5 * sy
    y_status = 367.0 * sy
    y_bottom = 486.0 * sy
    font_size = 16.2 * sx
    max_value_width = 405 * sx

    _idcard_draw_text_fit(draw, (x_value, y_username), username, dm_sans_extra, max_value_width, font_size, fill=text_fill, min_size=10 * sx, uppercase=False)
    _idcard_draw_text_fit(draw, (x_value, y_fullname), full_name, dm_sans_extra, max_value_width, font_size, fill=text_fill, min_size=10 * sx, uppercase=True)
    _idcard_draw_text_fit(draw, (x_value, y_codename), codename, dm_sans_extra, max_value_width, font_size, fill=text_fill, min_size=10 * sx, uppercase=True)
    _idcard_draw_text_fit(draw, (x_value, y_status), status, dm_sans_extra, max_value_width, font_size, fill=text_fill, min_size=9 * sx, uppercase=True)

    _idcard_draw_text_fit(draw, (402 * sx, y_bottom), expired_date, dm_sans_extra, 210 * sx, font_size, fill=text_fill, min_size=10 * sx, uppercase=False)
    member_font = _idcard_font(dm_sans_extra, font_size)
    member_w = _idcard_text_width(draw, member_since, member_font)
    draw.text((963 * sx - member_w, y_bottom), member_since, font=member_font, fill=text_fill)

    number_font = _idcard_font(playfair, 44.1 * sx)
    account_number = str(acc_no)
    account_number_center = (
        (923.7064 + (43.1758 / 2)) * sx,
        (49.205 + (48.4736 / 2)) * sy,
    )
    try:
        draw.text(account_number_center, account_number, font=number_font, fill=text_fill, anchor="mm")
    except TypeError:
        try:
            nb = draw.textbbox((0, 0), account_number, font=number_font)
            number_w = nb[2] - nb[0]
            number_h = nb[3] - nb[1]
        except Exception:
            number_w = len(account_number) * int(44.1 * sx)
            number_h = int(48.4736 * sy)
        draw.text((account_number_center[0] - number_w / 2, account_number_center[1] - number_h / 2), account_number, font=number_font, fill=text_fill)

    out = BytesIO()
    out.name = f"lethea_member_idcard_{rec.get('acc_no', user.id)}.png"
    canvas.save(out, format="PNG")
    out.seek(0)
    return out, None


async def _render_idcard_png(context, user, rec):
    """Router IDC: staff/owner pakai IDC staff lama; member pakai IDC member detail."""
    account_type = (rec.get("account_type") or "").strip().lower()
    if account_type in ("staff", "owner"):
        return await _render_staff_idcard_png(context, user, rec)
    return await _render_member_idcard_png(context, user, rec)


def _idcard_png_to_photo_jpeg(png_bytes):
    """Convert rendered IDC PNG/RGBA to a Telegram-safe JPEG photo."""
    if not IDCARD_IMAGE_AVAILABLE:
        return None

    try:
        png_bytes.seek(0)
        img = Image.open(png_bytes).convert("RGBA")

        # Telegram send_photo is picky with some PNG/transparent files.
        # Flatten to RGB and resize to a safe max side.
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.getchannel("A"))

        # Keep output light so Telegram upload is faster.
        max_side = 1024
        if max(bg.size) > max_side:
            bg.thumbnail((max_side, max_side), Image.LANCZOS)

        out = BytesIO()
        out.name = (getattr(png_bytes, "name", "lethea_idcard") or "lethea_idcard").replace(".png", ".jpg")
        bg.save(out, format="JPEG", quality=85, optimize=False)
        out.seek(0)
        return out
    except Exception as e:
        print(f"[_idcard_png_to_photo_jpeg] error: {e}")
        return None

def _mybalance_text(rec):
    return (
        "... 𖠷 ╱  𝐓𝐇𝐄 𝐏𝐀𝐑𝐀𝐃𝐈𝐒𝐄: 𝐋𝐄𝐓𝐇É𝐀 \n"
        "—— : 𝐴𝑐𝑐𝑜𝑢𝑛𝑡 𝑅𝑒𝑔𝑖𝑠𝑡𝑟𝑦 ༗  ’\n\n"
        f"› Account Number : {rec.get('acc_no', '-')}\n"
        f"› Balance : {_format_balance(rec.get('balance', 0))} ✦𝕷"
    )


async def my_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)

    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return

    _refresh_membership_status(rec)
    save_accounts()

    png, err = await _render_idcard_png(context, user, rec)
    if err:
        await update.message.reply_text(err)
        return

    photo = _idcard_png_to_photo_jpeg(png)
    if not photo:
        await update.message.reply_text("IDC belum berhasil kujadikan gambar. Periksa kembali template atau font IDC.")
        return

    try:
        await update.message.reply_photo(photo=photo)
    except Exception as e:
        print(f"[my_acc] send_photo jpg error: {e}")
        await update.message.reply_text("IDC telah terbentuk, namun belum berhasil kukirim. Periksa ukuran template atau font IDC.")


async def my_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)

    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return

    _refresh_membership_status(rec)
    save_accounts()
    await update.message.reply_text(_mybalance_text(rec))


async def change_pict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)
    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return

    rec["idcard_waiting_photo"] = True
    save_accounts()
    context.user_data["idcard_waiting_photo"] = True
    await update.message.reply_text(
        "Berikan foto untuk IDC kamu. Rasio bebas, Asmoday akan crop otomatis ke slot foto IDC."
    )


async def change_pict_image_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not update.effective_message or not update.effective_user:
        return

    user = update.effective_user
    rec = _get_existing_account(user.id)
    waiting = bool(context.user_data.get("idcard_waiting_photo")) or bool(rec and rec.get("idcard_waiting_photo"))
    if not waiting:
        return

    msg = update.effective_message
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id

    if not file_id:
        await msg.reply_text("Kirimkan wujudnya sebagai foto atau berkas gambar.")
        raise ApplicationHandlerStop

    if not rec:
        _ensure_owner_account(user)
        rec = _get_existing_account(user.id)
    if not rec:
        await msg.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        context.user_data.pop("idcard_waiting_photo", None)
        raise ApplicationHandlerStop

    rec["idcard_photo_file_id"] = file_id
    rec["idcard_waiting_photo"] = False
    context.user_data.pop("idcard_waiting_photo", None)
    save_accounts()

    # Jangan render preview otomatis di sini supaya upload foto tidak terasa lama.
    # User bisa panggil /myacc setelahnya untuk melihat IDC terbaru.
    await msg.reply_text("Rupa IDC telah kuperbarui. Gunakan /myacc untuk melihat wujud terbarunya.")
    raise ApplicationHandlerStop

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    flow = context.user_data.get("registration_flow")
    if flow and flow.get("flow_type") == "staff_form":
        _release_staff_interview_booking(flow, update.effective_user.id)
    context.user_data.pop("registration_flow", None)
    context.user_data.pop("menu_mode", None)
    context.user_data.pop("talk_mode", None)
    context.user_data.pop("talk_notified_once", None)
    context.user_data.pop("addcmd_flow", None)
    await update.message.reply_text("Sesi dibatalkan.")


async def where_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    await update.message.reply_text(
        f"FORWARD_PUBLIC_CHAT_ID = {FORWARD_PUBLIC_CHAT_ID}\n"
        f"FORWARD_STAFFTALK_CHAT_ID = {FORWARD_STAFFTALK_CHAT_ID}"
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    await update.message.reply_text(
        f"User ID: {user.id}\n"
        f"Chat ID: {chat.id}\n"
        f"Username: @{user.username or '-'}"
    )


async def __old_create_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    sent = await update.message.reply_text(
        "Pilih kategori menu baru yang ingin dibuat.",
        reply_markup=_create_menu_category_keyboard()
    )
    context.user_data["create_menu_flow"] = {
        "category": None,
        "name": None,
        "price": None,
        "ingredients": None,
        "how_to_make": None,
        "waiting_for": None,
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
    }


async def __old_menu_create_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    if not _can_manage_menu(query.from_user):
        await query.answer("Hanya Owner atau Currathor.", show_alert=True)
        return
    flow = context.user_data.get("create_menu_flow")
    data = query.data or ""
    if data == "menucreate:cancel":
        if flow:
            await _refresh_create_menu_message(context, flow, final_text="Pembuatan menu dibatalkan.", reply_markup=None)
        else:
            try:
                await query.edit_message_text("Pembuatan menu dibatalkan.")
            except Exception:
                pass
        context.user_data.pop("create_menu_flow", None)
        return
    if not flow:
        await query.edit_message_text("Sesi create menu tidak ditemukan. Gunakan /createmenu lagi.")
        return
    parts = data.split(":")
    if len(parts) < 3:
        return
    action = parts[1]
    if action == "category":
        category = parts[2]
        if category not in MENU_CATEGORY_LABELS:
            await query.answer("Kategori tidak valid.", show_alert=True)
            return
        flow["category"] = category
        flow["waiting_for"] = None
        flow["chat_id"] = query.message.chat_id
        flow["message_id"] = query.message.message_id
        await _refresh_create_menu_message(context, flow)
        return
    if action == "fill":
        target = parts[2]
        if target not in ("name", "price", "ingredients", "how_to_make"):
            return
        if target == "price" and not flow.get("name"):
            await query.answer("Isi nama dulu.", show_alert=True)
            return
        if target == "ingredients" and (not flow.get("name") or flow.get("price") is None):
            await query.answer("Isi nama dan harga dulu.", show_alert=True)
            return
        if target == "how_to_make" and (not flow.get("name") or flow.get("price") is None or not flow.get("ingredients")):
            await query.answer("Isi nama, harga, dan ingredients dulu.", show_alert=True)
            return
        flow["waiting_for"] = target
        await _refresh_create_menu_message(context, flow)
        if target == "name":
            await query.answer("Kirim nama menu di chat ini.", show_alert=True)
        elif target == "price":
            await query.answer("Kirim nominal harga dalam angka.", show_alert=True)
        elif target == "ingredients":
            await query.answer("Kirim daftar ingredients di chat ini.", show_alert=True)
        else:
            await query.answer("Kirim langkah how to make di chat ini.", show_alert=True)
        return
    if action == "confirm":
        confirm_type = parts[2]
        if confirm_type == "reset":
            flow["name"] = None
            flow["price"] = None
            flow["ingredients"] = None
            flow["how_to_make"] = None
            flow["waiting_for"] = None
            await _refresh_create_menu_message(context, flow)
            return
        if confirm_type == "yes":
            if not flow.get("category") or not flow.get("name") or flow.get("price") is None or not flow.get("ingredients") or not flow.get("how_to_make"):
                await query.answer("Data menu belum lengkap.", show_alert=True)
                return
            item = {
                "no": _next_menu_number(),
                "category": flow["category"],
                "name": flow["name"],
                "price": int(flow["price"]),
                "ingredients": flow.get("ingredients") or "",
                "how_to_make": flow.get("how_to_make") or "",
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": query.from_user.id,
            }
            MENU_ITEMS.append(item)
            save_menu_data()
            await _refresh_create_menu_message(
                context,
                flow,
                final_text=(
                    "✅ Menu baru berhasil disimpan.\n\n"
                    f"Tempat : {_menu_scope_label(item['menu_scope'])}\n"
                    f"Kategori : {_menu_category_label(item['category'])}\n"
                    f"Nama : {item['name']}\n"
                    f"Harga : {_normalize_price_text(item['price'])}\n"
                    "Ingredients : sudah disimpan\n"
                    "Deskripsi : sudah disimpan\n"
                    "Image : sudah disimpan\n"
                    f"Nomor Menu : {item['no']}"
                ),
                reply_markup=None,
            )
            context.user_data.pop("create_menu_flow", None)
            return


async def __old_create_menu_text_router_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("create_menu_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        context.user_data.pop("create_menu_flow", None)
        return
    waiting = flow.get("waiting_for")
    if not waiting:
        return
    text_in = (update.effective_message.text or "").strip()
    if not text_in:
        return
    if waiting == "name":
        flow["name"] = text_in
        flow["waiting_for"] = None
    elif waiting == "price":
        cleaned = text_in.replace(".", "").replace(",", "")
        if not cleaned.isdigit():
            await update.effective_message.reply_text("Harga harus berupa angka.")
            return
        price = int(cleaned)
        if price <= 0:
            await update.effective_message.reply_text("Harga harus lebih dari 0.")
            return
        flow["price"] = price
        flow["waiting_for"] = None
    elif waiting == "ingredients":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await update.effective_message.reply_text("Ingredients tidak boleh kosong.")
            return
        flow["ingredients"] = raw_text
        flow["waiting_for"] = None
    elif waiting == "how_to_make":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await update.effective_message.reply_text("How to make tidak boleh kosong.")
            return
        flow["how_to_make"] = raw_text
        flow["waiting_for"] = None
    await _refresh_create_menu_message(context, flow)


async def __old_roll_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not MENU_ITEMS:
        await update.message.reply_text("Belum ada menu tersimpan. Gunakan /createmenu dulu.")
        return
    import random
    grouped = _group_menu_items_by_category(_sorted_menu_items())
    rolled = {}
    for category in MENU_CATEGORY_ORDER:
        items = list(grouped.get(category) or [])
        if not items:
            continue
        count = _roll_count_for_category(category, len(items))
        selected = random.sample(items, count)
        selected.sort(key=lambda x: (int(x.get("no", 0)) if str(x.get("no", "")).isdigit() else 999999999))
        rolled[category] = [{"no": item.get("no"), "name": item.get("name"), "price": int(item.get("price", 0))} for item in selected]
    ROLLED_MENU.clear()
    ROLLED_MENU.update(rolled)
    save_menu_data()
    await update.message.reply_text(_format_rolled_menu_text())


async def __old_lethea_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    await update.message.reply_text(_format_rolled_menu_text())


async def __old_list_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    await update.message.reply_text(_format_full_menu_list_text())


async def __old_del_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /delmenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    idx = next((i for i, item in enumerate(MENU_ITEMS) if int(item.get("no", -1)) == menu_no), None)
    if idx is None:
        await update.message.reply_text("Nomor menu tidak ditemukan.")
        return
    deleted = MENU_ITEMS.pop(idx)
    for category, items in list(ROLLED_MENU.items()):
        ROLLED_MENU[category] = [item for item in items if int(item.get("no", -1)) != menu_no]
        if not ROLLED_MENU[category]:
            ROLLED_MENU.pop(category, None)
    save_menu_data()
    await update.message.reply_text(
        f"🗑️ Menu dihapus.\n{deleted.get('no')}. {deleted.get('name')} | {_normalize_price_text(deleted.get('price', 0))}"
    )


async def __old_add_price_all_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args:
        await update.message.reply_text("Format: /addpriceall <nominal>")
        return
    nominal = context.args[0].replace(".", "").replace(",", "")
    if not nominal.isdigit():
        await update.message.reply_text("Nominal harus angka.")
        return
    amount = int(nominal)
    if amount <= 0:
        await update.message.reply_text("Nominal harus lebih dari 0.")
        return
    if not MENU_ITEMS:
        await update.message.reply_text("Belum ada menu tersimpan.")
        return
    for item in MENU_ITEMS:
        item["price"] = int(item.get("price", 0)) + amount
    for items in ROLLED_MENU.values():
        for item in items:
            item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(f"✅ Semua harga menu naik {_normalize_price_text(amount)}.")


async def __old_add_price_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Format: /addprice <nomor_menu> <nominal>")
        return
    menu_no_text = context.args[0]
    nominal = context.args[1].replace(".", "").replace(",", "")
    if not menu_no_text.isdigit() or not nominal.isdigit():
        await update.message.reply_text("Nomor menu dan nominal harus angka.")
        return
    menu_no = int(menu_no_text)
    amount = int(nominal)
    if amount <= 0:
        await update.message.reply_text("Nominal harus lebih dari 0.")
        return
    target = next((item for item in MENU_ITEMS if int(item.get("no", -1)) == menu_no), None)
    if not target:
        await update.message.reply_text("Nomor menu tidak ditemukan.")
        return
    target["price"] = int(target.get("price", 0)) + amount
    for items in ROLLED_MENU.values():
        for item in items:
            if int(item.get("no", -1)) == menu_no:
                item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(
        f"✅ Harga menu {target.get('name')} sekarang {_normalize_price_text(target.get('price', 0))}."
    )


async def __old_info_menu_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /infomenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    target = next((item for item in MENU_ITEMS if int(item.get("no", -1)) == menu_no), None)
    if not target:
        await update.message.reply_text("Nomor menu tidak ditemukan.")
        return
    await update.message.reply_text(_format_menu_info_text(target))


async def __old_help_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user

    text = (
        "Perintah yang tersedia:\n\n"
        "User:\n"
        "• /start\n• /menu\n• /registration\n• /registrationstaff\n• /renewal\n• /upgradevip\n• /myacc\n• /changepict\n• /mybalance\n• /choicepoker\n• /letheamenu\n• /rentangel\n• /starttalk\n• /stoptalk\n• /cancel\n• /help\n"
    )

    if _can_manage_menu(user):
        text += (
            "\nMenu Management:\n"
            "• /createmenu\n• /rollmenu\n• /listmenu\n• /infomenu <nomor_menu>\n• /delmenu <nomor_menu>\n• /addpriceall <nominal>\n• /addprice <nomor_menu> <nominal>\n"
        )

    if _can_manage_staff(user):
        text += (
            "\nStaff Management:\n"
            "• /addstaff  (reply ke pesan user target)\n• /editrole <acc_no>\n• /delstaff <acc_no>\n• /ban <acc_no>\n• /unban <acc_no>\n• /inputangel\n• /listangel\n• /sendbill <acc_no> <nominal>\n• /openbar [link]\n• /closebar\n• /tagall [teks]\n• /tagvip [teks]\n• /tagangel [teks]\n• /tagstaff [teks]\n• /openshift\n• /closeshift\n"
        )

    if _is_admin(user):
        text += (
            "\nAdmin:\n"
            "• /addsaldo <acc_no> <jumlah>\n• /minsaldo <acc_no> <jumlah>\n• /listacc\n• /acc\n• /reject\n"
        )

    if _is_owner(user):
        text += (
            "\nOwner:\n"
            "• /addadmin <acc_no>\n• /deladmin <acc_no>\n• /listadmin\n• /delacc <acc_no>\n"
        )

    await update.message.reply_text(text)


# =========================================================
# STAFF / ADMIN COMMANDS
# =========================================================
# =========================================================
# FEATURE: STAFF / ADMIN / OWNER COMMANDS
# =========================================================
async def _staff_role_picker_message(update: Update, mode: str, target_user, existing_rec=None):
    username = getattr(target_user, "username", None) or (existing_rec.get("username") if existing_rec else None) or "-"
    name = getattr(target_user, "full_name", None) or (existing_rec.get("name") if existing_rec else None) or username
    target_uid = getattr(target_user, "id", None) or 0
    actor_id = update.effective_user.id
    rows = []
    current = []
    for key, label in STAFF_ROLE_KEYS:
        current.append(InlineKeyboardButton(label, callback_data=f"staffrole:{mode}:{actor_id}:{target_uid}:{key}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    text = (
        f"Pilih role untuk {name} (@{username if username != '-' else 'unknown'}).\n"
        f"Mode: {'Tambah staff' if mode == 'add' else 'Edit role'}"
    )
    await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(rows))

async def add_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Oxana.")
        return

    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return

    msg = update.effective_message
    if not msg or not msg.reply_to_message or not msg.reply_to_message.from_user:
        await update.message.reply_text("/addstaff sekarang hanya bisa dipakai dengan reply ke pesan user target.")
        return

    target_user = msg.reply_to_message.from_user
    if getattr(target_user, "is_bot", False):
        await update.message.reply_text("Tidak bisa memilih bot sebagai target staff.")
        return

    actor_uid = int(update.effective_user.id)
    target_uid = int(target_user.id)

    if target_uid == actor_uid:
        await update.message.reply_text("Kamu tidak bisa add diri sendiri sebagai staff lewat command ini.")
        return

    started = STARTED_USERS.get(str(target_uid))
    if not started:
        await update.message.reply_text("User target harus sudah /start Oxana dulu sebelum bisa di-add sebagai staff.")
        return

    existing = _get_existing_account(target_uid)
    if existing and existing.get("account_type") == "owner":
        await update.message.reply_text("Owner tidak bisa dijadikan staff.")
        return

    await _staff_role_picker_message(update, "add", target_user, existing)

async def edit_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Oxana.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return

    uid, rec, err = _get_target_account_from_acc_no_arg(update, context)
    if err:
        await update.message.reply_text(err)
        return

    if not rec or rec.get("account_type") != "staff":
        await update.message.reply_text("User itu belum terdaftar sebagai staff.")
        return

    class DummyTarget:
        id = uid
        username = rec.get("username")
        full_name = rec.get("name") or rec.get("username") or f"Account {rec.get('acc_no', uid)}"

    await _staff_role_picker_message(update, "edit", DummyTarget(), rec)

async def del_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Oxana.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return

    uid, rec, err = _get_target_account_from_acc_no_arg(update, context)
    if err:
        await update.message.reply_text(err)
        return

    if not rec or rec.get("account_type") != "staff":
        await update.message.reply_text("User itu bukan staff.")
        return

    rec["account_type"] = "member"
    rec["staff_role"] = None
    save_accounts()

    try:
        class _TargetUserSync:
            id = uid
            username = rec.get("username")
            full_name = rec.get("name")
        await _sync_private_commands_for_user(context, _TargetUserSync())
    except Exception:
        pass

    target_label = f"@{rec.get('username')}" if rec.get('username') and rec.get('username') != '-' else (rec.get('name') or f"Account {rec.get('acc_no', uid)}")
    await update.message.reply_text(f"🗑️ Status staff untuk {target_label} dihapus. Account Number: {rec.get('acc_no')}")

async def staff_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    _, mode, actor_id, target_uid, role_key = query.data.split(":", 4)
    if str(query.from_user.id) != actor_id:
        await query.answer("Bukan tombol kamu.", show_alert=True)
        return
    if not _can_manage_staff(query.from_user):
        await query.answer("Tidak punya akses.", show_alert=True)
        return
    role_label = _normalize_staff_role(role_key)
    if not role_label:
        await query.answer("Role tidak valid.", show_alert=True)
        return
    try:
        target_uid_int = int(target_uid)
    except Exception:
        target_uid_int = 0
    if not target_uid_int:
        await query.answer("User target tidak valid.", show_alert=True)
        return
    rec = _get_existing_account(target_uid_int)
    if not rec:
        started = STARTED_USERS.get(str(target_uid_int))
        if not started:
            await query.edit_message_text("User target belum pernah /start Oxana, jadi belum bisa di-add sebagai staff.")
            return
        class DummyUser:
            id = target_uid_int
            username = started.get("username") or "-"
            full_name = started.get("full_name") or started.get("username") or f"User {target_uid_int}"
        rec = _create_account(target_uid_int, DummyUser(), account_type="staff")
    rec["account_type"] = "staff"
    rec["staff_role"] = role_label
    rec["membership_type"] = None
    rec["membership_status"] = "deactive"
    rec["membership_started_at"] = None
    rec["membership_expires_at"] = None
    if rec.get("balance") is None:
        rec["balance"] = 0
    save_accounts()
    try:
        class _TargetUserSync:
            id = target_uid_int
            username = rec.get("username")
            full_name = rec.get("name")
        await _sync_private_commands_for_user(context, _TargetUserSync())
    except Exception:
        pass
    target_name = rec.get("name") or rec.get("username") or str(target_uid_int)
    action_text = "ditambahkan sebagai staff" if mode == "add" else "role staff diperbarui"
    await query.edit_message_text(f"✅ {target_name} {action_text}: {role_label}. Account Number: {rec.get('acc_no')}")

async def ban_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Asmoday.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /ban <account_number>")
        return
    target_uid, rec = _get_account_by_acc_no(context.args[0])
    if not rec:
        await update.message.reply_text("Account number tidak ditemukan.")
        return
    if str(target_uid) == str(update.effective_user.id):
        await update.message.reply_text("Kamu tidak bisa ban akunmu sendiri.")
        return
    if rec.get("account_type") == "owner":
        await update.message.reply_text("Owner tidak bisa diban.")
        return
    rec["banned"] = True
    save_accounts()
    await update.message.reply_text(f"Account #{rec.get('acc_no')} ({rec.get('name') or rec.get('username')}) diban dari semua fitur Asmoday.")

async def unban_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Asmoday.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /unban <account_number>")
        return
    _, rec = _get_account_by_acc_no(context.args[0])
    if not rec:
        await update.message.reply_text("Account number tidak ditemukan.")
        return
    rec["banned"] = False
    save_accounts()
    await update.message.reply_text(f"Account #{rec.get('acc_no')} ({rec.get('name') or rec.get('username')}) sudah di-unban.")

async def change_codename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)
    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return
    new_name = " ".join(context.args).strip()
    if not new_name:
        await update.message.reply_text("Format: /changecodename <nama baru>")
        return
    if len(new_name) > MAX_CODENAME_LEN:
        await update.message.reply_text(f"Codename maksimal {MAX_CODENAME_LEN} karakter. Contoh batas: {MAX_CODENAME_TEXT}")
        return
    rec["name"] = new_name
    save_accounts()
    await update.message.reply_text(f"Codename kamu sekarang: {new_name}")


async def change_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    _ensure_owner_account(user)
    rec = _get_existing_account(user.id)
    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return
    new_full_name = " ".join(context.args).strip()
    if not new_full_name:
        await update.message.reply_text("Format: /changefullname <full name baru>")
        return
    if len(new_full_name) > MAX_CODENAME_LEN:
        await update.message.reply_text(f"Full name maksimal {MAX_CODENAME_LEN} karakter. Contoh batas: {MAX_CODENAME_TEXT}")
        return
    rec["full_name"] = new_full_name
    save_accounts()
    await update.message.reply_text(f"Full name IDC kamu sekarang: {new_full_name}")


async def add_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_admin(caller):
        await update.message.reply_text("Hanya owner/admin.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Format: /addsaldo <acc_no> <jumlah>")
        return

    acc_no, amount_text = context.args

    if not acc_no.isdigit():
        await update.message.reply_text("Account number harus angka.")
        return

    try:
        amount = int(amount_text)
    except Exception:
        await update.message.reply_text("Jumlah saldo harus angka.")
        return

    if amount <= 0:
        await update.message.reply_text("Jumlah saldo harus lebih dari 0.")
        return

    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        await update.message.reply_text("Account tidak ditemukan.")
        return

    rec["balance"] = int(rec.get("balance", 0)) + amount
    save_accounts()

    await update.message.reply_text(
        f"✅ Saldo account {acc_no} bertambah {amount}.\n"
        f"Saldo sekarang: {rec['balance']}"
    )


async def min_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_admin(caller):
        await update.message.reply_text("Hanya owner/admin.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Format: /minsaldo <acc_no> <jumlah>")
        return

    acc_no, amount_text = context.args

    if not acc_no.isdigit():
        await update.message.reply_text("Account number harus angka.")
        return

    try:
        amount = int(amount_text)
    except Exception:
        await update.message.reply_text("Jumlah saldo harus angka.")
        return

    if amount <= 0:
        await update.message.reply_text("Jumlah saldo harus lebih dari 0.")
        return

    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        await update.message.reply_text("Account tidak ditemukan.")
        return

    current_balance = int(rec.get("balance", 0))
    if amount > current_balance:
        await update.message.reply_text(
            f"Saldo account {acc_no} tidak cukup.\nSaldo sekarang: {current_balance}"
        )
        return

    rec["balance"] = current_balance - amount
    save_accounts()

    await update.message.reply_text(
        f"✅ Saldo account {acc_no} berkurang {amount}.\n"
        f"Saldo sekarang: {rec['balance']}"
    )


async def del_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_owner(caller):
        await update.message.reply_text("Hanya owner yang bisa menghapus account.")
        return

    if not context.args:
        await update.message.reply_text("Format: /delacc <acc_no>")
        return

    acc_no = context.args[0]
    if not acc_no.isdigit():
        await update.message.reply_text("Account number harus angka.")
        return

    uid = ACCOUNT_INDEX.get(acc_no)
    if not uid:
        await update.message.reply_text("Account tidak ditemukan.")
        return

    uid_int = int(uid)
    rec = ACCOUNTS.get(str(uid_int))
    if not rec:
        await update.message.reply_text("Account tidak ditemukan.")
        return

    admin_ids.discard(uid_int)

    for key, value in list(talk_map.items()):
        if value == uid_int:
            talk_map.pop(key, None)

    for key, info in list(approval_map.items()):
        if info.get("uid") == uid_int:
            approval_map.pop(key, None)

    deleted_acc_no = rec.get("acc_no")
    FREED_NUMBERS.append(int(deleted_acc_no))

    ACCOUNTS.pop(str(uid_int), None)
    ACCOUNT_INDEX.pop(str(deleted_acc_no), None)

    save_accounts()
    save_state()

    await update.message.reply_text(f"Account {deleted_acc_no} berhasil dihapus.")


async def list_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_admin(caller):
        await update.message.reply_text("Hanya owner/admin.")
        return

    if not ACCOUNTS:
        await update.message.reply_text("(Belum ada account).")
        return

    lines = ["⟢ List Account:"]
    items = []

    for uid_str, rec in ACCOUNTS.items():
        rec = _normalize_account_record(int(uid_str), rec)
        username = rec.get("username", "-")
        username_text = f"@{username}" if username and username != "-" else rec.get("name", "-")
        items.append((
            int(rec.get("acc_no", 0)),
            username_text,
            rec.get("account_type", "member"),
            rec.get("balance", 0),
        ))

    items.sort(key=lambda x: x[0])

    for acc_no, username_text, account_type, balance in items:
        lines.append(f"- {username_text} | {acc_no} | {account_type} | saldo: {balance}")

    await update.message.reply_text("\n".join(lines))


# =========================================================
# ADMIN SYSTEM
# =========================================================
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_owner(caller):
        await update.message.reply_text("Hanya owner yang bisa menambahkan admin.")
        return

    if not context.args:
        await update.message.reply_text("Format: /addadmin <ACCOUNT_NUMBER>")
        return

    acc_no = context.args[0]
    if not acc_no.isdigit():
        await update.message.reply_text("Nomor akun harus berupa angka.")
        return

    uid = ACCOUNT_INDEX.get(acc_no)
    if not uid:
        await update.message.reply_text("Account Number tidak ditemukan.")
        return

    target_id = int(uid)

    if target_id in admin_ids:
        try:
            u = await context.bot.get_chat(target_id)
            await update.message.reply_html(f"{u.mention_html()} (Acc:{acc_no}) sudah menjadi admin.")
        except Exception:
            await update.message.reply_html(f"(Acc:{acc_no}) sudah menjadi admin.")
        return

    admin_ids.add(target_id)
    save_state()

    try:
        u = await context.bot.get_chat(target_id)
        label = u.mention_html()
    except Exception:
        label = f"<code>uid:{target_id}</code>"

    await update.message.reply_html(f"✅ {label} (Acc:{acc_no}) ditambahkan sebagai <b>admin</b>.")
    try:
        await _sync_private_commands_for_user(context, await context.bot.get_chat(target_id))
    except Exception:
        pass


async def del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_owner(caller):
        await update.message.reply_text("Hanya owner yang bisa mencabut admin.")
        return

    if not context.args:
        await update.message.reply_text("Format: /deladmin <ACCOUNT_NUMBER>")
        return

    acc_no = context.args[0]
    if not acc_no.isdigit():
        await update.message.reply_text("Nomor akun harus berupa angka.")
        return

    uid = ACCOUNT_INDEX.get(acc_no)
    if not uid:
        await update.message.reply_text("Account Number tidak ditemukan.")
        return

    target_id = int(uid)

    if target_id not in admin_ids:
        await update.message.reply_text("Ia bukan admin.")
        return

    admin_ids.discard(target_id)
    save_state()

    try:
        u = await context.bot.get_chat(target_id)
        label = u.mention_html()
    except Exception:
        label = f"<code>uid:{target_id}</code>"

    await update.message.reply_html(f"🗑️ {label} (Acc:{acc_no}) dicabut dari <b>admin</b>.")
    try:
        await _sync_private_commands_for_user(context, await context.bot.get_chat(target_id))
    except Exception:
        pass


async def list_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user

    if not _is_owner(caller):
        await update.message.reply_text("Hanya Owner.")
        return

    if not admin_ids:
        await update.message.reply_text("(Belum ada admin).")
        return

    lines = ["⟢ List Admin:"]
    for uid in sorted(admin_ids):
        rec = _get_existing_account(uid)
        if rec:
            try:
                u = await context.bot.get_chat(uid)
                label = u.mention_html()
            except Exception:
                username = rec.get("username", "-")
                label = f"@{username}" if username and username != "-" else (rec.get("name") or f"<code>uid:{uid}</code>")
            role_label = rec.get("staff_role") or "Admin"
            lines.append(f"- {label} | Acc:{rec.get('acc_no')} | Role: {role_label}")
        else:
            lines.append(f"- <code>uid:{uid}</code>")

    await update.message.reply_html("\n".join(lines))


# =========================================================
# FEATURE: PAYMENT BILL
# =========================================================
def _build_bill_dm_text(bill: dict) -> str:
    note = bill.get("note") or "-"
    return (
        "𖠷 ╱ .. Payment Bill\n\n"
        f"Tagihan : {_normalize_price_text(bill.get('amount', 0))} ✦𝕷\n"
        f"Catatan : {note}\n\n"
        "Tekan konfirmasi untuk membayar."
    )


def _bill_keyboard(bill_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Konfirmasi", callback_data=f"paybill:confirm:{bill_id}"),
            InlineKeyboardButton("Batal", callback_data=f"paybill:cancel:{bill_id}"),
        ]
    ])


def _parse_nominal_amount(text):
    cleaned = (str(text or "").replace(".", "").replace(",", "").strip())
    if not cleaned.isdigit():
        return None

    amount = int(cleaned)
    return amount if amount > 0 else None


async def send_bill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group yang ada Oxana.")
        return

    rec = _get_existing_account(update.effective_user.id)
    if not _is_staff_like(update.effective_user, rec):
        await update.message.reply_text("Hanya staff atau owner yang bisa mengirim bill.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Format: /sendbill <acc_no> <nominal>")
        return

    acc_no, nominal_raw = context.args
    if not acc_no.isdigit():
        await update.message.reply_text("Account number harus angka.")
        return

    amount = _parse_nominal_amount(nominal_raw)
    if amount is None:
        await update.message.reply_text("Nominal harus berupa angka dan lebih dari 0.")
        return

    target_uid, target_rec = _get_account_by_acc_no(acc_no)
    if not target_rec:
        await update.message.reply_text("Account target tidak ditemukan.")
        return

    status = await update.message.reply_text("⏳ Sedang dalam proses pembayaran...")
    sender_name = (
        rec.get("name")
        if rec
        else (update.effective_user.full_name or update.effective_user.username or "Staff")
    )
    note = f"Tagihan dari {sender_name}"
    await _create_payment_bill(
        context,
        requester_user=update.effective_user,
        target_uid=int(target_uid),
        amount=amount,
        status_chat_id=status.chat_id,
        status_message_id=status.message_id,
        note=note,
    )


async def __old_payment_bill_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3:
        return
    _, action, bill_id = parts
    bill = PENDING_BILLS.get(bill_id)
    if not bill:
        await query.answer("Bill tidak ditemukan atau sudah selesai.", show_alert=True)
        return
    if int(bill.get("target_uid", 0)) != int(query.from_user.id):
        await query.answer("Ini bukan bill milikmu.", show_alert=True)
        return
    target_rec = _get_existing_account(query.from_user.id)
    if not target_rec:
        await query.answer("Account kamu tidak ditemukan.", show_alert=True)
        return

    if action == "cancel":
        bill["status"] = "cancelled"
        if bill.get("angel_uid"):
            profile = _ensure_angel_profile(int(bill.get("angel_uid")))
            _angel_set_bill_booking_status(profile, bill_id, "cancelled")
            save_angel_data()
        save_payment_data()
        try:
            await query.edit_message_text("❌ Payment dibatalkan.")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(
                chat_id=bill["status_chat_id"],
                message_id=bill["status_message_id"],
                text="❌ Payment dibatalkan.",
            )
        except Exception:
            pass
        return

    amount = int(bill.get("amount", 0))
    balance = int(target_rec.get("balance", 0))
    if balance < amount:
        try:
            await query.answer("Saldo kamu tidak cukup.", show_alert=True)
            await query.edit_message_text(
                f"❌ Payment gagal. Saldo kamu tidak cukup.\nSaldo sekarang: {_normalize_price_text(balance)} ✦𝕷"
            )
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(
                chat_id=bill["status_chat_id"],
                message_id=bill["status_message_id"],
                text="❌ Payment gagal. Saldo target tidak cukup.",
            )
        except Exception:
            pass
        bill["status"] = "insufficient_balance"
        save_payment_data()
        return

    target_rec["balance"] = balance - amount
    save_accounts()
    bill["status"] = "paid"
    save_payment_data()

    angel_uid = bill.get("angel_uid")
    if angel_uid:
        angel_uid = int(angel_uid)
        angel_share = int(amount * 70 / 100)
        currathor_share = int(amount) - angel_share
        angel_rec = _get_existing_account(angel_uid)
        angel_name = _angel_display_name(angel_rec) if angel_rec else f"Angel {angel_uid}"
        await _credit_angel_income(
            context,
            angel_uid,
            angel_share,
            f"Rent Angel dari {target_rec.get('name') or (target_rec.get('username') and '@' + str(target_rec.get('username'))) or ('Account ' + str(target_rec.get('acc_no')))}",
        )
        await _credit_currathors(
            context,
            currathor_share,
            f"Bagi hasil rent Angel {angel_name}",
        )
        profile = _ensure_angel_profile(angel_uid)
        profile["total_orders"] = int(profile.get("total_orders", 0)) + 1
        save_angel_data()
    else:
        await _credit_currathors(
            context,
            int(amount * 50 / 100),
            f"Bagi hasil payment bill dari {target_rec.get('name') or (target_rec.get('username') and '@' + str(target_rec.get('username'))) or ('Account ' + str(target_rec.get('acc_no')))}",
        )

    try:
        await query.edit_message_text(
            f"✅ Konfirmasi reservasi berhasil. Booking kamu sekarang menunggu ACC admin. Saldo belum dipotong."
        )
    except Exception:
        pass
    try:
        await context.bot.edit_message_text(
            chat_id=bill["status_chat_id"],
            message_id=bill["status_message_id"],
            text="✅ Payment berhasil.",
        )
    except Exception:
        pass


# =========================================================
# FEATURE: ANGEL
# =========================================================
def _build_angel_input_text(flow: dict) -> str:
    rec = flow.get("angel_rec") or {}
    profile = flow.get("profile") or {}
    pop_label, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
    name = _angel_display_name(rec)
    desc = profile.get("short_desc") or "-"
    image_status = "sudah diisi" if profile.get("image_file_id") else "-"
    lines = [
        "𖠷 ╱ LETHÉA: INPUT ANGEL",
        "",
        f"Angel : {name}",
        f"Price : {_normalize_price_text(price)} ✦𝕷",
        f"Popularity : {pop_label}",
        f"Image : {image_status}",
        f"Short Description : {desc}",
        "",
        "Pilih bagian yang ingin diisi lewat tombol di bawah.",
    ]
    return "\n".join(lines)


def _angel_input_keyboard(flow: dict):
    rows = []
    row = []
    if not flow.get("profile", {}).get("image_file_id"):
        row.append(InlineKeyboardButton("Isi Image", callback_data="angelinput:fill:image"))
    if not flow.get("profile", {}).get("short_desc"):
        row.append(InlineKeyboardButton("Isi Desc", callback_data="angelinput:fill:desc"))
    if row:
        rows.append(row)
    if flow.get("profile", {}).get("image_file_id") and flow.get("profile", {}).get("short_desc"):
        rows.append([InlineKeyboardButton("✅ Simpan", callback_data="angelinput:confirm")])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="angelinput:cancel")])
    return InlineKeyboardMarkup(rows)


async def input_angel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    angels = _angel_staff_records()
    if not angels:
        await update.message.reply_text("Belum ada staff dengan role Angel.")
        return
    rows = []
    current = []
    for uid, rec in angels:
        current.append(InlineKeyboardButton(_angel_display_name(rec), callback_data=f"angelinput:select:{uid}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="angelinput:cancel")])
    await update.message.reply_text("Pilih Angel yang ingin diinput.", reply_markup=InlineKeyboardMarkup(rows))


async def angel_input_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    if action == "cancel":
        context.user_data.pop("angel_input_flow", None)
        try:
            await query.edit_message_text("Input Angel dibatalkan.")
        except Exception:
            pass
        return
    if not _can_manage_staff(query.from_user):
        await query.answer("Tidak punya akses.", show_alert=True)
        return
    if action == "select" and len(parts) >= 3:
        uid = int(parts[2])
        rec = _get_existing_account(uid)
        if not rec or (rec.get("staff_role") or "").lower() != "angel":
            await query.edit_message_text("Target bukan staff Angel.")
            return
        profile = _ensure_angel_profile(uid)
        context.user_data["angel_input_flow"] = {
            "angel_uid": uid,
            "angel_rec": rec,
            "profile": dict(profile),
            "message_id": query.message.message_id,
            "chat_id": query.message.chat_id,
            "waiting_for": None,
        }
        await query.edit_message_text(_build_angel_input_text(context.user_data["angel_input_flow"]), reply_markup=_angel_input_keyboard(context.user_data["angel_input_flow"]))
        return
    flow = context.user_data.get("angel_input_flow")
    if not flow:
        await query.answer("Sesi input Angel tidak ditemukan.", show_alert=True)
        return
    if action == "fill" and len(parts) >= 3:
        field = parts[2]
        flow["waiting_for"] = field
        try:
            await query.answer("Kirim input di chat ini.", show_alert=True)
        except Exception:
            pass
        return
    if action == "confirm":
        uid = int(flow["angel_uid"])
        ANGEL_PROFILES[str(uid)] = flow["profile"]
        save_angel_data()
        context.user_data.pop("angel_input_flow", None)
        await query.edit_message_text("✅ Data Angel berhasil disimpan.")


async def angel_input_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("angel_input_flow")
    if not flow or flow.get("waiting_for") != "desc":
        return
    text = (update.effective_message.text or "").strip()
    if not text:
        return
    flow["profile"]["short_desc"] = text
    flow["waiting_for"] = None
    try:
        await context.bot.edit_message_text(
            chat_id=flow["chat_id"],
            message_id=flow["message_id"],
            text=_build_angel_input_text(flow),
            reply_markup=_angel_input_keyboard(flow),
        )
    except Exception as e:
        print(f"[angel_input_text_router] error: {e}")


async def angel_input_image_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Jangan ganggu foto yang sedang ditunggu oleh /changepict.
    if context.user_data.get("idcard_waiting_photo"):
        return
    flow = context.user_data.get("angel_input_flow")
    if not flow or flow.get("waiting_for") != "image":
        return
    msg = update.effective_message
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id
    if not file_id:
        return
    flow["profile"]["image_file_id"] = file_id
    flow["waiting_for"] = None
    try:
        await context.bot.edit_message_text(
            chat_id=flow["chat_id"],
            message_id=flow["message_id"],
            text=_build_angel_input_text(flow),
            reply_markup=_angel_input_keyboard(flow),
        )
    except Exception as e:
        print(f"[angel_input_image_router] error: {e}")


async def __old_rent_angel_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not _can_rent_angel(update.effective_user, rec):
        await update.message.reply_text("Fitur ini hanya untuk Owner, Currathor, atau member VIP aktif.")
        return
    angels = _angel_staff_records()
    if not angels:
        await update.message.reply_text("Belum ada Angel yang tersedia.")
        return
    sent_any = False
    for uid, angel_rec in angels:
        profile = _ensure_angel_profile(uid)
        if not profile.get("image_file_id"):
            continue
        try:
            await update.effective_message.reply_photo(
                photo=profile.get("image_file_id"),
                caption=_angel_display_name(angel_rec),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Detail", callback_data=f"angelview:detail:{uid}")]]),
            )
            sent_any = True
        except Exception as e:
            print(f"[rent_angel_cmd] send photo error: {e}")
    if not sent_any:
        await update.message.reply_text("Belum ada rupa Angel yang lengkap untuk kutampilkan. Minimal image harus sudah diinput.")


async def __old_angel_view_callback_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    action = parts[1]
    uid = int(parts[2])
    rec = _get_existing_account(uid)
    profile = _ensure_angel_profile(uid)
    if not rec or (rec.get("staff_role") or "").lower() != "angel":
        await query.answer("Angel tidak ditemukan.", show_alert=True)
        return
    if action == "detail":
        await query.message.reply_text(
            _build_angel_detail_text(rec, profile),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💳 Rent", callback_data=f"angelview:rent:{uid}"),
                InlineKeyboardButton("❌ Cancel", callback_data="angelview:close:0"),
            ]])
        )
        return
    if action == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    if action == "rent":
        user_rec = _get_existing_account(query.from_user.id)
        if not _can_rent_angel(query.from_user, user_rec):
            await query.answer("Tidak punya akses untuk rent Angel.", show_alert=True)
            return
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        status = await query.message.reply_text("⏳ Sedang dalam proses pembayaran rent Angel...")
        ok, _ = await _create_payment_bill(
            context,
            requester_user=query.from_user,
            target_uid=int(query.from_user.id),
            amount=int(price),
            status_chat_id=status.chat_id,
            status_message_id=status.message_id,
            note=f"Rent Angel: {_angel_display_name(rec)} ({popularity})",
            angel_uid=uid,
        )
        if ok:
            await query.answer("Bill sudah dikirim ke DM kamu.", show_alert=True)


async def angel_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or (rec.get("staff_role") or "").lower() != "angel":
        await update.message.reply_text("Command ini hanya untuk staff Angel.")
        return
    profile = _ensure_angel_profile(update.effective_user.id)
    popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
    await update.message.reply_text(
        f"Nama : {_angel_display_name(rec)}\nPopularity : {popularity}\nTotal Orders : {int(profile.get('total_orders', 0) or 0)}\nPrice : {_normalize_price_text(price)} ✦𝕷"
    )


# =========================================================
# FEATURE: OPEN WARUNG / BAR / RESORT + SHIFT STAFF
# =========================================================
async def _send_openwarung_dm_broadcast(context: ContextTypes.DEFAULT_TYPE, kind: str, link: str):
    sent_count = 0
    fail_count = 0
    for uid, rec in _openwarung_recipients(kind):
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=_openwarung_dm_text(kind, link)
            )
            sent_count += 1
        except Exception as e:
            fail_count += 1
            print(f"[openwarung] DM failed kind={kind} uid={uid}: {e}")
    return sent_count, fail_count


async def _openwarung_start(update: Update, context: ContextTypes.DEFAULT_TYPE, preset_kind: str | None = None):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return

    uid_key = str(update.effective_user.id)

    if preset_kind:
        kind = preset_kind
    else:
        kind = None
        if context.args and (context.args[0] or "").strip().lower() in ("bar", "resort"):
            kind = context.args[0].strip().lower()
            context.args = context.args[1:]

    if kind and context.args:
        link = " ".join(context.args).strip()
        sent_count, fail_count = await _send_openwarung_dm_broadcast(context, kind, link)
        kwargs = {"chat_id": update.effective_chat.id, "text": _openwarung_done_text(kind, sent_count, fail_count)}
        thread_id = getattr(update.effective_message, "message_thread_id", None)
        if thread_id:
            kwargs["message_thread_id"] = thread_id
        await context.bot.send_message(**kwargs)
        return

    OPEN_BAR_PENDING[uid_key] = {
        "chat_id": update.effective_chat.id,
        "kind": kind,
    }

    if kind:
        label = _openwarung_label(kind)
        await update.message.reply_text(f"Kirim link open {label.lower()} di chat ini. Setelah itu Asmoday akan DM target member.")
    else:
        await update.message.reply_text(
            "Pilih warung yang mau dibuka terlebih dahulu.",
            reply_markup=_openwarung_choice_keyboard()
        )


async def open_warung_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _openwarung_start(update, context, None)


async def open_bar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _openwarung_start(update, context, "bar")


async def open_resort_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _openwarung_start(update, context, "resort")


async def open_warung_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Currathor atau Owner.", show_alert=True)
        return

    parts = (query.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""
    uid_key = str(query.from_user.id)

    if action == "cancel":
        OPEN_BAR_PENDING.pop(uid_key, None)
        await query.edit_message_text("Open warung dibatalkan.")
        return

    if action == "choose" and len(parts) >= 3:
        kind = parts[2]
        if kind not in ("bar", "resort"):
            await query.answer("Pilihan tidak valid.", show_alert=True)
            return
        OPEN_BAR_PENDING[uid_key] = {
            "chat_id": query.message.chat_id,
            "kind": kind,
        }
        await query.edit_message_text(f"Kirim link open {_openwarung_label(kind).lower()} di chat ini. Setelah itu Asmoday akan DM target member.")
        return


async def open_bar_link_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wait = OPEN_BAR_PENDING.get(str(update.effective_user.id))
    if not wait:
        return
    if update.effective_chat.id != int(wait.get("chat_id")):
        return
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        OPEN_BAR_PENDING.pop(str(update.effective_user.id), None)
        return

    link = (update.effective_message.text or "").strip()
    if not link:
        return

    kind = (wait.get("kind") or "").strip().lower()
    if kind not in ("bar", "resort"):
        await update.message.reply_text(
            "Pilih dulu mau open Bar atau Resort.",
            reply_markup=_openwarung_choice_keyboard()
        )
        return

    OPEN_BAR_PENDING.pop(str(update.effective_user.id), None)
    sent_count, fail_count = await _send_openwarung_dm_broadcast(context, kind, link)

    kwargs = {"chat_id": update.effective_chat.id, "text": _openwarung_done_text(kind, sent_count, fail_count)}
    thread_id = getattr(update.effective_message, "message_thread_id", None)
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    await context.bot.send_message(**kwargs)


# =========================================================
# FEATURE: CURRATHOR BROADCAST
# =========================================================
def _broadcast_started_recipients():
    recipients = []
    seen = set()
    for uid_key, data in (STARTED_USERS or {}).items():
        try:
            uid = int((data or {}).get("id") or uid_key)
        except Exception:
            continue
        if uid in seen:
            continue
        seen.add(uid)
        recipients.append(uid)
    recipients.sort()
    return recipients


async def _send_broadcast_to_started_users(context: ContextTypes.DEFAULT_TYPE, text: str):
    sent_count = 0
    fail_count = 0
    for uid in _broadcast_started_recipients():
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            sent_count += 1
        except Exception as e:
            fail_count += 1
            print(f"[broadcast] DM failed uid={uid}: {e}")
    return sent_count, fail_count


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner yang bisa broadcast.")
        return

    if context.args:
        text = " ".join(context.args).strip()
        if text:
            sent_count, fail_count = await _send_broadcast_to_started_users(context, text)
            await update.message.reply_text(
                "✅ Broadcast selesai.\n"
                f"Terkirim : {sent_count}\n"
                f"Gagal : {fail_count}"
            )
            return

    context.user_data["broadcast_waiting_text"] = True
    await update.message.reply_text(
        "Kirim text yang mau di-broadcast.\n"
        "Asmoday akan mengirimkannya ke semua user yang sudah /start.\n\n"
        "Ketik /cancel untuk batal."
    )


async def broadcast_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("broadcast_waiting_text"):
        return
    if not await _ensure_not_banned(update, context):
        raise ApplicationHandlerStop
    if not _can_manage_staff(update.effective_user):
        context.user_data.pop("broadcast_waiting_text", None)
        raise ApplicationHandlerStop

    text = (update.effective_message.text or "").strip()
    if not text:
        return

    context.user_data.pop("broadcast_waiting_text", None)
    sent_count, fail_count = await _send_broadcast_to_started_users(context, text)
    await update.message.reply_text(
        "✅ Broadcast selesai.\n"
        f"Terkirim : {sent_count}\n"
        f"Gagal : {fail_count}"
    )
    raise ApplicationHandlerStop


async def close_bar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    kwargs = {
        "chat_id": update.effective_chat.id,
        "text": "Bar telah ditutup. Terimakasih telah berkunjung. Jika ada kritik dan saran, silakan hubungi saya pada bagian kritik dan saran di menu.",
    }
    thread_id = getattr(update.effective_message, "message_thread_id", None)
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    await context.bot.send_message(**kwargs)


def _open_shift_mode_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Open Bar", callback_data="openshiftmode:bar"),
            InlineKeyboardButton("Open Resort", callback_data="openshiftmode:resort"),
        ]
    ])


async def _open_shift_mode(update_or_query, context: ContextTypes.DEFAULT_TYPE, mode: str):
    chat = update_or_query.effective_chat if hasattr(update_or_query, "effective_chat") else update_or_query.message.chat
    user = update_or_query.effective_user if hasattr(update_or_query, "effective_user") else update_or_query.from_user
    message = update_or_query.effective_message if hasattr(update_or_query, "effective_message") else update_or_query.message
    if chat.type == "private":
        if hasattr(message, "reply_text"):
            await message.reply_text("Gunakan command ini di group.")
        return False
    if not _can_manage_staff(user):
        if hasattr(message, "reply_text"):
            await message.reply_text("Hanya Currathor atau Owner.")
        return False
    key = _shift_session_key(chat.id)
    current = SHIFT_SESSIONS.get(key)
    if current and current.get("status") in ("open", "closed"):
        if hasattr(message, "reply_text"):
            await message.reply_text("Masih ada sesi shift yang belum di-accept di group ini.")
        return False
    session = _new_shift_session(chat.id, getattr(message, "message_thread_id", None), user.id, mode=mode)
    sent = await context.bot.send_message(
        chat_id=chat.id,
        text=_shift_panel_text(session),
        reply_markup=_shift_panel_keyboard(chat.id, True),
        message_thread_id=getattr(message, "message_thread_id", None),
    )
    session["panel_message_id"] = sent.message_id
    SHIFT_SESSIONS[key] = session
    save_shift_data()
    return True


async def open_shift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    await update.message.reply_text(
        "Pilih shift yang ingin dibuka.",
        reply_markup=_open_shift_mode_keyboard(),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )


async def open_shift_resort_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    await _open_shift_mode(update, context, "resort")


async def open_shift_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 2:
        return
    _, mode = parts
    if mode not in SHIFT_MODE_CONFIG:
        return
    ok = await _open_shift_mode(query, context, mode)
    if ok:
        try:
            await query.edit_message_text(f"✅ Shift {_shift_mode_label({'mode': mode})} dibuka.")
        except Exception:
            pass


async def shift_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 2:
        return
    chat_id = int(parts[1])
    key = _shift_session_key(chat_id)
    session = SHIFT_SESSIONS.get(key)
    if not session or session.get("status") != "open":
        await query.answer("Shift sedang tidak dibuka.", show_alert=True)
        return

    rec = _get_existing_account(query.from_user.id)
    if not rec or rec.get("account_type") != "staff":
        await query.answer("Hanya staff yang bisa join shift.", show_alert=True)
        return
    role_key = _shift_role_key_from_record(rec)
    allowed_roles = _shift_allowed_roles(session)
    if role_key not in allowed_roles:
        await query.answer("Role staff kamu tidak masuk slot shift ini.", show_alert=True)
        return
    if _find_shift_member_role(session, query.from_user.id):
        await query.answer("Kamu sudah join shift ini.", show_alert=True)
        return
    role_members = session.setdefault("attendees", {}).setdefault(role_key, [])
    if len(role_members) >= SHIFT_SLOT_LIMITS[role_key]:
        await query.answer(f"Slot {SHIFT_ROLE_LABELS[role_key]} sudah penuh.", show_alert=True)
        return
    role_members.append(int(query.from_user.id))
    save_shift_data()
    try:
        await context.bot.edit_message_text(
            chat_id=session["chat_id"],
            message_id=session["panel_message_id"],
            text=_shift_panel_text(session),
            reply_markup=_shift_panel_keyboard(chat_id, True),
        )
    except Exception as e:
        print(f"[shift_join_callback] edit error: {e}")
    await query.answer("Kamu berhasil join shift.", show_alert=True)


async def close_shift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan command ini di group.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    key = _shift_session_key(update.effective_chat.id)
    session = SHIFT_SESSIONS.get(key)
    if not session or session.get("status") != "open":
        await update.message.reply_text("Belum ada shift yang sedang dibuka.")
        return
    session["status"] = "closed"
    save_shift_data()
    try:
        await context.bot.edit_message_text(
            chat_id=session["chat_id"],
            message_id=session["panel_message_id"],
            text=_shift_panel_text(session),
            reply_markup=None,
        )
    except Exception as e:
        print(f"[close_shift_cmd] panel edit error: {e}")
    sent = await update.message.reply_text(
        _shift_recap_text(session, final=False),
        reply_markup=_shift_recap_keyboard(session),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    session["recap_message_id"] = sent.message_id
    save_shift_data()


async def shift_recap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Currathor atau Owner.", show_alert=True)
        return
    parts = (query.data or "").split(":")
    if len(parts) != 4:
        return
    _, action, chat_id_text, uid_text = parts
    chat_id = int(chat_id_text)
    key = _shift_session_key(chat_id)
    session = SHIFT_SESSIONS.get(key)
    if not session or session.get("status") != "closed":
        await query.answer("Rekap shift tidak ditemukan.", show_alert=True)
        return

    if action == "remove":
        uid = int(uid_text)
        role_key = _find_shift_member_role(session, uid)
        if not role_key:
            await query.answer("Staff itu tidak ada di rekap.", show_alert=True)
            return
        session["attendees"][role_key] = [int(x) for x in session["attendees"].get(role_key, []) if int(x) != uid]
        save_shift_data()
        await query.message.edit_text(_shift_recap_text(session, final=False), reply_markup=_shift_recap_keyboard(session))
        return

    if action == "accept":
        attendees = session.get("attendees") or {}
        role_salary_override = {
            "bartender": 950000,
            "strip_dancer": 950000,
            "server": 950000,
            "angel": 0,
            "chef": 950000,
            "performer": 950000,
        }
        role_cnit_override = {}
        for role_key, members in attendees.items():
            salary = int(role_salary_override.get(role_key, SHIFT_SALARY_BY_ROLE.get(role_key, 0) or 0) or 0)
            cnit_amount = int(role_cnit_override.get(role_key, 0) or 0)
            for uid in members:
                rec = _get_existing_account(int(uid))
                if not rec:
                    continue
                bonus_cnit, month_shift_count, month_key = _apply_staff_shift_rewards(rec, role_key)
                if salary > 0:
                    rec["balance"] = int(rec.get("balance", 0)) + salary
                    await _notify_shift_salary(context, int(uid), salary, role_key)
                if cnit_amount > 0:
                    rec["cnit_pending"] = int(rec.get("cnit_pending", 0) or 0) + cnit_amount
                    try:
                        await context.bot.send_message(
                            chat_id=int(uid),
                            text=(
                                "💠 CNIT Bertambah\n\n"
                                f"Jumlah : {cnit_amount} CNIT\n"
                                f"Sumber : Shift {SHIFT_ROLE_LABELS.get(role_key, role_key)} diterima"
                            ),
                        )
                    except Exception as e:
                        print(f"[shift cnit notify] failed uid={uid}: {e}")
                if bonus_cnit > 0:
                    try:
                        await context.bot.send_message(
                            chat_id=int(uid),
                            text=(
                                "💠 Bonus CNIT Masuk\n\n"
                                f"Jumlah : {bonus_cnit} CNIT\n"
                                f"Sumber : Bonus 8 shift bulan {month_key} untuk role {SHIFT_ROLE_LABELS.get(role_key, role_key)}"
                            ),
                        )
                    except Exception as e:
                        print(f"[shift bonus cnit notify] failed uid={uid}: {e}")
        save_accounts()
        session["status"] = "accepted"
        save_shift_data()
        await query.message.edit_text(_shift_recap_text(session, final=True), reply_markup=None)
        SHIFT_SESSIONS.pop(key, None)
        save_shift_data()

# =========================================================
# ERROR HANDLER
# =========================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Exception while handling an update:", context.error)


async def __old_list_angel_cmd_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    angels = _angel_staff_records()
    if not angels:
        await update.message.reply_text("Belum ada staff Angel.")
        return
    lines = ["Lethéa Angel:\n"]
    for i, (uid, rec) in enumerate(angels, start=1):
        profile = _ensure_angel_profile(uid)
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        lines.append(
            f"O{i}. {_angel_display_name(rec)} | {rec.get('acc_no', '-')} | {popularity} | {_normalize_price_text(price)}"
        )
    await update.message.reply_text("\n".join(lines))


# =========================================================
# SHIFT HELPERS
# =========================================================
def _new_shift_session(chat_id: int, thread_id, opened_by: int, mode: str = "bar"):
    mode = mode if mode in SHIFT_MODE_CONFIG else "bar"
    allowed_roles = list(SHIFT_MODE_CONFIG.get(mode, {}).get("roles", []))
    attendees = {k: [] for k in allowed_roles}
    return {
        "chat_id": int(chat_id),
        "thread_id": thread_id,
        "opened_by": int(opened_by),
        "opened_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "open",
        "mode": mode,
        "panel_message_id": None,
        "recap_message_id": None,
        "attendees": attendees,
    }


def _shift_panel_text(session: dict) -> str:
    lines = [
        "𖠷 ╱ .. LETHÉA: SHIFT STAFF",
        "",
        f"Mode : {_shift_mode_label(session)}",
        f"Status : {('Dibuka' if session.get('status') == 'open' else 'Ditutup')}",
        "",
        "Slot Shift:",
    ]
    attendees = session.get("attendees") or {}
    for role_key in _shift_allowed_roles(session):
        members = attendees.get(role_key) or []
        labels = []
        for uid in members:
            rec = _get_existing_account(int(uid))
            if rec:
                labels.append(_shift_display_name(rec))
        joined_text = ", ".join(labels) if labels else "-"
        lines.append(f"› {SHIFT_ROLE_LABELS[role_key]} [{len(members)}/{SHIFT_SLOT_LIMITS[role_key]}] : {joined_text}")
    lines.extend(["", "Tekan Join untuk masuk ke presensi shift sesuai role staff kamu."])
    return "\n".join(lines)


def _shift_recap_text(session: dict, final: bool = False) -> str:
    lines = [
        "𖠷 ╱ .. LETHÉA: SHIFT RECAP",
        "",
        f"Mode : {_shift_mode_label(session)}",
        f"Status : {'Final' if final else 'Menunggu review'}",
        "",
    ]
    attendees = session.get("attendees") or {}
    has_any = False
    num = 1
    for role_key in _shift_allowed_roles(session):
        members = attendees.get(role_key) or []
        if not members:
            continue
        has_any = True
        lines.append(f"{SHIFT_ROLE_LABELS[role_key]}:")
        for uid in members:
            rec = _get_existing_account(int(uid))
            if rec:
                lines.append(f"O{num}. {_shift_display_name(rec)} | {rec.get('acc_no', '-')}")
                num += 1
        lines.append("")
    if not has_any:
        lines.append("Belum ada staff yang join.")
        lines.append("")
    if final:
        lines.append("Presensi telah di-accept. Salary sudah masuk ke balance staff yang tercatat.")
    else:
        lines.append("Currathor/Owner bisa hapus staff yang tidak valid, lalu accept presensi.")
    return "\n".join(lines).strip()


def _shift_recap_keyboard(session: dict):
    rows = []
    attendees = session.get("attendees") or {}
    for role_key in _shift_allowed_roles(session):
        for uid in attendees.get(role_key) or []:
            rec = _get_existing_account(int(uid))
            label = _shift_display_name(rec) if rec else f"UID {uid}"
            rows.append([InlineKeyboardButton(f"🗑️ Hapus {label[:18]}", callback_data=f"shiftrecap:remove:{session.get('chat_id')}:{int(uid)}")])
    rows.append([InlineKeyboardButton("✅ Accept Presensi", callback_data=f"shiftrecap:accept:{session.get('chat_id')}:0")])
    return InlineKeyboardMarkup(rows)

# =========================================================
# RESTAURANT MENU EXTENSION
# =========================================================
RESTAURANT_CATEGORY_LABELS = {
    "standard_cuisine": "Standard Cuisine 🍽️",
    "premium_cuisine": "Premium Cuisine 🍽️",
    "luxury_dining": "Luxury Dining 🍽️",
    "limited_edition_cuisine": "Limited Edition Cuisine 🍽️",
    "refreshment": "Refreshment 🥤",
    "dining_drinks": "Dining Drinks 🥂",
    "alcohol_pairing": "Alcohol Pairing (Optional) 🍷",
}
RESTAURANT_CATEGORY_ORDER = [
    "standard_cuisine",
    "premium_cuisine",
    "luxury_dining",
    "limited_edition_cuisine",
    "refreshment",
    "dining_drinks",
    "alcohol_pairing",
]
RESTAURANT_CATEGORY_CREATE_ROWS = [
    [("standard_cuisine", "Standard Cuisine"), ("premium_cuisine", "Premium Cuisine")],
    [("luxury_dining", "Luxury Dining"), ("limited_edition_cuisine", "Limited Edition Cuisine")],
    [("refreshment", "Refreshment"), ("dining_drinks", "Dining Drinks")],
    [("alcohol_pairing", "Alcohol Pairing (Optional)")],
]
RESTAURANT_ROLLED_MENU = {}


def save_menu_data():
    try:
        data = {
            "items": MENU_ITEMS,
            "rolled_menu": ROLLED_MENU,
            "restaurant_rolled_menu": RESTAURANT_ROLLED_MENU,
        }
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_menu_data failed: {e}")


def load_menu_data():
    global MENU_ITEMS, ROLLED_MENU, RESTAURANT_ROLLED_MENU
    try:
        p = Path(MENU_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        MENU_ITEMS = data.get("items", [])
        ROLLED_MENU = data.get("rolled_menu", {})
        RESTAURANT_ROLLED_MENU = data.get("restaurant_rolled_menu", {})
        if not isinstance(MENU_ITEMS, list):
            MENU_ITEMS = []
        if not isinstance(ROLLED_MENU, dict):
            ROLLED_MENU = {}
        if not isinstance(RESTAURANT_ROLLED_MENU, dict):
            RESTAURANT_ROLLED_MENU = {}
        changed = False
        for item in MENU_ITEMS:
            if item.get("menu_scope") not in ("bar", "restaurant"):
                item["menu_scope"] = "bar"
                changed = True
        if changed:
            save_menu_data()
    except Exception as e:
        print(f"[WARN] load_menu_data failed: {e}")
        MENU_ITEMS = []
        ROLLED_MENU = {}
        RESTAURANT_ROLLED_MENU = {}


def _category_order_for_scope(scope: str):
    return RESTAURANT_CATEGORY_ORDER if scope == "restaurant" else MENU_CATEGORY_ORDER


def _menu_category_label(key):
    if not key:
        return "-"
    if key in MENU_CATEGORY_LABELS:
        return MENU_CATEGORY_LABELS[key]
    return RESTAURANT_CATEGORY_LABELS.get(key, str(key).title())


def _create_menu_category_keyboard(flow=None):
    scope = (flow or {}).get("menu_scope") or "bar"
    rows = []
    for row in _category_rows_for_scope(scope):
        rows.append([InlineKeyboardButton(label, callback_data=f"menucreate:category:{key}") for key, label in row])
    rows.append([InlineKeyboardButton("⬅️ Ganti Tempat", callback_data="menucreate:backscope")])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="menucreate:cancel")])
    return InlineKeyboardMarkup(rows)


def _menu_items_for_scope(scope: str):
    return [item for item in MENU_ITEMS if (item.get("menu_scope") or "bar") == scope]


def _next_menu_number_for_scope(scope: str) -> int:
    used = []
    for item in _menu_items_for_scope(scope):
        try:
            used.append(int(item.get("no", 0)))
        except Exception:
            pass
    return (max(used) + 1) if used else 1


def _sorted_menu_items_for_scope(scope: str):
    out = []
    for item in _menu_items_for_scope(scope):
        try:
            sort_no = int(item.get("no", 0))
        except Exception:
            sort_no = 999999999
        out.append((sort_no, item))
    out.sort(key=lambda x: x[0])
    return [item for _, item in out]


def _group_menu_items_by_category_for_scope(scope: str):
    grouped = {key: [] for key in _category_order_for_scope(scope)}
    for item in _sorted_menu_items_for_scope(scope):
        cat = item.get("category")
        grouped.setdefault(cat, []).append(item)
    return grouped


def _roll_count_for_scope(scope: str, category: str, item_count: int) -> int:
    if item_count <= 0:
        return 0
    import random
    if scope == "restaurant":
        ranges = {
            "standard_cuisine": (4, 7),
            "premium_cuisine": (3, 5),
            "luxury_dining": (2, 3),
            "limited_edition_cuisine": (0, 1),
            "refreshment": (2, 4),
            "dining_drinks": (2, 3),
            "alcohol_pairing": (0, 1),
        }
        min_count, max_count = ranges.get(category, (1, item_count))
        if max_count == 1 and min_count == 0:
            return 1 if random.random() >= 0.55 else 0
        if item_count < min_count:
            return item_count
        return random.randint(min_count, min(max_count, item_count))
    return _roll_count_for_category(category, item_count)


def _format_rolled_menu_text_for(scope: str):
    title = "𝐑𝐄𝐒𝐓𝐀𝐔𝐑𝐀𝐍𝐓: 𝐓𝐇𝐄 𝐌𝐄𝐍𝐔" if scope == "restaurant" else "𝐋𝐄𝐓𝐇É𝐀: 𝐓𝐇𝐄 𝐌𝐄𝐍𝐔"
    rolled_map = RESTAURANT_ROLLED_MENU if scope == "restaurant" else ROLLED_MENU
    lines = ["ㅤ", f"𖠷 ╱ {title} ", "───────────────`"]
    has_any = False
    for category in _category_order_for_scope(scope):
        items = rolled_map.get(category) or []
        if not items:
            continue
        has_any = True
        lines.append(f"࣪ ˖ ੭ .. : {_menu_category_label(category)}")
        for item in items:
            lines.append(f"› {item.get('name', '-')} — {_normalize_price_text(item.get('price', 0))}")
        lines.append("")
    if not has_any:
        if scope == "restaurant":
            return "Belum ada hasil roll menu restaurant. Gunakan /rollrestaurantmenu dulu."
        return "Belum ada hasil roll menu. Gunakan /rollmenu dulu."
    return "\n".join(lines).strip()


def _format_full_menu_list_text_for(scope: str):
    items = _sorted_menu_items_for_scope(scope)
    if not items:
        return "Belum ada menu tersimpan."
    title = "Restaurant Menu List:" if scope == "restaurant" else "Lethéa Menu List:"
    lines = [title, ""]
    grouped = _group_menu_items_by_category_for_scope(scope)
    for category in _category_order_for_scope(scope):
        cat_items = grouped.get(category) or []
        if not cat_items:
            continue
        lines.append(f"[{_menu_category_label(category)}]")
        for item in cat_items:
            lines.append(f"{item.get('no')}. {item.get('name')} | {_normalize_price_text(item.get('price', 0))}")
        lines.append("")
    return "\n".join(lines).strip()


def _find_menu_item(scope: str, menu_no: int):
    return next((item for item in MENU_ITEMS if (item.get("menu_scope") or "bar") == scope and int(item.get("no", -1)) == menu_no), None)


async def __old_create_menu_cmd_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    sent = await update.message.reply_text(
        "Pilih tempat menu yang ingin dibuat.",
        reply_markup=_create_menu_scope_keyboard(),
    )
    context.user_data["create_menu_flow"] = {
        "menu_scope": None,
        "category": None,
        "name": None,
        "price": None,
        "ingredients": None,
        "description": None,
        "how_to_make": None,
        "image_file_id": None,
        "waiting_for": None,
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
    }


async def __old_menu_create_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    if not _can_manage_menu(query.from_user):
        await query.answer("Hanya Owner atau Currathor.", show_alert=True)
        return
    flow = context.user_data.get("create_menu_flow")
    data = query.data or ""
    if data == "menucreate:cancel":
        if flow:
            await _refresh_create_menu_message(context, flow, final_text="Pembuatan menu dibatalkan.", reply_markup=None)
        else:
            try:
                await query.edit_message_text("Pembuatan menu dibatalkan.")
            except Exception:
                pass
        context.user_data.pop("create_menu_flow", None)
        return
    if not flow:
        await query.edit_message_text("Sesi create menu tidak ditemukan. Gunakan /createmenu lagi.")
        return
    parts = data.split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    if action == "backscope":
        flow.update({"menu_scope": None, "category": None, "waiting_for": None})
        await _refresh_create_menu_message(context, flow)
        return
    if action == "scope" and len(parts) >= 3:
        scope = parts[2]
        if scope not in ("bar", "restaurant"):
            await query.answer("Pilihan tempat tidak valid.", show_alert=True)
            return
        flow.update({"menu_scope": scope, "category": None, "waiting_for": None})
        await _refresh_create_menu_message(context, flow)
        return
    if len(parts) < 3:
        return
    if not flow.get("menu_scope"):
        await query.answer("Pilih tempat menu dulu.", show_alert=True)
        return
    if action == "category":
        category = parts[2]
        if category not in _category_label_map(flow["menu_scope"]):
            await query.answer("Kategori tidak valid.", show_alert=True)
            return
        flow["category"] = category
        flow["waiting_for"] = None
        flow["chat_id"] = query.message.chat_id
        flow["message_id"] = query.message.message_id
        await _refresh_create_menu_message(context, flow)
        return
    if action == "fill":
        target = parts[2]
        if target not in ("name", "price", "ingredients", "description", "image"):
            return
        prereq_map = {
            "price": ["name"],
            "ingredients": ["name", "price"],
            "description": ["name", "price", "ingredients"],
            "image": ["name", "price", "ingredients", "description"],
        }
        missing = []
        for need in prereq_map.get(target, []):
            if need == "price":
                if flow.get("price") is None:
                    missing.append(need)
            elif need == "description":
                if not _menu_description_value(flow):
                    missing.append(need)
            elif not flow.get(need):
                missing.append(need)
        if missing:
            await query.answer("Lengkapi bagian sebelumnya dulu.", show_alert=True)
            return
        flow["waiting_for"] = target
        await _refresh_create_menu_message(context, flow)
        hints = {
            "name": "Kirim nama menu di chat ini.",
            "price": "Kirim nominal harga dalam angka.",
            "ingredients": "Kirim daftar ingredients di chat ini.",
            "description": "Kirim deskripsi menu di chat ini.",
            "image": "Kirim photo atau document image di chat ini.",
        }
        await query.answer(hints.get(target, "Kirim input di chat ini."), show_alert=True)
        return
    if action == "confirm":
        confirm_type = parts[2]
        if confirm_type == "reset":
            flow.update({
                "name": None,
                "price": None,
                "ingredients": None,
                "description": None,
                "how_to_make": None,
                "image_file_id": None,
                "waiting_for": None,
            })
            await _refresh_create_menu_message(context, flow)
            return
        if confirm_type == "yes":
            description_value = _menu_description_value(flow)
            if not flow.get("menu_scope") or not flow.get("category") or not flow.get("name") or flow.get("price") is None or not flow.get("ingredients") or not description_value or not flow.get("image_file_id"):
                await query.answer("Data menu belum lengkap.", show_alert=True)
                return
            item = {
                "no": _next_menu_number_for_scope(flow["menu_scope"]),
                "menu_scope": flow["menu_scope"],
                "category": flow["category"],
                "name": flow["name"],
                "price": int(flow["price"]),
                "ingredients": flow.get("ingredients") or "",
                "description": description_value,
                "how_to_make": description_value,
                "image_file_id": flow.get("image_file_id"),
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": query.from_user.id,
            }
            MENU_ITEMS.append(item)
            save_menu_data()
            await _refresh_create_menu_message(
                context,
                flow,
                final_text=(
                    "✅ Menu baru berhasil disimpan.\n\n"
                    f"Tempat : {_menu_scope_label(item['menu_scope'])}\n"
                    f"Kategori : {_menu_category_label(item['category'])}\n"
                    f"Nama : {item['name']}\n"
                    f"Harga : {_normalize_price_text(item['price'])}\n"
                    "Ingredients : sudah disimpan\n"
                    "Deskripsi : sudah disimpan\n"
                    "Image : sudah disimpan\n"
                    f"Nomor Menu : {item['no']}"
                ),
                reply_markup=None,
            )
            context.user_data.pop("create_menu_flow", None)
            return


async def create_menu_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("create_menu_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        context.user_data.pop("create_menu_flow", None)
        return
    msg = update.effective_message
    if not msg or msg.chat_id != flow.get("chat_id"):
        return
    waiting = flow.get("waiting_for")
    if not waiting or waiting == "image":
        return
    text_in = (msg.text or msg.caption or "").strip()
    if waiting == "name":
        if not text_in:
            await msg.reply_text("Nama menu tidak boleh kosong.")
            return
        flow["name"] = text_in
    elif waiting == "price":
        raw = text_in.replace(".", "").replace(",", "")
        if not raw.isdigit():
            await msg.reply_text("Harga harus angka.")
            return
        amount = int(raw)
        if amount <= 0:
            await msg.reply_text("Harga harus lebih dari 0.")
            return
        flow["price"] = amount
    elif waiting == "ingredients":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await msg.reply_text("Ingredients tidak boleh kosong.")
            return
        flow["ingredients"] = raw_text
    elif waiting == "description":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await msg.reply_text("Deskripsi tidak boleh kosong.")
            return
        flow["description"] = raw_text
        flow["how_to_make"] = raw_text
    else:
        return
    flow["waiting_for"] = None
    await _refresh_create_menu_message(context, flow)


async def __old_create_menu_image_router_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("create_menu_flow")
    if not flow or flow.get("waiting_for") != "image":
        return
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        context.user_data.pop("create_menu_flow", None)
        return
    msg = update.effective_message
    if not msg or msg.chat_id != flow.get("chat_id"):
        return
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id
    if not file_id:
        await msg.reply_text("Image menu harus berupa photo atau document image.")
        return
    flow["image_file_id"] = file_id
    flow["waiting_for"] = None
    await _refresh_create_menu_message(context, flow)


async def roll_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    items = _sorted_menu_items_for_scope("bar")
    if not items:
        await update.message.reply_text("Belum ada menu bar tersimpan. Gunakan /createmenu dulu.")
        return
    import random
    grouped = _group_menu_items_by_category_for_scope("bar")
    rolled = {}
    for category in _category_order_for_scope("bar"):
        cat_items = list(grouped.get(category) or [])
        if not cat_items:
            continue
        count = _roll_count_for_scope("bar", category, len(cat_items))
        if count <= 0:
            continue
        selected = random.sample(cat_items, count)
        selected.sort(key=lambda x: int(x.get("no", 0)))
        rolled[category] = [{"no": item.get("no"), "name": item.get("name"), "price": int(item.get("price", 0))} for item in selected]
    ROLLED_MENU.clear()
    ROLLED_MENU.update(rolled)
    save_menu_data()
    await update.message.reply_text(_format_rolled_menu_text_for("bar"))


async def roll_restaurant_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    items = _sorted_menu_items_for_scope("restaurant")
    if not items:
        await update.message.reply_text("Belum ada menu restaurant tersimpan. Gunakan /createmenu dulu.")
        return
    import random
    grouped = _group_menu_items_by_category_for_scope("restaurant")
    rolled = {}
    for category in _category_order_for_scope("restaurant"):
        cat_items = list(grouped.get(category) or [])
        if not cat_items:
            continue
        count = _roll_count_for_scope("restaurant", category, len(cat_items))
        if count <= 0:
            continue
        selected = random.sample(cat_items, count)
        selected.sort(key=lambda x: int(x.get("no", 0)))
        rolled[category] = [{"no": item.get("no"), "name": item.get("name"), "price": int(item.get("price", 0))} for item in selected]
    RESTAURANT_ROLLED_MENU.clear()
    RESTAURANT_ROLLED_MENU.update(rolled)
    save_menu_data()
    await update.message.reply_text(_format_rolled_menu_text_for("restaurant"))


async def lethea_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    await update.message.reply_text(_format_rolled_menu_text_for("bar"))


async def restaurant_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    await update.message.reply_text(_format_rolled_menu_text_for("restaurant"))


async def list_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    await update.message.reply_text(_format_full_menu_list_text_for("bar"))


async def list_restaurant_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    await update.message.reply_text(_format_full_menu_list_text_for("restaurant"))


async def del_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /delmenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    idx = next((i for i, item in enumerate(MENU_ITEMS) if (item.get("menu_scope") or "bar") == "bar" and int(item.get("no", -1)) == menu_no), None)
    if idx is None:
        await update.message.reply_text("Nomor menu bar tidak ditemukan.")
        return
    deleted = MENU_ITEMS.pop(idx)
    for category, items in list(ROLLED_MENU.items()):
        ROLLED_MENU[category] = [item for item in items if int(item.get("no", -1)) != menu_no]
    save_menu_data()
    await update.message.reply_text(f"✅ Menu bar {deleted.get('name')} dihapus.")


async def del_restaurant_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /delrestaurantmenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    idx = next((i for i, item in enumerate(MENU_ITEMS) if (item.get("menu_scope") or "bar") == "restaurant" and int(item.get("no", -1)) == menu_no), None)
    if idx is None:
        await update.message.reply_text("Nomor menu restaurant tidak ditemukan.")
        return
    deleted = MENU_ITEMS.pop(idx)
    for category, items in list(RESTAURANT_ROLLED_MENU.items()):
        RESTAURANT_ROLLED_MENU[category] = [item for item in items if int(item.get("no", -1)) != menu_no]
    save_menu_data()
    await update.message.reply_text(f"✅ Menu restaurant {deleted.get('name')} dihapus.")


async def add_price_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args:
        await update.message.reply_text("Format: /addpriceall <nominal>")
        return
    raw = context.args[0].replace(".", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text("Nominal harus berupa angka.")
        return
    amount = int(raw)
    if amount <= 0:
        await update.message.reply_text("Nominal harus lebih dari 0.")
        return
    changed = 0
    for item in MENU_ITEMS:
        if (item.get("menu_scope") or "bar") != "bar":
            continue
        item["price"] = int(item.get("price", 0)) + amount
        changed += 1
    for items in ROLLED_MENU.values():
        for item in items:
            item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(f"✅ Harga semua menu bar naik {_normalize_price_text(amount)}. Total menu terubah: {changed}.")


async def add_price_restaurant_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args:
        await update.message.reply_text("Format: /addpricerestaurantall <nominal>")
        return
    raw = context.args[0].replace(".", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text("Nominal harus berupa angka.")
        return
    amount = int(raw)
    if amount <= 0:
        await update.message.reply_text("Nominal harus lebih dari 0.")
        return
    changed = 0
    for item in MENU_ITEMS:
        if (item.get("menu_scope") or "bar") != "restaurant":
            continue
        item["price"] = int(item.get("price", 0)) + amount
        changed += 1
    for items in RESTAURANT_ROLLED_MENU.values():
        for item in items:
            item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(f"✅ Harga semua menu restaurant naik {_normalize_price_text(amount)}. Total menu terubah: {changed}.")


async def add_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text("Format: /addprice <nomor_menu> <nominal>")
        return
    menu_no = int(context.args[0])
    raw = context.args[1].replace(".", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text("Nominal harus berupa angka.")
        return
    amount = int(raw)
    target = _find_menu_item("bar", menu_no)
    if not target:
        await update.message.reply_text("Nomor menu bar tidak ditemukan.")
        return
    target["price"] = int(target.get("price", 0)) + amount
    for items in ROLLED_MENU.values():
        for item in items:
            if int(item.get("no", -1)) == menu_no:
                item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(f"✅ Harga menu bar {target.get('name')} sekarang {_normalize_price_text(target.get('price', 0))}.")


async def add_price_restaurant_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.message.reply_text("Format: /addpricerestaurant <nomor_menu> <nominal>")
        return
    menu_no = int(context.args[0])
    raw = context.args[1].replace(".", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text("Nominal harus berupa angka.")
        return
    amount = int(raw)
    target = _find_menu_item("restaurant", menu_no)
    if not target:
        await update.message.reply_text("Nomor menu restaurant tidak ditemukan.")
        return
    target["price"] = int(target.get("price", 0)) + amount
    for items in RESTAURANT_ROLLED_MENU.values():
        for item in items:
            if int(item.get("no", -1)) == menu_no:
                item["price"] = int(item.get("price", 0)) + amount
    save_menu_data()
    await update.message.reply_text(f"✅ Harga menu restaurant {target.get('name')} sekarang {_normalize_price_text(target.get('price', 0))}.")


async def __old_info_menu_cmd_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /infomenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    target = _find_menu_item("bar", menu_no)
    if not target:
        await update.message.reply_text("Nomor menu bar tidak ditemukan.")
        return
    text = _format_menu_info_text(target)
    image_file_id = target.get("image_file_id")
    if image_file_id:
        try:
            await update.message.reply_photo(photo=image_file_id, caption=text)
            return
        except Exception as e:
            print(f"[info_menu_cmd] send photo failed: {e}")
    await update.message.reply_text(text)


async def info_restaurant_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /inforestaurantmenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    target = _find_menu_item("restaurant", menu_no)
    if not target:
        await update.message.reply_text("Nomor menu restaurant tidak ditemukan.")
        return
    text = _format_menu_info_text(target)
    image_file_id = target.get("image_file_id")
    if image_file_id:
        try:
            await update.message.reply_photo(photo=image_file_id, caption=text)
            return
        except Exception as e:
            print(f"[info_restaurant_menu_cmd] send photo failed: {e}")
    await update.message.reply_text(text)


async def __old_help_cmd_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    text = (
        "Perintah yang tersedia:\n\n"
        "User:\n"
        "• /start\n• /menu\n• /registration\n• /registrationstaff\n• /renewal\n• /upgradevip\n• /myacc\n• /changepict\n• /mybalance\n• /choicepoker\n• /letheamenu\n• /restaurantmenu\n• /rentangel\n• /starttalk\n• /stoptalk\n• /cancel\n• /help\n"
    )
    if _can_manage_menu(user):
        text += (
            "\nMenu Management:\n"
            "• /createmenu\n• /rollmenu\n• /letheamenu\n• /listmenu\n• /infomenu <nomor_menu>\n• /delmenu <nomor_menu>\n• /addpriceall <nominal>\n• /addprice <nomor_menu> <nominal>\n"
            "\nRestaurant Management:\n"
            "• /rollrestaurantmenu\n• /restaurantmenu\n• /listrestaurantmenu\n• /inforestaurantmenu <nomor_menu>\n• /delrestaurantmenu <nomor_menu>\n• /addpricerestaurantall <nominal>\n• /addpricerestaurant <nomor_menu> <nominal>\n"
        )
    if _can_manage_staff(user):
        text += (
            "\nStaff Management:\n"
            "• /addstaff  (reply ke pesan user target)\n• /editrole <acc_no>\n• /delstaff <acc_no>\n• /ban <acc_no>\n• /unban <acc_no>\n• /inputangel\n• /listangel\n• /sendbill <acc_no> <nominal>\n• /openbar [link]\n• /closebar\n• /openshift\n• /closeshift\n• /listroom\n •delroom\n"
        )
    if _is_admin(user):
        text += (
            "\nAdmin:\n"
            "• /addsaldo <acc_no> <jumlah>\n• /minsaldo <acc_no> <jumlah>\n• /listacc\n• /acc\n• /reject\n"
        )
    if _is_owner(user):
        text += (
            "\nOwner:\n"
            "• /addadmin <acc_no>\n• /deladmin <acc_no>\n• /listadmin\n• /delacc <acc_no>\n"
        )
    await update.message.reply_text(text)


# =========================================================
# FEATURE EXTENSIONS
# CNIT + ANGEL BOOKING + MENU IMAGE SUPPORT
# =========================================================
CNIT_CLAIM_FILE = "oxana_cnit_claims.json"
CNIT_BOOK_FILE = "oxana_cnit_book.json"
CNIT_CLAIMS = {}
CNIT_BOOK = {"entries": [], "payments": {}}

# Biaya bot bulanan. Ubah angka ini kalau biaya bot berubah.
BOT_MONTHLY_FEE_RUPIAH = 15000

# Rate CNIT -> rupiah. Angka di tabel khusus dipakai exact match.
# Untuk jumlah lain, Asmoday pakai rumus lanjutan: 10.000 CNIT = Rp750.
CNIT_RUPIAH_RATE_PER_10000 = 750
CNIT_RUPIAH_PRICE_TABLE = {
    10000: 750,
    20000: 1500,
    30000: 2250,
    40000: 3000,
    50000: 3750,
    60000: 4520,
    70000: 5250,
    80000: 6000,
    90000: 6750,
    100000: 7500,
    200000: 15000,
    300000: 22500,
    400000: 30000,
    500000: 37500,
}


def save_cnit_claims():
    try:
        with open(CNIT_CLAIM_FILE, "w", encoding="utf-8") as f:
            json.dump({"claims": CNIT_CLAIMS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_cnit_claims failed: {e}")


def load_cnit_claims():
    global CNIT_CLAIMS
    try:
        p = Path(CNIT_CLAIM_FILE)
        if not p.exists():
            CNIT_CLAIMS = {}
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        CNIT_CLAIMS = data.get("claims", {}) if isinstance(data, dict) else {}
        if not isinstance(CNIT_CLAIMS, dict):
            CNIT_CLAIMS = {}
    except Exception as e:
        print(f"[WARN] load_cnit_claims failed: {e}")
        CNIT_CLAIMS = {}




def save_cnit_book():
    try:
        data = CNIT_BOOK if isinstance(CNIT_BOOK, dict) else {"entries": []}
        data.setdefault("entries", [])
        data.setdefault("payments", {})
        with open(CNIT_BOOK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_cnit_book failed: {e}")


def load_cnit_book():
    global CNIT_BOOK
    try:
        p = Path(CNIT_BOOK_FILE)
        if not p.exists():
            CNIT_BOOK = {"entries": [], "payments": {}}
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        CNIT_BOOK = data if isinstance(data, dict) else {"entries": [], "payments": {}}
        if not isinstance(CNIT_BOOK.get("entries"), list):
            CNIT_BOOK["entries"] = []
        if not isinstance(CNIT_BOOK.get("payments"), dict):
            CNIT_BOOK["payments"] = {}
    except Exception as e:
        print(f"[WARN] load_cnit_book failed: {e}")
        CNIT_BOOK = {"entries": []}


def _month_key(dt_text=None):
    if dt_text:
        parsed = _parse_dt(str(dt_text))
        if parsed:
            return parsed.strftime("%Y-%m")
        if re.match(r"^\d{4}-\d{2}$", str(dt_text).strip()):
            return str(dt_text).strip()
    return _now().strftime("%Y-%m")


def _format_rupiah(amount) -> str:
    try:
        return f"Rp{int(amount):,}".replace(",", ".")
    except Exception:
        return f"Rp{amount}"


def _cnit_to_rupiah(amount: int) -> int:
    amount = int(amount or 0)
    if amount <= 0:
        return 0
    if amount in CNIT_RUPIAH_PRICE_TABLE:
        return int(CNIT_RUPIAH_PRICE_TABLE[amount])
    return (amount * int(CNIT_RUPIAH_RATE_PER_10000) + 9999) // 10000


def _currathor_labels():
    out = {}
    for uid in _currathor_uids():
        rec = _get_existing_account(int(uid))
        if not rec:
            continue
        username = rec.get("username")
        label = f"@{username}" if username and username != "-" else (rec.get("name") or f"UID {uid}")
        out[str(uid)] = {"uid": int(uid), "acc_no": rec.get("acc_no"), "label": label}
    return out


def _split_rupiah_to_currathors(total: int):
    labels = _currathor_labels()
    shares = _split_evenly(int(total or 0), [int(uid) for uid in labels.keys()])
    result = {}
    for uid, amount in shares.items():
        meta = labels.get(str(uid), {"uid": int(uid), "acc_no": None, "label": f"UID {uid}"})
        result[str(uid)] = {**meta, "amount": int(amount)}
    return result


def _record_cnit_claim_book_entry(claim: dict, rec: dict, actor_user=None):
    amount_cnit = int(claim.get("amount", 0) or 0)
    amount_rupiah = _cnit_to_rupiah(amount_cnit)
    resolved_at = claim.get("resolved_at") or _now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "type": "cnit_claim",
        "month": _month_key(resolved_at),
        "created_at": resolved_at,
        "acc_no": str(claim.get("acc_no") or rec.get("acc_no") or "-"),
        "uid": int(claim.get("uid", 0) or 0),
        "username": rec.get("username") or "-",
        "staff_role": rec.get("staff_role") or rec.get("account_type") or "-",
        "nitroseen_id": claim.get("nitroseen_id") or rec.get("nitroseen_id") or "-",
        "cnit": amount_cnit,
        "rupiah": amount_rupiah,
        "confirmed_by": getattr(actor_user, "id", None),
        "shares": _split_rupiah_to_currathors(amount_rupiah),
    }
    CNIT_BOOK.setdefault("entries", []).append(entry)
    save_cnit_book()
    return entry


def _cnit_book_summary(month_key: str):
    month_key = _month_key(month_key)
    entries = [e for e in CNIT_BOOK.get("entries", []) if e.get("month") == month_key]
    currathors = _currathor_labels()
    claim_total = sum(int(e.get("rupiah", 0) or 0) for e in entries if e.get("type") == "cnit_claim")
    bot_fee = int(BOT_MONTHLY_FEE_RUPIAH or 0)
    per_currathor = {uid: {**meta, "claim": 0, "bot": 0, "total": 0} for uid, meta in currathors.items()}
    for e in entries:
        if e.get("type") != "cnit_claim":
            continue
        for uid, share in (e.get("shares") or {}).items():
            if uid not in per_currathor:
                per_currathor[uid] = {"uid": int(uid), "acc_no": share.get("acc_no"), "label": share.get("label") or f"UID {uid}", "claim": 0, "bot": 0, "total": 0}
            per_currathor[uid]["claim"] += int(share.get("amount", 0) or 0)
    bot_shares = _split_rupiah_to_currathors(bot_fee)
    for uid, share in bot_shares.items():
        if uid not in per_currathor:
            per_currathor[uid] = {**share, "claim": 0, "bot": 0, "total": 0}
        per_currathor[uid]["bot"] += int(share.get("amount", 0) or 0)
    for uid in list(per_currathor.keys()):
        per_currathor[uid]["total"] = int(per_currathor[uid].get("claim", 0)) + int(per_currathor[uid].get("bot", 0))
    return {"month": month_key, "entries": entries, "claim_total": claim_total, "bot_fee": bot_fee, "grand_total": claim_total + bot_fee, "per_currathor": per_currathor}


def _format_cnit_book_text(month_key: str):
    summary = _cnit_book_summary(month_key)
    lines = ["𖠷 ╱ PEMBUKUAN CNIT", "", f"Bulan : {summary['month']}", f"Total claim CNIT : {_format_rupiah(summary['claim_total'])}", f"Biaya bot bulanan : {_format_rupiah(summary['bot_fee'])}", f"Total tagihan : {_format_rupiah(summary['grand_total'])}", "", "Tagihan per Currathor:"]
    rows = sorted(summary["per_currathor"].values(), key=lambda x: (str(x.get("label") or ""), int(x.get("uid", 0) or 0)))
    if not rows:
        lines.append("› Belum ada Currathor terdaftar. Biaya belum bisa dibagi.")
    else:
        for row in rows:
            lines.append(f"› {row.get('label')} | claim {_format_rupiah(row.get('claim', 0))} + bot {_format_rupiah(row.get('bot', 0))} = {_format_rupiah(row.get('total', 0))}")
    lines.extend(["", "Detail claim bulan ini:"])
    claim_entries = [e for e in summary["entries"] if e.get("type") == "cnit_claim"]
    if not claim_entries:
        lines.append("› Belum ada claim CNIT yang di-confirm bulan ini.")
    else:
        for i, e in enumerate(claim_entries[-20:], start=1):
            uname = e.get("username") or "-"
            user_label = f"@{uname}" if uname != "-" else f"Acc {e.get('acc_no', '-')}"
            lines.append(f"O{i}. {user_label} | {int(e.get('cnit', 0) or 0)} CNIT | {_format_rupiah(e.get('rupiah', 0))} | {e.get('created_at', '-')}")
    return "\n".join(lines)


async def cnit_book_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    month = context.args[0].strip() if context.args else _now().strftime("%Y-%m")
    if not re.match(r"^\d{4}-\d{2}$", month):
        await update.message.reply_text("Format: /cnitbook atau /cnitbook YYYY-MM")
        return
    await update.message.reply_text(_format_cnit_book_text(month))


async def bot_fee_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    month = context.args[0].strip() if context.args else _now().strftime("%Y-%m")
    if not re.match(r"^\d{4}-\d{2}$", month):
        await update.message.reply_text("Format: /botfee atau /botfee YYYY-MM")
        return
    summary = _cnit_book_summary(month)
    lines = ["𖠷 ╱ BIAYA BOT", "", f"Bulan : {summary['month']}", f"Total biaya bot : {_format_rupiah(summary['bot_fee'])}", "", "Dibagi ke Currathor:"]
    rows = sorted(summary["per_currathor"].values(), key=lambda x: (str(x.get("label") or ""), int(x.get("uid", 0) or 0)))
    if not rows:
        lines.append("› Belum ada Currathor terdaftar.")
    else:
        for row in rows:
            lines.append(f"› {row.get('label')} : {_format_rupiah(row.get('bot', 0))}")
    await update.message.reply_text("\n".join(lines))


def _cnit_payment_records(month_key: str):
    month_key = _month_key(month_key)
    payments = CNIT_BOOK.setdefault("payments", {})
    month_records = payments.setdefault(month_key, {})
    if not isinstance(month_records, dict):
        payments[month_key] = {}
        month_records = payments[month_key]
    return month_records


def _set_cnit_bill_paid(month_key: str, uid: int, actor_user=None):
    month_key = _month_key(month_key)
    month_records = _cnit_payment_records(month_key)
    month_records[str(int(uid))] = {
        "paid": True,
        "paid_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "confirmed_by": getattr(actor_user, "id", None),
    }
    save_cnit_book()
    return month_records[str(int(uid))]


def _currathor_bill_row(month_key: str, uid: int):
    summary = _cnit_book_summary(month_key)
    row = summary.get("per_currathor", {}).get(str(int(uid)))
    if not row:
        rec = _get_existing_account(int(uid))
        username = (rec or {}).get("username") or "-"
        label = f"@{username}" if username != "-" else ((rec or {}).get("name") or f"UID {uid}")
        row = {"uid": int(uid), "acc_no": (rec or {}).get("acc_no"), "label": label, "claim": 0, "bot": 0, "total": 0}
    row = dict(row)
    paid_rec = _cnit_payment_records(summary["month"]).get(str(int(uid))) or {}
    row["paid"] = bool(paid_rec.get("paid"))
    row["paid_at"] = paid_rec.get("paid_at")
    row["confirmed_by"] = paid_rec.get("confirmed_by")
    return summary, row


def _format_my_bill_text(month_key: str, uid: int):
    summary, row = _currathor_bill_row(month_key, uid)
    status = "☑ Lunas" if row.get("paid") else "☒ Belum Lunas"
    lines = [
        "𖠷 ╱ CURRATHOR MONTHLY BILL",
        "",
        f"Bulan : {summary['month']}",
        f"Currathor : {row.get('label')}",
        f"Status : {status}",
        "",
        f"Tagihan claim CNIT staff/angel : {_format_rupiah(row.get('claim', 0))}",
        f"Biaya bot bulanan : {_format_rupiah(row.get('bot', 0))}",
        f"Total perlu dibayar : {_format_rupiah(row.get('total', 0))}",
    ]
    if row.get("paid_at"):
        lines.append(f"Tanggal konfirmasi : {row.get('paid_at')}")
    lines.extend(["", "Gunakan /paymentbill untuk menandai tagihan bulan ini sudah dibayar."])
    return "\n".join(lines)


def _parse_month_key_to_date(month_key: str):
    try:
        return datetime.strptime(month_key, "%Y-%m")
    except Exception:
        return None


def _iter_month_keys(start_month: str, end_month: str):
    start = _parse_month_key_to_date(start_month)
    end = _parse_month_key_to_date(end_month)
    if not start or not end or start > end:
        return []
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y += 1
            m = 1
    return out


def _known_cnit_bill_months():
    months = set()
    for entry in CNIT_BOOK.get("entries", []) or []:
        month = str(entry.get("month") or "").strip()
        if re.match(r"^\d{4}-\d{2}$", month):
            months.add(month)
    for month in (CNIT_BOOK.get("payments", {}) or {}).keys():
        month = str(month or "").strip()
        if re.match(r"^\d{4}-\d{2}$", month):
            months.add(month)
    current = _now().strftime("%Y-%m")
    months.add(current)
    return _iter_month_keys(min(months), current) if months else [current]


def _format_unpaid_my_bills_text(uid: int):
    rec = _get_existing_account(int(uid)) or {}
    username = rec.get("username") or "-"
    label = f"@{username}" if username != "-" else (rec.get("name") or f"UID {uid}")
    rows = []
    for month in _known_cnit_bill_months():
        summary, row = _currathor_bill_row(month, int(uid))
        if row.get("paid"):
            continue
        total = int(row.get("total", 0) or 0)
        if total <= 0:
            continue
        rows.append((summary["month"], total))
    lines = [
        "𖠷 ╱ CURRATHOR UNPAID BILLS",
        "",
        f"Currathor : {label}",
        "",
        "Tagihan belum lunas:",
    ]
    if not rows:
        lines.append("› Tidak ada tagihan yang belum lunas.")
    else:
        for month, total in rows:
            lines.append(f"› {month} | ☒ Belum Lunas | {_format_rupiah(total)}")
    lines.extend([
        "",
        "Gunakan /mybill YYYY-MM untuk melihat detail bulan tertentu.",
        "Gunakan /paymentbill YYYY-MM kalau tagihan bulan itu sudah dibayar.",
    ])
    return "\n".join(lines)


async def my_bill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or (rec.get("staff_role") or "").lower() != "currathor":
        await update.message.reply_text("Command ini hanya untuk Currathor.")
        return
    if not context.args:
        await update.message.reply_text(_format_unpaid_my_bills_text(update.effective_user.id))
        return
    month = context.args[0].strip()
    if not re.match(r"^\d{4}-\d{2}$", month):
        await update.message.reply_text("Format: /mybill atau /mybill YYYY-MM")
        return
    await update.message.reply_text(_format_my_bill_text(month, update.effective_user.id))


async def payment_bill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    actor = update.effective_user
    actor_rec = _get_existing_account(actor.id)
    is_actor_currathor = bool(actor_rec and (actor_rec.get("staff_role") or "").lower() == "currathor")
    if not is_actor_currathor and not _is_owner(actor):
        await update.message.reply_text("Command ini hanya untuk Currathor atau Owner.")
        return

    month = _now().strftime("%Y-%m")
    target_uid = int(actor.id)

    if context.args:
        first = context.args[0].strip()
        if re.match(r"^\d{4}-\d{2}$", first):
            month = first
            if len(context.args) >= 2:
                if not _is_owner(actor):
                    await update.message.reply_text("Hanya Owner yang bisa menandai bill Currathor lain.")
                    return
                acc_no = context.args[1].strip()
                if not acc_no.isdigit():
                    await update.message.reply_text("Format: /paymentbill [YYYY-MM] [acc_no]")
                    return
                uid, rec = _get_account_by_acc_no(acc_no)
                if not rec or (rec.get("staff_role") or "").lower() != "currathor":
                    await update.message.reply_text("Account target bukan Currathor.")
                    return
                target_uid = int(uid)
        elif first.isdigit():
            if not _is_owner(actor):
                await update.message.reply_text("Hanya Owner yang bisa menandai bill Currathor lain.")
                return
            uid, rec = _get_account_by_acc_no(first)
            if not rec or (rec.get("staff_role") or "").lower() != "currathor":
                await update.message.reply_text("Account target bukan Currathor.")
                return
            target_uid = int(uid)
        else:
            await update.message.reply_text("Format: /paymentbill atau /paymentbill YYYY-MM")
            return

    _set_cnit_bill_paid(month, target_uid, actor)
    await update.message.reply_text(_format_my_bill_text(month, target_uid))


def _normalize_account_record(uid: int, rec: dict) -> dict:
    defaults = {
        "acc_no": None,
        "name": "-",
        "full_name": None,
        "username": "-",
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "account_type": "member",
        "staff_role": None,
        "balance": 0,
        "membership_type": None,
        "membership_status": "deactive",
        "membership_started_at": None,
        "membership_expires_at": None,
        "last_expiry_notified_at": None,
        "renewal_pending": None,
        "upgrade_pending": None,
        "banned": False,
        "owner_override": False,
        "cnit_pending": 0,
        "nitroseen_id": None,
        "cnit_claim_active": False,
        "cnit_claim_requested_at": None,
        "cnit_claim_history": [],
        "staff_shift_total": 0,
        "staff_shift_monthly": {},
        "idcard_photo_file_id": None,
        "idcard_waiting_photo": False,
    }
    for k, v in defaults.items():
        if k not in rec:
            rec[k] = v
    if rec["acc_no"] is None:
        rec["acc_no"] = uid
    if rec.get("balance") is None:
        rec["balance"] = 0
    for num_key in ("cnit_pending", "staff_shift_total"):
        try:
            rec[num_key] = int(rec.get(num_key, 0) or 0)
        except Exception:
            rec[num_key] = 0
    rec["cnit_claim_active"] = bool(rec.get("cnit_claim_active"))
    if not isinstance(rec.get("cnit_claim_history"), list):
        rec["cnit_claim_history"] = []
    if not isinstance(rec.get("staff_shift_monthly"), dict):
        rec["staff_shift_monthly"] = {}
    if not rec.get("account_type"):
        rec["account_type"] = "member"
    return rec


def _create_account(uid: int, user, account_type="member"):
    uid_str = str(uid)
    if uid_str in ACCOUNTS:
        rec = _normalize_account_record(uid, ACCOUNTS[uid_str])
        if not rec.get("full_name"):
            rec["full_name"] = user.full_name or rec.get("name", "-")
        rec["username"] = user.username or rec.get("username", "-")
        rec["account_type"] = account_type or rec.get("account_type", "member")
        ACCOUNTS[uid_str] = rec
        save_accounts()
        return rec
    acc_no = _next_account_number()
    rec = _normalize_account_record(uid, {
        "acc_no": acc_no,
        "name": user.full_name or "-",
        "full_name": user.full_name or "-",
        "username": user.username or "-",
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "account_type": account_type,
    })
    ACCOUNTS[uid_str] = rec
    ACCOUNT_INDEX[str(acc_no)] = uid_str
    save_accounts()
    return rec


def _ensure_angel_profile(uid: int):
    key = str(uid)
    profile = ANGEL_PROFILES.get(key)
    if not isinstance(profile, dict):
        profile = {}
    defaults = {
        "image_file_id": None,
        "short_desc": "",
        "total_orders": 0,
        "is_available": True,
        "bookings": [],
        "off_dates": [],
    }
    for k, v in defaults.items():
        profile.setdefault(k, v)
    if not isinstance(profile.get("bookings"), list):
        profile["bookings"] = []
    if not isinstance(profile.get("off_dates"), list):
        profile["off_dates"] = []
    profile["is_available"] = True
    ANGEL_PROFILES[key] = profile
    return profile


RESTAURANT_CATEGORY_LABELS = {
    "standard_cuisine": "Standard Cuisine 🍽️",
    "premium_cuisine": "Premium Cuisine 🍽️",
    "luxury_dining": "Luxury Dining 🍽️",
    "limited_edition_cuisine": "Limited Edition Cuisine 🍽️",
    "refreshment": "Refreshment 🥤",
    "dining_drinks": "Dining Drinks 🥂",
    "alcohol_pairing": "Alcohol Pairing (Optional) 🍷",
}
RESTAURANT_CATEGORY_ORDER = [
    "standard_cuisine",
    "premium_cuisine",
    "luxury_dining",
    "limited_edition_cuisine",
    "refreshment",
    "dining_drinks",
    "alcohol_pairing",
]
RESTAURANT_CATEGORY_CREATE_ROWS = [
    [("standard_cuisine", "Standard Cuisine"), ("premium_cuisine", "Premium Cuisine")],
    [("luxury_dining", "Luxury Dining"), ("limited_edition_cuisine", "Limited Edition Cuisine")],
    [("refreshment", "Refreshment"), ("dining_drinks", "Dining Drinks")],
    [("alcohol_pairing", "Alcohol Pairing (Optional)")],
]


def _menu_scope_label(scope: str) -> str:
    return "Restaurant" if scope == "restaurant" else "Lethéa Bar"


def _menu_title_label(scope: str) -> str:
    return "𝐑𝐄𝐒𝐓𝐀𝐔𝐑𝐀𝐍𝐓" if scope == "restaurant" else "𝐋𝐄𝐓𝐇É𝐀"


def _category_label_map(scope: str):
    return RESTAURANT_CATEGORY_LABELS if scope == "restaurant" else MENU_CATEGORY_LABELS


def _category_rows_for_scope(scope: str):
    return RESTAURANT_CATEGORY_CREATE_ROWS if scope == "restaurant" else MENU_CATEGORY_CREATE_ROWS


def _menu_description_value(item_or_flow):
    data = item_or_flow or {}
    return data.get("description") or data.get("how_to_make") or ""


def _create_menu_scope_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Lethéa Bar", callback_data="menucreate:scope:bar"),
            InlineKeyboardButton("Restaurant", callback_data="menucreate:scope:restaurant"),
        ],
        [InlineKeyboardButton("❌ Batal", callback_data="menucreate:cancel")],
    ])


def _menu_image_status(item_or_flow):
    return "sudah diisi" if (item_or_flow or {}).get("image_file_id") else "belum"


def _create_menu_input_keyboard(flow: dict):
    rows = [
        [
            InlineKeyboardButton("Nama", callback_data="menucreate:fill:name"),
            InlineKeyboardButton("Harga", callback_data="menucreate:fill:price"),
        ],
        [
            InlineKeyboardButton("Ingredients", callback_data="menucreate:fill:ingredients"),
            InlineKeyboardButton("Deskripsi", callback_data="menucreate:fill:description"),
        ],
        [InlineKeyboardButton("Gambar Menu", callback_data="menucreate:fill:image")],
    ]
    if flow.get("name") and flow.get("price") is not None and flow.get("ingredients") and _menu_description_value(flow) and flow.get("image_file_id"):
        rows.append([
            InlineKeyboardButton("✅ Simpan", callback_data="menucreate:confirm:yes"),
            InlineKeyboardButton("🔄 Reset", callback_data="menucreate:confirm:reset"),
        ])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="menucreate:cancel")])
    return InlineKeyboardMarkup(rows)


def _build_menu_create_text(flow: dict) -> str:
    scope = flow.get("menu_scope") or "bar"
    category = _menu_category_label(flow.get("category", "-"))
    name = flow.get("name") or "-"
    price = _normalize_price_text(flow.get("price")) if flow.get("price") is not None else "-"
    ingredients = flow.get("ingredients") or "-"
    description = _menu_description_value(flow) or "-"
    waiting = flow.get("waiting_for")
    image_status = "sudah diisi" if flow.get("image_file_id") else "belum"
    lines = [
        f"𖠷 ╱ {_menu_title_label(scope)}: 𝐂𝐑𝐄𝐀𝐓𝐄 𝐌𝐄𝐍𝐔",
        "",
        f"Tempat : {_menu_scope_label(scope)}",
        f"Kategori : {category}",
        f"Nama : {name}",
        f"Harga : {price}",
        f"Ingredients : {ingredients}",
        f"Deskripsi : {description}",
        f"Image : {image_status}",
        "",
    ]
    prompts = {
        "name": "Sedang mengisi nama menu. Kirim teks nama menu di chat ini.",
        "price": "Sedang mengisi harga menu. Kirim nominal harga dalam angka di chat ini.",
        "ingredients": "Sedang mengisi ingredients. Kirim daftar ingredients di chat ini. Bisa satu baris atau multi-line.",
        "description": "Sedang mengisi deskripsi menu. Kirim teks deskripsi di chat ini. Bisa satu baris atau multi-line.",
        "image": "Sedang mengisi image. Kirim photo atau document image di chat ini.",
    }
    if waiting in prompts:
        lines.append(prompts[waiting])
    elif flow.get("name") and flow.get("price") is not None and flow.get("ingredients") and _menu_description_value(flow) and flow.get("image_file_id"):
        lines.append("Apakah sudah sesuai?")
    elif flow.get("menu_scope") and not flow.get("category"):
        lines.append("Pilih kategori menu di bawah.")
    elif not flow.get("menu_scope"):
        lines.append("Pilih tempat menu di bawah.")
    else:
        lines.append("Pilih bagian yang ingin diisi lewat tombol di bawah.")
    return "\n".join(lines)


async def _refresh_create_menu_message(context, flow: dict, *, final_text: str = None, reply_markup=None):
    chat_id = flow.get("chat_id")
    message_id = flow.get("message_id")
    if not chat_id or not message_id:
        return False
    text_out = final_text if final_text is not None else _build_menu_create_text(flow)
    if reply_markup is None and final_text is None:
        if not flow.get("menu_scope"):
            reply_markup = _create_menu_scope_keyboard()
        elif not flow.get("category"):
            reply_markup = _create_menu_category_keyboard(flow)
        else:
            reply_markup = _create_menu_input_keyboard(flow)
    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text_out, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"[_refresh_create_menu_message] error: {e}")
        return False


async def create_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    sent = await update.message.reply_text(
        "Pilih tempat menu yang ingin dibuat.",
        reply_markup=_create_menu_scope_keyboard(),
    )
    context.user_data["create_menu_flow"] = {
        "menu_scope": None,
        "category": None,
        "name": None,
        "price": None,
        "ingredients": None,
        "description": None,
        "how_to_make": None,
        "image_file_id": None,
        "waiting_for": None,
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
    }


async def menu_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    if not _can_manage_menu(query.from_user):
        await query.answer("Hanya Owner atau Currathor.", show_alert=True)
        return
    flow = context.user_data.get("create_menu_flow")
    data = query.data or ""
    if data == "menucreate:cancel":
        if flow:
            await _refresh_create_menu_message(context, flow, final_text="Pembuatan menu dibatalkan.", reply_markup=None)
        else:
            try:
                await query.edit_message_text("Pembuatan menu dibatalkan.")
            except Exception:
                pass
        context.user_data.pop("create_menu_flow", None)
        return
    if not flow:
        await query.edit_message_text("Sesi create menu tidak ditemukan. Gunakan /createmenu lagi.")
        return
    parts = data.split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    if action == "backscope":
        flow.update({"menu_scope": None, "category": None, "waiting_for": None})
        await _refresh_create_menu_message(context, flow)
        return
    if action == "scope" and len(parts) >= 3:
        scope = parts[2]
        if scope not in ("bar", "restaurant"):
            await query.answer("Pilihan tempat tidak valid.", show_alert=True)
            return
        flow.update({"menu_scope": scope, "category": None, "waiting_for": None})
        await _refresh_create_menu_message(context, flow)
        return
    if len(parts) < 3:
        return
    if not flow.get("menu_scope"):
        await query.answer("Pilih tempat menu dulu.", show_alert=True)
        return
    if action == "category":
        category = parts[2]
        if category not in _category_label_map(flow["menu_scope"]):
            await query.answer("Kategori tidak valid.", show_alert=True)
            return
        flow["category"] = category
        flow["waiting_for"] = None
        flow["chat_id"] = query.message.chat_id
        flow["message_id"] = query.message.message_id
        await _refresh_create_menu_message(context, flow)
        return
    if action == "fill":
        target = parts[2]
        if target not in ("name", "price", "ingredients", "description", "image"):
            return
        prereq_map = {
            "price": ["name"],
            "ingredients": ["name", "price"],
            "description": ["name", "price", "ingredients"],
            "image": ["name", "price", "ingredients", "description"],
        }
        missing = []
        for need in prereq_map.get(target, []):
            if need == "price":
                if flow.get("price") is None:
                    missing.append(need)
            elif need == "description":
                if not _menu_description_value(flow):
                    missing.append(need)
            elif not flow.get(need):
                missing.append(need)
        if missing:
            await query.answer("Lengkapi bagian sebelumnya dulu.", show_alert=True)
            return
        flow["waiting_for"] = target
        await _refresh_create_menu_message(context, flow)
        hints = {
            "name": "Kirim nama menu di chat ini.",
            "price": "Kirim nominal harga dalam angka.",
            "ingredients": "Kirim daftar ingredients di chat ini.",
            "description": "Kirim deskripsi menu di chat ini.",
            "image": "Kirim photo atau document image di chat ini.",
        }
        await query.answer(hints.get(target, "Kirim input di chat ini."), show_alert=True)
        return
    if action == "confirm":
        confirm_type = parts[2]
        if confirm_type == "reset":
            flow.update({
                "name": None,
                "price": None,
                "ingredients": None,
                "description": None,
                "how_to_make": None,
                "image_file_id": None,
                "waiting_for": None,
            })
            await _refresh_create_menu_message(context, flow)
            return
        if confirm_type == "yes":
            description_value = _menu_description_value(flow)
            if not flow.get("menu_scope") or not flow.get("category") or not flow.get("name") or flow.get("price") is None or not flow.get("ingredients") or not description_value or not flow.get("image_file_id"):
                await query.answer("Data menu belum lengkap.", show_alert=True)
                return
            existing_numbers = []
            for item in MENU_ITEMS:
                if (item.get("menu_scope") or "bar") == flow["menu_scope"]:
                    try:
                        existing_numbers.append(int(item.get("no", 0)))
                    except Exception:
                        pass
            next_no = (max(existing_numbers) + 1) if existing_numbers else 1
            item = {
                "no": next_no,
                "menu_scope": flow["menu_scope"],
                "category": flow["category"],
                "name": flow["name"],
                "price": int(flow["price"]),
                "ingredients": flow.get("ingredients") or "",
                "description": description_value,
                "how_to_make": description_value,
                "image_file_id": flow.get("image_file_id"),
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": query.from_user.id,
            }
            MENU_ITEMS.append(item)
            save_menu_data()
            await _refresh_create_menu_message(
                context,
                flow,
                final_text=(
                    "✅ Menu baru berhasil disimpan.\n\n"
                    f"Tempat : {_menu_scope_label(item['menu_scope'])}\n"
                    f"Kategori : {_menu_category_label(item['category'])}\n"
                    f"Nama : {item['name']}\n"
                    f"Harga : {_normalize_price_text(item['price'])}\n"
                    "Ingredients : sudah disimpan\n"
                    "Deskripsi : sudah disimpan\n"
                    "Image : sudah disimpan\n"
                    f"Nomor Menu : {item['no']}"
                ),
                reply_markup=None,
            )
            context.user_data.pop("create_menu_flow", None)
            return
    if not _can_manage_menu(update.effective_user):
        context.user_data.pop("create_menu_flow", None)
        return
    msg = update.effective_message
    if not msg or msg.chat_id != flow.get("chat_id"):
        return
    waiting = flow.get("waiting_for")
    if not waiting or waiting == "image":
        return
    text_in = (msg.text or msg.caption or "").strip()
    if waiting == "name":
        if not text_in:
            await msg.reply_text("Nama menu tidak boleh kosong.")
            return
        flow["name"] = text_in
    elif waiting == "price":
        raw = text_in.replace(".", "").replace(",", "")
        if not raw.isdigit():
            await msg.reply_text("Harga harus angka.")
            return
        amount = int(raw)
        if amount <= 0:
            await msg.reply_text("Harga harus lebih dari 0.")
            return
        flow["price"] = amount
    elif waiting == "ingredients":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await msg.reply_text("Ingredients tidak boleh kosong.")
            return
        flow["ingredients"] = raw_text
    elif waiting == "description":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await msg.reply_text("Deskripsi tidak boleh kosong.")
            return
        flow["description"] = raw_text
        flow["how_to_make"] = raw_text
    else:
        return
    flow["waiting_for"] = None
    await _refresh_create_menu_message(context, flow)


async def create_menu_image_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Jangan ganggu foto yang sedang ditunggu oleh /changepict.
    if context.user_data.get("idcard_waiting_photo"):
        return
    flow = context.user_data.get("create_menu_flow")
    if not flow or flow.get("waiting_for") != "image":
        return
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_menu(update.effective_user):
        context.user_data.pop("create_menu_flow", None)
        return
    msg = update.effective_message
    if not msg or msg.chat_id != flow.get("chat_id"):
        return
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id
    if not file_id:
        await msg.reply_text("Image menu harus berupa photo atau document image.")
        return
    flow["image_file_id"] = file_id
    flow["waiting_for"] = None
    await _refresh_create_menu_message(context, flow)


async def info_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /infomenu <nomor_menu>")
        return
    menu_no = int(context.args[0])
    target = next((item for item in MENU_ITEMS if int(item.get("no", -1)) == menu_no), None)
    if not target:
        await update.message.reply_text("Nomor menu tidak ditemukan.")
        return
    text = _format_menu_info_text(target)
    image_file_id = target.get("image_file_id")
    if image_file_id:
        try:
            await update.message.reply_photo(photo=image_file_id, caption=text)
            return
        except Exception as e:
            print(f"[info_menu_cmd] send photo failed: {e}")
    await update.message.reply_text(text)


def _cnit_status_text(rec):
    return "Pending Claim" if rec.get("cnit_claim_active") else "Tidak ada claim aktif"


def _push_cnit_claim_history(rec, amount: int, status: str, note: str = ""):
    history = rec.setdefault("cnit_claim_history", [])
    history.insert(0, {
        "amount": int(amount or 0),
        "status": status,
        "note": note or "-",
        "at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    del history[10:]


def _build_claim_history_lines(rec):
    status_map = {
        "pending": "Pending",
        "paid": "ACC",
        "confirmed": "ACC",
        "approved": "ACC",
        "rejected": "Reject",
    }
    lines = []
    for item in rec.get("cnit_claim_history", [])[:10]:
        status_key = str(item.get("status", "-")).lower()
        status_label = status_map.get(status_key, item.get("status", "-"))
        note = item.get("note") or "-"
        lines.append(
            f"• {item.get('at', '-')} | {int(item.get('amount', 0) or 0)} CNIT | {status_label} | {note}"
        )
    return lines or ["• Belum ada riwayat claim."]


def _apply_staff_shift_rewards(rec, role_key: str):
    role_key = (role_key or "").strip().lower()

    rec["staff_shift_total"] = int(rec.get("staff_shift_total", 0) or 0) + 1

    month_key = _now().strftime("%Y-%m")
    monthly = rec.setdefault("staff_shift_monthly", {})

    current_month = monthly.setdefault(month_key, {"count": 0})

    shift_count = int(current_month.get("count", 0)) + 1
    current_month["count"] = shift_count

    bonus_cnit = 0

    # Angel tidak masuk bonus shift; Angel mendapat CNIT hanya dari rent Angel.
    shift_cnit_roles = ("dj", "bartender", "strip_dancer", "server", "chef", "performer")
    if role_key in shift_cnit_roles:
        if shift_count == 8:
            bonus_cnit = 10000
            rec["cnit_pending"] = int(rec.get("cnit_pending", 0) or 0) + bonus_cnit

    return bonus_cnit, shift_count, month_key


# =========================================================
# CNIT FEATURES
# =========================================================
async def set_nitro_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return
    if not context.args:
        await update.message.reply_text("Format: /setnitroid <id>")
        return
    nitro_id = " ".join(context.args).strip()
    if not nitro_id:
        await update.message.reply_text("NitroSeen ID tidak boleh kosong.")
        return
    rec["nitroseen_id"] = nitro_id
    save_accounts()
    await update.message.reply_text(f"✅ NitroSeen ID kamu disimpan: {nitro_id}")


async def my_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    viewer = update.effective_user
    target_rec = None
    target_uid = None

    if _can_manage_staff(viewer) and context.args and str(context.args[0]).isdigit():
        target_uid, target_rec = _get_account_by_acc_no(str(int(context.args[0])))
        if not target_rec:
            await update.message.reply_text("Account target tidak ditemukan.")
            return
    else:
        target_rec = _get_existing_account(viewer.id)
        target_uid = viewer.id

    if not target_rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return

    last_paid = None
    for item in target_rec.get("cnit_claim_history", []):
        if str(item.get("status", "")).lower() in ("paid", "confirmed", "approved"):
            last_paid = item
            break

    role_name = str(target_rec.get("staff_role") or target_rec.get("account_type") or "-")
    lines = [
        "𖠷 ╱ STAFF LOG",
        "",
        f"Account Number : {target_rec.get('acc_no', '-')}",
        f"Role : {role_name}",
        f"Balance CNIT : {int(target_rec.get('cnit_pending', 0) or 0)}",
        f"NitroSeen ID : {target_rec.get('nitroseen_id') or '-'}",
        f"Claim Status : {_cnit_status_text(target_rec)}",
    ]
    if role_name.lower() != "angel":
        lines.insert(6, f"Total Shift : {int(target_rec.get('staff_shift_total', 0) or 0)}")
    if last_paid:
        lines.append(f"Claim terakhir ACC : {last_paid.get('at', '-')} | {int(last_paid.get('amount', 0) or 0)} CNIT")
    else:
        lines.append("Claim terakhir ACC : Belum ada")

    if _can_manage_staff(viewer) and str(target_uid) != str(viewer.id):
        lines.extend(["", "History Claim:"])
        lines.extend(_build_claim_history_lines(target_rec))

    await update.message.reply_text("\n".join(lines))

# CNIT Claim Flow:
def _cnit_claim_action_keyboard(acc_no: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"cnitclaim:confirm:{acc_no}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"cnitclaim:reject:{acc_no}"),
        ]
    ])


def _can_manage_cnit(user) -> bool:
    return _can_manage_staff(user) or _is_owner(user)


def _build_cnit_claim_admin_text(rec, amount: int):
    username = rec.get("username") or "-"
    rupiah = _cnit_to_rupiah(int(amount or 0))
    shares = _split_rupiah_to_currathors(rupiah)
    if shares:
        share_lines = [f"› {v.get('label')} : {_format_rupiah(v.get('amount', 0))}" for v in shares.values()]
        share_text = "\n".join(share_lines)
    else:
        share_text = "› Belum ada Currathor terdaftar."
    return (
        "💠 CNIT Claim Request\n\n"
        f"Username : @{username if username != '-' else 'unknown'}\n"
        f"Account Number : {rec.get('acc_no', '-')}\n"
        f"Role : {rec.get('staff_role') or rec.get('account_type') or '-'}\n"
        f"NitroSeen ID : {rec.get('nitroseen_id') or '-'}\n"
        f"Jumlah Claim : {int(amount or 0)} CNIT\n"
        f"Nominal Rupiah : {_format_rupiah(rupiah)}\n"
        f"Balance Saat Ini : {int(rec.get('cnit_pending', 0) or 0)} CNIT\n\n"
        "Pembagian bayar Currathor jika di-confirm:\n"
        f"{share_text}\n\n"
        "Gunakan /confirmcnit <acc_no> atau reply pesan ini dengan /confirmcnit\n"
        "Gunakan /rejectcnit <acc_no> atau reply pesan ini dengan /rejectcnit"
    )


async def claim_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec:
        await update.message.reply_text("Belum ada jejak account atas namamu di tatanan ini.")
        return
    balance = int(rec.get("cnit_pending", 0) or 0)
    if balance <= 0:
        await update.message.reply_text("Balance CNIT kamu masih 0.")
        return
    if not rec.get("nitroseen_id"):
        await update.message.reply_text("Set NitroSeen ID dulu dengan /setnitroid <id>.")
        return
    if rec.get("cnit_claim_active"):
        await update.message.reply_text("Claim sebelumnya masih aktif. Tunggu sampai admin menyelesaikannya.")
        return
    if not context.args:
        await update.message.reply_text(f"Format: /claimcnit <jumlah>\nBalance CNIT kamu saat ini: {balance}")
        return
    raw = str(context.args[0]).replace('.', '').replace(',', '').strip()
    if not raw.isdigit():
        await update.message.reply_text("Jumlah claim harus berupa angka.")
        return
    amount = int(raw)
    if amount <= 0:
        await update.message.reply_text("Jumlah claim harus lebih dari 0.")
        return
    if amount > balance:
        await update.message.reply_text(f"Jumlah claim melebihi balance CNIT kamu. Balance saat ini: {balance}")
        return
    try:
        sent = await context.bot.send_message(chat_id=FORWARD_PUBLIC_CHAT_ID, text=_build_cnit_claim_admin_text(rec, amount), reply_markup=_cnit_claim_action_keyboard(str(rec.get("acc_no"))))
    except Exception as e:
        print(f"[claim_cnit_cmd] send admin failed: {e}")
        await update.message.reply_text("Gagal mengirim request claim ke admin.")
        return
    acc_no = str(rec.get("acc_no"))
    claim = {
        "acc_no": acc_no,
        "uid": int(update.effective_user.id),
        "amount": amount,
        "nitroseen_id": rec.get("nitroseen_id"),
        "admin_chat_id": FORWARD_PUBLIC_CHAT_ID,
        "admin_message_id": sent.message_id,
        "status": "pending",
        "requested_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    CNIT_CLAIMS[acc_no] = claim
    save_cnit_claims()
    rec["cnit_claim_active"] = True
    rec["cnit_claim_requested_at"] = claim["requested_at"]
    _push_cnit_claim_history(rec, amount, "pending", "Menunggu payout manual admin")
    save_accounts()
    await update.message.reply_text("✅ Claim CNIT kamu sudah dikirim ke admin dan sedang menunggu payout.")


def _resolve_cnit_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc_no = None
    if context.args and str(context.args[0]).isdigit():
        acc_no = str(int(context.args[0]))
    elif update.effective_message and update.effective_message.reply_to_message:
        reply_id = update.effective_message.reply_to_message.message_id
        for key, claim in CNIT_CLAIMS.items():
            if int(claim.get("admin_message_id", 0) or 0) == int(reply_id):
                acc_no = str(key)
                break
    if not acc_no:
        return None, None, "Format: /confirmcnit <acc_no> atau reply ke pesan claim."
    claim = CNIT_CLAIMS.get(str(acc_no))
    if not claim:
        return acc_no, None, "Claim CNIT tidak ditemukan atau sudah selesai."
    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        return acc_no, claim, "Account target tidak ditemukan."
    return acc_no, claim, None


def _finalize_cnit_claim_record(rec, claim: dict, status: str, note: str):
    amount = int(claim.get("amount", 0) or 0)
    if status == "confirmed":
        current_balance = int(rec.get("cnit_pending", 0) or 0)
        rec["cnit_pending"] = max(0, current_balance - amount)
        history_status = "paid"
    else:
        history_status = "rejected"
    rec["cnit_claim_active"] = False
    rec["cnit_claim_requested_at"] = None
    _push_cnit_claim_history(rec, amount, history_status, note)
    claim["status"] = status
    claim["resolved_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
    save_accounts()
    save_cnit_claims()
    CNIT_CLAIMS.pop(str(claim.get("acc_no")), None)
    save_cnit_claims()
    return amount


async def _confirm_cnit_claim_by_acc_no(context, actor_user, acc_no: str):
    if not _is_admin(actor_user):
        return False, "Hanya admin atau owner."
    claim = CNIT_CLAIMS.get(str(acc_no))
    if not claim:
        return False, "Claim CNIT tidak ditemukan atau sudah selesai."
    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        return False, "Account target tidak ditemukan."
    amount = _finalize_cnit_claim_record(rec, claim, "confirmed", "Payout manual dikonfirmasi admin")
    book_entry = _record_cnit_claim_book_entry(claim, rec, actor_user)
    rupiah = int(book_entry.get("rupiah", 0) or 0)
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "✅ CNIT Payout Selesai\n\n"
                f"Jumlah CNIT : {int(claim.get('amount', amount) or 0)}\n"
                f"Nominal Rupiah : {_format_rupiah(rupiah)}\n"
                f"NitroSeen ID : {rec.get('nitroseen_id') or '-'}\n"
                f"Tanggal ACC : {claim.get('resolved_at') or '-'}\n\n"
                "CNIT kamu sudah dibayarkan oleh admin."
            ),
        )
    except Exception as e:
        print(f"[_confirm_cnit_claim_by_acc_no] DM failed: {e}")
    share_lines = []
    for share in (book_entry.get("shares") or {}).values():
        share_lines.append(f"{share.get('label')}: {_format_rupiah(share.get('amount', 0))}")
    share_text = " | ".join(share_lines) if share_lines else "belum ada Currathor terdaftar"
    return True, f"✅ CNIT payout account {acc_no} dikonfirmasi. Nominal {_format_rupiah(rupiah)}. Dibagi: {share_text}"


async def _reject_cnit_claim_by_acc_no(context, actor_user, acc_no: str):
    if not _is_admin(actor_user):
        return False, "Hanya admin atau owner."
    claim = CNIT_CLAIMS.get(str(acc_no))
    if not claim:
        return False, "Claim CNIT tidak ditemukan atau sudah selesai."
    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        return False, "Account target tidak ditemukan."
    _finalize_cnit_claim_record(rec, claim, "rejected", "Claim ditolak admin")
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "❌ CNIT Claim Ditolak\n\n"
                f"Jumlah claim : {int(claim.get('amount', 0) or 0)}\n"
                f"Tanggal Update : {claim.get('resolved_at') or '-'}\n"
                "Balance CNIT kamu tetap aman. Silakan hubungi admin bila perlu."
            ),
        )
    except Exception as e:
        print(f"[_reject_cnit_claim_by_acc_no] DM failed: {e}")
    return True, f"❌ Claim CNIT untuk account {acc_no} ditolak."


async def confirm_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _is_admin(update.effective_user):
        await update.message.reply_text("Hanya admin atau owner.")
        return
    acc_no, claim, err = _resolve_cnit_claim(update, context)
    if err:
        await update.message.reply_text(err)
        return
    ok, msg = await _confirm_cnit_claim_by_acc_no(context, update.effective_user, str(acc_no))
    await update.message.reply_text(msg)


async def reject_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _is_admin(update.effective_user):
        await update.message.reply_text("Hanya admin atau owner.")
        return
    acc_no, claim, err = _resolve_cnit_claim(update, context)
    if err:
        await update.message.reply_text(err)
        return
    ok, msg = await _reject_cnit_claim_by_acc_no(context, update.effective_user, str(acc_no))
    await update.message.reply_text(msg)


async def cnit_claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    if not _is_admin(query.from_user):
        await query.answer("Hanya admin atau owner.", show_alert=True)
        return
    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return
    _, action, acc_no = parts
    if action == "confirm":
        ok, msg = await _confirm_cnit_claim_by_acc_no(context, query.from_user, str(acc_no))
    elif action == "reject":
        ok, msg = await _reject_cnit_claim_by_acc_no(context, query.from_user, str(acc_no))
    else:
        return
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    try:
        await query.answer(msg, show_alert=True)
    except Exception:
        pass
    try:
        await context.bot.send_message(chat_id=query.message.chat_id, text=msg)
    except Exception:
        pass


#ADD CNIT MANUALLY BY STAFF
async def add_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_cnit(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Format: /addcnit <acc_no> <jumlah>")
        return
    acc_no, amount_text = context.args
    raw_amount = str(amount_text).replace('.', '').replace(',', '').strip()
    if not acc_no.isdigit() or not raw_amount.isdigit():
        await update.message.reply_text("Format: /addcnit <acc_no> <jumlah>")
        return
    amount = int(raw_amount)
    if amount <= 0:
        await update.message.reply_text("Jumlah CNIT harus lebih dari 0.")
        return
    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        await update.message.reply_text("Account tidak ditemukan.")
        return
    rec["cnit_pending"] = int(rec.get("cnit_pending", 0) or 0) + amount
    save_accounts()
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "💠 CNIT Bertambah\n\n"
                f"Jumlah : {amount} CNIT\n"
                f"Balance CNIT : {int(rec.get('cnit_pending', 0) or 0)} CNIT\n"
                "Sumber : Penambahan manual staff"
            ),
        )
    except Exception as e:
        print(f"[add_cnit_cmd] notify failed uid={uid}: {e}")
    await update.message.reply_text(
        f"✅ CNIT account {acc_no} bertambah {amount}.\nBalance CNIT sekarang: {int(rec.get('cnit_pending', 0) or 0)}"
    )

#DEL CNIT MANUALLY BY STAFF
async def del_cnit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_cnit(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Format: /dellcnit <acc_no> <jumlah>")
        return
    acc_no, amount_text = context.args
    raw_amount = str(amount_text).replace('.', '').replace(',', '').strip()
    if not acc_no.isdigit() or not raw_amount.isdigit():
        await update.message.reply_text("Format: /dellcnit <acc_no> <jumlah>")
        return
    amount = int(raw_amount)
    if amount <= 0:
        await update.message.reply_text("Jumlah CNIT harus lebih dari 0.")
        return
    uid, rec = _get_account_by_acc_no(acc_no)
    if not rec:
        await update.message.reply_text("Account tidak ditemukan.")
        return
    current = int(rec.get("cnit_pending", 0) or 0)
    if amount > current:
        await update.message.reply_text(f"CNIT tidak cukup. Balance CNIT sekarang: {current}")
        return
    rec["cnit_pending"] = current - amount
    save_accounts()
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "💠 CNIT Berkurang\n\n"
                f"Jumlah : {amount} CNIT\n"
                f"Balance CNIT : {int(rec.get('cnit_pending', 0) or 0)} CNIT\n"
                "Sumber : Pengurangan manual staff"
            ),
        )
    except Exception as e:
        print(f"[del_cnit_cmd] notify failed uid={uid}: {e}")
    await update.message.reply_text(
        f"✅ CNIT account {acc_no} berkurang {amount}.\nBalance CNIT sekarang: {int(rec.get('cnit_pending', 0) or 0)}"
    )

# =========================================================
# ANGEL BOOKING FEATURES
# =========================================================
def _angel_booking_guest_label(uid: int):
    rec = _get_existing_account(int(uid))
    if not rec:
        return f"UID {uid}"
    username = rec.get("username")
    if username and username != "-":
        return f"@{username}"
    return rec.get("name") or f"Account {rec.get('acc_no', '-')}"


def _is_valid_booking_date(date_text: str):
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d")
    except Exception:
        return False, None
    return True, dt


ANGEL_BLOCKING_BOOKING_STATUSES = {"waiting_payment", "pending_admin", "confirmed", "link_sent"}


def _angel_has_booking(profile: dict, booking_date: str, *, exclude_bill_id=None, exclude_resort_booking_id=None):
    for booking in profile.get("bookings", []):
        if booking.get("date") != booking_date:
            continue
        if exclude_bill_id and str(booking.get("bill_id") or "") == str(exclude_bill_id):
            continue
        if exclude_resort_booking_id and str(booking.get("resort_booking_id") or "") == str(exclude_resort_booking_id):
            continue
        if booking.get("status") in ANGEL_BLOCKING_BOOKING_STATUSES:
            return True
    return False


def _angel_set_bill_booking_status(profile: dict, bill_id: str, status: str):
    changed = False
    for booking in profile.get("bookings", []):
        if str(booking.get("bill_id") or "") == str(bill_id):
            booking["status"] = status
            changed = True
    return changed


def _angel_lock_payment_booking(profile: dict, *, date_text: str, guest_uid: int, guest_rec: dict, bill_id: str):
    if not date_text:
        return False
    existing = next((b for b in profile.get("bookings", []) if b.get("date") == date_text and str(b.get("bill_id") or "") == str(bill_id)), None)
    payload = {
        "date": date_text,
        "guest_uid": int(guest_uid),
        "guest_acc_no": (guest_rec or {}).get("acc_no"),
        "guest_name": (guest_rec or {}).get("name") or (guest_rec or {}).get("username") or f"Account {(guest_rec or {}).get('acc_no', '-')}",
        "status": "waiting_payment",
        "bill_id": bill_id,
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if existing:
        existing.update(payload)
    else:
        profile.setdefault("bookings", []).append(payload)
    return True


def _angel_is_off_date(profile: dict, booking_date: str) -> bool:
    return booking_date in set(profile.get("off_dates", []) or [])


def _angel_calendar_month_shift(year: int, month: int, delta: int):
    month = int(month) + int(delta)
    year = int(year)
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return year, month


def _angel_range_dates(start_date: str, end_date: str):
    start = _date_only(start_date)
    end = _date_only(end_date)
    if not start or not end or end <= start:
        return []
    out = []
    cur = start
    while cur < end:
        out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out


def _angel_range_unavailable(profile: dict, start_date: str, end_date: str, *, exclude_bill_id=None, exclude_resort_booking_id=None):
    unavailable = []
    for date_text in _angel_range_dates(start_date, end_date):
        if _angel_is_off_date(profile, date_text) or _angel_has_booking(profile, date_text, exclude_bill_id=exclude_bill_id, exclude_resort_booking_id=exclude_resort_booking_id):
            unavailable.append(date_text)
    return unavailable


def _angel_booking_range_label(start_date: str, end_date: str) -> str:
    days = _resort_stay_nights(start_date, end_date)
    return f"{start_date} - {end_date} | ({days} hari)"


def _angel_booking_total(flow: dict) -> int:
    return int(flow.get("price", 0) or 0) * int(flow.get("nights", 0) or 0)


def _angel_calendar_text(flow: dict, year: int, month: int) -> str:
    title = datetime(year, month, 1).strftime("%B %Y")
    selected_date = flow.get("booking_date")
    total_text = _normalize_price_text(flow.get("price", 0))

    return (
        "🗓️ Pilih tanggal booking Angel\n\n"
        f"Angel : {flow.get('angel_name', '-')}\n"
        f"Price : {total_text} ✦𝕷\n"
        f"Month : {title}\n"
        f"Tanggal : {selected_date or '-'}\n"
        f"Total : {total_text} ✦𝕷\n\n"
        "Pilih satu tanggal yang tersedia.\n"
        "Tanggal bertanda ❌ sudah tidak tersedia.\n"
        "Booking Angel langsung berhasil setelah payment sukses, tanpa menunggu ACC admin."
    )


def _angel_calendar_keyboard(flow: dict, year: int, month: int):
    import calendar

    requester_uid = int(flow.get("requester_uid", 0) or 0)
    cal = calendar.Calendar(firstweekday=0)
    today = _now().strftime("%Y-%m-%d")
    rows = [[
        InlineKeyboardButton("Mo", callback_data="angelcal:noop"),
        InlineKeyboardButton("Tu", callback_data="angelcal:noop"),
        InlineKeyboardButton("We", callback_data="angelcal:noop"),
        InlineKeyboardButton("Th", callback_data="angelcal:noop"),
        InlineKeyboardButton("Fr", callback_data="angelcal:noop"),
        InlineKeyboardButton("Sa", callback_data="angelcal:noop"),
        InlineKeyboardButton("Su", callback_data="angelcal:noop"),
    ]]

    angel_uid = int(flow.get("angel_uid", 0) or 0)
    profile = _ensure_angel_profile(angel_uid)
    selected_date = flow.get("booking_date")

    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="angelcal:noop"))
                continue

            booking_date = f"{year:04d}-{month:02d}-{day:02d}"
            if (
                booking_date < today
                or _angel_has_booking(profile, booking_date)
                or _angel_is_off_date(profile, booking_date)
            ):
                row.append(InlineKeyboardButton(f"❌{day}", callback_data="angelcal:noop"))
                continue

            label = f"✅{day}" if selected_date == booking_date else str(day)
            row.append(InlineKeyboardButton(label, callback_data=f"angelcal:pick:{requester_uid}:{booking_date}"))
        rows.append(row)

    prev_y, prev_m = _angel_calendar_month_shift(year, month, -1)
    next_y, next_m = _angel_calendar_month_shift(year, month, 1)
    rows.append([
        InlineKeyboardButton("◀️", callback_data=f"angelcal:nav:{requester_uid}:{prev_y}:{prev_m}"),
        InlineKeyboardButton("Reset", callback_data=f"angelcal:resetdate:{requester_uid}"),
        InlineKeyboardButton("▶️", callback_data=f"angelcal:nav:{requester_uid}:{next_y}:{next_m}"),
    ])
    if selected_date:
        rows.append([InlineKeyboardButton("✅ Lanjut Payment", callback_data=f"angelcal:checkout:{requester_uid}")])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data=f"angelcal:cancel:{requester_uid}")])
    return InlineKeyboardMarkup(rows)


def _build_angel_detail_text(rec, profile):
    popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
    availability = "Open by schedule"
    confirmed_count = len([b for b in profile.get("bookings", []) if b.get("status") == "confirmed"])
    return (
        f"𖠷 ╱ LETHÉA: ANGEL\n\n"
        f"Nama : {_angel_display_name(rec)}\n"
        f"Price : {_normalize_price_text(price)} ✦𝕷\n"
        f"Popularity : {popularity}\n"
        f"Availability : {availability}\n"
        f"Confirmed Booking : {confirmed_count}\n\n"
        f"{profile.get('short_desc') or '-'}"
    )


async def angel_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or (rec.get("staff_role") or "").lower() != "angel":
        await update.message.reply_text("Command ini hanya untuk staff Angel.")
        return
    profile = _ensure_angel_profile(update.effective_user.id)
    profile["is_available"] = True
    save_angel_data()
    await update.message.reply_text("Angel sekarang memakai sistem schedule. Gunakan /angeloff untuk menandai tanggal off.")


async def angel_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or (rec.get("staff_role") or "").lower() != "angel":
        await update.message.reply_text("Command ini hanya untuk staff Angel.")
        return
    now = _now()
    context.user_data["angel_off_flow"] = {
        "angel_uid": int(update.effective_user.id),
        "year": now.year,
        "month": now.month,
    }
    sent = await update.message.reply_text(
        _angel_off_calendar_text(context.user_data["angel_off_flow"]),
        reply_markup=_angel_off_calendar_keyboard(context.user_data["angel_off_flow"]),
    )
    context.user_data["angel_off_flow"]["chat_id"] = sent.chat_id
    context.user_data["angel_off_flow"]["message_id"] = sent.message_id


async def my_angel_book_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    viewer_rec = _get_existing_account(update.effective_user.id)
    targets = []
    if viewer_rec and (viewer_rec.get("staff_role") or "").lower() == "angel":
        targets = [(update.effective_user.id, viewer_rec)]
    elif _can_manage_staff(update.effective_user):
        if context.args and str(context.args[0]).isdigit():
            uid, rec = _get_account_by_acc_no(context.args[0])
            if rec and (rec.get("staff_role") or "").lower() == "angel":
                targets = [(int(uid), rec)]
        if not targets:
            targets = _angel_staff_records()
    else:
        await update.message.reply_text("Command ini hanya untuk Angel, Currathor, atau Owner.")
        return
    if not targets:
        await update.message.reply_text("Data booking Angel tidak ditemukan.")
        return
    chunks = []
    for uid, rec in targets:
        profile = _ensure_angel_profile(int(uid))
        lines = [f"{_angel_display_name(rec)} | schedule active"]
        off_dates = sorted(profile.get("off_dates", []))
        if off_dates:
            lines.append("Off Dates:")
            for d in off_dates:
                lines.append(f"› {d} | off")
        bookings = sorted(profile.get("bookings", []), key=lambda x: x.get("date", ""))
        if bookings:
            lines.append("Bookings:")
            for book in bookings:
                guest_label = _angel_booking_guest_label(int(book.get("guest_uid", 0) or 0))
                lines.append(f"› {book.get('date')} | {guest_label} | {book.get('status', '-')}")
        if not off_dates and not bookings:
            lines.append("› Belum ada data off date atau booking.")
        chunks.append("\n".join(lines))
    await update.message.reply_text("\n\n".join(chunks))

# =========================================================
# ANGEL RENTING FLOW
# =========================================================
async def rent_angel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not _can_rent_angel(update.effective_user, rec):
        await update.message.reply_text("Fitur ini hanya untuk Owner, Currathor, atau member VIP aktif.")
        return
    angels = [(uid, angel_rec) for uid, angel_rec in _angel_staff_records()]
    if not angels:
        await update.message.reply_text("Belum ada Angel yang sedang available.")
        return
    sent_any = False
    for uid, angel_rec in angels:
        profile = _ensure_angel_profile(uid)
        if not profile.get("image_file_id"):
            continue
        try:
            await update.effective_message.reply_photo(
                photo=profile.get("image_file_id"),
                caption=_angel_display_name(angel_rec),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Detail", callback_data=f"angelview:detail:{uid}")]]),
            )
            sent_any = True
        except Exception as e:
            print(f"[rent_angel_cmd] send photo error: {e}")
    if not sent_any:
        await update.message.reply_text("Belum ada rupa Angel yang lengkap untuk kutampilkan. Minimal image harus sudah diinput.")


async def angel_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    action = parts[1]
    uid = int(parts[2])
    rec = _get_existing_account(uid)
    profile = _ensure_angel_profile(uid)
    if not rec or (rec.get("staff_role") or "").lower() != "angel":
        await query.answer("Angel tidak ditemukan.", show_alert=True)
        return
    if action == "detail":
        await query.message.reply_text(
            _build_angel_detail_text(rec, profile),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💳 Rent", callback_data=f"angelview:rent:{uid}"),
                InlineKeyboardButton("❌ Cancel", callback_data="angelview:close:0"),
            ]])
        )
        return
    if action == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    if action == "rent":
        user_rec = _get_existing_account(query.from_user.id)
        if not _can_rent_angel(query.from_user, user_rec):
            await query.answer("Tidak punya akses untuk rent Angel.", show_alert=True)
            return
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        now = _now()
        context.user_data["angel_booking_flow"] = {
            "requester_uid": int(query.from_user.id),
            "angel_uid": uid,
            "angel_name": _angel_display_name(rec),
            "price": int(price),
            "popularity": popularity,
            "calendar_year": now.year,
            "calendar_month": now.month,
        }
        flow = context.user_data["angel_booking_flow"]
        sent = await query.message.reply_text(
            _angel_calendar_text(flow, now.year, now.month),
            reply_markup=_angel_calendar_keyboard(flow, now.year, now.month),
        )
        flow["calendar_chat_id"] = sent.chat_id
        flow["calendar_message_id"] = sent.message_id
        await query.answer("Pilih tanggal lewat kalender.", show_alert=True)


async def angel_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return

    parts = (query.data or "").split(":")
    if len(parts) < 2:
        await query.answer()
        return

    action = parts[1]
    if action == "noop":
        await query.answer()
        return

    flow = context.user_data.get("angel_booking_flow")
    if not flow:
        await query.answer("Sesi booking tidak ditemukan atau sudah berakhir.", show_alert=True)
        return

    owner_uid = int(flow.get("requester_uid", 0) or 0)
    if owner_uid and int(query.from_user.id) != owner_uid:
        await query.answer("Panel kalender ini bukan milikmu.", show_alert=True)
        return

    if action == "cancel":
        context.user_data.pop("angel_booking_flow", None)
        try:
            await query.edit_message_text("Booking Angel dibatalkan.")
        except Exception:
            pass
        await query.answer("Booking dibatalkan.")
        return

    if action in ("resetdate", "resetdates"):
        flow["booking_date"] = None
        flow.pop("start_date", None)
        flow.pop("end_date", None)
        flow.pop("nights", None)
        year = int(flow.get("calendar_year") or _now().year)
        month = int(flow.get("calendar_month") or _now().month)
        await query.edit_message_text(
            _angel_calendar_text(flow, year, month),
            reply_markup=_angel_calendar_keyboard(flow, year, month),
        )
        await query.answer("Tanggal direset.")
        return

    if action == "nav":
        if len(parts) < 5:
            await query.answer()
            return
        try:
            year = int(parts[3])
            month = int(parts[4])
        except Exception:
            await query.answer("Data kalender tidak valid.", show_alert=True)
            return

        flow["calendar_year"] = year
        flow["calendar_month"] = month
        await query.edit_message_text(
            _angel_calendar_text(flow, year, month),
            reply_markup=_angel_calendar_keyboard(flow, year, month),
        )
        await query.answer()
        return

    if action == "pick":
        if len(parts) < 4:
            await query.answer()
            return

        date_text = parts[3]
        valid, dt = _is_valid_booking_date(date_text)
        if not valid:
            await query.answer("Tanggal tidak valid.", show_alert=True)
            return

        booking_date = dt.strftime("%Y-%m-%d")
        if booking_date < _now().strftime("%Y-%m-%d"):
            await query.answer("Tanggal booking tidak boleh di masa lalu.", show_alert=True)
            return

        angel_uid = int(flow.get("angel_uid", 0) or 0)
        profile = _ensure_angel_profile(angel_uid)
        if _angel_is_off_date(profile, booking_date) or _angel_has_booking(profile, booking_date):
            await query.answer("Tanggal itu tidak tersedia. Pilih tanggal lain.", show_alert=True)
            return

        flow["booking_date"] = booking_date
        flow.pop("start_date", None)
        flow.pop("end_date", None)
        flow.pop("nights", None)
        year = int(flow.get("calendar_year") or dt.year)
        month = int(flow.get("calendar_month") or dt.month)
        await query.edit_message_text(
            _angel_calendar_text(flow, year, month),
            reply_markup=_angel_calendar_keyboard(flow, year, month),
        )
        await query.answer("Tanggal booking dipilih.")
        return

    if action == "checkout":
        booking_date = flow.get("booking_date")
        if not booking_date:
            await query.answer("Pilih tanggal dulu.", show_alert=True)
            return

        angel_uid = int(flow.get("angel_uid", 0) or 0)
        profile = _ensure_angel_profile(angel_uid)
        if _angel_is_off_date(profile, booking_date) or _angel_has_booking(profile, booking_date):
            await query.answer("Tanggal itu tidak tersedia. Pilih tanggal lain.", show_alert=True)
            return

        total = int(flow.get("price", 0) or 0)
        try:
            await query.edit_message_text(
                f"Tanggal dipilih : {booking_date}\n"
                f"Angel : {flow.get('angel_name', '-')}\n"
                f"Total : {_normalize_price_text(total)} ✦𝕷\n\n"
                "⏳ Sedang dalam proses pembayaran rent Angel..."
            )
        except Exception:
            pass

        status = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ Sedang dalam proses pembayaran rent Angel...",
        )
        ok, bill_id = await _create_payment_bill(
            context,
            requester_user=query.from_user,
            target_uid=int(query.from_user.id),
            amount=int(total),
            status_chat_id=status.chat_id,
            status_message_id=status.message_id,
            note=f"Rent Angel: {flow['angel_name']} ({flow['popularity']}) | {booking_date}",
            angel_uid=angel_uid,
            booking_date=booking_date,
        )
        if ok:
            requester_rec = _get_existing_account(query.from_user.id)
            profile = _ensure_angel_profile(angel_uid)
            _angel_lock_payment_booking(profile, date_text=booking_date, guest_uid=query.from_user.id, guest_rec=requester_rec, bill_id=bill_id)
            save_angel_data()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"Bill sudah dikirim ke DM kamu untuk booking tanggal {booking_date}.",
            )
        context.user_data.pop("angel_booking_flow", None)
        await query.answer()
        return

    await query.answer()



async def angel_booking_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("angel_booking_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    text = (update.effective_message.text or "").strip()
    valid, dt = _is_valid_booking_date(text)
    if not valid:
        await update.message.reply_text("Format tanggal harus YYYY-MM-DD.")
        return
    booking_date = dt.strftime("%Y-%m-%d")
    if booking_date < _now().strftime("%Y-%m-%d"):
        await update.message.reply_text("Tanggal booking tidak boleh di masa lalu.")
        return
    angel_uid = int(flow["angel_uid"])
    profile = _ensure_angel_profile(angel_uid)
    if not profile.get("is_available"):
        await update.message.reply_text("Angel sedang OFF / tidak available.")
        context.user_data.pop("angel_booking_flow", None)
        return
    if _angel_has_booking(profile, booking_date):
        await update.message.reply_text("Tanggal itu sudah full booked. Pilih tanggal lain.")
        return
    status = await update.message.reply_text("⏳ Sedang dalam proses pembayaran rent Angel...")
    ok, bill_id = await _create_payment_bill(
        context,
        requester_user=update.effective_user,
        target_uid=int(update.effective_user.id),
        amount=int(flow["price"]),
        status_chat_id=status.chat_id,
        status_message_id=status.message_id,
        note=f"Rent Angel: {flow['angel_name']} ({flow['popularity']}) | {booking_date}",
        angel_uid=angel_uid,
        booking_date=booking_date,
    )
    if ok:
        requester_rec = _get_existing_account(update.effective_user.id)
        _angel_lock_payment_booking(profile, date_text=booking_date, guest_uid=update.effective_user.id, guest_rec=requester_rec, bill_id=bill_id)
        save_angel_data()
        await update.message.reply_text(f"Bill sudah dikirim ke DM kamu untuk booking tanggal {booking_date}.")
    context.user_data.pop("angel_booking_flow", None)


async def _create_payment_bill(
    context,
    *,
    requester_user,
    target_uid: int,
    amount: int,
    status_chat_id: int,
    status_message_id: int,
    note: str = None,
    angel_uid: int = None,
    booking_date: str = None,
    booking_start: str = None,
    booking_end: str = None,
    booking_nights: int = None,
):
    target_rec = _get_existing_account(target_uid)
    if not target_rec:
        return False, "Account target tidak ditemukan."
    bill_id = _new_bill_id()
    bill = {
        "bill_id": bill_id,
        "requester_uid": requester_user.id if requester_user else None,
        "target_uid": int(target_uid),
        "amount": int(amount),
        "status": "pending",
        "status_chat_id": status_chat_id,
        "status_message_id": status_message_id,
        "note": note or "Tagihan Lethéa",
        "angel_uid": int(angel_uid) if angel_uid else None,
        "booking_date": booking_date,
        "booking_start": booking_start or booking_date,
        "booking_end": booking_end,
        "booking_nights": int(booking_nights or 0),
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "dm_message_id": None,
    }
    PENDING_BILLS[bill_id] = bill
    save_payment_data()
    target_name = target_rec.get("name") or (f"@{target_rec.get('username')}" if target_rec.get("username") and target_rec.get("username") != "-" else f"Account {target_rec.get('acc_no')}")
    try:
        dm = await context.bot.send_message(
            chat_id=int(target_uid),
            text=_build_bill_dm_text(bill),
            reply_markup=_bill_keyboard(bill_id),
        )
        bill["dm_message_id"] = dm.message_id
        save_payment_data()
        try:
            await context.bot.edit_message_text(
                chat_id=status_chat_id,
                message_id=status_message_id,
                text=f"⏳ Payment untuk {target_name} sedang dalam proses pembayaran.",
            )
        except Exception:
            pass
        return True, bill_id
    except Exception as e:
        bill["status"] = "dm_failed"
        save_payment_data()
        try:
            await context.bot.edit_message_text(
                chat_id=status_chat_id,
                message_id=status_message_id,
                text=f"❌ Payment gagal dikirim ke DM {target_name}. Pastikan user sudah /start Oxana.\nError: {e}",
            )
        except Exception:
            pass
        return False, "DM gagal dikirim."


def _bill_angel_cnit_days(bill: dict) -> int:
    try:
        nights = int((bill or {}).get("booking_nights", 0) or 0)
    except Exception:
        nights = 0
    if nights > 0:
        return nights

    start_date = (bill or {}).get("booking_start") or (bill or {}).get("booking_date")
    end_date = (bill or {}).get("booking_end")
    if start_date and end_date:
        days = len(_angel_range_dates(start_date, end_date))
        return max(1, int(days or 0))
    if start_date:
        return 1
    return 0


async def __old_payment_bill_callback_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3:
        return
    _, action, bill_id = parts
    bill = PENDING_BILLS.get(bill_id)
    if not bill:
        await query.answer("Bill tidak ditemukan atau sudah selesai.", show_alert=True)
        return
    if int(bill.get("target_uid", 0)) != int(query.from_user.id):
        await query.answer("Ini bukan bill milikmu.", show_alert=True)
        return
    target_rec = _get_existing_account(query.from_user.id)
    if not target_rec:
        await query.answer("Account kamu tidak ditemukan.", show_alert=True)
        return
    if action == "cancel":
        bill["status"] = "cancelled"
        if bill.get("angel_uid"):
            profile = _ensure_angel_profile(int(bill.get("angel_uid")))
            _angel_set_bill_booking_status(profile, bill_id, "cancelled")
            save_angel_data()
        save_payment_data()
        try:
            await query.edit_message_text("❌ Payment dibatalkan.")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment dibatalkan.")
        except Exception:
            pass
        return
    amount = int(bill.get("amount", 0))
    balance = int(target_rec.get("balance", 0))
    if balance < amount:
        try:
            await query.answer("Saldo kamu tidak cukup.", show_alert=True)
            await query.edit_message_text(f"❌ Payment gagal. Saldo kamu tidak cukup.\nSaldo sekarang: {_normalize_price_text(balance)} ✦𝕷")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment gagal. Saldo target tidak cukup.")
        except Exception:
            pass
        bill["status"] = "insufficient_balance"
        if bill.get("angel_uid"):
            profile = _ensure_angel_profile(int(bill.get("angel_uid")))
            _angel_set_bill_booking_status(profile, bill_id, "insufficient_balance")
            save_angel_data()
        save_payment_data()
        return
    angel_uid = bill.get("angel_uid")
    if angel_uid:
        profile = _ensure_angel_profile(int(angel_uid))
        start_date = bill.get("booking_start") or bill.get("booking_date")
        end_date = bill.get("booking_end")
        if start_date and end_date:
            unavailable = _angel_range_unavailable(profile, start_date, end_date, exclude_bill_id=bill_id)
        elif start_date:
            unavailable = [start_date] if (_angel_is_off_date(profile, start_date) or _angel_has_booking(profile, start_date, exclude_bill_id=bill_id)) else []
        else:
            unavailable = []
        if unavailable:
            bill["status"] = "angel_unavailable"
            _angel_set_bill_booking_status(profile, bill_id, "angel_unavailable")
            save_angel_data()
            save_payment_data()
            try:
                await query.edit_message_text(
                    "❌ Payment dibatalkan. Angel sudah tidak tersedia pada tanggal tersebut. "
                    f"Tanggal bermasalah: {', '.join(unavailable[:3])}"
                )
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(
                    chat_id=bill["status_chat_id"],
                    message_id=bill["status_message_id"],
                    text="❌ Payment gagal. Angel sudah tidak tersedia pada tanggal tersebut.",
                )
            except Exception:
                pass
            return

    target_rec["balance"] = balance - amount
    save_accounts()
    bill["status"] = "paid"
    save_payment_data()
    angel_uid = bill.get("angel_uid")
    if angel_uid:
        angel_uid = int(angel_uid)
        angel_share = int(amount * 70 / 100)
        currathor_share = int(amount) - angel_share
        angel_rec = _get_existing_account(angel_uid)
        angel_name = _angel_display_name(angel_rec) if angel_rec else f"Angel {angel_uid}"
        guest_name = target_rec.get("name") or (target_rec.get("username") and "@" + str(target_rec.get("username"))) or ("Account " + str(target_rec.get("acc_no")))
        await _credit_angel_income(context, angel_uid, angel_share, f"Rent Angel dari {guest_name}")
        if not bill.get("angel_cnit_paid_at"):
            angel_days = _bill_angel_cnit_days(bill)
            angel_cnit_amount = 1000 * angel_days
            if angel_cnit_amount > 0:
                await _grant_angel_rent_cnit(
                    context,
                    angel_uid,
                    f"Rent Angel dari {guest_name} ({angel_days} hari)",
                    angel_cnit_amount,
                )
            bill["angel_cnit_paid_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
            bill["angel_cnit_amount"] = angel_cnit_amount
            bill["angel_cnit_days"] = angel_days
            save_payment_data()
        await _credit_currathors(context, currathor_share, f"Bagi hasil rent Angel {angel_name}")
        profile = _ensure_angel_profile(angel_uid)
        start_date = bill.get("booking_start") or bill.get("booking_date")
        end_date = bill.get("booking_end")
        booking_dates = _angel_range_dates(start_date, end_date) if start_date and end_date else ([start_date] if start_date else [])
        for date_text in booking_dates:
            existing = next((x for x in profile.get("bookings", []) if x.get("date") == date_text and str(x.get("bill_id") or "") == str(bill_id)), None)
            payload = {
                "date": date_text,
                "booking_start": start_date,
                "booking_end": end_date,
                "guest_uid": int(query.from_user.id),
                "guest_acc_no": target_rec.get("acc_no"),
                "guest_name": target_rec.get("name") or target_rec.get("username") or f"Account {target_rec.get('acc_no', '-')}",
                "status": "confirmed",
                "bill_id": bill_id,
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            if existing:
                existing.update(payload)
            else:
                if _angel_has_booking(profile, date_text, exclude_bill_id=bill_id):
                    continue
                profile.setdefault("bookings", []).append(payload)
        profile["total_orders"] = int(profile.get("total_orders", 0)) + 1
        save_angel_data()
        label = _angel_booking_range_label(start_date, end_date) if start_date and end_date else (start_date or "-")
        try:
            await query.edit_message_text(
                "✅ Payment berhasil. Booking Angel langsung terkonfirmasi.\n\n"
                f"Angel : {angel_name}\n"
                f"Tanggal : {label}\n"
                f"Total : {_normalize_price_text(amount)} ✦𝕷"
            )
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(
                chat_id=bill["status_chat_id"],
                message_id=bill["status_message_id"],
                text=(
                    "✅ Payment Rent Angel berhasil. Booking langsung terkonfirmasi.\n"
                    f"Angel : {angel_name}\n"
                    f"Tanggal : {label}\n"
                    f"Total : {_normalize_price_text(amount)} ✦𝕷"
                ),
            )
        except Exception:
            pass
        return
    else:
        await _credit_currathors(
            context,
            int(amount * 50 / 100),
            f"Bagi hasil payment bill dari {target_rec.get('name') or (target_rec.get('username') and '@' + str(target_rec.get('username'))) or ('Account ' + str(target_rec.get('acc_no')))}",
        )
    try:
        await query.edit_message_text(f"✅ Konfirmasi reservasi berhasil. Booking kamu sekarang menunggu ACC admin. Saldo belum dipotong.")
    except Exception:
        pass
    try:
        await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="✅ Payment berhasil.")
    except Exception:
        pass


async def list_angel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    angels = _angel_staff_records()
    if not angels:
        await update.message.reply_text("Belum ada staff Angel.")
        return
    lines = ["Lethéa Angel:\n"]
    for i, (uid, rec) in enumerate(angels, start=1):
        profile = _ensure_angel_profile(uid)
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        availability = "Open by schedule"
        lines.append(f"O{i}. {_angel_display_name(rec)} | {rec.get('acc_no', '-')} | {popularity} | {_normalize_price_text(price)} | {availability}")
    await update.message.reply_text("\n".join(lines))


# =========================================================
# FEATURE: CURATED DINING
# =========================================================

def save_curated_dining_data():
    try:
        with open(CURATED_DINING_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": CURATED_DININGS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_curated_dining_data failed: {e}")


def load_curated_dining_data():
    global CURATED_DININGS
    try:
        p = Path(CURATED_DINING_FILE)
        if not p.exists():
            CURATED_DININGS = []
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        CURATED_DININGS = data.get("items", []) if isinstance(data, dict) else []
        if not isinstance(CURATED_DININGS, list):
            CURATED_DININGS = []
    except Exception as e:
        print(f"[WARN] load_curated_dining_data failed: {e}")
        CURATED_DININGS = []


def _new_curated_id() -> str:
    return f"curated_{int(_now().timestamp() * 1000)}_{len(CURATED_DININGS)+1}"


def _find_curated(curated_id: str):
    for item in CURATED_DININGS:
        if item.get("id") == curated_id:
            return item
    return None


def _curated_status_label(item: dict) -> str:
    status = (item or {}).get("status") or "draft"
    if status == "open":
        return "🟢 Available"
    if status in {"waiting_payment", "pending_admin", "confirmed"}:
        return "🔴 Fully Booked"
    if status == "closed":
        return "⚫ Closed"
    return status.replace("_", " ").title()



def _message_text_with_entities(msg):
    """Ambil teks/caption persis; kalau ada rich formatting Telegram, simpan sebagai HTML."""
    raw = (getattr(msg, "text", None) or getattr(msg, "caption", None) or "").strip()
    entities = list(getattr(msg, "entities", None) or []) + list(getattr(msg, "caption_entities", None) or [])
    if entities:
        html_text = (getattr(msg, "text_html", None) or getattr(msg, "caption_html", None) or raw).strip()
        return raw, html_text, "HTML"
    return raw, raw, None


def _curated_caption_for_send(item: dict):
    text = item.get("caption_html") or item.get("caption") or ""
    parse_mode = item.get("caption_parse_mode") or None
    return text, parse_mode


def _curated_create_keyboard(flow: dict):
    rows = [
        [InlineKeyboardButton("Caption Optional", callback_data="curatedcreate:fill:caption")],
        [InlineKeyboardButton("Foto Optional", callback_data="curatedcreate:fill:photo")],
        [InlineKeyboardButton("Harga Payment", callback_data="curatedcreate:fill:price")],
    ]
    has_content = bool(flow.get("caption") or flow.get("photo_file_id"))
    has_price = flow.get("price") is not None
    if has_content and has_price:
        rows.append([InlineKeyboardButton("✅ Publish", callback_data="curatedcreate:publish")])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="curatedcreate:cancel")])
    return InlineKeyboardMarkup(rows)


def _curated_create_panel_text(flow: dict) -> str:
    waiting = flow.get("waiting_for")
    photo_status = "Sudah ada" if flow.get("photo_file_id") else "-"
    caption_status = "Sudah ada" if flow.get("caption") else "-"
    price_status = f"{_normalize_price_text(flow.get('price'))} ✦𝕷" if flow.get("price") is not None else "-"
    lines = [
        "𖠷 ╱ LETHÉA: CURATED DINING",
        "",
        f"Caption : {caption_status}",
        f"Foto : {photo_status}",
        f"Harga Payment : {price_status}",
        "",
    ]
    if waiting == "caption":
        lines.append("Kirim caption post Curated Dining. Asmoday akan menyalin teksnya persis, termasuk format Telegram yang kamu pakai.")
    elif waiting == "photo":
        lines.append("Kirim foto Curated Dining. Jika foto punya caption, caption itu juga akan disimpan persis.")
    elif waiting == "price":
        lines.append("Kirim harga payment dalam angka. Harga ini wajib dan akan dipotong dari saldo user yang reserve setelah ACC pengurus.")
    elif flow.get("price") is not None and (flow.get("caption") or flow.get("photo_file_id")):
        lines.append("Data sudah siap dipublish. Pilih Publish, atau ubah caption/foto/harga lewat tombol.")
    else:
        lines.append("Isi harga payment dan minimal salah satu: caption atau foto.")
    return "\n".join(lines)


def _curated_display_caption(item: dict) -> str:
    caption, _parse_mode = _curated_caption_for_send(item)
    return caption or ""


def _curated_public_keyboard(item: dict):
    if (item or {}).get("status") != "open":
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("Reserve Now", callback_data=f"curatedreserve:start:{item.get('id')}")]])


async def _refresh_curated_create_message(context, flow: dict, *, final_text: str = None, reply_markup=None):
    chat_id = flow.get("chat_id")
    message_id = flow.get("message_id")
    if not chat_id or not message_id:
        return False
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=final_text if final_text is not None else _curated_create_panel_text(flow),
            reply_markup=reply_markup if final_text is not None else _curated_create_keyboard(flow),
        )
        return True
    except Exception as e:
        print(f"[_refresh_curated_create_message] error: {e}")
        return False


async def open_curated_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor yang bisa membuka Curated Dining.")
        return
    sent = await update.message.reply_text("Mulai input Curated Dining.", reply_markup=_curated_create_keyboard({}))
    context.user_data["curated_create_flow"] = {
        "caption": None,
        "caption_html": None,
        "caption_parse_mode": None,
        "photo_file_id": None,
        "price": None,
        "waiting_for": None,
        "publish_chat_id": update.effective_chat.id,
        "publish_thread_id": getattr(update.effective_message, "message_thread_id", None),
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
    }
    await _refresh_curated_create_message(context, context.user_data["curated_create_flow"])


async def curated_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Owner atau Currathor.", show_alert=True)
        return
    flow = context.user_data.get("curated_create_flow")
    data = query.data or ""
    if data == "curatedcreate:cancel":
        if flow:
            await _refresh_curated_create_message(context, flow, final_text="Pembuatan Curated Dining dibatalkan.", reply_markup=None)
        else:
            await query.edit_message_text("Pembuatan Curated Dining dibatalkan.")
        context.user_data.pop("curated_create_flow", None)
        return
    if not flow:
        await query.edit_message_text("Sesi Curated Dining tidak ditemukan. Gunakan /opencurated lagi.")
        return
    if data.startswith("curatedcreate:fill:"):
        target = data.split(":", 2)[2]
        if target not in {"caption", "photo", "price"}:
            return
        flow["waiting_for"] = target
        flow["chat_id"] = query.message.chat_id
        flow["message_id"] = query.message.message_id
        await _refresh_curated_create_message(context, flow)
        await query.answer("Kirim input di chat ini.", show_alert=True)
        return
    if data == "curatedcreate:publish":
        if flow.get("price") is None:
            await query.answer("Harga payment belum diisi.", show_alert=True)
            return
        if not (flow.get("caption") or flow.get("photo_file_id")):
            await query.answer("Isi caption atau foto terlebih dahulu.", show_alert=True)
            return
        item = {
            "id": _new_curated_id(),
            "caption": flow.get("caption"),
            "caption_html": flow.get("caption_html"),
            "caption_parse_mode": flow.get("caption_parse_mode"),
            "photo_file_id": flow.get("photo_file_id"),
            "price": int(flow.get("price", 0) or 0),
            "status": "open",
            "booking": None,
            "created_by": int(query.from_user.id),
            "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
            "public_chat_id": flow.get("publish_chat_id") or query.message.chat_id,
            "public_thread_id": flow.get("publish_thread_id"),
            "public_message_id": None,
        }
        CURATED_DININGS.append(item)
        save_curated_dining_data()
        caption, parse_mode = _curated_caption_for_send(item)
        try:
            kwargs = {"chat_id": item["public_chat_id"], "reply_markup": _curated_public_keyboard(item)}
            if item.get("public_thread_id"):
                kwargs["message_thread_id"] = item.get("public_thread_id")
            if item.get("photo_file_id"):
                kwargs["photo"] = item.get("photo_file_id")
                if caption:
                    kwargs["caption"] = caption
                    if parse_mode:
                        kwargs["parse_mode"] = parse_mode
                public_msg = await context.bot.send_photo(**kwargs)
            else:
                kwargs["text"] = caption
                if parse_mode:
                    kwargs["parse_mode"] = parse_mode
                public_msg = await context.bot.send_message(**kwargs)
            item["public_message_id"] = public_msg.message_id
            save_curated_dining_data()
        except Exception as e:
            print(f"[curated publish] send failed: {e}")
            await query.answer("Publish gagal. Cek izin bot di chat ini.", show_alert=True)
            return
        await _refresh_curated_create_message(context, flow, final_text="✅ Curated Dining telah dibuka.", reply_markup=None)
        context.user_data.pop("curated_create_flow", None)
        return


async def curated_create_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("curated_create_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    waiting = flow.get("waiting_for")
    if waiting not in {"caption", "price"}:
        return
    msg = update.effective_message
    if waiting == "price":
        amount = _parse_bet_amount(msg.text or "")
        if amount is None:
            await msg.reply_text("Harga harus angka lebih dari 0.")
            raise ApplicationHandlerStop
        flow["price"] = int(amount)
    else:
        raw, html_text, parse_mode = _message_text_with_entities(msg)
        if not raw:
            await msg.reply_text("Caption tidak boleh kosong.")
            raise ApplicationHandlerStop
        flow["caption"] = raw
        flow["caption_html"] = html_text
        flow["caption_parse_mode"] = parse_mode
    flow["waiting_for"] = None
    await _refresh_curated_create_message(context, flow)
    raise ApplicationHandlerStop


async def curated_create_photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("curated_create_flow")
    if not flow or flow.get("waiting_for") != "photo":
        return
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id
    if not file_id:
        await msg.reply_text("Kirim foto atau dokumen gambar untuk Curated Dining.")
        raise ApplicationHandlerStop
    flow["photo_file_id"] = file_id
    raw, html_text, parse_mode = _message_text_with_entities(msg)
    if raw:
        flow["caption"] = raw
        flow["caption_html"] = html_text
        flow["caption_parse_mode"] = parse_mode
    flow["waiting_for"] = None
    await _refresh_curated_create_message(context, flow)
    raise ApplicationHandlerStop


def _curated_booking_form_text(item: dict) -> str:
    price_text = html.escape(_normalize_price_text(item.get("price", 0)))
    return (
        "<b>› 𝖭𝖮𝖳𝖨𝖥𝖨𝖤𝖣! CURATED DINING RESERVATION</b>\n\n"
        f"Harga Persembahan : {price_text} ✦𝕷\n\n"
        "Sila titipkan identitasmu pada lembar sunyi ini; satu meja hanya membuka satu takdir. "
        "Barang siapa lebih dahulu menghaturkan bentuk yang sah, dialah yang sementara memegang pintu perjamuan.\n\n"
        "<i>Perlu diingat, dirimu pun terhitung dalam jumlah hadirin. "
        "Jika engkau membawa tiga nama, maka genaplah menjadi empat jiwa.</i>\n\n"
        "<pre>"
        "nama_pemesan    = \n"
        "jumlah_orang    = 3-4 \n"
        "datang_bersama  = @username \n"
        "catatan         = "
        "</pre>"
    )


def _parse_curated_booking_form(text: str):
    text = (text or "").strip()
    if not text:
        return None, "Form tidak dapat kuhaturkan dalam keadaan hampa."
    def grab(*labels):
        for label in labels:
            label_pattern = re.escape(label).replace(r"\ ", r"[ _\-]+")
            m = re.search(
                rf"(?:^|\n)\s*(?:›\s*)?{label_pattern}\s*(?:[:=])\s*(.*)",
                text,
                flags=re.IGNORECASE,
            )
            if m:
                return (m.group(1) or "").strip()
        return ""
    name = grab("Nama Pemesan", "nama_pemesan", "Nama")
    count_raw = grab("Jumlah Orang", "jumlah_orang", "Jumlah")
    companions = grab("Datang Bersama", "datang_bersama", "Bersama")
    notes = grab("Catatan", "catatan") or "-"
    if not name:
        return None, "Nama Pemesan belum diisi."
    m_count = re.search(r"\d+", count_raw or "")
    if not m_count:
        return None, "Jumlah Orang harus diisi angka 3 atau 4."
    count = int(m_count.group(0))
    if count not in (3, 4):
        return None, "Curated Dining hanya untuk 3-4 orang."
    if not companions:
        return None, "Bagian Datang Bersama belum diisi."
    return {"name": name, "guest_count": count, "companions": companions, "notes": notes}, None


async def curated_reserve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3:
        return
    item = _find_curated(parts[2])
    if not item:
        await query.answer("Curated Dining tidak ditemukan.", show_alert=True)
        return
    if item.get("status") != "open":
        await query.answer("Sorry, this curated dining is already fully booked.", show_alert=True)
        return
    rec = _get_existing_account(query.from_user.id)
    if not _can_use_locked_features(query.from_user, rec):
        await query.answer("Kamu harus punya membership aktif / staff access untuk reservasi.", show_alert=True)
        return
    try:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=_curated_booking_form_text(item),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        context.user_data["curated_booking_flow"] = {"curated_id": item.get("id"), "step": "fill_form"}
        await query.answer("Form reservasi sudah dikirim ke DM Asmoday.", show_alert=True)
    except Exception:
        await query.answer("Asmoday belum bisa DM kamu. Start bot dulu, lalu klik Reserve Now lagi.", show_alert=True)


async def curated_booking_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("curated_booking_flow")
    if not flow or flow.get("step") != "fill_form":
        return
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type != "private":
        return
    item = _find_curated(flow.get("curated_id"))
    if not item:
        context.user_data.pop("curated_booking_flow", None)
        await update.message.reply_text("Curated Dining tidak ditemukan.")
        raise ApplicationHandlerStop
    form, err = _parse_curated_booking_form(update.effective_message.text or "")
    if err:
        await update.message.reply_text(err)
        raise ApplicationHandlerStop
    if item.get("status") != "open":
        context.user_data.pop("curated_booking_flow", None)
        await update.message.reply_text("Sorry, this curated dining is already fully booked.")
        raise ApplicationHandlerStop
    rec = _get_existing_account(update.effective_user.id)
    if not rec:
        await update.message.reply_text("Account kamu tidak ditemukan.")
        raise ApplicationHandlerStop
    booking_id = f"curated_booking_{int(_now().timestamp() * 1000)}_{update.effective_user.id}"
    item["status"] = "waiting_payment"
    item["booking"] = {
        "booking_id": booking_id,
        "guest_uid": int(update.effective_user.id),
        "guest_acc_no": rec.get("acc_no"),
        "guest_username": update.effective_user.username or "-",
        "guest_display": update.effective_user.full_name or update.effective_user.username or f"User {update.effective_user.id}",
        "name": form.get("name"),
        "guest_count": int(form.get("guest_count", 0) or 0),
        "companions": form.get("companions"),
        "notes": form.get("notes"),
        "status": "waiting_payment",
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_curated_dining_data()
    status = await update.message.reply_text("⏳ Slot Curated Dining telah dipegang sementara. Payment sedang dikirim ke DM kamu...")
    ok, result = await _create_payment_bill(
        context,
        requester_user=update.effective_user,
        target_uid=int(update.effective_user.id),
        amount=int(item.get("price", 0) or 0),
        status_chat_id=status.chat_id,
        status_message_id=status.message_id,
        note=f"Curated Dining | {item.get('id')}",
    )
    if ok:
        bill = PENDING_BILLS.get(result)
        if bill is not None:
            bill["curated_booking_id"] = booking_id
            bill["curated_id"] = item.get("id")
            save_payment_data()
        await update.message.reply_text("Bill sudah dikirim. Slot akan kembali available kalau payment dibatalkan atau gagal.")
    else:
        item["status"] = "open"
        item["booking"] = None
        save_curated_dining_data()
        await update.message.reply_text("Payment gagal dibuat. Slot Curated Dining kembali available.")
    context.user_data.pop("curated_booking_flow", None)
    await _curated_refresh_public_message(context, item)
    raise ApplicationHandlerStop


def _curated_admin_recap_text(item: dict) -> str:
    booking = item.get("booking") or {}
    caption_preview = (item.get("caption") or "-").replace("\n", " ")
    if len(caption_preview) > 500:
        caption_preview = caption_preview[:500] + "..."
    return "\n".join([
        "𖠷╱ .. CURATED DINING PENDING", "",
        f"Booking ID : {booking.get('booking_id', '-')}",
        f"Curated ID : {item.get('id', '-')}",
        f"Informasi Pemesan : {booking.get('guest_display', '-')} | Acc {booking.get('guest_acc_no', '-')}",
        f"Nama Pemesan : {booking.get('name', '-')}",
        f"Jumlah Orang : {booking.get('guest_count', '-')}",
        f"Datang Bersama : {booking.get('companions', '-')}",
        f"Catatan : {booking.get('notes', '-')}", "",
        f"Total Payment : {_normalize_price_text(item.get('price', 0))} ✦𝕷",
        f"Currathor Pool 50% : {_normalize_price_text(int(item.get('price', 0) or 0) * 50 // 100)} ✦𝕷", "",
        "Caption Preview:", caption_preview,
    ])


async def _curated_refresh_public_message(context, item: dict):
    chat_id = item.get("public_chat_id")
    message_id = item.get("public_message_id")
    if not chat_id or not message_id:
        return
    caption, parse_mode = _curated_caption_for_send(item)
    try:
        if item.get("photo_file_id"):
            kwargs = {"chat_id": chat_id, "message_id": message_id, "reply_markup": _curated_public_keyboard(item)}
            if caption:
                kwargs["caption"] = caption
                if parse_mode:
                    kwargs["parse_mode"] = parse_mode
                await context.bot.edit_message_caption(**kwargs)
            else:
                await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=_curated_public_keyboard(item))
        else:
            kwargs = {"chat_id": chat_id, "message_id": message_id, "text": caption or "Curated Dining", "reply_markup": _curated_public_keyboard(item)}
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
            await context.bot.edit_message_text(**kwargs)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[_curated_refresh_public_message] error: {e}")


async def list_curated_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not CURATED_DININGS:
        await update.message.reply_text("Belum ada Curated Dining tersimpan.")
        return
    lines = ["Lethéa Curated Dining:", ""]
    for i, item in enumerate(CURATED_DININGS, start=1):
        booking = item.get("booking") or {}
        holder = booking.get("guest_display") or "-"
        caption_preview = (item.get("caption") or "-").replace("\n", " ")
        if len(caption_preview) > 45:
            caption_preview = caption_preview[:45] + "..."
        lines.append(f"{i}. {caption_preview} | Harga: {_normalize_price_text(item.get('price', 0))} | {_curated_status_label(item)} | Holder: {holder} | ID: {item.get('id')}")
    await update.message.reply_text("\n".join(lines))


async def close_curated_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args:
        await update.message.reply_text("Format: /closecurated <id>\nLihat ID dengan /listcurated")
        return
    item = _find_curated(context.args[0])
    if not item:
        await update.message.reply_text("Curated Dining tidak ditemukan.")
        return
    item["status"] = "closed"
    save_curated_dining_data()
    await _curated_refresh_public_message(context, item)
    await update.message.reply_text("Curated Dining ditutup.")


async def del_curated_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    if not context.args:
        await update.message.reply_text("Format: /delcurated <id>\nLihat ID dengan /listcurated")
        return
    curated_id = context.args[0]
    item = _find_curated(curated_id)
    if not item:
        await update.message.reply_text("Curated Dining tidak ditemukan.")
        return
    try:
        if item.get("public_chat_id") and item.get("public_message_id"):
            await context.bot.delete_message(chat_id=item.get("public_chat_id"), message_id=item.get("public_message_id"))
    except Exception as e:
        print(f"[del_curated_cmd] delete public message failed: {e}")
    try:
        CURATED_DININGS.remove(item)
    except ValueError:
        pass
    save_curated_dining_data()
    await update.message.reply_text("Curated Dining dihapus dari list/history.")


def _curated_inline_title(item: dict) -> str:
    raw = (item.get("caption") or item.get("caption_html") or "Curated Dining").strip()
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = raw.replace("\n", " ").strip()
    if not raw:
        raw = "Curated Dining"
    return raw[:55]


def _curated_inline_description(item: dict) -> str:
    status = _curated_status_label(item)
    price = _normalize_price_text(item.get("price", 0))
    return f"{status} · {price} ✦𝕷"


async def curated_inline_query_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jawab inline query cepat, termasuk query kosong, supaya Telegram tidak loading terus."""
    query = update.inline_query
    if not query:
        return

    q = (query.query or "").strip().lower()
    results = []

    candidates = []
    for item in reversed(CURATED_DININGS):
        if (item.get("status") or "") != "open":
            continue
        haystack = " ".join([
            str(item.get("id") or ""),
            str(item.get("caption") or ""),
            str(item.get("caption_html") or ""),
        ]).lower()
        if q and q not in {"curated", "curated dining", "dining"} and q not in haystack:
            continue
        candidates.append(item)
        if len(candidates) >= 20:
            break

    for idx, item in enumerate(candidates):
        curated_id = item.get("id") or f"curated_{idx}"
        title = _curated_inline_title(item)
        description = _curated_inline_description(item)
        caption, parse_mode = _curated_caption_for_send(item)
        reply_markup = _curated_public_keyboard(item)
        result_id = str(curated_id)[:64]

        if item.get("photo_file_id"):
            kwargs = {
                "id": result_id,
                "photo_file_id": item.get("photo_file_id"),
                "title": title,
                "description": description,
                "reply_markup": reply_markup,
            }
            if caption:
                kwargs["caption"] = caption
                if parse_mode:
                    kwargs["parse_mode"] = parse_mode
            results.append(InlineQueryResultCachedPhoto(**kwargs))
        else:
            message_text = caption or "Curated Dining"
            content_kwargs = {"message_text": message_text}
            if parse_mode:
                content_kwargs["parse_mode"] = parse_mode
            results.append(InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(**content_kwargs),
                reply_markup=reply_markup,
            ))

    try:
        await query.answer(results, cache_time=1, is_personal=True)
    except Exception as e:
        print(f"[curated_inline_query_router] error: {e}")
        try:
            await query.answer([], cache_time=1, is_personal=True)
        except Exception:
            pass

# =========================================================
# ROOM MANAGEMENT FLOW
# =========================================================

def save_room_data():
    try:
        with open(ROOM_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": ROOM_ITEMS, "bookings": ROOM_BOOKINGS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save_room_data failed: {e}")


def load_room_data():
    global ROOM_ITEMS, ROOM_BOOKINGS
    try:
        p = Path(ROOM_FILE)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ROOM_ITEMS = data.get("items", [])
        ROOM_BOOKINGS = data.get("bookings", [])
        if not isinstance(ROOM_ITEMS, list):
            ROOM_ITEMS = []
        if not isinstance(ROOM_BOOKINGS, list):
            ROOM_BOOKINGS = []
    except Exception as e:
        print(f"[WARN] load_room_data failed: {e}")
        ROOM_ITEMS = []
        ROOM_BOOKINGS = []

def _next_room_number() -> int:
    used = []
    for item in ROOM_ITEMS:
        try:
            used.append(int(item.get("no", 0)))
        except Exception:
            pass
    return (max(used) + 1) if used else 1


def _create_room_input_keyboard(flow: dict):
    rows = [
        [
            InlineKeyboardButton("Nama Room", callback_data="roomcreate:fill:name"),
            InlineKeyboardButton("Harga / Malam", callback_data="roomcreate:fill:price"),
        ],
        [InlineKeyboardButton("Deskripsi Room", callback_data="roomcreate:fill:description")],
        [InlineKeyboardButton("Link Room", callback_data="roomcreate:fill:link")],
    ]
    if flow.get("name") and flow.get("price") is not None and flow.get("description") and flow.get("link"):
        rows.append([
            InlineKeyboardButton("✅ Simpan", callback_data="roomcreate:confirm:yes"),
            InlineKeyboardButton("🔄 Reset", callback_data="roomcreate:confirm:reset"),
        ])
    rows.append([InlineKeyboardButton("❌ Batal", callback_data="roomcreate:cancel")])
    return InlineKeyboardMarkup(rows)


def _build_room_create_text(flow: dict) -> str:
    name = flow.get("name") or "-"
    price = _normalize_price_text(flow.get("price")) if flow.get("price") is not None else "-"
    description = flow.get("description") or "-"
    link = flow.get("link") or "-"
    waiting = flow.get("waiting_for")
    lines = [
        "𖠷 ╱ LETHÉA RESORT: CREATE ROOM",
        "",
        f"Nama Room : {name}",
        f"Harga / Malam : {price}",
        f"Deskripsi : {description}",
        f"Link Room : {link}",
        "",
    ]
    prompts = {
        "name": "Sedang mengisi nama room. Kirim teks nama room di chat ini.",
        "price": "Sedang mengisi harga per malam. Kirim nominal harga dalam angka di chat ini.",
        "description": "Sedang mengisi deskripsi room. Kirim teks deskripsi di chat ini. Bisa satu baris atau multi-line.",
        "link": "Sedang mengisi link room. Kirim link group / room di chat ini.",
    }
    if waiting in prompts:
        lines.append(prompts[waiting])
    elif flow.get("name") and flow.get("price") is not None and flow.get("description") and flow.get("link"):
        lines.append("Apakah data room sudah sesuai?")
    else:
        lines.append("Pilih bagian yang ingin diisi lewat tombol di bawah.")
    return "\n".join(lines)


async def _refresh_create_room_message(context, flow: dict, *, final_text: str = None, reply_markup=None):
    chat_id = flow.get("chat_id")
    message_id = flow.get("message_id")
    if not chat_id or not message_id:
        return False
    text_out = final_text if final_text is not None else _build_room_create_text(flow)
    if reply_markup is None and final_text is None:
        reply_markup = _create_room_input_keyboard(flow)
    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text_out, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"[_refresh_create_room_message] error: {e}")
        return False


async def create_room_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return
    sent = await update.message.reply_text(
        "Mulai input data room resort baru.",
        reply_markup=_create_room_input_keyboard({}),
    )
    context.user_data["create_room_flow"] = {
        "name": None,
        "price": None,
        "description": None,
        "link": None,
        "waiting_for": None,
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
    }
    await _refresh_create_room_message(context, context.user_data["create_room_flow"])


async def room_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    query = update.callback_query
    await query.answer()

    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Owner atau Currathor.", show_alert=True)
        return

    flow = context.user_data.get("create_room_flow")
    data = query.data or ""

    if data == "roomcreate:cancel":
        if flow:
            await _refresh_create_room_message(
                context,
                flow,
                final_text="Pembuatan room dibatalkan.",
                reply_markup=None,
            )
        else:
            try:
                await query.edit_message_text("Pembuatan room dibatalkan.")
            except Exception:
                pass
        context.user_data.pop("create_room_flow", None)
        return

    if not flow:
        await query.edit_message_text("Sesi create room tidak ditemukan. Gunakan /createroom lagi.")
        return

    parts = data.split(":")
    if len(parts) < 3:
        return

    action = parts[1]

    if action == "fill":
        target = parts[2]
        if target not in ("name", "price", "description", "link"):
            return

        prereq_map = {
            "price": ["name"],
            "description": ["name", "price"],
            "link": ["name", "price", "description"],
        }

        missing = []
        for need in prereq_map.get(target, []):
            if need == "price":
                if flow.get("price") is None:
                    missing.append(need)
            elif not flow.get(need):
                missing.append(need)

        if missing:
            await query.answer("Lengkapi bagian sebelumnya dulu.", show_alert=True)
            return

        flow["waiting_for"] = target
        flow["chat_id"] = query.message.chat_id
        flow["message_id"] = query.message.message_id

        await _refresh_create_room_message(context, flow)

        hints = {
            "name": "Kirim nama room di chat ini.",
            "price": "Kirim harga per malam dalam angka.",
            "description": "Kirim deskripsi room di chat ini.",
            "link": "Kirim link room di chat ini.",
        }
        await query.answer(hints.get(target, "Kirim input di chat ini."), show_alert=True)
        return

    if action == "confirm":
        confirm_type = parts[2]

        if confirm_type == "reset":
            flow.update({
                "name": None,
                "price": None,
                "description": None,
                "link": None,
                "waiting_for": None,
            })
            await _refresh_create_room_message(context, flow)
            return

        if confirm_type == "yes":
            if not flow.get("name") or flow.get("price") is None or not flow.get("description") or not flow.get("link"):
                await query.answer("Data room belum lengkap.", show_alert=True)
                return

            item = {
                "no": _next_room_number(),
                "name": flow["name"],
                "price": int(flow["price"]),
                "description": flow.get("description") or "",
                "link": flow.get("link") or "",
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": query.from_user.id,
            }

            ROOM_ITEMS.append(item)
            save_room_data()

            await _refresh_create_room_message(
                context,
                flow,
                final_text=(
                    "✅ Room baru berhasil disimpan.\n\n"
                    f"Nama Room : {item['name']}\n"
                    f"Harga / Malam : {_normalize_price_text(item['price'])}\n"
                    "Deskripsi : sudah disimpan\n"
                    "Link Room : sudah disimpan\n"
                    f"Nomor Room : {item['no']}"
                ),
                reply_markup=None,
            )

            context.user_data.pop("create_room_flow", None)
            return


async def create_room_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("create_room_flow")
    if not flow:
        return

    if not await _ensure_not_banned(update, context):
        return

    if not _can_manage_staff(update.effective_user):
        context.user_data.pop("create_room_flow", None)
        return

    msg = update.effective_message
    if not msg:
        return

    if int(msg.chat_id) != int(flow.get("chat_id", 0) or 0):
        return

    waiting = flow.get("waiting_for")
    if not waiting:
        return

    text_in = (msg.text or msg.caption or "").strip()
    if not text_in:
        await msg.reply_text("Input tidak boleh kosong.")
        return

    if waiting == "name":
        flow["name"] = text_in
        flow["waiting_for"] = None
        await _refresh_create_room_message(context, flow)
        await msg.reply_text(f"✅ Nama room disimpan: {flow['name']}")
        return

    elif waiting == "price":
        raw = text_in.replace(".", "").replace(",", "")
        if not raw.isdigit():
            await msg.reply_text("Harga per malam harus angka.")
            return
        amount = int(raw)
        if amount <= 0:
            await msg.reply_text("Harga per malam harus lebih dari 0.")
            return
        flow["price"] = amount
        flow["waiting_for"] = None
        await _refresh_create_room_message(context, flow)
        await msg.reply_text(f"✅ Harga room disimpan: {_normalize_price_text(flow['price'])}")
        return

    elif waiting == "description":
        raw_text = _normalize_menu_block_text(text_in)
        if not raw_text:
            await msg.reply_text("Deskripsi room tidak boleh kosong.")
            return
        flow["description"] = raw_text
        flow["waiting_for"] = None
        await _refresh_create_room_message(context, flow)
        await msg.reply_text("✅ Deskripsi room disimpan.")
        return

    elif waiting == "link":
        flow["link"] = text_in
        flow["waiting_for"] = None
        await _refresh_create_room_message(context, flow)
        await msg.reply_text("✅ Link room disimpan.")
        return
    
#List Room
async def list_room_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return

    if not ROOM_ITEMS:
        await update.message.reply_text("Belum ada room tersimpan.")
        return

    items = sorted(
        ROOM_ITEMS,
        key=lambda x: int(x.get("no", 0)) if str(x.get("no", "")).isdigit() else 999999999
    )

    lines = ["𖠷 ╱.. Lethéa Room List:\n"]

    for item in items:
        lines.append(
            f"{item.get('no')}. {item.get('name', '-')}\n"
            f"Harga : {_normalize_price_text(item.get('price', 0))} / malam\n"
            f"Link : {item.get('link', '-')}\n"
        )

    await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)

#Del Room
async def del_room_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Owner atau Currathor.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /delroom <nomor_room>")
        return

    room_no = int(context.args[0])

    idx = next(
        (i for i, item in enumerate(ROOM_ITEMS) if int(item.get("no", -1)) == room_no),
        None
    )
    if idx is None:
        await update.message.reply_text("Nomor room tidak ditemukan.")
        return

    deleted = ROOM_ITEMS.pop(idx)
    save_room_data()

    await update.message.reply_text(
        "🗑️ Room dihapus.\n"
        f"{deleted.get('no')}. {deleted.get('name', '-')} | "
        f"{_normalize_price_text(deleted.get('price', 0))} / malam"
    )


# =========================================================
# =======
# POKER
# =======
# =========================================================
POKER_DEFAULT_BIG_BLIND = 200
POKER_MIN_PLAYERS = 2
POKER_MAX_PLAYERS = 8


def _poker_room_key(chat_id: int) -> str:
    return str(chat_id)


def _poker_active_uids(room: dict):
    return [uid for uid in room.get("player_order", []) if not room["players"][uid].get("folded")]


def _poker_live_uids(room: dict):
    return [uid for uid in room.get("player_order", []) if not room["players"][uid].get("folded") and not room["players"][uid].get("all_in")]


def _poker_first_active_from(room: dict, start_idx: int):
    order = room.get("player_order", [])
    total = len(order)
    if total <= 0:
        return None
    for step in range(total):
        idx = (start_idx + step) % total
        uid = order[idx]
        pdata = room["players"].get(uid) or {}
        if pdata.get("folded"):
            continue
        if pdata.get("all_in"):
            continue
        return uid
    return None


def _poker_dealer_uid(room: dict):
    order = room.get("player_order", [])
    if not order:
        return None
    return order[int(room.get("dealer_index", 0)) % len(order)]


def _poker_small_blind_uid(room: dict):
    order = room.get("player_order", [])
    n = len(order)
    if n < 2:
        return None
    dealer_idx = int(room.get("dealer_index", 0)) % n
    if n == 2:
        return order[dealer_idx]
    return order[(dealer_idx + 1) % n]


def _poker_big_blind_uid(room: dict):
    order = room.get("player_order", [])
    n = len(order)
    if n < 2:
        return None
    dealer_idx = int(room.get("dealer_index", 0)) % n
    if n == 2:
        return order[(dealer_idx + 1) % n]
    return order[(dealer_idx + 2) % n]


def _poker_preflop_first_uid(room: dict):
    order = room.get("player_order", [])
    n = len(order)
    if n < 2:
        return None
    dealer_idx = int(room.get("dealer_index", 0)) % n
    if n == 2:
        start_idx = dealer_idx
    else:
        start_idx = (dealer_idx + 3) % n
    return _poker_first_active_from(room, start_idx)


def _poker_postflop_first_uid(room: dict):
    order = room.get("player_order", [])
    if not order:
        return None
    dealer_idx = int(room.get("dealer_index", 0)) % len(order)
    return _poker_first_active_from(room, dealer_idx + 1)


def _poker_next_active_uid(room: dict, uid: str):
    order = room.get("player_order", [])
    if not order or uid not in order:
        return None
    idx = order.index(uid)
    return _poker_first_active_from(room, idx + 1)


def _poker_reset_street(room: dict):
    room["current_bet"] = 0
    room["awaiting_raise_uid"] = None
    room["pending_action_uids"] = []
    room["current_turn_uid"] = None
    for uid in room.get("player_order", []):
        pdata = room["players"][uid]
        pdata["street_commitment"] = 0
        pdata["acted_this_street"] = False


async def _poker_send_room_message(context, room: dict, text: str, *, reply_markup=None, reply_to_room: bool = True):
    kwargs = {"chat_id": room.get("chat_id"), "text": text}
    thread_id = room.get("thread_id")
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    if reply_to_room and room.get("message_id"):
        kwargs["reply_to_message_id"] = room.get("message_id")
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    return await context.bot.send_message(**kwargs)


def _poker_board_text(room: dict):
    cards = room.get("community_cards") or []
    return _format_cards(cards) if cards else "-"


def _poker_stage_label(stage: str) -> str:
    labels = {
        "waiting": "WAITING",
        "preflop": "PRE-FLOP",
        "flop": "FLOP",
        "turn": "TURN",
        "river": "RIVER",
        "showdown": "SHOWDOWN",
        "resolved": "RESOLVED",
    }
    return labels.get(stage or "waiting", str(stage).upper())


def _poker_status_text(room: dict) -> str:
    lines = [
        "♠️ … [ Texas Hold'em Poker ]",
        "",
        f"• [] Status : {_poker_stage_label(room.get('stage'))}",
        f"• [] Dealer : {(room['players'].get(_poker_dealer_uid(room), {}) or {}).get('name', '-')}",
        f"• [] Small Blind : {(room['players'].get(_poker_small_blind_uid(room), {}) or {}).get('name', '-')} ({room.get('small_blind', 0)})",
        f"• [] Big Blind : {(room['players'].get(_poker_big_blind_uid(room), {}) or {}).get('name', '-')} ({room.get('big_blind', 0)})",
        f"• [] Pot : {room.get('pot', 0)}",
        f"• [] Current Bet : {room.get('current_bet', 0)}",
        f"• [] Board : {_poker_board_text(room)}",
        "",
        "———— ╱╱ Player List :",
    ]
    for uid in room.get("player_order", []):
        pdata = room["players"].get(uid) or {}
        flags = []
        if uid == _poker_dealer_uid(room):
            flags.append("D")
        if uid == _poker_small_blind_uid(room):
            flags.append("SB")
        if uid == _poker_big_blind_uid(room):
            flags.append("BB")
        if pdata.get("folded"):
            flags.append("FOLD")
        if pdata.get("all_in"):
            flags.append("ALL-IN")
        marker = f" [{' / '.join(flags)}]" if flags else ""
        lines.append(
            f"› {pdata.get('name', 'Player')}{marker} | Stack: {pdata.get('stack_total', 0)} | In Pot: {pdata.get('total_commitment', 0)}"
        )
    turn_uid = room.get("current_turn_uid")
    if turn_uid and turn_uid in room.get("players", {}):
        lines.extend(["", f"• [] Turn : {room['players'][turn_uid].get('name', '-')}"])
    if room.get("stage") == "waiting":
        lines.extend([
            "",
            "Texas Hold'em Multiplayer • Oxana sebagai dealer • 2-8 pemain.",
            "Tombol dealer akan atur blind, bagikan 2 hole cards via DM, buka flop/turn/river, lalu hitung pemenang.",
        ])
    return "\n".join(lines)


def _poker_waiting_keyboard(room: dict):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎴 Join", callback_data="poker:join"),
            InlineKeyboardButton("↩️ Leave", callback_data="poker:leave"),
        ],
        [
            InlineKeyboardButton("▶️ Start", callback_data="poker:start"),
            InlineKeyboardButton("🗑️ Cancel", callback_data="poker:cancel"),
        ],
    ])


def _poker_action_keyboard(room: dict, uid: str):
    pdata = room["players"].get(uid) or {}
    outstanding = max(0, int(room.get("current_bet", 0)) - int(pdata.get("street_commitment", 0)))
    first_row = [InlineKeyboardButton("❌ Fold", callback_data=f"pokeract:{room['chat_id']}:fold")]
    if outstanding > 0:
        first_row.append(InlineKeyboardButton(f"📞 Call {outstanding}", callback_data=f"pokeract:{room['chat_id']}:call"))
    else:
        first_row.append(InlineKeyboardButton("✅ Check", callback_data=f"pokeract:{room['chat_id']}:check"))
    second_row = [
        InlineKeyboardButton("📈 Raise", callback_data=f"pokeract:{room['chat_id']}:raise"),
        InlineKeyboardButton("🔥 All-in", callback_data=f"pokeract:{room['chat_id']}:allin"),
    ]
    return InlineKeyboardMarkup([first_row, second_row])


async def _poker_refresh_message(context, room: dict):
    if not room.get("message_id"):
        return
    reply_markup = None
    if room.get("stage") == "waiting":
        reply_markup = _poker_waiting_keyboard(room)
    elif room.get("current_turn_uid"):
        reply_markup = _poker_action_keyboard(room, room["current_turn_uid"])
    text_value = _poker_status_text(room)
    markup_value = reply_markup.to_dict() if reply_markup else None
    if room.get("_last_render_text") == text_value and room.get("_last_render_markup") == markup_value:
        return
    try:
        await context.bot.edit_message_text(
            chat_id=room["chat_id"],
            message_id=room["message_id"],
            text=text_value,
            reply_markup=reply_markup,
        )
        room["_last_render_text"] = text_value
        room["_last_render_markup"] = markup_value
    except Exception as e:
        if "message is not modified" in str(e).lower():
            room["_last_render_text"] = text_value
            room["_last_render_markup"] = markup_value
            return
        print(f"[_poker_refresh_message] error: {e}")


def _poker_shuffle_deck(room: dict):
    import random
    deck = _new_deck()
    random.shuffle(deck)
    room["deck"] = deck


def _poker_draw(room: dict, n: int):
    out = []
    deck = room.setdefault("deck", [])
    for _ in range(n):
        if not deck:
            _poker_shuffle_deck(room)
            deck = room["deck"]
        out.append(deck.pop(0))
    return out


def _holdem_eval_5(cards):
    score = _evaluate_poker_hand(cards)
    if score[0] == 8 and sorted((_card_rank(c) for c in cards), reverse=True) == [14, 13, 12, 11, 10]:
        return (9, score[1])
    return score


def _holdem_hand_label(score):
    if score[0] == 9:
        return "Royal Flush"
    mapping = {
        8: "Straight Flush",
        7: "Four of a Kind",
        6: "Full House",
        5: "Flush",
        4: "Straight",
        3: "Three of a Kind",
        2: "Two Pair",
        1: "One Pair",
        0: "High Card",
    }
    return mapping.get(score[0], "High Card")


def _holdem_best_from_seven(cards):
    best_score = None
    best_cards = None
    for combo in combinations(cards, 5):
        score = _holdem_eval_5(list(combo))
        if best_score is None or score > best_score:
            best_score = score
            best_cards = list(combo)
    return best_score, best_cards


def _poker_settle_balances(room: dict, winner_uids, pot: int):
    winner_uids = [str(x) for x in winner_uids]
    players = room.get("players", {})
    share = pot // len(winner_uids) if winner_uids else 0
    rem = pot % len(winner_uids) if winner_uids else 0
    for uid in room.get("player_order", []):
        rec = _get_existing_account(int(uid))
        pdata = players[uid]
        start = int(pdata.get("stack_total", rec.get("balance", 0) if rec else 0))
        final = start - int(pdata.get("total_commitment", 0))
        if uid in winner_uids:
            final += share
            if rem > 0:
                final += 1
                rem -= 1
        pdata["balance_after"] = max(0, final)
        if rec:
            rec["balance"] = pdata["balance_after"]
    save_accounts()


async def _poker_finish_early(context, room: dict, winner_uid: str):
    room["stage"] = "resolved"
    _poker_settle_balances(room, [winner_uid], int(room.get("pot", 0)))
    winner = room["players"][winner_uid]
    await _poker_refresh_message(context, room)
    await _poker_send_room_message(
        context,
        room,
        (
            f"🏆 Semua pemain lain fold. {winner.get('name')} menang langsung dan mengambil pot {room.get('pot', 0)}.\n"
            f"Saldo akhir: {winner.get('balance_after', 0)}"
        ),
    )
    POKER_ROOMS.pop(_poker_room_key(room["chat_id"]), None)


async def _poker_showdown(context, room: dict):
    room["stage"] = "showdown"
    contenders = _poker_active_uids(room)
    results = []
    best_score = None
    for uid in contenders:
        pdata = room["players"][uid]
        score, best_cards = _holdem_best_from_seven((pdata.get("hole_cards") or []) + (room.get("community_cards") or []))
        pdata["best_score"] = score
        pdata["best_cards"] = best_cards
        results.append((uid, score, best_cards))
        if best_score is None or score > best_score:
            best_score = score
    winners = [uid for uid, score, _ in results if score == best_score]
    _poker_settle_balances(room, winners, int(room.get("pot", 0)))
    await _poker_refresh_message(context, room)
    lines = ["🂡 Showdown Texas Hold'em", "", f"Board : {_poker_board_text(room)}", ""]
    for uid, score, best_cards in results:
        pdata = room["players"][uid]
        lines.append(
            f"• {pdata.get('name')}\n"
            f"  Hole Cards : {_format_cards(pdata.get('hole_cards') or [])}\n"
            f"  Best Hand : {_holdem_hand_label(score)}\n"
            f"  Best 5 : {_format_cards(best_cards or [])}\n"
            f"  Balance : {pdata.get('balance_after', pdata.get('stack_total', 0))}"
        )
        lines.append("")
    if len(winners) == 1:
        lines.append(f"🏆 Winner : {room['players'][winners[0]].get('name')} memenangkan pot {room.get('pot', 0)}")
    else:
        names = ", ".join(room['players'][uid].get('name', '-') for uid in winners)
        lines.append(f"🤝 Split Pot : {names} membagi pot {room.get('pot', 0)}")
    await _poker_send_room_message(context, room, "\n".join(lines).strip())
    POKER_ROOMS.pop(_poker_room_key(room["chat_id"]), None)


async def _poker_begin_betting_round(context, room: dict, stage: str):
    room["stage"] = stage
    if stage != "preflop":
        _poker_reset_street(room)
    active = _poker_active_uids(room)
    if len(active) <= 1:
        await _poker_finish_early(context, room, active[0])
        return
    if stage == "preflop":
        first_uid = _poker_preflop_first_uid(room)
        pending = [uid for uid in active if not room["players"][uid].get("all_in")]
    else:
        first_uid = _poker_postflop_first_uid(room)
        pending = [uid for uid in active if not room["players"][uid].get("all_in")]
    room["current_turn_uid"] = first_uid
    room["pending_action_uids"] = [uid for uid in pending if uid != first_uid]
    await _poker_refresh_message(context, room)
    if first_uid:
        await _poker_send_room_message(
            context,
            room,
            f"🫀 { _poker_stage_label(stage) } dimulai. Giliran {room['players'][first_uid].get('name')}.",
            reply_markup=_poker_action_keyboard(room, first_uid),
        )


async def _poker_deal_hole_cards(context, room: dict):
    _poker_shuffle_deck(room)
    for uid in room.get("player_order", []):
        pdata = room["players"][uid]
        pdata["hole_cards"] = _poker_draw(room, 2)
        pdata["folded"] = False
        pdata["all_in"] = False
        pdata["street_commitment"] = 0
        pdata["total_commitment"] = 0
        pdata["acted_this_street"] = False
    dm_failed = False
    for uid in room.get("player_order", []):
        pdata = room["players"][uid]
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=(
                    f"⌜ Texas Hold'em — Hole Cards ⌟\n"
                    f"Room: {room.get('chat_title') or room.get('chat_id')}\n"
                    f"Kartumu: {_format_cards(pdata.get('hole_cards') or [])}"
                ),
            )
            pdata["dm_ok"] = True
        except Exception:
            pdata["dm_ok"] = False
            dm_failed = True
    await _poker_send_room_message(context, room, "🃏 Oxana membagikan 2 hole cards ke semua player via DM.")
    if dm_failed:
        await _poker_send_room_message(context, room, "⚠️ Ada player yang belum bisa menerima DM. Meja Poker dibatalkan supaya kartu private tidak bocor dan game tidak nyangkut. Semua pemain wajib /start bot dulu sebelum buka ulang room.")
        POKER_ROOMS.pop(_poker_room_key(room.get("chat_id")), None)
        return False
    return True


async def _poker_reveal_flop(context, room: dict):
    room.setdefault("community_cards", []).extend(_poker_draw(room, 3))
    await _poker_send_room_message(context, room, f"🃏 Flop dibuka: {_poker_board_text(room)}")
    await _poker_begin_betting_round(context, room, "flop")


async def _poker_reveal_turn(context, room: dict):
    room.setdefault("community_cards", []).extend(_poker_draw(room, 1))
    await _poker_send_room_message(context, room, f"🃏 Turn dibuka: {_poker_board_text(room)}")
    await _poker_begin_betting_round(context, room, "turn")


async def _poker_reveal_river(context, room: dict):
    room.setdefault("community_cards", []).extend(_poker_draw(room, 1))
    await _poker_send_room_message(context, room, f"🃏 River dibuka: {_poker_board_text(room)}")
    await _poker_begin_betting_round(context, room, "river")


async def _poker_advance_after_round(context, room: dict):
    active = _poker_active_uids(room)
    if len(active) == 1:
        await _poker_finish_early(context, room, active[0])
        return
    stage = room.get("stage")
    if stage == "preflop":
        await _poker_reveal_flop(context, room)
        return
    if stage == "flop":
        await _poker_reveal_turn(context, room)
        return
    if stage == "turn":
        await _poker_reveal_river(context, room)
        return
    await _poker_showdown(context, room)


async def _poker_apply_action(context, room: dict, uid: str, action: str, raise_total: int = None):
    pdata = room["players"][uid]
    current_bet = int(room.get("current_bet", 0))
    street_commitment = int(pdata.get("street_commitment", 0))
    total_commitment = int(pdata.get("total_commitment", 0))
    stack_total = int(pdata.get("stack_total", 0))
    chips_left = max(0, stack_total - total_commitment)
    outstanding = max(0, current_bet - street_commitment)
    note = None
    raised = False

    if action == "fold":
        pdata["folded"] = True
        note = f"❌ {pdata.get('name')} fold."
    elif action == "check":
        if outstanding != 0:
            return False, "Tidak bisa check karena masih ada bet yang harus disamakan."
        pdata["acted_this_street"] = True
        note = f"✅ {pdata.get('name')} check."
    elif action == "call":
        if outstanding <= 0:
            return False, "Tidak ada bet untuk di-call."
        pay = min(chips_left, outstanding)
        pdata["street_commitment"] = street_commitment + pay
        pdata["total_commitment"] = total_commitment + pay
        room["pot"] = int(room.get("pot", 0)) + pay
        pdata["acted_this_street"] = True
        if pay < outstanding or pdata["total_commitment"] >= stack_total:
            pdata["all_in"] = True
            note = f"🔥 {pdata.get('name')} all-in {pdata.get('total_commitment')}"
        else:
            note = f"📞 {pdata.get('name')} call {pay}."
    elif action == "allin":
        if chips_left <= 0:
            return False, "Chip kamu sudah habis."
        new_street_total = street_commitment + chips_left
        pdata["street_commitment"] = new_street_total
        pdata["total_commitment"] = total_commitment + chips_left
        room["pot"] = int(room.get("pot", 0)) + chips_left
        pdata["all_in"] = True
        pdata["acted_this_street"] = True
        if new_street_total > current_bet:
            room["current_bet"] = new_street_total
            raised = True
        note = f"🔥 {pdata.get('name')} all-in {pdata.get('total_commitment')}"
    elif action == "raise":
        if raise_total is None:
            return False, "Raise total tidak valid."
        if raise_total <= current_bet:
            return False, f"Raise harus lebih besar dari current bet {current_bet}."
        add_needed = raise_total - street_commitment
        if add_needed > chips_left:
            return False, f"Chip tidak cukup. Sisa chip kamu: {chips_left}"
        pdata["street_commitment"] = raise_total
        pdata["total_commitment"] = total_commitment + add_needed
        room["pot"] = int(room.get("pot", 0)) + add_needed
        room["current_bet"] = raise_total
        pdata["acted_this_street"] = True
        if pdata["total_commitment"] >= stack_total:
            pdata["all_in"] = True
        raised = True
        note = f"📈 {pdata.get('name')} raise ke {raise_total}."
    else:
        return False, "Aksi tidak dikenal."

    others = [x for x in _poker_active_uids(room) if x != uid and not room['players'][x].get('all_in')]
    if action == "fold":
        pending = [x for x in room.get("pending_action_uids", []) if x != uid]
    elif raised:
        pending = others
    else:
        pending = [x for x in room.get("pending_action_uids", []) if x != uid]
    room["pending_action_uids"] = pending
    await _poker_send_room_message(context, room, note)
    active = _poker_active_uids(room)
    if len(active) == 1:
        await _poker_finish_early(context, room, active[0])
        return True, None
    next_uid = _poker_next_active_uid(room, uid)
    if room.get("pending_action_uids"):
        if next_uid is None or next_uid not in room.get("pending_action_uids"):
            target = None
            for cand in room.get("player_order", []):
                if cand in room.get("pending_action_uids"):
                    target = cand
                    break
            next_uid = target
    else:
        next_uid = None
    room["current_turn_uid"] = next_uid
    await _poker_refresh_message(context, room)
    if next_uid:
        await _poker_send_room_message(
            context,
            room,
            f"🫀 Giliran {room['players'][next_uid].get('name')}.",
            reply_markup=_poker_action_keyboard(room, next_uid),
        )
    else:
        await _poker_advance_after_round(context, room)
    return True, None


async def poker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Poker hanya bisa dibuka di group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu sebelum buka room Poker.")
        return
    room_key = _poker_room_key(chat.id)
    if room_key in POKER_ROOMS:
        await update.message.reply_text("Masih ada room Poker aktif di grup ini.")
        return
    big_blind = POKER_DEFAULT_BIG_BLIND
    if context.args and str(context.args[0]).isdigit():
        big_blind = max(2, int(context.args[0]))
    small_blind = max(1, big_blind // 2)
    room = {
        "chat_id": chat.id,
        "chat_title": chat.title or str(chat.id),
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "message_id": None,
        "stage": "waiting",
        "dealer_index": 0,
        "small_blind": small_blind,
        "big_blind": big_blind,
        "pot": 0,
        "current_bet": 0,
        "community_cards": [],
        "deck": [],
        "current_turn_uid": None,
        "awaiting_raise_uid": None,
        "pending_action_uids": [],
        "player_order": [str(user.id)],
        "players": {
            str(user.id): {
                "name": user.full_name or user.username or f"User {user.id}",
                "stack_total": int(rec.get("balance", 0)),
                "total_commitment": 0,
                "street_commitment": 0,
                "hole_cards": [],
                "folded": False,
                "all_in": False,
                "acted_this_street": False,
            }
        },
    }
    sent = await update.message.reply_text(
        _poker_status_text(room),
        reply_markup=_poker_waiting_keyboard(room),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    room["message_id"] = sent.message_id
    POKER_ROOMS[room_key] = room
    await _poker_send_room_message(
        context,
        room,
        (
            "♠️ Oxana membuka meja Texas Hold'em.\n"
            f"Blind: {small_blind}/{big_blind}\n"
            "Host sudah duduk sebagai player. Minimum 2 pemain, maksimum 8 pemain. Oxana bertindak sebagai dealer."
        ),
    )


async def _poker_start_hand(context, room: dict):
    for uid in room.get("player_order", []):
        rec = _get_existing_account(int(uid))
        if rec:
            room["players"][uid]["stack_total"] = int(rec.get("balance", 0))
        room["players"][uid]["total_commitment"] = 0
        room["players"][uid]["street_commitment"] = 0
        room["players"][uid]["folded"] = False
        room["players"][uid]["all_in"] = False
    room["community_cards"] = []
    room["pot"] = 0
    room["current_bet"] = 0
    _poker_shuffle_deck(room)
    if not await _poker_deal_hole_cards(context, room):
        return
    sb_uid = _poker_small_blind_uid(room)
    bb_uid = _poker_big_blind_uid(room)
    for uid, forced in [(sb_uid, int(room.get("small_blind", 0))), (bb_uid, int(room.get("big_blind", 0)) )]:
        if not uid:
            continue
        pdata = room["players"][uid]
        stack_total = int(pdata.get("stack_total", 0))
        pay = min(stack_total, forced)
        pdata["street_commitment"] += pay
        pdata["total_commitment"] += pay
        room["pot"] += pay
        if pdata["total_commitment"] >= stack_total:
            pdata["all_in"] = True
    room["current_bet"] = max(int(room.get("big_blind", 0)), max((room['players'][uid].get('street_commitment', 0) for uid in room.get('player_order', [])), default=0))
    await _poker_send_room_message(
        context,
        room,
        (
            f"🎯 Posisi meja:\n"
            f"Dealer : {room['players'].get(_poker_dealer_uid(room), {}).get('name', '-')}\n"
            f"Small Blind : {room['players'].get(sb_uid, {}).get('name', '-')} ({room['players'].get(sb_uid, {}).get('street_commitment', 0)})\n"
            f"Big Blind : {room['players'].get(bb_uid, {}).get('name', '-')} ({room['players'].get(bb_uid, {}).get('street_commitment', 0)})"
        ),
    )
    await _poker_begin_betting_round(context, room, "preflop")


async def poker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    room = POKER_ROOMS.get(_poker_room_key(query.message.chat_id))
    if not room:
        await query.answer("Room poker tidak ditemukan atau sudah selesai.", show_alert=True)
        return
    action = (query.data or '').split(':', 1)[1]
    uid = str(user.id)
    if action == 'join':
        rec = _get_existing_account(user.id)
        if not _has_gamble_access(rec):
            await query.answer("Nomor account perlu kau miliki sebelum ikut bermain.", show_alert=True)
            return
        if uid in room['players']:
            return
        if room.get('stage') != 'waiting':
            await query.answer("Game sudah berjalan.", show_alert=True)
            return
        if len(room.get('player_order', [])) >= POKER_MAX_PLAYERS:
            await query.answer("Meja sudah penuh. Maksimum 8 pemain.", show_alert=True)
            return
        room['player_order'].append(uid)
        room['players'][uid] = {
            'name': user.full_name or user.username or f'User {user.id}',
            'stack_total': int(rec.get('balance', 0)),
            'total_commitment': 0,
            'street_commitment': 0,
            'hole_cards': [],
            'folded': False,
            'all_in': False,
            'acted_this_street': False,
        }
        await _poker_refresh_message(context, room)
        await _poker_send_room_message(context, room, f"🎴 {room['players'][uid]['name']} duduk di meja Poker.")
        return
    if action == 'leave':
        if room.get('stage') != 'waiting':
            await query.answer("Game sudah berjalan. Tidak bisa leave sekarang.", show_alert=True)
            return
        if uid == str(room.get('host_id')):
            await query.answer("Host tidak bisa leave. Gunakan Cancel room.", show_alert=True)
            return
        if uid in room['players']:
            room['players'].pop(uid, None)
            room['player_order'] = [x for x in room.get('player_order', []) if x != uid]
            await _poker_refresh_message(context, room)
        return
    if action == 'cancel':
        if user.id != room.get('host_id') and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa membatalkan room.", show_alert=True)
            return
        POKER_ROOMS.pop(_poker_room_key(room['chat_id']), None)
        await query.edit_message_text("🗑️ Room Poker dibatalkan.")
        return
    if action == 'start':
        if user.id != room.get('host_id') and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa memulai.", show_alert=True)
            return
        if len(room.get('player_order', [])) < POKER_MIN_PLAYERS:
            await query.answer("Minimal 2 pemain untuk mulai.", show_alert=True)
            return
        await _poker_start_hand(context, room)
        return


async def poker_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or '').split(':')
    if len(parts) != 3:
        return
    _, room_chat_id_raw, action = parts
    try:
        room_chat_id = int(room_chat_id_raw)
    except Exception:
        await query.answer("Room tidak valid.", show_alert=True)
        return
    room = POKER_ROOMS.get(_poker_room_key(room_chat_id))
    if not room:
        await query.answer("Room poker tidak ditemukan.", show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid != str(room.get('current_turn_uid')):
        await query.answer("Bukan giliranmu.", show_alert=True)
        return
    if action == 'raise':
        room['awaiting_raise_uid'] = uid
        await _poker_send_room_message(context, room, f"📈 {room['players'][uid].get('name')} sedang menyiapkan raise. Kirim nominal TOTAL bet-mu dengan angka saja.")
        return
    ok, error = await _poker_apply_action(context, room, uid, action)
    if not ok and error:
        await query.answer(error, show_alert=True)


async def poker_bet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == 'private' or not msg or not msg.text:
        return
    room = POKER_ROOMS.get(_poker_room_key(chat.id))
    if not room:
        return
    uid = str(user.id)
    if uid != str(room.get('awaiting_raise_uid') or ''):
        return
    raw = (msg.text or '').strip().replace('.', '').replace(',', '')
    if not raw.isdigit():
        return
    raise_total = int(raw)
    room['awaiting_raise_uid'] = None
    ok, error = await _poker_apply_action(context, room, uid, 'raise', raise_total=raise_total)
    if not ok and error:
        await msg.reply_text(error)


# =========================================================
# FEATURE: STAFF TAGGING / TAGALL
# =========================================================
TAG_ROLE_ALIASES = {
    "all": "Semua user",
    "member": "Member",
    "vip": "VIP aktif",
    "regular": "Regular aktif",
    "staff": "Staff",
    "currathor": "Currathor",
    "server": "Server",
    "dj": "DJ",
    "bartender": "Bartender",
    "angel": "Angel",
    "stripdancer": "Strip Dancer",
    "chef": "Chef",
    "performer": "Performer",
}

TAG_COMMAND_ROLE_MAP = {
    "tagall": "all",
    "tagmember": "member",
    "tagvip": "vip",
    "tagregular": "regular",
    "tagstaff": "staff",
    "tagcurrathor": "currathor",
    "tagserver": "server",
    "tagdj": "dj",
    "tagbartender": "bartender",
    "tagangel": "angel",
    "tagstripdancer": "stripdancer",
    "tagchef": "chef",
    "tagperformer": "performer",
}


def _can_use_tag_command(user) -> bool:
    return _is_staff_like(user)


def _tag_started_display_name(uid: int, rec=None) -> str:
    started = STARTED_USERS.get(str(uid)) or {}
    name = (started.get("full_name") or "").strip()
    if not name and rec:
        name = (rec.get("name") or rec.get("username") or "").strip()
    if not name:
        name = f"User {uid}"
    return name


def _tag_mention_html(uid: int, rec=None) -> str:
    started = STARTED_USERS.get(str(uid)) or {}
    username = (started.get("username") or "").strip().lstrip("@")
    if not username and rec:
        username = (rec.get("username") or "").strip().lstrip("@")
    if username:
        # Kalau user punya username, tampilkan clean sebagai @username agar notifikasi Telegram tetap muncul.
        return "@" + html.escape(username)
    # Kalau tidak punya username, fallback ke text mention by user id.
    return f'<a href="tg://user?id={int(uid)}">{html.escape(_tag_started_display_name(uid, rec))}</a>'


def _tag_role_match(uid: int, role_key: str) -> bool:
    if role_key == "all":
        return True

    rec = _get_existing_account(int(uid))
    if not rec:
        return False

    account_type = (rec.get("account_type") or "").strip().lower()
    staff_role = (rec.get("staff_role") or "").strip().lower().replace(" ", "").replace("_", "")
    membership_type = (rec.get("membership_type") or "").strip().lower()

    if role_key == "member":
        return account_type == "member"
    if role_key == "vip":
        _refresh_membership_status(rec)
        return account_type == "member" and membership_type == "vip" and rec.get("membership_status") == "active"
    if role_key == "regular":
        _refresh_membership_status(rec)
        return account_type == "member" and membership_type == "regular" and rec.get("membership_status") == "active"
    if role_key == "staff":
        return account_type in ("staff", "owner")
    if role_key == "currathor":
        return account_type == "staff" and staff_role == "currathor"
    if role_key == "stripdancer":
        return account_type == "staff" and staff_role in ("stripdancer", "stripdancer")
    return account_type == "staff" and staff_role == role_key


async def _tag_user_is_in_chat(context, chat_id: int, uid: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=int(uid))
        status = getattr(member, "status", "")
        if status in ("left", "kicked"):
            return False
        if status == "restricted" and getattr(member, "is_member", True) is False:
            return False
        return True
    except Exception:
        return False


async def _collect_tag_targets(context, chat_id: int, role_key: str):
    targets = []
    seen = set()
    for uid_raw, started in list(STARTED_USERS.items()):
        try:
            uid = int(started.get("id") or uid_raw)
        except Exception:
            continue
        if uid in seen:
            continue
        if not _tag_role_match(uid, role_key):
            continue
        if not await _tag_user_is_in_chat(context, chat_id, uid):
            continue
        seen.add(uid)
        targets.append((uid, _get_existing_account(uid)))
    targets.sort(key=lambda item: _tag_started_display_name(item[0], item[1]).lower())
    return targets


def _tag_chunks(header: str, mentions):
    chunks = []
    current = header.strip() + "\n\n"
    for mention in mentions:
        piece = mention + " "
        if len(current) + len(piece) > 3500 and current.strip() != header.strip():
            chunks.append(current.strip())
            current = ""
        current += piece
    if current.strip():
        chunks.append(current.strip())
    return chunks


async def tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.effective_message.reply_text("Tag hanya bisa dipakai di group.")
        return
    if not _can_use_tag_command(update.effective_user):
        await update.effective_message.reply_text("Hanya staff yang bisa memakai fitur tag.")
        return

    text = update.effective_message.text or ""
    command = text.split(maxsplit=1)[0].split("@", 1)[0].lstrip("/").lower()
    role_key = TAG_COMMAND_ROLE_MAP.get(command, "all")
    extra_text = text.split(maxsplit=1)[1].strip() if len(text.split(maxsplit=1)) > 1 else ""

    targets = await _collect_tag_targets(context, update.effective_chat.id, role_key)
    if not targets:
        await update.effective_message.reply_text(f"Tidak ada target {TAG_ROLE_ALIASES.get(role_key, role_key)} yang sudah /start dan sedang ada di group ini.")
        return

    header_lines = [
        "𖠷 ╱ .. 𝐀𝐒𝐌𝐎𝐃𝐀𝐘 𝐒𝐔𝐌𝐌𝐎𝐍𝐒",
        "",
        "❯ Notice : Asmoday menyebut anda.",
        f"❯ Scope : {TAG_ROLE_ALIASES.get(role_key, role_key)}",
        f"❯ Total : {len(targets)} user",
    ]
    if extra_text:
        header_lines.extend(["❯ Message :", extra_text])
    header_lines.extend(["", "─────"])
    header = "\n".join(header_lines)
    mentions = [_tag_mention_html(uid, rec) for uid, rec in targets]

    first = True
    for chunk in _tag_chunks(header, mentions):
        if first:
            await update.effective_message.reply_text(chunk, parse_mode="HTML", disable_web_page_preview=True)
            first = False
        else:
            await asyncio.sleep(0.9)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="HTML", disable_web_page_preview=True)


# =========================================================
# FEATURE: ADD CUSTOM COMMAND
# =========================================================
_BUILTIN_COMMAND_NAMES = {
    "start", "menu", "registration", "registrationstaff", "oprecstaff", "renewal", "upgradevip",
    "starttalk", "stoptalk", "myacc", "changeidcphoto", "changepict", "changefullname",
    "mybalance", "mystafflog", "setnitroid", "claimcnit", "confirmcnit", "rejectcnit",
    "changecodename", "cancel", "where_forward", "getid", "help", "letheamenu", "createmenu",
    "createroom", "listroom", "bookinglist", "delroom", "rollmenu", "listmenu", "infomenu",
    "delmenu", "addpriceall", "addprice", "sendbill", "inputangel", "rentangel", "reserveresort",
    "tarot", "angelprice", "angeloff", "myangelbook", "listangel", "openwarung", "broadcast",
    "openbar", "openresort", "opencurated", "listcurated", "closecurated", "delcurated",
    "closebar", "openshift", "shiftresortopen", "closeshift", "choicepoker", "thirtyone", "poker",
    "blackjack", "booray", "dicepoker", "symphony", "alluringsymphony", "alluring", "baccarat",
    "baccaratbet", "jugement", "judgment", "jugdment", "joinjudgment", "bet", "take", "pass",
    "lock", "chess", "joinchess", "chessstart", "chessclose", "addstaff", "editrole", "delstaff",
    "ban", "unban", "addsaldo", "minsaldo", "listacc", "addadmin", "deladmin", "listadmin",
    "delacc", "acc", "reject", "addcnit", "dellcnit", "cnitbook", "botfee", "mybill",
    "paymentbill", "tagall", "tagmember", "tagvip", "tagregular", "tagstaff", "tagcurrathor",
    "tagserver", "tagdj", "tagbartender", "tagangel", "tagstripdancer", "tagchef", "tagperformer",
    "topup", "openevent", "closeevent", "addcmd", "listcmd", "delcmd",
}


def _addcmd_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Text", callback_data="addcmd:mode:text")],
        [InlineKeyboardButton("Foto", callback_data="addcmd:mode:photo")],
        [InlineKeyboardButton("Foto + Text", callback_data="addcmd:mode:both")],
        [InlineKeyboardButton("Batalkan", callback_data="addcmd:cancel")],
    ])


def _entity_to_plain_dict(entity) -> dict:
    try:
        raw = entity.to_dict()
    except Exception:
        raw = {}
    allowed = {"type", "offset", "length", "url", "language", "custom_emoji_id"}
    return {k: v for k, v in raw.items() if k in allowed and v is not None}


def _entities_to_plain_list(entities) -> list:
    return [_entity_to_plain_dict(ent) for ent in (entities or [])]


def _entities_from_plain_list(context, entities):
    out = []
    for ent in entities or []:
        try:
            out.append(MessageEntity.de_json(ent, context.bot))
        except Exception:
            pass
    return out or None


def _normalize_custom_command_name(raw: str):
    text = (raw or "").strip()
    text = text.strip("[](){} ")
    if text.startswith("/"):
        text = text[1:]
    if "@" in text:
        text = text.split("@", 1)[0]
    text = text.strip().lower()
    if not re.match(r"^[a-z0-9_]{1,32}$", text or ""):
        return None
    return text


def _extract_invoked_command(update: Update):
    msg = update.effective_message
    text = (getattr(msg, "text", None) or "").strip()
    if not text.startswith("/"):
        return None
    first = text.split(maxsplit=1)[0]
    return _normalize_custom_command_name(first)


def _addcmd_flow_summary(flow: dict) -> str:
    command = flow.get("command") or "-"
    mode = flow.get("mode") or "-"
    has_photo = "tersedia" if flow.get("photo_file_id") else "-"
    text = (flow.get("text") or "").strip()
    if text:
        preview = text if len(text) <= 240 else text[:237] + "..."
    else:
        preview = "-"
    return (
        "⌜ Add Command Recap ⌟\n\n"
        f"Mode : {mode}\n"
        f"Foto : {has_photo}\n"
        f"Text :\n{preview}\n\n"
        f"Command : /{command}"
    )


def _addcmd_payload_ready(flow: dict) -> bool:
    mode = flow.get("mode")
    has_text = bool((flow.get("text") or "").strip())
    has_photo = bool(flow.get("photo_file_id"))
    if mode == "text":
        return has_text
    if mode == "photo":
        return has_photo
    if mode == "both":
        return has_text and has_photo
    return False


async def _addcmd_send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    msg = update.effective_message
    if flow.get("photo_file_id"):
        caption = (flow.get("text") or "").strip() or None
        caption_entities = _entities_from_plain_list(context, flow.get("text_entities") or []) if caption else None
        if caption and len(caption) <= 1024:
            if flow.get("media_type") == "document":
                await msg.reply_document(document=flow.get("photo_file_id"), caption=caption, caption_entities=caption_entities)
            else:
                await msg.reply_photo(photo=flow.get("photo_file_id"), caption=caption, caption_entities=caption_entities)
        else:
            if flow.get("media_type") == "document":
                await msg.reply_document(document=flow.get("photo_file_id"))
            else:
                await msg.reply_photo(photo=flow.get("photo_file_id"))
            if caption:
                await msg.reply_text(caption, entities=caption_entities)
    elif (flow.get("text") or "").strip():
        await msg.reply_text(flow.get("text"), entities=_entities_from_plain_list(context, flow.get("text_entities") or []))


async def _addcmd_ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict):
    flow["step"] = "command"
    await _addcmd_send_preview(update, context, flow)
    await update.effective_message.reply_text(
        "𖠷 ╱ .. Jejak titah telah kurangkai.\n\n"
        "Kini tuliskan nama command yang hendak dijadikan gerbang.\n"
        "Contoh: mieayam atau /mieayam atau [mieayam]"
    )


async def addcmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.effective_message.reply_text("Hanya Currathor atau Owner yang dapat menambahkan custom command.")
        return
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text("Sila buka /addcmd melalui private chat Asmoday, agar rupa dan teksnya tidak tercerai di ruang publik.")
        return
    context.user_data.pop("addcmd_flow", None)
    context.user_data["addcmd_flow"] = {
        "step": "choose_mode",
        "created_by": int(update.effective_user.id),
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    await update.effective_message.reply_text(
        "⌜ Add Command ⌟\n\n"
        "Pilih wujud yang ingin Asmoday simpan sebagai titah baru.\n"
        "Boleh hanya text, hanya foto, atau keduanya.",
        reply_markup=_addcmd_choice_keyboard(),
    )




def _sorted_custom_command_items():
    items = []
    for cmd, item in (CUSTOM_COMMANDS or {}).items():
        if not isinstance(item, dict):
            continue
        items.append((cmd, item))
    items.sort(key=lambda x: x[0])
    return items


def _custom_command_list_text() -> str:
    items = _sorted_custom_command_items()
    if not items:
        return (
            "⌜ Custom Command List ⌟\n\n"
            "Belum ada titah tambahan yang tersimpan.\n"
            "Gunakan /addcmd untuk menambahkan command baru."
        )
    lines = ["⌜ Custom Command List ⌟", ""]
    for idx, (cmd, item) in enumerate(items, start=1):
        mode = item.get("mode") or "-"
        marker = "foto + text" if item.get("photo_file_id") and (item.get("text") or "").strip() else "foto" if item.get("photo_file_id") else "text"
        lines.append(f"{idx}. /{cmd} — {marker}")
    lines.extend(["", f"Total: {len(items)} command", "", "Untuk menghapus: /delcmd [nomor]", "Contoh: /delcmd 1"])
    return "\n".join(lines)


async def listcmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.effective_message.reply_text("Hanya Currathor atau Owner yang dapat melihat custom command.")
        return
    await update.effective_message.reply_text(_custom_command_list_text())


async def delcmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not _can_manage_staff(update.effective_user):
        await update.effective_message.reply_text("Hanya Currathor atau Owner yang dapat menghapus custom command.")
        return

    items = _sorted_custom_command_items()
    if not items:
        await update.effective_message.reply_text(
            "⌜ Delete Custom Command ⌟\n\n"
            "Belum ada command yang dapat dihapus."
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            _custom_command_list_text() + "\n\nFormat hapus: /delcmd [nomor]"
        )
        return

    raw = (context.args[0] or "").strip()
    if not raw.isdigit():
        await update.effective_message.reply_text("Nomor tidak sah. Contoh: /delcmd 1")
        return

    idx = int(raw)
    if idx < 1 or idx > len(items):
        await update.effective_message.reply_text(
            f"Nomor tidak ditemukan. Pilih angka 1 sampai {len(items)}.\n\n" + _custom_command_list_text()
        )
        return

    command, _item = items[idx - 1]
    CUSTOM_COMMANDS.pop(command, None)
    save_custom_command_data()
    await update.effective_message.reply_text(
        "⌜ Delete Custom Command ⌟\n\n"
        f"Titah /{command} telah dihapus dari lemari Asmoday."
    )

async def addcmd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Currathor atau Owner.", show_alert=True)
        return
    data = query.data or ""
    if data == "addcmd:cancel":
        context.user_data.pop("addcmd_flow", None)
        await query.edit_message_text("Sesi addcmd dibatalkan.")
        return
    flow = context.user_data.get("addcmd_flow") or {}
    if not flow:
        await query.edit_message_text("Sesi addcmd tidak ditemukan. Gunakan /addcmd ulang.")
        return
    if data.startswith("addcmd:mode:"):
        mode = data.split(":", 2)[2]
        if mode not in {"text", "photo", "both"}:
            return
        flow["mode"] = mode
        flow["step"] = "await_content"
        context.user_data["addcmd_flow"] = flow
        if mode == "text":
            await query.edit_message_text(
                "Sila titipkan text yang hendak Asmoday simpan.\n"
                "Format Telegram seperti bold, italic, link, dan code akan kuusahakan tetap terjaga."
            )
        elif mode == "photo":
            await query.edit_message_text("Sila kirim foto yang hendak Asmoday simpan.")
        else:
            await query.edit_message_text(
                "Sila kirim foto dan text.\n\n"
                "Cara paling rapi: kirim foto dengan caption.\n"
                "Boleh juga kirim text dulu, lalu foto; atau foto dulu, lalu text."
            )
        return


async def addcmd_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    flow = context.user_data.get("addcmd_flow")
    if not flow:
        return
    msg = update.effective_message
    text = (msg.text or "").strip()
    if not text:
        return
    step = flow.get("step")
    mode = flow.get("mode")

    if step == "await_content":
        if mode not in {"text", "both"}:
            await msg.reply_text("Yang diminta saat ini adalah foto. Kirim foto, atau gunakan /cancel untuk membatalkan.")
            raise ApplicationHandlerStop
        flow["text"] = msg.text or ""
        flow["text_entities"] = _entities_to_plain_list(msg.entities)
        if mode == "both" and not flow.get("photo_file_id"):
            flow["step"] = "await_photo_after_text"
            await msg.reply_text("Text telah kuterima. Kini kirim foto yang hendak dipasangkan dengannya.")
        else:
            await _addcmd_ask_command(update, context, flow)
        raise ApplicationHandlerStop

    if step == "await_text_after_photo":
        flow["text"] = msg.text or ""
        flow["text_entities"] = _entities_to_plain_list(msg.entities)
        await _addcmd_ask_command(update, context, flow)
        raise ApplicationHandlerStop

    if step == "command":
        command = _normalize_custom_command_name(text)
        if not command:
            await msg.reply_text("Command tidak sah. Gunakan huruf kecil/angka/underscore saja, maksimal 32 karakter. Contoh: mieayam")
            raise ApplicationHandlerStop
        if command in _BUILTIN_COMMAND_NAMES:
            await msg.reply_text(f"/{command} sudah dipakai fitur utama Asmoday. Pilih nama command lain.")
            raise ApplicationHandlerStop
        if not _addcmd_payload_ready(flow):
            await msg.reply_text("Isi command belum lengkap. Gunakan /addcmd ulang.")
            context.user_data.pop("addcmd_flow", None)
            raise ApplicationHandlerStop
        flow["command"] = command
        CUSTOM_COMMANDS[command] = {
            "command": command,
            "mode": flow.get("mode"),
            "text": flow.get("text") or "",
            "text_entities": flow.get("text_entities") or [],
            "photo_file_id": flow.get("photo_file_id"),
            "media_type": flow.get("media_type") or "photo",
            "created_by": flow.get("created_by"),
            "created_at": flow.get("created_at") or _now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_custom_command_data()
        context.user_data.pop("addcmd_flow", None)
        await msg.reply_text(
            _addcmd_flow_summary(CUSTOM_COMMANDS[command]) +
            "\n\nTitah telah disimpan.\n"
            f"Mulai kini, /{command} dapat dipanggil di ruang mana pun yang dihuni Asmoday."
        )
        raise ApplicationHandlerStop


async def addcmd_media_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    flow = context.user_data.get("addcmd_flow")
    if not flow:
        return
    msg = update.effective_message
    step = flow.get("step")
    mode = flow.get("mode")
    if step not in {"await_content", "await_photo_after_text"}:
        return
    if mode not in {"photo", "both"}:
        return

    if msg.photo:
        flow["photo_file_id"] = msg.photo[-1].file_id
        flow["media_type"] = "photo"
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        flow["photo_file_id"] = msg.document.file_id
        flow["media_type"] = "document"
    else:
        await msg.reply_text("Rupa yang diminta harus berupa foto atau dokumen gambar.")
        raise ApplicationHandlerStop

    caption = (msg.caption or "").strip()
    if mode == "both" and caption:
        flow["text"] = msg.caption or ""
        flow["text_entities"] = _entities_to_plain_list(msg.caption_entities)

    if mode == "both" and not (flow.get("text") or "").strip():
        flow["step"] = "await_text_after_photo"
        await msg.reply_text("Foto telah kuterima. Kini kirim text yang hendak menjadi keterangan command ini.")
    else:
        await _addcmd_ask_command(update, context, flow)
    raise ApplicationHandlerStop


async def custom_command_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    command = _extract_invoked_command(update)
    if not command:
        return
    item = CUSTOM_COMMANDS.get(command)
    if not item:
        return
    msg = update.effective_message
    text = (item.get("text") or "").strip()
    entities = _entities_from_plain_list(context, item.get("text_entities") or []) if text else None
    photo_file_id = item.get("photo_file_id")
    media_type = item.get("media_type") or "photo"

    try:
        if photo_file_id:
            if text and len(text) <= 1024:
                if media_type == "document":
                    await msg.reply_document(document=photo_file_id, caption=text, caption_entities=entities)
                else:
                    await msg.reply_photo(photo=photo_file_id, caption=text, caption_entities=entities)
            else:
                if media_type == "document":
                    await msg.reply_document(document=photo_file_id)
                else:
                    await msg.reply_photo(photo=photo_file_id)
                if text:
                    await msg.reply_text(text, entities=entities)
        elif text:
            await msg.reply_text(text, entities=entities)
        else:
            return
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        print(f"[custom_command_router] failed /{command}: {e}")
        await msg.reply_text("Custom command gagal dikirim. Coba perbarui lagi lewat /addcmd.")
    raise ApplicationHandlerStop

# =========================================================
# HELP & COMMANDS
# =========================================================
def _build_commands_for_user(user, rec=None):
    commands = [
        BotCommand("start", "Open menu"),
        BotCommand("menu", "Open menu"),
        BotCommand("registration", "Open registration menu"),
        BotCommand("registrationstaff", "Send staff application form"),
        BotCommand("renewal", "Renew current plan"),
        BotCommand("upgradevip", "Upgrade Regular plan to VIP"),
        BotCommand("myacc", "Show Lethéa ID card"),
        BotCommand("changeidcphoto", "Change IDC photo"),
            BotCommand("changepict", "Change IDC photo"),
            BotCommand("changefullname", "Change IDC full name"),
        BotCommand("mybalance", "Check Luxen balance"),
        BotCommand("mystafflog", "Check CNIT and shift log"),
        BotCommand("setnitroid", "Set NitroSeen ID"),
        BotCommand("claimcnit", "Claim CNIT payout"),
        BotCommand("changecodename", "Change your codename"),
        BotCommand("starttalk", "Start Oxana Talk"),
        BotCommand("stoptalk", "Stop Oxana Talk"),
        BotCommand("choicepoker", "Create Choice Poker room"),
        BotCommand("poker", "Create Texas Hold'em room"),
        BotCommand("thirtyone", "Create Thirty-One room"),
        BotCommand("blackjack", "Create Blackjack table"),
        BotCommand("booray", "Create Booray table"),
        BotCommand("dicepoker", "Create Dice Poker table"),
        BotCommand("baccarat", "Create Baccarat table"),
        BotCommand("judgment", "Open Judgment de Cardinale"),
        BotCommand("symphony", "Open Alluring Symphony"),
        BotCommand("chess", "Create Chess room (optional bet)"),
        BotCommand("joinchess", "Join Chess room"),
        BotCommand("chessstart", "Start Chess match"),
        BotCommand("chessclose", "Close Chess room"),
        BotCommand("letheamenu", "Show rolled Lethéa menu"),
        BotCommand("reserveresort", "Reserve resort room"),
        BotCommand("rentangel", "Browse and rent Angel"),
            BotCommand("topup", "Top up Luxen reward"),
            BotCommand("openevent", "Open internal event reward"),
            BotCommand("closeevent", "Close internal event reward"),
        BotCommand("tarot", "Open tarot reading"),
        BotCommand("cancel", "Cancel current session"),
        BotCommand("help", "Show help"),
    ]
    rec = rec or (_get_existing_account(user.id) if user else None)
    if rec and (rec.get("staff_role") or "").lower() == "angel":
        commands.extend([
            BotCommand("angeloff", "Set Angel off dates"),
            BotCommand("myangelbook", "See your Angel bookings"),
            BotCommand("angelprice", "See your Angel price"),
        ])
    if _can_manage_staff(user):
        commands.extend([
            BotCommand("addstaff", "Add staff role"),
            BotCommand("editrole", "Edit staff role"),
            BotCommand("delstaff", "Remove staff role"),
            BotCommand("ban", "Ban by account number"),
            BotCommand("unban", "Unban by account number"),
            BotCommand("inputangel", "Input Angel profile"),
            BotCommand("sendbill", "Send payment bill"),
            BotCommand("listangel", "List all Angel profiles"),
            BotCommand("myangelbook", "See Angel booking list"),
            BotCommand("openwarung", "Open Bar/Resort and DM members"),
            BotCommand("broadcast", "Broadcast to started users"),
            BotCommand("openbar", "Open bar and DM active members"),
            BotCommand("openresort", "Open resort and DM VIP members"),
            BotCommand("opencurated", "Open curated dining"),
            BotCommand("listcurated", "List curated dining"),
            BotCommand("closecurated", "Close curated dining"),
            BotCommand("delcurated", "Delete curated dining"),
            BotCommand("addcmd", "Add custom command"),
            BotCommand("listcmd", "List custom commands"),
            BotCommand("delcmd", "Delete custom command by number"),
            BotCommand("closebar", "Close bar announcement"),
            BotCommand("tagall", "Tag all started users in group"),
            BotCommand("tagmember", "Tag members in group"),
            BotCommand("tagvip", "Tag active VIP members in group"),
            BotCommand("tagregular", "Tag active Regular members in group"),
            BotCommand("tagstaff", "Tag staff in group"),
            BotCommand("tagcurrathor", "Tag Currathors in group"),
            BotCommand("tagserver", "Tag Servers in group"),
            BotCommand("tagdj", "Tag DJs in group"),
            BotCommand("tagbartender", "Tag Bartenders in group"),
            BotCommand("tagangel", "Tag Angels in group"),
            BotCommand("tagstripdancer", "Tag Strip Dancers in group"),
            BotCommand("tagchef", "Tag Chefs in group"),
            BotCommand("tagperformer", "Tag Performers in group"),
            BotCommand("openshift", "Open staff shift attendance"),
            BotCommand("closeshift", "Close shift and review attendance"),
            BotCommand("addcnit", "Add CNIT to account"),
            BotCommand("dellcnit", "Reduce CNIT from account"),
            BotCommand("cnitbook", "CNIT payout bookkeeping"),
            BotCommand("botfee", "Monthly bot fee split"),
            BotCommand("mybill", "My monthly Currathor bill"),
            BotCommand("paymentbill", "Confirm Currathor bill payment"),
            BotCommand("listroom", "List all saved rooms"),
            BotCommand("delroom", "Delete room by number"),
        ])
    if _can_manage_menu(user):
        commands.extend([
            BotCommand("createmenu", "Create a new menu item"),
            BotCommand("rollmenu", "Roll Lethéa menu"),
            BotCommand("listmenu", "List all saved menu items"),
            BotCommand("infomenu", "Show ingredients and how to make"),
            BotCommand("delmenu", "Delete menu by number"),
            BotCommand("addpriceall", "Increase all menu prices"),
            BotCommand("addprice", "Increase one menu price"),
        ])
    if _is_admin(user):
        commands.extend([
            BotCommand("addsaldo", "Add account balance"),
            BotCommand("minsaldo", "Reduce account balance"),
            BotCommand("listacc", "List all accounts"),
            BotCommand("acc", "Approve pending request"),
            BotCommand("reject", "Reject pending request"),
            BotCommand("confirmcnit", "Confirm CNIT payout"),
            BotCommand("rejectcnit", "Reject CNIT payout"),
        ])
    if _is_owner(user):
        commands.extend([
            BotCommand("addadmin", "Add admin"),
            BotCommand("deladmin", "Remove admin"),
            BotCommand("listadmin", "List admins"),
            BotCommand("delacc", "Delete account"),
        ])
    return commands


def _help_screen_text(user):
    extra = []
    if _can_manage_menu(user):
        extra.append("Menu Staff: /createmenu, /rollmenu, /listmenu, /infomenu, /delmenu, /addpriceall, /addprice")
    if _can_manage_staff(user):
        extra.append("Staff Tools: /addstaff, /editrole, /delstaff, /inputangel, /listangel, /myangelbook, /sendbill, /addcnit, /dellcnit, /cnitbook, /botfee, /mybill, /paymentbill, /openwarung, /broadcast, /openbar, /openresort, /opencurated, /listcurated, /closecurated, /delcurated, /addcmd, /listcmd, /delcmd, /closebar, /openshift, /closeshift")
    extra.append("Staff Log: /mystafflog, /setnitroid, /claimcnit <jumlah>")
    if _is_admin(user):
        extra.append("Admin Tools: /addsaldo, /minsaldo, /listacc, /acc, /reject, /confirmcnit, /rejectcnit")
    if _is_owner(user):
        extra.append("Owner Tools: /addadmin, /deladmin, /listadmin, /delacc")
    body = "\n".join(extra)
    if body:
        body = "\n\n" + body
    return "𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀: 𝐇𝐄𝐋𝐏\n\nQuick commands:\n/start, /menu, /registration, /renewal, /upgradevip, /myacc, /changepict, /mybalance, /mystafflog, /setnitroid, /claimcnit, /choicepoker, /poker, /thirtyone, /blackjack, /booray, /dicepoker, /letheamenu, /rentangel, /tarot, /starttalk, /stoptalk, /cancel" + body


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    user = update.effective_user
    text = (
        "Perintah yang tersedia:\n\n"
        "User:\n"
        "• /start\n• /menu\n• /registration\n• /registrationstaff\n• /renewal\n• /upgradevip\n• /myacc\n• /changepict\n• /mybalance\n• /mystafflog\n• /setnitroid <id>\n• /claimcnit\n• /choicepoker\n• /letheamenu\n• /rentangel\n• /starttalk\n• /stoptalk\n• /cancel\n• /help\n"
    )
    rec = _get_existing_account(user.id)
    if rec and (rec.get("staff_role") or "").lower() == "angel":
        text += "\nAngel:\n• /angelon\n• /angeloff\n• /myangelbook\n• /angelprice\n"
    if _can_manage_menu(user):
        text += "\nMenu Management:\n• /createmenu\n• /rollmenu\n• /listmenu\n• /infomenu <nomor_menu>\n• /delmenu <nomor_menu>\n• /addpriceall <nominal>\n• /addprice <nomor_menu> <nominal>\n"
    if _can_manage_staff(user):
        text += "\nStaff Management:\n• /addstaff  (reply ke pesan user target)\n• /editrole <acc_no>\n• /delstaff <acc_no>\n• /ban <acc_no>\n• /unban <acc_no>\n• /inputangel\n• /listangel\n• /myangelbook [acc_no]\n• /sendbill <acc_no> <nominal>\n• /addcnit <acc_no> <jumlah>\n• /dellcnit <acc_no> <jumlah>\n• /cnitbook [YYYY-MM]\n• /botfee [YYYY-MM]\n• /openbar [link]\n• /closebar\n• /openshift\n• /closeshift\n"
    if _is_admin(user):
        text += "\nAdmin:\n• /addsaldo <acc_no> <jumlah>\n• /minsaldo <acc_no> <jumlah>\n• /listacc\n• /acc\n• /reject\n• /confirmcnit <acc_no>\n• /rejectcnit <acc_no>\n"
    if _is_owner(user):
        text += "\nOwner:\n• /addadmin <acc_no>\n• /deladmin <acc_no>\n• /listadmin\n• /delacc <acc_no>\n"
    await update.message.reply_text(text)


async def post_init(application):
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "Open menu"),
            BotCommand("menu", "Open menu"),
            BotCommand("registration", "Open registration menu"),
            BotCommand("registrationstaff", "Send staff application form"),
            BotCommand("oprecstaff", "Open staff interview schedule"),
            BotCommand("renewal", "Renew current plan"),
            BotCommand("upgradevip", "Upgrade Regular plan to VIP"),
            BotCommand("myacc", "Show Lethéa ID card"),
            BotCommand("changeidcphoto", "Change IDC photo"),
            BotCommand("changepict", "Change IDC photo"),
            BotCommand("changefullname", "Change IDC full name"),
            BotCommand("mybalance", "Check Luxen balance"),
            BotCommand("mystafflog", "Check CNIT and shift log"),
            BotCommand("setnitroid", "Set NitroSeen ID"),
            BotCommand("claimcnit", "Claim CNIT payout"),
            BotCommand("changecodename", "Change your codename"),
            BotCommand("cancel", "Cancel current session"),
            BotCommand("help", "Show help"),
            BotCommand("choicepoker", "Create Choice Poker room"),
            BotCommand("poker", "Create Texas Hold'em room"),
            BotCommand("thirtyone", "Create Thirty-One room"),
            BotCommand("blackjack", "Create Blackjack table"),
            BotCommand("booray", "Create Booray table"),
            BotCommand("dicepoker", "Create Dice Poker table"),
            BotCommand("baccarat", "Create Baccarat table"),
            BotCommand("judgment", "Open Judgment de Cardinale"),
            BotCommand("symphony", "Open Alluring Symphony"),
            BotCommand("chess", "Create Chess room (optional bet)"),
            BotCommand("joinchess", "Join Chess room"),
            BotCommand("chessstart", "Start Chess match"),
            BotCommand("chessclose", "Close Chess room"),
            BotCommand("letheamenu", "Show rolled Lethéa menu"),
            BotCommand("openwarung", "Open Bar/Resort and DM members"),
            BotCommand("broadcast", "Broadcast to started users"),
            BotCommand("openbar", "Open bar and DM active members"),
            BotCommand("openresort", "Open resort and DM VIP members"),
            BotCommand("opencurated", "Open curated dining"),
            BotCommand("listcurated", "List curated dining"),
            BotCommand("closecurated", "Close curated dining"),
            BotCommand("delcurated", "Delete curated dining"),
            BotCommand("addcmd", "Add custom command"),
            BotCommand("listcmd", "List custom commands"),
            BotCommand("delcmd", "Delete custom command by number"),
            BotCommand("rentangel", "Browse and rent Angel"),
            BotCommand("tagall", "Tag all started users in group"),
            BotCommand("tagmember", "Tag members in group"),
            BotCommand("tagvip", "Tag active VIP members in group"),
            BotCommand("tagregular", "Tag active Regular members in group"),
            BotCommand("tagstaff", "Tag staff in group"),
            BotCommand("tagcurrathor", "Tag Currathors in group"),
            BotCommand("tagserver", "Tag Servers in group"),
            BotCommand("tagdj", "Tag DJs in group"),
            BotCommand("tagbartender", "Tag Bartenders in group"),
            BotCommand("tagangel", "Tag Angels in group"),
            BotCommand("tagstripdancer", "Tag Strip Dancers in group"),
            BotCommand("tagchef", "Tag Chefs in group"),
            BotCommand("tagperformer", "Tag Performers in group"),
            BotCommand("topup", "Top up Luxen reward"),
            BotCommand("openevent", "Open internal event reward"),
            BotCommand("closeevent", "Close internal event reward"),
            BotCommand("tarot", "Tarot reading"),
            BotCommand("starttalk", "Talk to Asmoday"),
            BotCommand("stoptalk", "Stop talking to Asmoday"),
        ], scope=BotCommandScopeDefault())
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        await application.bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
    except Exception as e:
        print(f"[post_init] error: {e}")

# =========================================================
# TAROT CARD
# =========================================================
TAROT_CARDS = [
    {"name": "The Fool", "meaning": "awal baru, keberanian, langkah spontan", "advice": "Berani mulai, tapi jangan buta arah."},
    {"name": "The Magician", "meaning": "inisiatif, daya tarik, manifestasi", "advice": "Pakai apa yang sudah kamu punya dengan sadar."},
    {"name": "The High Priestess", "meaning": "intuisi, hal tersembunyi, perasaan dalam", "advice": "Jangan abaikan firasatmu."},
    {"name": "The Empress", "meaning": "kasih, perhatian, pertumbuhan", "advice": "Rawat yang kamu inginkan agar berkembang."},
    {"name": "The Emperor", "meaning": "kendali, batas, kepastian", "advice": "Tegaskan batas dan niatmu."},
    {"name": "The Lovers", "meaning": "ketertarikan, pilihan hati, koneksi", "advice": "Jujur pada apa yang benar-benar kamu rasa."},
    {"name": "The Chariot", "meaning": "gerak maju, tekad, kemenangan", "advice": "Kalau sudah yakin, maju terus."},
    {"name": "The Hermit", "meaning": "jarak, refleksi, mencari arah", "advice": "Tidak semua jawaban datang sekarang."},
    {"name": "Wheel of Fortune", "meaning": "perubahan, timing, perputaran nasib", "advice": "Sabar pada waktu yang sedang bergerak."},
    {"name": "The Star", "meaning": "harapan, penyembuhan, optimisme", "advice": "Tetap percaya pada arah baik yang datang."},
]


def _draw_tarot_cards(n: int):
    import random
    cards = TAROT_CARDS[:]
    random.shuffle(cards)
    return cards[:max(1, n)]


def _format_tarot_card_line(card: dict) -> str:
    return f"🔮 {card['name']}\nMakna : {card['meaning']}\nAdvice : {card['advice']}"


def _build_one_card_reading(question: str, card: dict) -> str:
    return (
        "𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀 𝐓𝐀𝐑𝐎𝐓\n\n"
        f"Pertanyaan : {question}\n\n"
        + _format_tarot_card_line(card)
    )


def _build_three_card_reading(question: str, cards: list) -> str:
    labels = ["Past", "Present", "Future"]
    lines = ["𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀 𝐓𝐀𝐑𝐎𝐓", "", f"Pertanyaan : {question}", ""]
    for label, card in zip(labels, cards):
        lines.append(f"{label} — {card['name']}")
        lines.append(f"Makna : {card['meaning']}")
        lines.append(f"Advice : {card['advice']}")
        lines.append("")
    return "\n".join(lines).strip()


def _build_yes_no_reading(question: str, card: dict) -> str:
    positive = {"The Sun", "The Star", "The Lovers", "The Magician", "The Empress", "The Chariot", "Wheel of Fortune"}
    answer = "Yes" if card['name'] in positive else "Not yet"
    return (
        "𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀 𝐓𝐀𝐑𝐎𝐓\n\n"
        f"Pertanyaan : {question}\n"
        f"Jawaban : {answer}\n\n"
        + _format_tarot_card_line(card)
    )


def _tarot_mode_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Card Reading", callback_data="tarot:mode:one")],
        [InlineKeyboardButton("3 Card Spread", callback_data="tarot:mode:three")],
        [InlineKeyboardButton("Yes / No Tarot", callback_data="tarot:mode:yesno")],
        [InlineKeyboardButton("❌ Cancel", callback_data="tarot:cancel:0")],
    ])


async def tarot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    context.user_data.pop("tarot_flow", None)
    await update.effective_message.reply_text(
        "𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀 𝐓𝐀𝐑𝐎𝐓\n\nPilih mode pembacaan tarot yang kamu inginkan.",
        reply_markup=_tarot_mode_keyboard(),
    )


async def tarot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    kind = parts[1]
    action = parts[2]
    if kind == "cancel":
        context.user_data.pop("tarot_flow", None)
        try:
            await query.edit_message_text("Pembacaan tarot dibatalkan.")
        except Exception:
            pass
        return
    if kind != "mode":
        return
    mode_map = {
        "one": ("one", "Kirim pertanyaanmu untuk 1 card reading."),
        "three": ("three", "Kirim pertanyaanmu untuk 3 card spread."),
        "yesno": ("yesno", "Kirim pertanyaan yes/no kamu."),
    }
    if action not in mode_map:
        return
    mode_key, prompt = mode_map[action]
    context.user_data["tarot_flow"] = {
        "mode": mode_key,
        "chat_id": query.message.chat_id,
        "prompt_message_id": query.message.message_id,
    }
    await query.edit_message_text(
        f"𖠷 ╱ 𝐎𝐗𝐀𝐍𝐀 𝐓𝐀𝐑𝐎𝐓\n\n{prompt}\n\nContoh: kira-kira kapan ya aku akan menemukan pasangan?\n\nDi grup, balas prompt ini atau kirim pertanyaan di chat yang sama."
    )


async def tarot_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("tarot_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    question = (msg.text or "").strip()
    if not question:
        return
    if flow.get("chat_id") and msg.chat_id != flow.get("chat_id"):
        return
    if update.effective_chat.type in ("group", "supergroup"):
        replied = getattr(msg, "reply_to_message", None)
        prompt_message_id = flow.get("prompt_message_id")
        if replied and prompt_message_id and replied.message_id != prompt_message_id:
            return
    mode = flow.get("mode")
    if mode == "one":
        text_out = _build_one_card_reading(question, _draw_tarot_cards(1)[0])
    elif mode == "three":
        text_out = _build_three_card_reading(question, _draw_tarot_cards(3))
    elif mode == "yesno":
        text_out = _build_yes_no_reading(question, _draw_tarot_cards(1)[0])
    else:
        return
    context.user_data.pop("tarot_flow", None)
    await msg.reply_text(text_out)


def _angel_off_calendar_text(flow: dict) -> str:
    year = int(flow.get("year"))
    month = int(flow.get("month"))
    title = datetime(year, month, 1).strftime("%B %Y")
    profile = _ensure_angel_profile(int(flow.get("angel_uid", 0) or 0))
    selected = sorted([d for d in profile.get("off_dates", []) if d.startswith(f"{year:04d}-{month:02d}-")])
    selected_text = "\n".join(f"• {d}" for d in selected[:10]) or "Belum ada off date di bulan ini."
    return (
        "🗓️ ANGEL OFF SCHEDULE\n\n"
        f"Month : {title}\n"
        "Tap tanggal untuk toggle off / available.\n"
        "Tanggal bertanda ❌ sedang off.\n\n"
        f"Daftar off date bulan ini:\n{selected_text}"
    )


def _angel_off_calendar_keyboard(flow: dict):
    import calendar
    year = int(flow.get("year"))
    month = int(flow.get("month"))
    cal = calendar.Calendar(firstweekday=0)
    profile = _ensure_angel_profile(int(flow.get("angel_uid", 0) or 0))
    today = _now().strftime("%Y-%m-%d")
    rows = [[
        InlineKeyboardButton("Mo", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("Tu", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("We", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("Th", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("Fr", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("Sa", callback_data="angeloffcal:noop"),
        InlineKeyboardButton("Su", callback_data="angeloffcal:noop"),
    ]]
    off_dates = set(profile.get("off_dates", []) or [])
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="angeloffcal:noop"))
                continue
            date_text = f"{year:04d}-{month:02d}-{day:02d}"
            if date_text < today:
                row.append(InlineKeyboardButton(f"·{day}", callback_data="angeloffcal:noop"))
            elif date_text in off_dates:
                row.append(InlineKeyboardButton(f"❌{day}", callback_data=f"angeloffcal:toggle:{date_text}"))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=f"angeloffcal:toggle:{date_text}"))
        rows.append(row)
    prev_y, prev_m = _angel_calendar_month_shift(year, month, -1)
    next_y, next_m = _angel_calendar_month_shift(year, month, 1)
    rows.append([
        InlineKeyboardButton("◀️", callback_data=f"angeloffcal:nav:{prev_y}:{prev_m}"),
        InlineKeyboardButton("✅ Selesai", callback_data="angeloffcal:done:0"),
        InlineKeyboardButton("▶️", callback_data=f"angeloffcal:nav:{next_y}:{next_m}"),
    ])
    return InlineKeyboardMarkup(rows)


async def angel_off_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    flow = context.user_data.get("angel_off_flow")
    if not flow:
        return
    if int(flow.get("angel_uid", 0) or 0) != int(query.from_user.id):
        await query.answer("Panel ini bukan milikmu.", show_alert=True)
        return
    parts = (query.data or "").split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    if action == "noop":
        return
    if action == "done":
        context.user_data.pop("angel_off_flow", None)
        try:
            await query.edit_message_text("✅ Off date Angel berhasil diperbarui.")
        except Exception:
            pass
        save_angel_data()
        return
    if action == "nav" and len(parts) >= 4:
        flow["year"] = int(parts[2])
        flow["month"] = int(parts[3])
    elif action == "toggle" and len(parts) >= 3:
        date_text = parts[2]
        valid, dt = _is_valid_booking_date(date_text)
        if not valid or date_text < _now().strftime("%Y-%m-%d"):
            await query.answer("Tanggal tidak valid.", show_alert=True)
            return
        profile = _ensure_angel_profile(int(flow.get("angel_uid", 0) or 0))
        off_dates = set(profile.get("off_dates", []) or [])
        if _angel_has_booking(profile, date_text):
            await query.answer("Tanggal itu sudah ada booking confirmed.", show_alert=True)
            return
        if date_text in off_dates:
            off_dates.remove(date_text)
            await query.answer("Tanggal off dihapus.")
        else:
            off_dates.add(date_text)
            await query.answer("Tanggal ditandai off.")
        profile["off_dates"] = sorted(off_dates)
        save_angel_data()
        flow["year"] = dt.year
        flow["month"] = dt.month
    await query.edit_message_text(
        _angel_off_calendar_text(flow),
        reply_markup=_angel_off_calendar_keyboard(flow),
    )


# =========================================================
# Resort Reservation
# =========================================================

def _date_only(date_text: str):
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except Exception:
        return None


def _resort_booking_sequence_for_today() -> int:
    today_key = _now().strftime("%Y-%m-%d")
    seq = 0
    for booking in ROOM_BOOKINGS:
        created_at = str(booking.get("created_at") or "")
        if created_at[:10] == today_key:
            seq += 1
    return seq + 1


def _resort_booking_id() -> str:
    now = _now()
    return f"RSV{now.strftime('%d%m')}-{_resort_booking_sequence_for_today():02d}"



RESORT_BLOCKING_STATUSES = {"waiting_payment", "pending_admin", "confirmed", "link_sent"}


def _resort_booking_status_occupies(status: str) -> bool:
    return (status or "") in RESORT_BLOCKING_STATUSES


def _ranges_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    a1 = _date_only(start_a)
    a2 = _date_only(end_a)
    b1 = _date_only(start_b)
    b2 = _date_only(end_b)
    if not all([a1, a2, b1, b2]):
        return False
    return a1 < b2 and b1 < a2


def _resort_room_available(room_no: int, checkin: str, checkout: str, exclude_booking_id: str = None) -> bool:
    for booking in ROOM_BOOKINGS:
        if int(booking.get("room_no", 0) or 0) != int(room_no):
            continue
        if exclude_booking_id and booking.get("booking_id") == exclude_booking_id:
            continue
        if not _resort_booking_status_occupies(booking.get("status")):
            continue
        if _ranges_overlap(checkin, checkout, booking.get("checkin"), booking.get("checkout")):
            return False
    return True


def _resort_available_rooms(checkin: str, checkout: str):
    out = []
    for item in ROOM_ITEMS:
        room_no = int(item.get("no", 0) or 0)
        if _resort_room_available(room_no, checkin, checkout):
            out.append(item)
    out.sort(key=lambda x: int(x.get("no", 0) or 0))
    return out


def _angel_has_blocking_booking(profile: dict, booking_date: str, exclude_resort_booking_id: str = None) -> bool:
    for booking in profile.get("bookings", []):
        if exclude_resort_booking_id and booking.get("resort_booking_id") == exclude_resort_booking_id:
            continue
        if booking.get("date") == booking_date and booking.get("status") in RESORT_BLOCKING_STATUSES:
            return True
    return False


def _resort_available_angels(booking_date: str):
    result = []
    for uid, rec in _angel_staff_records():
        profile = _ensure_angel_profile(uid)
        if _angel_is_off_date(profile, booking_date):
            continue
        if _angel_has_blocking_booking(profile, booking_date):
            continue
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        result.append({
            "uid": uid,
            "rec": rec,
            "profile": profile,
            "popularity": popularity,
            "price": int(price),
        })
    return result


def _resort_stay_dates(checkin: str, checkout: str):
    start = _date_only(checkin)
    end = _date_only(checkout)
    if not start or not end or end <= start:
        return []
    out = []
    cur = start
    while cur < end:
        out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out


def _resort_angel_available_on_date(angel_uid: int, booking_date: str, exclude_resort_booking_id: str = None) -> bool:
    profile = _ensure_angel_profile(int(angel_uid))
    if _angel_is_off_date(profile, booking_date):
        return False
    if _angel_has_blocking_booking(profile, booking_date, exclude_resort_booking_id=exclude_resort_booking_id):
        return False
    return True


def _resort_mark_angel_booking_status(booking: dict, status: str, bill_id: str = None):
    if not booking or not booking.get("angel_uid"):
        return

    profile = _ensure_angel_profile(int(booking.get("angel_uid")))
    dates = list(booking.get("angel_dates") or [])
    if not dates and booking.get("checkin"):
        dates = [booking.get("checkin")]

    for date_text in dates:
        existing = next(
            (x for x in profile.get("bookings", [])
             if x.get("resort_booking_id") == booking.get("booking_id") and x.get("date") == date_text),
            None,
        )
        if existing:
            existing["status"] = status
            if bill_id:
                existing["bill_id"] = bill_id
        else:
            profile.setdefault("bookings", []).append({
                "date": date_text,
                "guest_uid": int(booking.get("guest_uid", 0) or 0),
                "guest_acc_no": booking.get("guest_acc_no"),
                "guest_name": booking.get("guest_name"),
                "status": status,
                "bill_id": bill_id,
                "resort_booking_id": booking.get("booking_id"),
                "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    save_angel_data()


def _resort_available_angels_for_range(checkin: str, checkout: str):
    stay_dates = _resort_stay_dates(checkin, checkout)
    result = []
    for uid, rec in _angel_staff_records():
        profile = _ensure_angel_profile(uid)
        available_dates = [d for d in stay_dates if _resort_angel_available_on_date(uid, d)]
        if not available_dates:
            continue
        popularity, price = _angel_popularity_info(int(profile.get("total_orders", 0) or 0))
        result.append({
            "uid": uid,
            "rec": rec,
            "profile": profile,
            "popularity": popularity,
            "price": int(price),
            "available_dates": available_dates,
        })
    return result


def _resort_angel_date_text(flow: dict) -> str:
    selected = list(flow.get("angel_dates") or [])
    unit_price = int(flow.get("angel_unit_price", flow.get("angel_price", 0)) or 0)
    total = unit_price * len(selected)
    lines = [
        "𖠷╱ .. LETHÉA RESORT: RENT ANGEL",
        "",
        f"Angel : {flow.get('angel_name', '-')}",
        f"Harga : {_normalize_price_text(unit_price)} / hari",
        f"Rentang resort : {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
        "",
        "Pilih tanggal Angel akan menemani selama rentang resort.",
        "Tanggal yang bertanda ☑ sudah dipilih; × berarti Angel tidak tersedia.",
        "",
        "Tanggal dipilih : " + (", ".join(selected) if selected else "-"),
        f"Subtotal Angel : {_normalize_price_text(total)} ✦𝕷",
    ]
    return "\n".join(lines)


def _resort_angel_date_keyboard(flow: dict):
    rows = []
    selected = set(flow.get("angel_dates") or [])
    angel_uid = flow.get("angel_uid")
    for date_text in _resort_stay_dates(flow.get("checkin"), flow.get("checkout")):
        if angel_uid and _resort_angel_available_on_date(int(angel_uid), date_text):
            mark = "☑" if date_text in selected else "□"
            rows.append([InlineKeyboardButton(f"{mark} {date_text}", callback_data=f"resortreserve:angeldate:{date_text}")])
        else:
            rows.append([InlineKeyboardButton(f"× {date_text}", callback_data="resortreserve:noop:0")])
    if selected:
        rows.append([InlineKeyboardButton("✅ Selesai pilih tanggal Angel", callback_data="resortreserve:confirmangeldates:0")])
    rows.append([InlineKeyboardButton("← Pilih Angel lain", callback_data="resortreserve:backangels:0")])
    rows.append([InlineKeyboardButton("Lewati Angel", callback_data="resortreserve:skipangel:0")])
    rows.append([InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")])
    return InlineKeyboardMarkup(rows)


def _resort_stay_nights(checkin: str, checkout: str) -> int:
    d1 = _date_only(checkin)
    d2 = _date_only(checkout)
    if not d1 or not d2:
        return 0
    return max(0, (d2 - d1).days)


def _resort_date_range_label(checkin: str, checkout: str) -> str:
    nights = _resort_stay_nights(checkin, checkout)
    return f"{checkin} - {checkout} | ({nights} malam)"


def _resort_payment_total(flow: dict) -> int:
    room_total = int(flow.get("room_price", 0) or 0) * int(flow.get("nights", 0) or 0)
    angel_total = int(flow.get("angel_price", 0) or 0)
    return room_total + angel_total


def _resort_recap_text(flow: dict) -> str:
    guest_info = flow.get("guest_info") or "-"
    notes = flow.get("notes") or "-"
    angel_name = flow.get("angel_name") or "Tidak"
    angel_dates = list(flow.get("angel_dates") or [])
    angel_unit_price = int(flow.get("angel_unit_price", flow.get("angel_price", 0)) or 0)
    room_total = int(flow.get("room_price", 0) or 0) * int(flow.get("nights", 0) or 0)
    angel_total = int(flow.get("angel_price", 0) or 0)
    total = room_total + angel_total
    lines = [
        "𖠷 ╱ LETHÉA RESORT: RESERVATION RECAP",
        "",
        f"Tanggal : {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
        f"Room : {flow.get('room_name', '-')} | {_normalize_price_text(flow.get('room_price', 0))} / malam",
        f"Datang : {guest_info}",
        f"Angel : {angel_name}",
    ]
    if flow.get("angel_name"):
        lines.append(f"Tanggal Angel : {', '.join(angel_dates) if angel_dates else '-'}")
        lines.append(f"Harga Angel : {_normalize_price_text(angel_unit_price)} / hari × {len(angel_dates)} hari = {_normalize_price_text(angel_total)}")
    lines.extend([
        f"Notes Admin : {notes}",
        "",
        f"Subtotal Room : {_normalize_price_text(room_total)}",
        f"Subtotal Angel : {_normalize_price_text(angel_total)}",
        f"Total Payment : {_normalize_price_text(total)} ✦𝕷",
    ])
    return "\n".join(lines)


def _resort_summary_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sudah selesai", callback_data="resortreserve:finish:0")],
        [InlineKeyboardButton("📝 Tambahkan notes untuk Currathor", callback_data="resortreserve:addnote:0")],
        [InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")],
    ])


def _resort_room_keyboard(rooms):
    rows = []
    for item in rooms:
        rows.append([InlineKeyboardButton(f"{item.get('name')} | {_normalize_price_text(item.get('price', 0))}/mlm", callback_data=f"resortreserve:room:{int(item.get('no', 0) or 0)}")])
    rows.append([InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")])
    return InlineKeyboardMarkup(rows)


def _resort_yes_no_keyboard(yes_data: str, no_data: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Iya", callback_data=yes_data), InlineKeyboardButton("Tidak", callback_data=no_data)],
        [InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")],
    ])


def _resort_calendar_text(flow: dict, year: int, month: int) -> str:
    start_date = flow.get("checkin")
    end_date = flow.get("checkout")
    nights = int(flow.get("nights", 0) or 0)

    if not start_date:
        mode = "Tetapkan hari tibamu, sebelum lembar berikutnya tersibak."
    elif not end_date:
        mode = "Hari tiba telah terpatri, kini tentukan hari kamu akan beranjak."
    else:
        mode = f"Range terpilih: {_resort_date_range_label(start_date, end_date)}"

    lines = [
        "𖠷╱ .. LETHÉA RESORT: RESEVATION FORM",
        "",
        mode,
        "",
        f"› … Rona Waktu : {year:04d}-{month:02d}",
        f"› … 𝘊𝘩𝘦𝘤𝘬-𝘐𝘯: {start_date or '-'}",
        f"› … 𝘊𝘩𝘦𝘤𝘬-𝘰𝘶𝘵: {end_date or '-'}",
        f"› … Lama Singgah : {nights if end_date else 0} malam",
        "",
        "﴾ … | Pedoman:",
        "→ Pilih satu tanggal sebagai titik mula yang terpatri",
        "→ Lanjutkan pada tanggal sesudahnya sebagai akhir yang dituju",
        "→ Bila waktu yang lebih awal disentuh, ia akan terpatri sebagai titik mula",
        "",
        "﴾ … | Penanda Kala:",
        "→ CI = 𝘊𝘩𝘦𝘤𝘬-𝘐𝘯",
        "→ CO = 𝘊𝘩𝘦𝘤𝘬-𝘰𝘶𝘵",
        "→ • = Sela waktu yang teranyam di antaranya",
    ]
    return "\n".join(lines)


def _resort_date_in_selected_range(date_text: str, start_date: str, end_date: str) -> bool:
    if not start_date or not end_date:
        return False
    d = _date_only(date_text)
    s = _date_only(start_date)
    e = _date_only(end_date)
    if not d or not s or not e:
        return False
    return s < d < e


def _resort_calendar_keyboard(flow: dict, year: int, month: int):
    import calendar
    cal = calendar.Calendar(firstweekday=0)
    today = _now().strftime("%Y-%m-%d")
    rows = [
        [
            InlineKeyboardButton("𝗖𝗜 : 𝘐𝘯", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("𝗖𝗢 : 𝘖𝘶𝘵", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("• = 𝘙𝘢𝘯𝘨𝘦", callback_data="resortreserve:noop:0"),
        ],
        [
            InlineKeyboardButton("Mo", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("Tu", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("We", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("Th", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("Fr", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("Sa", callback_data="resortreserve:noop:0"),
            InlineKeyboardButton("Su", callback_data="resortreserve:noop:0"),
        ]
    ]
    start_date = flow.get("checkin")
    end_date = flow.get("checkout")
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="resortreserve:noop:0"))
                continue
            date_text = f"{year:04d}-{month:02d}-{day:02d}"
            if date_text < today:
                label = f"·{day}"
                cb = "resortreserve:noop:0"
            else:
                label = str(day)
                if start_date == date_text:
                    label = f"CI {day}"
                elif end_date == date_text:
                    label = f"CO {day}"
                elif _resort_date_in_selected_range(date_text, start_date, end_date):
                    label = f"•{day}"
                cb = f"resortreserve:pick:{date_text}"
            row.append(InlineKeyboardButton(label, callback_data=cb))
        rows.append(row)
    prev_y, prev_m = _angel_calendar_month_shift(year, month, -1)
    next_y, next_m = _angel_calendar_month_shift(year, month, 1)
    rows.append([
        InlineKeyboardButton("◀️", callback_data=f"resortreserve:nav:{prev_y}:{prev_m}"),
        InlineKeyboardButton("Reset", callback_data="resortreserve:resetdates:0"),
        InlineKeyboardButton("▶️", callback_data=f"resortreserve:nav:{next_y}:{next_m}"),
    ])
    rows.append([InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")])
    return InlineKeyboardMarkup(rows)


async def reserver_resort_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Tempuh /reserveresort dalam ruang privat bersama Asmoday")
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec:
        await update.message.reply_text("Kau perlu memiliki ikatan terlebih dahulu sebelum menautkan reservasi.")
        return
    _refresh_membership_status(rec)
    is_vip = (
        rec.get("account_type") == "member"
        and rec.get("membership_type") == "VIP"
        and rec.get("membership_status") == "active"
    )

    is_currathor = (
        rec.get("account_type") == "staff"
        and (rec.get("staff_role") or "").lower() == "currathor"
    )
    is_owner_access = _is_owner(update.effective_user)
    if not (is_owner_access or is_vip or is_currathor):
        await update.message.reply_text("Reservasi resort terbatas pada mereka berstatus VIP yang masih aktif.")
        return
    if not ROOM_ITEMS:
        await update.message.reply_text("Tiada kamar yang tersedia untuk saat ini.")
        return
    now = _now()
    flow = {
        "step": "pick_dates",
        "checkin": None,
        "checkout": None,
        "calendar_year": now.year,
        "calendar_month": now.month,
        "room_no": None,
        "room_name": None,
        "room_price": 0,
        "room_link": None,
        "guest_info": None,
        "angel_uid": None,
        "angel_name": None,
        "angel_unit_price": 0,
        "angel_price": 0,
        "angel_dates": [],
        "notes": None,
        "nights": 0,
    }
    sent = await update.message.reply_text(
        _resort_calendar_text(flow, now.year, now.month),
        reply_markup=_resort_calendar_keyboard(flow, now.year, now.month),
    )
    flow["panel_chat_id"] = sent.chat_id
    flow["panel_message_id"] = sent.message_id
    context.user_data["resort_reservation_flow"] = flow


async def _resort_refresh_panel(context, flow: dict, text_out: str = None, reply_markup=None):
    final_text = text_out or _resort_calendar_text(flow, flow.get("calendar_year"), flow.get("calendar_month"))
    final_markup = reply_markup if reply_markup is not None else _resort_calendar_keyboard(flow, flow.get("calendar_year"), flow.get("calendar_month"))
    try:
        await context.bot.edit_message_text(
            chat_id=flow.get("panel_chat_id"),
            message_id=flow.get("panel_message_id"),
            text=final_text,
            reply_markup=final_markup,
        )
        return
    except Exception as e:
        print(f"[_resort_refresh_panel] edit error: {e}")

    try:
        sent = await context.bot.send_message(
            chat_id=flow.get("panel_chat_id"),
            text=final_text,
            reply_markup=final_markup,
        )
        flow["panel_chat_id"] = sent.chat_id
        flow["panel_message_id"] = sent.message_id
    except Exception as e:
        print(f"[_resort_refresh_panel] send fallback error: {e}")


async def resort_reservation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    flow = context.user_data.get("resort_reservation_flow")
    if not flow:
        await query.answer("Sesi reserve tidak ditemukan.", show_alert=True)
        return
    parts = (query.data or "").split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    if action == "noop":
        return
    if action == "cancel":
        try:
            await context.bot.delete_message(
                chat_id=flow.get("panel_chat_id"),
                message_id=flow.get("panel_message_id"),
            )
        except Exception as e:
            print(f"[resort cancel delete panel] error: {e}")

        context.user_data.pop("resort_reservation_flow", None)
        await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Jejak reservasi telah diluruhkan.",
        )
        return
    if action == "resetdates":
        flow["checkin"] = None
        flow["checkout"] = None
        await _resort_refresh_panel(context, flow)
        return
    if action == "nav" and len(parts) >= 4:
        flow["calendar_year"] = int(parts[2])
        flow["calendar_month"] = int(parts[3])
        await _resort_refresh_panel(context, flow)
        return
    if action == "pick" and len(parts) >= 3:
        date_text = parts[2]
        valid, dt = _is_valid_booking_date(date_text)
        if not valid or date_text < _now().strftime("%Y-%m-%d"):
            await query.answer("Tanggal tidak valid.", show_alert=True)
            return
        if not flow.get("checkin") or (flow.get("checkin") and flow.get("checkout")):
            flow["checkin"] = date_text
            flow["checkout"] = None
            flow["calendar_year"] = dt.year
            flow["calendar_month"] = dt.month
            await _resort_refresh_panel(context, flow)
            await query.answer("Tiba telah terpatri, kini tetapkan tanggal saat beranjak.", show_alert=True)
            return
        if date_text <= flow.get("checkin"):
            flow["checkin"] = date_text
            flow["checkout"] = None
            flow["calendar_year"] = dt.year
            flow["calendar_month"] = dt.month
            await _resort_refresh_panel(context, flow)
            await query.answer("Tanggal itu kini menjadi mula yang baru—pilihlah hari beranjak.", show_alert=True)
            return
        flow["checkout"] = date_text
        flow["nights"] = _resort_stay_nights(flow.get("checkin"), flow.get("checkout"))
        rooms = _resort_available_rooms(flow.get("checkin"), flow.get("checkout"))
        if not rooms:
            flow["checkout"] = None
            flow["nights"] = 0
            await _resort_refresh_panel(context, flow, text_out=(
                "Maaf, tiada ruang tersisa dalam rentang tanggal tersebut.\n\n"
                f"Check-in yang masih dipilih: {flow.get('checkin')}\n"
                "Tentukan hari beranjak yang berbeda, atau ulangi susunan waktumu."
            ), reply_markup=_resort_calendar_keyboard(flow, flow.get("calendar_year"), flow.get("calendar_month")))
            return
        flow["step"] = "pick_room"
        text_out = [
            "𖠷╱ .. LETHÉA RESORT: ROOM AVAILABLE",
            "",
            f"Tanggal : {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
            "",
            "Pilih ruang yang masih tersisa di antara yang telah terisi:",
        ]
        for item in rooms:
            text_out.append(f"• {item.get('name')} | {_normalize_price_text(item.get('price', 0))} / malam")
        await _resort_refresh_panel(context, flow, text_out="\n".join(text_out), reply_markup=_resort_room_keyboard(rooms))
        return
    if action == "room" and len(parts) >= 3:
        room_no = int(parts[2])
        room = next((x for x in ROOM_ITEMS if int(x.get("no", 0) or 0) == room_no), None)
        if not room:
            await query.answer("Kamar tidak ditemukan.", show_alert=True)
            return
        if not _resort_room_available(room_no, flow.get("checkin"), flow.get("checkout")):
            await query.answer("Kamar itu telah terambil sesaat lalu, pilihlah yang lain.", show_alert=True)
            return
        flow["room_no"] = room_no
        flow["room_name"] = room.get("name")
        flow["room_price"] = int(room.get("price", 0) or 0)
        flow["room_link"] = room.get("link")
        flow["step"] = "wait_guest_info"
        await _resort_refresh_panel(context, flow, text_out=(
            "Jejak kamar telah disematkan untuk sesaat.\n\n"
            "Kini katakan lah, hadirmu seorang diri atau beriring?:\n"
            "› Datang seorang diri\n"
            "atau\n"
            "› Hadir bersama @username1 @username2 ...\n\n"
        ), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")]]))
        return
    if action == "askangel":
        want = parts[2] if len(parts) >= 3 else "no"
        if want == "yes":
            angels = _resort_available_angels_for_range(flow.get("checkin"), flow.get("checkout"))
            if not angels:
                flow["angel_uid"] = None
                flow["angel_name"] = None
                flow["angel_unit_price"] = 0
                flow["angel_price"] = 0
                flow["angel_dates"] = []
                flow["step"] = "summary"
                await _resort_refresh_panel(context, flow, text_out=(
                    f"Tiada Angel yang tersedia dalam rentang tanggal itu {flow.get('checkin')} sampai {flow.get('checkout')}.\n\n" + _resort_recap_text(flow)
                ), reply_markup=_resort_summary_keyboard())
                return
            rows = []
            text_lines = [
                "Tentukan pula Angel yang hendak kau ajak:",
                "",
                f"Rentang resort : {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
                "Setelah memilih Angel, kamu akan memilih tanggal mana saja Angel itu dirent.",
                "",
            ]
            for item in angels:
                available_count = len(item.get("available_dates") or [])
                text_lines.append(f"• {_angel_display_name(item['rec'])} | {item['popularity']} | {_normalize_price_text(item['price'])}/hari | tersedia {available_count} hari")
                rows.append([InlineKeyboardButton(f"{_angel_display_name(item['rec'])} | {_normalize_price_text(item['price'])}/hari", callback_data=f"resortreserve:angel:{item['uid']}")])
            rows.append([InlineKeyboardButton("Lewati", callback_data="resortreserve:skipangel:0")])
            rows.append([InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")])
            flow["step"] = "pick_angel"
            await _resort_refresh_panel(context, flow, text_out="\n".join(text_lines), reply_markup=InlineKeyboardMarkup(rows))
            return
        flow["angel_uid"] = None
        flow["angel_name"] = None
        flow["angel_unit_price"] = 0
        flow["angel_price"] = 0
        flow["angel_dates"] = []
        flow["step"] = "summary"
        await _resort_refresh_panel(context, flow, text_out=_resort_recap_text(flow), reply_markup=_resort_summary_keyboard())
        return
    if action == "backangels":
        angels = _resort_available_angels_for_range(flow.get("checkin"), flow.get("checkout"))
        rows = []
        text_lines = [
            "Tentukan pula Angel yang hendak kau ajak:",
            "",
            f"Rentang resort : {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
            "",
        ]
        for item in angels:
            available_count = len(item.get("available_dates") or [])
            text_lines.append(f"• {_angel_display_name(item['rec'])} | {item['popularity']} | {_normalize_price_text(item['price'])}/hari | tersedia {available_count} hari")
            rows.append([InlineKeyboardButton(f"{_angel_display_name(item['rec'])} | {_normalize_price_text(item['price'])}/hari", callback_data=f"resortreserve:angel:{item['uid']}")])
        rows.append([InlineKeyboardButton("Lewati", callback_data="resortreserve:skipangel:0")])
        rows.append([InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")])
        flow["step"] = "pick_angel"
        await _resort_refresh_panel(context, flow, text_out="\n".join(text_lines), reply_markup=InlineKeyboardMarkup(rows))
        return
    if action == "angel" and len(parts) >= 3:
        angel_uid = int(parts[2])
        chosen = None
        for item in _resort_available_angels_for_range(flow.get("checkin"), flow.get("checkout")):
            if int(item["uid"]) == angel_uid:
                chosen = item
                break
        if not chosen:
            await query.answer("Angel tersebut tidak tersedia dalam rentang resort ini.", show_alert=True)
            return
        flow["angel_uid"] = angel_uid
        flow["angel_name"] = _angel_display_name(chosen["rec"])
        flow["angel_unit_price"] = int(chosen["price"])
        flow["angel_price"] = 0
        flow["angel_dates"] = []
        flow["step"] = "pick_angel_dates"
        await _resort_refresh_panel(context, flow, text_out=_resort_angel_date_text(flow), reply_markup=_resort_angel_date_keyboard(flow))
        return
    if action == "angeldate" and len(parts) >= 3:
        date_text = parts[2]
        if date_text not in _resort_stay_dates(flow.get("checkin"), flow.get("checkout")):
            await query.answer("Tanggal itu di luar rentang resort.", show_alert=True)
            return
        if not flow.get("angel_uid") or not _resort_angel_available_on_date(int(flow.get("angel_uid")), date_text):
            await query.answer("Angel tidak tersedia pada tanggal itu.", show_alert=True)
            return
        selected = list(flow.get("angel_dates") or [])
        if date_text in selected:
            selected.remove(date_text)
        else:
            selected.append(date_text)
        selected.sort()
        flow["angel_dates"] = selected
        flow["angel_price"] = int(flow.get("angel_unit_price", 0) or 0) * len(selected)
        await _resort_refresh_panel(context, flow, text_out=_resort_angel_date_text(flow), reply_markup=_resort_angel_date_keyboard(flow))
        return
    if action == "confirmangeldates":
        selected = list(flow.get("angel_dates") or [])
        if not selected:
            await query.answer("Pilih minimal satu tanggal Angel, atau tekan Lewati Angel.", show_alert=True)
            return
        for date_text in selected:
            if not _resort_angel_available_on_date(int(flow.get("angel_uid")), date_text):
                await query.answer("Ada tanggal Angel yang baru saja tidak tersedia. Silakan pilih ulang.", show_alert=True)
                flow["angel_dates"] = [d for d in selected if _resort_angel_available_on_date(int(flow.get("angel_uid")), d)]
                flow["angel_price"] = int(flow.get("angel_unit_price", 0) or 0) * len(flow.get("angel_dates") or [])
                await _resort_refresh_panel(context, flow, text_out=_resort_angel_date_text(flow), reply_markup=_resort_angel_date_keyboard(flow))
                return
        flow["angel_price"] = int(flow.get("angel_unit_price", 0) or 0) * len(selected)
        flow["step"] = "summary"
        await _resort_refresh_panel(context, flow, text_out=_resort_recap_text(flow), reply_markup=_resort_summary_keyboard())
        return
    if action == "skipangel":
        flow["angel_uid"] = None
        flow["angel_name"] = None
        flow["angel_unit_price"] = 0
        flow["angel_price"] = 0
        flow["angel_dates"] = []
        flow["step"] = "summary"
        await _resort_refresh_panel(context, flow, text_out=_resort_recap_text(flow), reply_markup=_resort_summary_keyboard())
        return
    if action == "addnote":
        flow["step"] = "wait_notes"
        await _resort_refresh_panel(context, flow, text_out="Sampaikan catatanmu untuk Currathor, lalu rekap akan kusampaikan.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Lewati", callback_data="resortreserve:skipnote:0")], [InlineKeyboardButton("❌ Batalkan", callback_data="resortreserve:cancel:0")]]))
        return
    if action == "skipnote":
        flow["notes"] = flow.get("notes") or None
        flow["step"] = "summary"
        await _resort_refresh_panel(context, flow, text_out=_resort_recap_text(flow), reply_markup=_resort_summary_keyboard())
        return
    if action == "finish":
        if not flow.get("room_no") or not flow.get("guest_info"):
            await query.answer("Data belum lengkap.", show_alert=True)
            return
        if not _resort_room_available(flow.get("room_no"), flow.get("checkin"), flow.get("checkout")):
            await query.answer("Kamar itu telah terambil sesaat lalu, pilihlah yang lain.", show_alert=True)
            return
        booking_id = _resort_booking_id()
        total = _resort_payment_total(flow)
        booking = {
            "booking_id": booking_id,
            "guest_uid": int(query.from_user.id),
            "guest_acc_no": (_get_existing_account(query.from_user.id) or {}).get("acc_no"),
            "guest_name": (_get_existing_account(query.from_user.id) or {}).get("name") or query.from_user.full_name or query.from_user.username or f"User {query.from_user.id}",
            "checkin": flow.get("checkin"),
            "checkout": flow.get("checkout"),
            "nights": int(flow.get("nights", 0) or 0),
            "room_no": int(flow.get("room_no")),
            "room_name": flow.get("room_name"),
            "room_price": int(flow.get("room_price", 0) or 0),
            "room_link": flow.get("room_link"),
            "guest_info": flow.get("guest_info"),
            "angel_uid": int(flow.get("angel_uid", 0) or 0) or None,
            "angel_name": flow.get("angel_name"),
            "angel_unit_price": int(flow.get("angel_unit_price", 0) or 0),
            "angel_price": int(flow.get("angel_price", 0) or 0),
            "angel_dates": list(flow.get("angel_dates") or []),
            "notes": flow.get("notes"),
            "total_amount": int(total),
            "status": "waiting_payment",
            "admin_message_id": None,
            "link_sent_at": None,
            "angel_income_paid_at": None,
            "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        ROOM_BOOKINGS.append(booking)
        _resort_mark_angel_booking_status(booking, "waiting_payment")
        save_room_data()
        status = await context.bot.send_message(chat_id=query.message.chat_id, text="⏳ Sedang dalam proses pembayaran reservasi resort...")
        ok, result = await _create_payment_bill(
            context,
            requester_user=query.from_user,
            target_uid=int(query.from_user.id),
            amount=int(total),
            status_chat_id=status.chat_id,
            status_message_id=status.message_id,
            note=f"Resort Reservation: {flow.get('room_name')} | {_resort_date_range_label(flow.get('checkin'), flow.get('checkout'))}",
            angel_uid=int(flow.get("angel_uid", 0) or 0) or None,
            booking_date=(flow.get("angel_dates") or [None])[0] if flow.get("angel_uid") else None,
            booking_start=flow.get("checkin"),
            booking_end=flow.get("checkout"),
            booking_nights=int(flow.get("nights", 0) or 0),
        )
        if ok:
            bill = PENDING_BILLS.get(result)
            if bill is not None:
                bill["resort_booking_id"] = booking_id
                _resort_mark_angel_booking_status(booking, "waiting_payment", bill.get("bill_id") or result)
                save_payment_data()
            try:
                await context.bot.delete_message(
                    chat_id=flow.get("panel_chat_id"),
                    message_id=flow.get("panel_message_id"),
                )
            except Exception as e:
                print(f"[resort finish delete panel] error: {e}")
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=_resort_recap_text(flow) + "\n\nTagihan telah kusampaikan ke ruang pribadimu. Setelah pembayaran tuntas, rekap akan mengalir ke para pengurus.",
            )
            context.user_data.pop("resort_reservation_flow", None)
        else:
            booking["status"] = "payment_failed"
            _resort_mark_angel_booking_status(booking, "payment_failed")
            save_room_data()
        return


async def resort_reservation_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("resort_reservation_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type != "private":
        return
    text_in = (update.effective_message.text or "").strip()
    if not text_in:
        return
    lowered = text_in.lower()
    if flow.get("step") == "wait_guest_info":
        if lowered in {"datang seorang diri", "datang sendiri"}:
            flow["guest_info"] = "Datang seorang diri"
        elif lowered.startswith("hadir bersama") or lowered.startswith("bersama"):
            flow["guest_info"] = text_in
        else:
            await update.message.reply_text("Balas dengan format: Datang seorang diri atau Hadir bersama @username1 @username2 ...")
            return
        flow["step"] = "ask_angel"
        await _resort_refresh_panel(context, flow, text_out=(
            "Data tamu telah terpatri dalam tatanan ini.\n\nApakah kau hendak mengajak Angel sekaligus?"
        ), reply_markup=_resort_yes_no_keyboard("resortreserve:askangel:yes", "resortreserve:askangel:no"))
        return
    if flow.get("step") == "wait_notes":
        flow["notes"] = text_in
        flow["step"] = "summary"
        await _resort_refresh_panel(context, flow, text_out=_resort_recap_text(flow), reply_markup=_resort_summary_keyboard())
        return


def _resort_admin_recap_text(booking: dict) -> str:
    lines = [
        "𖠷╱ .. RESORT RESERVATION PENDING\n\n",
        "",
        f"Booking ID : {booking.get('booking_id')}",
        f"Informasi Pemesan : {booking.get('guest_name')} | Acc {booking.get('guest_acc_no', '-')}",
        f"Tanggal Booking : {_resort_date_range_label(booking.get('checkin'), booking.get('checkout'))}\n",
        f"Tipe Kamar : {booking.get('room_name')} | {_normalize_price_text(booking.get('room_price', 0))} / malam",
        f"Informasi Tamu Lain : {booking.get('guest_info') or '-'}",
        f"Angel : {booking.get('angel_name') or 'Tidak'}",
        f"Tanggal Angel : {', '.join(booking.get('angel_dates') or []) if booking.get('angel_name') else '-'}",
        f"Notes : {booking.get('notes') or '-'}",
        "",
        f"Total Payment : {_normalize_price_text(booking.get('total_amount', 0))} ✦𝕷",
        "",
        "Saat admin ACC: saldo guest akan dipotong, payout Angel diproses, dan Currathor pool dibagi rata.",
    ]
    return "\n".join(lines)


def _resort_currathor_pool_amount(booking: dict) -> int:
    room_total = int(booking.get("room_price", 0) or 0) * int(booking.get("nights", 0) or 0)
    angel_total = int(booking.get("angel_price", 0) or 0)
    room_pool = room_total // 2
    angel_pool = int(angel_total * 30 / 100)
    return room_pool + angel_pool


def _resort_angel_share_amount(booking: dict) -> int:
    angel_total = int(booking.get("angel_price", 0) or 0)
    return int(angel_total * 70 / 100)


__old_payment_bill_callback = __old_payment_bill_callback_2
async def payment_bill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = (query.data or "").split(":", 2)
    bill = PENDING_BILLS.get(parts[2]) if len(parts) == 3 else None

    if bill and bill.get("curated_booking_id"):
        if not await _ensure_not_banned(update, context):
            return
        await query.answer()
        if int(bill.get("target_uid", 0)) != int(query.from_user.id):
            await query.answer("Ini bukan bill milikmu.", show_alert=True)
            return
        item = _find_curated(bill.get("curated_id"))
        if not item or not item.get("booking") or item["booking"].get("booking_id") != bill.get("curated_booking_id"):
            await query.answer("Data Curated Dining tidak ditemukan.", show_alert=True)
            return
        action = parts[1]
        if action == "cancel":
            bill["status"] = "cancelled"
            item["status"] = "open"
            item["booking"] = None
            save_payment_data(); save_curated_dining_data()
            await _curated_refresh_public_message(context, item)
            try:
                await query.edit_message_text("❌ Payment dibatalkan. Slot Curated Dining kembali available.")
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment dibatalkan. Slot kembali available.")
            except Exception:
                pass
            return
        target_rec = _get_existing_account(query.from_user.id)
        if not target_rec:
            await query.answer("Account tidak ditemukan.", show_alert=True)
            return
        amount = int(bill.get("amount", 0) or 0)
        balance = int(target_rec.get("balance", 0) or 0)
        if balance < amount:
            bill["status"] = "insufficient_balance"
            item["status"] = "open"
            item["booking"] = None
            save_payment_data(); save_curated_dining_data()
            await _curated_refresh_public_message(context, item)
            try:
                await query.edit_message_text(f"❌ Payment gagal. Saldo kamu tidak cukup.\nSaldo sekarang: {_normalize_price_text(balance)} ✦𝕷\nSlot Curated Dining kembali available.")
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment gagal. Saldo target tidak cukup. Slot kembali available.")
            except Exception:
                pass
            return
        bill["status"] = "pending_admin"
        item["status"] = "pending_admin"
        item["booking"]["status"] = "pending_admin"
        save_payment_data(); save_curated_dining_data()
        sent = await context.bot.send_message(chat_id=FORWARD_PUBLIC_CHAT_ID, text=_curated_admin_recap_text(item), reply_markup=_approval_keyboard())
        item["booking"]["admin_message_id"] = sent.message_id
        approval_map[(FORWARD_PUBLIC_CHAT_ID, sent.message_id)] = {"uid": int(query.from_user.id), "kind": "curated_dining", "curated_id": item.get("id"), "booking_id": bill.get("curated_booking_id")}
        save_state(); save_curated_dining_data()
        try:
            await query.edit_message_text("✅ Payment terkonfirmasi, kini menunggu ACC pengurus. Saldo belum dipotong.")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="✅ Payment terkonfirmasi, menunggu ACC pengurus.")
        except Exception:
            pass
        return

    # Bill biasa dan rent Angel tidak punya resort_booking_id.
    # Jangan return diam-diam, karena tombol Telegram akan loading terus.
    # Arahkan ke payment callback lama yang memang menangani bill non-resort.
    if not bill or not bill.get("resort_booking_id"):
        return await __old_payment_bill_callback(update, context)

    if not await _ensure_not_banned(update, context):
        return

    await query.answer()

    if int(bill.get("target_uid", 0)) != int(query.from_user.id):
        await query.answer("Ini bukan bill milikmu.", show_alert=True)
        return
    booking = next((x for x in ROOM_BOOKINGS if x.get("booking_id") == bill.get("resort_booking_id")), None)
    if not booking:
        await query.answer("Data booking tidak ditemukan.", show_alert=True)
        return
    action = parts[1]
    if action == "cancel":
        bill["status"] = "cancelled"
        booking["status"] = "cancelled"
        _resort_mark_angel_booking_status(booking, "cancelled")
        save_payment_data(); save_room_data()
        try:
            await query.edit_message_text("❌ Payment dibatalkan.")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment dibatalkan.")
        except Exception:
            pass
        return
    target_rec = _get_existing_account(query.from_user.id)
    if not target_rec:
        await query.answer("Account tidak ditemukan.", show_alert=True)
        return
    amount = int(bill.get("amount", 0) or 0)
    if not _resort_room_available(booking.get("room_no"), booking.get("checkin"), booking.get("checkout"), exclude_booking_id=booking.get("booking_id")):
        bill["status"] = "room_unavailable"
        booking["status"] = "room_unavailable"
        _resort_mark_angel_booking_status(booking, "room_unavailable")
        save_payment_data(); save_room_data()
        try:
            await query.edit_message_text("❌ Pembayaran dibatalkan, dan ruang itu kini telah terambil.")
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Payment gagal. Room sudah tidak tersedia.")
        except Exception:
            pass
        return
    if booking.get("angel_uid"):
        unavailable_dates = []
        for date_text in (booking.get("angel_dates") or [booking.get("checkin")]):
            if not _resort_angel_available_on_date(int(booking.get("angel_uid")), date_text, exclude_resort_booking_id=booking.get("booking_id")):
                unavailable_dates.append(date_text)
        if unavailable_dates:
            bill["status"] = "angel_unavailable"
            booking["status"] = "angel_unavailable"
            _resort_mark_angel_booking_status(booking, "angel_unavailable")
            save_payment_data(); save_room_data()
            try:
                await query.edit_message_text("❌ Pembayaran dibatalkan, dan Angel itu kini telah terambil pada tanggal: " + ", ".join(unavailable_dates))
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="❌ Pembayaran gagal, Angel itu telah terambil.")
            except Exception:
                pass
            return
    bill["status"] = "pending_admin"
    booking["status"] = "pending_admin"
    if booking.get("angel_uid"):
        profile = _ensure_angel_profile(int(booking.get("angel_uid")))
        for date_text in (booking.get("angel_dates") or [booking.get("checkin")]):
            existing = next((x for x in profile.get("bookings", []) if x.get("resort_booking_id") == booking.get("booking_id") and x.get("date") == date_text), None)
            if existing:
                existing["status"] = "pending_admin"
            else:
                profile.setdefault("bookings", []).append({
                    "date": date_text,
                    "guest_uid": int(query.from_user.id),
                    "guest_acc_no": target_rec.get("acc_no"),
                    "guest_name": booking.get("guest_name"),
                    "status": "pending_admin",
                    "bill_id": bill.get("bill_id"),
                    "resort_booking_id": booking.get("booking_id"),
                    "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                })
        save_angel_data()
    save_payment_data(); save_room_data()
    sent = await context.bot.send_message(
        chat_id=FORWARD_PUBLIC_CHAT_ID,
        text=_resort_admin_recap_text(booking),
        reply_markup=_approval_keyboard(),
    )
    booking["admin_message_id"] = sent.message_id
    approval_map[(FORWARD_PUBLIC_CHAT_ID, sent.message_id)] = {
        "uid": int(query.from_user.id),
        "kind": "resort_reservation",
        "booking_id": booking.get("booking_id"),
    }
    save_state(); save_room_data()
    try:
        await query.edit_message_text(f"✅ Konfirmasi reservasi telah terpatri, kini menanti restu para pengurus. Saldo belum tersentuh")
    except Exception:
        pass
    try:
        await context.bot.edit_message_text(chat_id=bill["status_chat_id"], message_id=bill["status_message_id"], text="✅ Jejak reservasi telah terlipat dalam antrian pengurus—saldo tetap tak tersentuh, menanti saat restu terpatri.")
    except Exception:
        pass
    try:
        await context.bot.send_message(chat_id=query.from_user.id, text="Jejak reservasi telah sampai ke lingkar pengurus—saldo tetap tak tersentuh, menanti restu yang mengesahkan. Tautan ruang akan disampaikan pada hari tiba, setelah persetujuan terpatri.")
    except Exception:
        pass


async def __old_process_approval_action_base(
    context: ContextTypes.DEFAULT_TYPE,
    actor,
    chat_id: int,
    target_message,
    mode: str,
    reply_message=None,
):
    if chat_id != FORWARD_PUBLIC_CHAT_ID:
        return False, "Pengesahan hanya dapat terwujud dalam lingkup para pengurus."

    if not _is_admin(actor):
        return False, "Hanya Deitte atau Currathor."

    if not target_message:
        return False, "Pesan target tidak ditemukan."

    info = approval_map.get((chat_id, target_message.message_id))
    target_uid = None
    kind = None

    if info:
        target_uid = info.get("uid")
        kind = info.get("kind")
    else:
        txt = (target_message.text or target_message.caption or "")
        m_uid = re.search(r"UID\s*:\s*(\d+)", txt)
        if m_uid:
            target_uid = int(m_uid.group(1))

    if not target_uid:
        return False, "Data target tidak ditemukan."

    uid_str = str(target_uid)
    existing_rec = _get_existing_account(target_uid)

    if not kind:
        if existing_rec and existing_rec.get("upgrade_pending"):
            kind = "upgrade_vip"
        elif existing_rec and existing_rec.get("renewal_pending"):
            kind = "renewal"
        elif uid_str in PENDING_MEMBERSHIP:
            kind = "membership"

    if mode == "acc":
        if kind == "membership":
            pending = PENDING_MEMBERSHIP.get(uid_str)
            if not pending:
                return False, "Tidak ada membership registration pending."

            try:
                chat_user = await context.bot.get_chat(target_uid)
            except Exception:
                chat_user = None

            class DummyUser:
                id = target_uid
                username = getattr(chat_user, "username", None)
                full_name = getattr(chat_user, "full_name", pending.get("name", "-"))

            was_member_before = bool(
                existing_rec
                and (existing_rec.get("membership_type") or existing_rec.get("membership_started_at"))
            )
            rec = _create_account(target_uid, DummyUser(), account_type="member")
            package = pending.get("package", "Regular")

            now = _now()
            rec["membership_type"] = package
            rec["membership_status"] = "active"
            rec["membership_started_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            rec["membership_expires_at"] = (now + timedelta(days=_membership_days(package))).strftime("%Y-%m-%d %H:%M:%S")
            rec["last_expiry_notified_at"] = None
            rec["balance"] = int(rec.get("balance", 0))
            if not was_member_before and not rec.get("initial_membership_balance_granted"):
                initial_balance = _initial_member_balance(package)
                rec["balance"] = int(rec.get("balance", 0)) + initial_balance
                rec["initial_membership_balance_granted"] = True
                rec["initial_membership_balance_amount"] = initial_balance
                rec["initial_membership_balance_granted_at"] = now.strftime("%Y-%m-%d %H:%M:%S")

            PENDING_MEMBERSHIP.pop(uid_str, None)
            save_accounts()
            save_pending()

            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "✅ Keanggotaanmu telah disahkan dalam tatanan ini.\n\n"
                        f"› … Account Number : {rec.get('acc_no')}\n"
                        f"› … Package : {package}\n"
                        f"› … Status : active\n"
                        f"› … Expired At : {rec.get('membership_expires_at')}\n"
                        f"› … Saldo : {rec.get('balance', 0)}"
                    )
                )
            except Exception as e:
                print(f"[notify acc member failed] {e}")

            try:
                chat_obj = await context.bot.get_chat(target_uid)
                await _sync_private_commands_for_user(context, chat_obj)
            except Exception:
                pass

            result_text = (
                f"› … Akun Keanggotaan {rec.get('acc_no')} diaktifkan.\n"
                f"Package: {package}\n"
                f"Saldo: {rec.get('balance', 0)}"
            )

        elif kind == "renewal":
            if not existing_rec or not existing_rec.get("renewal_pending"):
                return False, "Tidak ada renewal pending."

            package = existing_rec["renewal_pending"].get("package") or existing_rec.get("membership_type") or "Regular"
            _extend_membership_from_current(existing_rec, package)
            existing_rec["renewal_pending"] = None
            existing_rec["balance"] = int(existing_rec.get("balance", 0))
            save_accounts()

            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "✅ Renewal kamu telah disetujui.\n\n"
                        f"› … Package : {existing_rec.get('membership_type')}\n"
                        f"› … Status : {existing_rec.get('membership_status')}\n"
                        f"› … Expired At : {existing_rec.get('membership_expires_at')}\n"
                        f"› … Saldo : {existing_rec.get('balance', 0)}"
                    )
                )
            except Exception as e:
                print(f"[notify renewal failed] {e}")

            result_text = (
                f"✅ Renewal account {existing_rec.get('acc_no')} berhasil.\n"
                f"› … Package: {existing_rec.get('membership_type')}\n"
                f"› … Expired At: {existing_rec.get('membership_expires_at')}\n"
                f"› … Saldo: {existing_rec.get('balance', 0)}"
            )

        elif kind == "upgrade_vip":
            if not existing_rec or not existing_rec.get("upgrade_pending"):
                return False, "Tidak ada upgrade pending."

            _extend_membership_from_current(existing_rec, "VIP")
            existing_rec["upgrade_pending"] = None
            existing_rec["membership_type"] = "VIP"
            existing_rec["balance"] = int(existing_rec.get("balance", 0))
            save_accounts()

            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "✅ Upgrade Plan VIP kamu telah disetujui.\n\n"
                        "› … Package : VIP\n"
                        f"› … Status : {existing_rec.get('membership_status')}\n"
                        f"› … Expired At : {existing_rec.get('membership_expires_at')}\n"
                        f"› … Saldo : {existing_rec.get('balance', 0)}"
                    )
                )
            except Exception as e:
                print(f"[notify upgrade failed] {e}")

            result_text = (
                f"✅ Upgrade VIP account {existing_rec.get('acc_no')} berhasil.\n"
                f"› … Package: VIP\n"
                f"› … Expired At: {existing_rec.get('membership_expires_at')}\n"
                f"› … Saldo: {existing_rec.get('balance', 0)}"
            )

        else:
            return False, "Jenis approval tidak dikenali."

    elif mode == "reject":
        if uid_str in PENDING_MEMBERSHIP:
            PENDING_MEMBERSHIP.pop(uid_str, None)
            save_pending()

        if existing_rec:
            existing_rec["renewal_pending"] = None
            existing_rec["upgrade_pending"] = None
            save_accounts()

        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text="Permohonanmu tiada memperoleh restu."
            )
        except Exception as e:
            print(f"[notify reject failed] {e}")

        result_text = "Pengajuan ditolak."

    else:
        return False, "Mode approval tidak valid."

    for key, value in list(approval_map.items()):
        if value.get("uid") == target_uid:
            approval_map.pop(key, None)
    save_state()

    if reply_message:
        try:
            await reply_message.reply_text(result_text)
        except Exception:
            pass

    return True, result_text


_old_process_approval_action = __old_process_approval_action_base

async def _process_approval_action(context, actor, chat_id: int, target_message, mode: str, reply_message=None):
    info = approval_map.get((chat_id, target_message.message_id)) if target_message else None
    if not info or info.get("kind") != "resort_reservation":
        return await _old_process_approval_action(context, actor, chat_id, target_message, mode, reply_message)

    if chat_id != FORWARD_PUBLIC_CHAT_ID:
        return False, "Approval hanya bisa dilakukan di grup pengurus."
    if not _is_admin(actor):
        return False, "Hanya Deittee atau Currathor."

    booking = next((x for x in ROOM_BOOKINGS if x.get("booking_id") == info.get("booking_id")), None)
    if not booking:
        return False, "Data booking resort tidak ditemukan."

    if mode == "acc":
        guest_uid = int(booking.get("guest_uid"))
        guest_rec = _get_existing_account(guest_uid)
        if not guest_rec:
            return False, "Account guest tidak ditemukan."

        total_amount = int(booking.get("total_amount", 0) or 0)
        current_balance = int(guest_rec.get("balance", 0) or 0)
        if current_balance < total_amount:
            try:
                await context.bot.send_message(
                    chat_id=guest_uid,
                    text=(
                        "ⓘ Jejak reservasi belum dapat terpatri sebab saldo yang ada belum mencukupi.\n"
                        f"Total dibutuhkan : {_normalize_price_text(total_amount)} ✦𝕷\n"
                        f"Saldo sekarang : {_normalize_price_text(current_balance)} ✦𝕷"
                    ),
                )
            except Exception:
                pass
            return False, "Saldo tamu belum memadai—mintalah ia menambahkannya terlebih dahulu"

        if not _resort_room_available(
            booking.get("room_no"),
            booking.get("checkin"),
            booking.get("checkout"),
            exclude_booking_id=booking.get("booking_id"),
        ):
            return False, "Kamar sudah tidak tersedia."

        if booking.get("angel_uid"):
            profile = _ensure_angel_profile(int(booking.get("angel_uid")))
            if _angel_is_off_date(profile, booking.get("checkin")):
                return False, "Pada waktu tersebut, Angel tak membuka kehadirannya"

            blocking = False
            for item in profile.get("bookings", []):
                if item.get("resort_booking_id") == booking.get("booking_id"):
                    continue
                if item.get("date") == booking.get("checkin") and item.get("status") in RESORT_BLOCKING_STATUSES:
                    blocking = True
                    break
            if blocking:
                return False, "Angel telah terlepas dari lingkup yang tersedia."

        guest_rec["balance"] = current_balance - total_amount
        save_accounts()

        angel_share = _resort_angel_share_amount(booking)
        currathor_pool = _resort_currathor_pool_amount(booking)

        if booking.get("angel_uid"):
            profile = _ensure_angel_profile(int(booking.get("angel_uid")))
            for item in profile.get("bookings", []):
                if item.get("resort_booking_id") == booking.get("booking_id"):
                    item["status"] = "confirmed"
            profile["total_orders"] = int(profile.get("total_orders", 0) or 0) + 1
            save_angel_data()

            if angel_share > 0 and not booking.get("angel_income_paid_at"):
                await _credit_angel_income(
                    context,
                    int(booking.get("angel_uid")),
                    angel_share,
                    f"Resort booking {booking.get('booking_id')} dari {booking.get('guest_name')}",
                )
                booking["angel_income_paid_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")

            if not booking.get("angel_cnit_paid_at"):
                angel_days = len(booking.get("angel_dates") or [])
                if angel_days <= 0 and booking.get("angel_uid"):
                    angel_days = 1
                await _grant_angel_rent_cnit(
                    context,
                    int(booking.get("angel_uid")),
                    f"Resort booking {booking.get('booking_id')} dari {booking.get('guest_name')} ({angel_days} hari)",
                    1000 * angel_days,
                )
                booking["angel_cnit_paid_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
                booking["angel_cnit_amount"] = 1000 * angel_days
                booking["angel_cnit_days"] = angel_days

        currathor_payouts = await _credit_currathors(
            context,
            currathor_pool,
            f"Resort booking {booking.get('booking_id')} room {booking.get('room_name')}",
        )
        booking["currathor_pool_amount"] = currathor_pool
        booking["currathor_payouts"] = {str(k): int(v) for k, v in (currathor_payouts or {}).items()}
        booking["guest_balance_deducted_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
        booking["status"] = "confirmed"

        send_at = _resort_link_send_time(booking)
        booking["link_send_after"] = send_at.strftime("%Y-%m-%d %H:%M:%S")
        booking["link_sent_at"] = None

        bill_ref = next((x for x in PENDING_BILLS.values() if x.get("resort_booking_id") == booking.get("booking_id")), None)
        if bill_ref:
            bill_ref["status"] = "confirmed"
            save_payment_data()

        save_room_data()

        try:
            await context.bot.send_message(
                chat_id=guest_uid,
                text=(
                    "Reservasi itu kini telah terpatri dengan restu pengurus.\n\n"
                    f"› … Saldo terpotong : {_normalize_price_text(total_amount)} ✦𝕷\n"
                    f"› … Sisa saldo : {_normalize_price_text(guest_rec.get('balance', 0))} ✦𝕷\n"
                    f"› … Tanggal : {_resort_date_range_label(booking.get('checkin'), booking.get('checkout'))}\n"
                    f"› … Room : {booking.get('room_name')}\n"
                    f"Tautan ruang dijadwalkan terkirim pada {send_at.strftime('%Y-%m-%d %H:%M:%S')}."
                ),
            )
        except Exception:
            pass

        result_text = (
            f"𐂗 ``Reservasi resort {booking.get('booking_id')} di-ACC. "
            f"› …Saldo guest dipotong {_normalize_price_text(total_amount)}. "
        )
        return True, result_text

    if mode == "reject":
        if booking.get("angel_uid"):
            try:
                profile = _ensure_angel_profile(int(booking.get("angel_uid")))
                for item in profile.get("bookings", []):
                    if item.get("resort_booking_id") == booking.get("booking_id"):
                        item["status"] = "rejected"
                save_angel_data()
            except Exception:
                pass

        booking["status"] = "rejected"
        save_room_data()

        bill_ref = next((x for x in PENDING_BILLS.values() if x.get("resort_booking_id") == booking.get("booking_id")), None)
        if bill_ref:
            bill_ref["status"] = "rejected"
            save_payment_data()

        try:
            await context.bot.send_message(
                chat_id=int(booking.get("guest_uid")),
                text=(
                    "ⓘ Jejak reservasi resort itu tak memperoleh restu pengurus.\n"
                    "Silakan hubungi admin bila ingin menenun ulang pengajuanmu."
                ),
            )
        except Exception:
            pass

        return True, f"ⓘ Reservasi resort {booking.get('booking_id')} ditolak."

    return False, "Mode approval tidak dikenali."



# =========================================================
# FEATURE: TOPUP LUXEN / PROMOTION / EVENT REWARD
# =========================================================
# Nominal reward bisa di-adjust dari sini.
TOPUP_PROMOTION_REWARD = 150000
TOPUP_PROMOTION_WEEKLY_LIMIT = 3
TOPUP_EXTERNAL_EVENT_REWARDS = {
    "participant": 200000,
    "first": 500000,
    "second": 350000,
}
OPEN_EVENTS = {}

# wrap label helpers supaya flow topup tampil rapi tanpa merusak registration lama
_old_registration_label_for_topup = _registration_label

def _registration_label(kind: str) -> str:
    mapping = {
        "topup_promotion": "Top Up Luxen — Promotion",
        "topup_external_event": "Top Up Luxen — External Event",
        "internal_event_reward": "Internal Event Reward",
    }
    return mapping.get(kind, _old_registration_label_for_topup(kind))

_old_proof_label_for_topup = _proof_label

def _proof_label(flow):
    kind = (flow or {}).get("kind")
    if kind == "topup_promotion":
        return "Top Up Luxen — Promotion Proof"
    if kind == "topup_external_event":
        return "Top Up Luxen — External Event Proof"
    return _old_proof_label_for_topup(flow)


def _topup_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Promotion", callback_data="topup:promotion")],
        [InlineKeyboardButton("External Event", callback_data="topup:external")],
        [InlineKeyboardButton("Internal Event Info", callback_data="topup:internalinfo")],
    ])


def _topup_external_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Participant — {_normalize_price_text(TOPUP_EXTERNAL_EVENT_REWARDS.get('participant', 0))} ✦𝕷", callback_data="topup:external:participant")],
        [InlineKeyboardButton(f"First Place — {_normalize_price_text(TOPUP_EXTERNAL_EVENT_REWARDS.get('first', 0))} ✦𝕷", callback_data="topup:external:first")],
        [InlineKeyboardButton(f"Second Place — {_normalize_price_text(TOPUP_EXTERNAL_EVENT_REWARDS.get('second', 0))} ✦𝕷", callback_data="topup:external:second")],
    ])


def _topup_week_key(dt=None):
    dt = dt or _now()
    y, w, _ = dt.isocalendar()
    return f"{y}-W{int(w):02d}"


def _topup_promo_used_this_week(rec):
    claims = (rec or {}).get("topup_promotion_claims") or []
    week_key = _topup_week_key()
    return sum(1 for item in claims if (item or {}).get("week") == week_key and (item or {}).get("status") == "approved")


def _topup_source_text(kind, meta=None):
    meta = meta or {}
    if kind == "topup_promotion":
        return "Promotion reward"
    if kind == "topup_external_event":
        rank = meta.get("external_rank", "participant")
        labels = {"participant": "External Event Participant", "first": "External Event First Place", "second": "External Event Second Place"}
        return labels.get(rank, "External Event")
    if kind == "internal_event_reward":
        return f"Internal Event: {meta.get('title') or meta.get('synopsis') or '-'}"
    return "Top Up reward"


async def topup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    rec = _get_existing_account(update.effective_user.id)
    if not rec or rec.get("account_type") != "member":
        await update.message.reply_text("Kamu harus punya account member dulu untuk top up Luxen reward.")
        return
    # Tidak wajib aktif. Member expired/deactive tetap boleh.
    await update.message.reply_text(
        "𖠷 ╱ .. TOP UP LUXEN REWARD\n\n"
        "Pilih cara penambahan Luxen yang ingin diajukan.\n"
        f"Promotion : {_normalize_price_text(TOPUP_PROMOTION_REWARD)} ✦𝕷 per promosi, maksimal {TOPUP_PROMOTION_WEEKLY_LIMIT} per minggu.\n"
        "External Event : pilih participant / juara lalu kirim bukti.\n"
        "Internal Event : join event yang dibuka Currathor melalui tombol event.",
        reply_markup=_topup_keyboard(),
    )


async def topup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    rec = _get_existing_account(query.from_user.id)
    if not rec or rec.get("account_type") != "member":
        await query.answer("Kamu harus punya account member dulu.", show_alert=True)
        return
    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "promotion":
        used = _topup_promo_used_this_week(rec)
        if used >= TOPUP_PROMOTION_WEEKLY_LIMIT:
            await query.edit_message_text(
                f"Limit promotion minggu ini sudah penuh ({used}/{TOPUP_PROMOTION_WEEKLY_LIMIT})."
            )
            return
        context.user_data["registration_flow"] = {
            "flow_type": "topup_reward",
            "kind": "topup_promotion",
            "package": None,
            "step": "upload_proof",
            "needs_proof": True,
            "form_data": f"Top Up Promotion Reward\nReward : {_normalize_price_text(TOPUP_PROMOTION_REWARD)} ✦𝕷\nLimit minggu ini : {used}/{TOPUP_PROMOTION_WEEKLY_LIMIT}",
            "proof_items": [],
            "proof_summary_message_id": None,
            "replace_index": None,
            "reward_amount": int(TOPUP_PROMOTION_REWARD),
        }
        await query.edit_message_text("Kirim bukti promosi yang valid dan tidak duplikatif.")
        await _start_proof_upload_flow(context, query.message.chat_id, context.user_data["registration_flow"])
        return

    if action == "external" and len(parts) == 2:
        await query.edit_message_text(
            "Pilih posisi/jenis reward External Event.",
            reply_markup=_topup_external_keyboard(),
        )
        return

    if action == "external" and len(parts) >= 3:
        rank = parts[2]
        if rank not in TOPUP_EXTERNAL_EVENT_REWARDS:
            await query.answer("Pilihan tidak valid.", show_alert=True)
            return
        amount = int(TOPUP_EXTERNAL_EVENT_REWARDS.get(rank, 0) or 0)
        rank_label = {"participant": "Participant", "first": "First Place", "second": "Second Place"}.get(rank, rank)
        context.user_data["registration_flow"] = {
            "flow_type": "topup_reward",
            "kind": "topup_external_event",
            "package": None,
            "step": "upload_proof",
            "needs_proof": True,
            "form_data": f"Top Up External Event\nType : {rank_label}\nReward : {_normalize_price_text(amount)} ✦𝕷",
            "proof_items": [],
            "proof_summary_message_id": None,
            "replace_index": None,
            "reward_amount": amount,
            "external_rank": rank,
        }
        await query.edit_message_text("Kirim bukti External Event. Bukti akan diteruskan ke Currathor untuk ACC.")
        await _start_proof_upload_flow(context, query.message.chat_id, context.user_data["registration_flow"])
        return

    if action == "internalinfo":
        await query.edit_message_text(
            "Internal Event hanya bisa dibuka oleh Currathor/Owner dengan /openevent.\n"
            "Jika event sedang open, join melalui tombol Join pada panel event."
        )
        return


# wrap submit pending supaya topup proof masuk approval_map dengan detail reward
_old_submit_pending_to_admin_for_topup = _submit_pending_to_admin

async def _submit_pending_to_admin(context, user, flow):
    if (flow or {}).get("flow_type") != "topup_reward":
        return await _old_submit_pending_to_admin_for_topup(context, user, flow)

    uid = int(user.id)
    rec = _get_existing_account(uid)
    if not rec or rec.get("account_type") != "member":
        return False
    kind = flow.get("kind")
    amount = int(flow.get("reward_amount", 0) or 0)
    label = _registration_label(kind)
    header_lines = [
        f"ⓘ ► {label}",
        "",
        f"UID : {uid}",
        f"Username : @{user.username or user.id}",
        f"Account Number : {rec.get('acc_no', '-')}",
        f"Reward : {_normalize_price_text(amount)} ✦𝕷",
    ]
    if kind == "topup_external_event":
        rank = flow.get("external_rank", "participant")
        header_lines.append(f"External Type : {rank}")
    if flow.get("form_data"):
        header_lines.extend(["", flow.get("form_data")])

    try:
        hdr = await context.bot.send_message(
            chat_id=FORWARD_PUBLIC_CHAT_ID,
            text="\n".join(header_lines),
            reply_markup=_approval_keyboard(),
        )
        approval_map[(FORWARD_PUBLIC_CHAT_ID, hdr.message_id)] = {
            "uid": uid,
            "kind": kind,
            "reward_amount": amount,
            "external_rank": flow.get("external_rank"),
            "submitted_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        for item in flow.get("proof_items", []) or []:
            copied = await context.bot.copy_message(
                chat_id=FORWARD_PUBLIC_CHAT_ID,
                from_chat_id=item["chat_id"],
                message_id=item["message_id"],
            )
            approval_map[(FORWARD_PUBLIC_CHAT_ID, copied.message_id)] = dict(approval_map[(FORWARD_PUBLIC_CHAT_ID, hdr.message_id)])
        save_state()
        return True
    except Exception as e:
        print(f"[_submit_pending_to_admin topup] error: {e}")
        return False


# =========================================================
# FEATURE: INTERNAL EVENT REWARD
# =========================================================
def _event_session_key(chat_id: int) -> str:
    return str(chat_id)


def _event_join_keyboard(chat_id: int):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join Event", callback_data=f"eventjoin:{chat_id}")]])


def _find_internal_event_by_id(event_id: str):
    for ev in OPEN_EVENTS.values():
        if ev.get("event_id") == event_id:
            return ev
    return None


def _event_admin_keyboard(event: dict):
    rows = []
    participants = event.get("participants") or {}
    for uid_str, pdata in participants.items():
        label_name = pdata.get("name") or pdata.get("username") or f"UID {uid_str}"
        rows.append([
            InlineKeyboardButton(
                f"Remove {label_name}"[:60],
                callback_data=f"eventadmin:remove:{event.get('event_id')}:{uid_str}",
            )
        ])
    rows.append([
        InlineKeyboardButton("ACC Reward", callback_data="approve:acc"),
        InlineKeyboardButton("Reject Event", callback_data="approve:reject"),
    ])
    return InlineKeyboardMarkup(rows)


def _event_admin_text(event: dict) -> str:
    participants = event.get("participants") or {}
    text = _event_status_text(event)
    text += "\n\nSebelum ACC, Currathor bisa hapus participant yang tidak valid dari tombol Remove."
    text += "\nParticipant tersisa saat ACC akan menerima reward."
    if not participants:
        text += "\n\n⚠️ Tidak ada participant tersisa."
    return text


def _event_status_text(event: dict) -> str:
    participants = event.get("participants") or {}
    lines = [
        "𖠷 ╱ .. LETHÉA INTERNAL EVENT",
        "",
        f"Status : {(event.get('status') or 'open').upper()}",
        f"Reward : {_normalize_price_text(event.get('reward', 0))} ✦𝕷 per participant",
        "",
        "Synopsis:",
        event.get("synopsis") or "-",
        "",
        f"Participants : {len(participants)}",
    ]
    if participants:
        for pdata in participants.values():
            lines.append(f"› {pdata.get('name', '-')}")
    return "\n".join(lines)


async def openevent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan /openevent di group event.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner yang bisa membuka event.")
        return

    key = _event_session_key(update.effective_chat.id)
    if key in OPEN_EVENTS and OPEN_EVENTS[key].get("status") == "open":
        await update.message.reply_text("Masih ada internal event yang open di chat ini. Tutup dulu dengan /closeevent.")
        return

    raw = " ".join(context.args or []).strip()
    if raw:
        # Format cepat: /openevent 350000 | sinopsis event
        if "|" in raw:
            amount_text, synopsis = raw.split("|", 1)
            amount = _parse_bet_amount(amount_text.strip())
            synopsis = synopsis.strip()
            if amount and synopsis:
                await _open_internal_event_now(update, context, amount, synopsis)
                return
        await update.message.reply_text("Format cepat: /openevent 350000 | sinopsis singkat event")
        return

    context.user_data["open_event_flow"] = {"step": "synopsis", "chat_id": update.effective_chat.id}
    await update.message.reply_text("Kirim sinopsis singkat event yang mau dibuka.")


async def _open_internal_event_now(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int, synopsis: str):
    key = _event_session_key(update.effective_chat.id)
    event_id = f"event_{int(_now().timestamp()*1000)}"
    event = {
        "event_id": event_id,
        "chat_id": update.effective_chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "opened_by": int(update.effective_user.id),
        "opened_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "open",
        "reward": int(amount),
        "synopsis": synopsis,
        "participants": {},
        "message_id": None,
    }
    kwargs = {"text": _event_status_text(event), "reply_markup": _event_join_keyboard(update.effective_chat.id)}
    thread_id = getattr(update.effective_message, "message_thread_id", None)
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    sent = await update.message.reply_text(**kwargs)
    event["message_id"] = sent.message_id
    OPEN_EVENTS[key] = event


async def event_open_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("open_event_flow")
    if not flow:
        return
    if not await _ensure_not_banned(update, context):
        raise ApplicationHandlerStop
    if not _can_manage_staff(update.effective_user):
        context.user_data.pop("open_event_flow", None)
        raise ApplicationHandlerStop
    if update.effective_chat.id != int(flow.get("chat_id")):
        return
    text = (update.effective_message.text or "").strip()
    if flow.get("step") == "synopsis":
        flow["synopsis"] = text
        flow["step"] = "reward"
        await update.message.reply_text("Kirim nominal hadiah event untuk tiap participant. Contoh: 350000")
        raise ApplicationHandlerStop
    if flow.get("step") == "reward":
        amount = _parse_bet_amount(text)
        if amount is None:
            await update.message.reply_text("Nominal harus angka. Contoh: 350000")
            raise ApplicationHandlerStop
        synopsis = flow.get("synopsis") or "-"
        context.user_data.pop("open_event_flow", None)
        await _open_internal_event_now(update, context, amount, synopsis)
        raise ApplicationHandlerStop


async def event_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 2:
        return
    chat_id = int(parts[1])
    event = OPEN_EVENTS.get(_event_session_key(chat_id))
    if not event or event.get("status") != "open":
        await query.answer("Event sudah ditutup atau tidak ditemukan.", show_alert=True)
        return
    rec = _get_existing_account(query.from_user.id)
    if not rec or rec.get("account_type") != "member":
        await query.answer("Hanya account member yang bisa join event reward.", show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid in event.setdefault("participants", {}):
        await query.answer("Kamu sudah join event ini.", show_alert=True)
        return
    event["participants"][uid] = {
        "uid": int(query.from_user.id),
        "name": query.from_user.full_name or query.from_user.username or f"User {uid}",
        "username": query.from_user.username or "-",
        "acc_no": rec.get("acc_no"),
        "joined_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=event.get("message_id"),
            text=_event_status_text(event),
            reply_markup=_event_join_keyboard(chat_id),
        )
    except Exception:
        pass
    await query.answer("Kamu berhasil join event.", show_alert=True)


async def closeevent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if update.effective_chat.type == "private":
        await update.message.reply_text("Gunakan /closeevent di group event.")
        return
    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner yang bisa menutup event.")
        return
    key = _event_session_key(update.effective_chat.id)
    event = OPEN_EVENTS.get(key)
    if not event or event.get("status") != "open":
        await update.message.reply_text("Tidak ada event yang sedang open di chat ini.")
        return
    event["status"] = "closed"
    event["closed_by"] = int(update.effective_user.id)
    event["closed_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(
        "Event ditutup. Data participant akan dikirim ke Currathor untuk ACC reward."
    )
    sent = await context.bot.send_message(
        chat_id=FORWARD_PUBLIC_CHAT_ID,
        text=_event_admin_text(event),
        reply_markup=_event_admin_keyboard(event),
    )
    approval_map[(FORWARD_PUBLIC_CHAT_ID, sent.message_id)] = {
        "uid": int(update.effective_user.id),
        "kind": "internal_event_reward",
        "event_id": event.get("event_id"),
        "chat_id": int(update.effective_chat.id),
    }
    save_state()


async def event_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()

    if query.message.chat_id != FORWARD_PUBLIC_CHAT_ID:
        await query.answer("Panel event hanya bisa di grup pengurus.", show_alert=True)
        return
    if not _is_admin(query.from_user):
        await query.answer("Hanya Deittee atau Currathor.", show_alert=True)
        return

    parts = (query.data or "").split(":")
    if len(parts) < 4 or parts[1] != "remove":
        return

    event_id = parts[2]
    uid_str = parts[3]
    event = _find_internal_event_by_id(event_id)
    if not event:
        await query.answer("Data event tidak ditemukan.", show_alert=True)
        return
    if event.get("status") not in {"closed", "open"}:
        await query.answer("Event ini sudah diproses.", show_alert=True)
        return

    participants = event.setdefault("participants", {})
    removed = participants.pop(str(uid_str), None)
    if not removed:
        await query.answer("Participant sudah tidak ada di daftar.", show_alert=True)
    else:
        await query.answer(f"Participant {removed.get('name', uid_str)} dihapus.", show_alert=True)

    try:
        await query.edit_message_text(
            _event_admin_text(event),
            reply_markup=_event_admin_keyboard(event),
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[event_admin_callback] edit error: {e}")



# wrap approval supaya topup dan event reward bisa di-ACC tanpa mengganggu resort/registration
_resort_or_old_process_approval_action = _process_approval_action

async def _process_approval_action(context, actor, chat_id: int, target_message, mode: str, reply_message=None):
    info = approval_map.get((chat_id, target_message.message_id)) if target_message else None
    kind = (info or {}).get("kind")
    if kind not in {"topup_promotion", "topup_external_event", "internal_event_reward"}:
        return await _resort_or_old_process_approval_action(context, actor, chat_id, target_message, mode, reply_message)

    if chat_id != FORWARD_PUBLIC_CHAT_ID:
        return False, "Approval hanya bisa dilakukan di grup pengurus."
    if not _is_admin(actor):
        return False, "Hanya Deittee atau Currathor."

    if kind in {"topup_promotion", "topup_external_event"}:
        target_uid = int(info.get("uid"))
        rec = _get_existing_account(target_uid)
        if not rec:
            return False, "Account target tidak ditemukan."
        amount = int(info.get("reward_amount", 0) or 0)
        if amount <= 0:
            return False, "Nominal reward belum valid."
        if mode == "acc":
            if kind == "topup_promotion":
                used = _topup_promo_used_this_week(rec)
                if used >= TOPUP_PROMOTION_WEEKLY_LIMIT:
                    return False, f"Limit promotion user minggu ini sudah penuh ({used}/{TOPUP_PROMOTION_WEEKLY_LIMIT})."
                rec.setdefault("topup_promotion_claims", []).append({
                    "week": _topup_week_key(),
                    "amount": amount,
                    "status": "approved",
                    "approved_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            rec["balance"] = int(rec.get("balance", 0) or 0) + amount
            save_accounts()
            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "✅ Top Up Luxen Reward disetujui.\n\n"
                        f"Sumber : {_topup_source_text(kind, info)}\n"
                        f"Masuk : {_normalize_price_text(amount)} ✦𝕷\n"
                        f"Balance : {_normalize_price_text(rec.get('balance', 0))} ✦𝕷"
                    ),
                )
            except Exception:
                pass
            result_text = f"Top Up reward {_normalize_price_text(amount)} ✦𝕷 untuk account {rec.get('acc_no')} berhasil."
        elif mode == "reject":
            try:
                await context.bot.send_message(chat_id=target_uid, text="Top Up Luxen Reward tidak memperoleh restu.")
            except Exception:
                pass
            result_text = "Top Up reward ditolak."
        else:
            return False, "Mode approval tidak valid."

    elif kind == "internal_event_reward":
        event = _find_internal_event_by_id(info.get("event_id"))
        if not event:
            return False, "Data event tidak ditemukan."
        amount = int(event.get("reward", 0) or 0)
        participants = event.get("participants") or {}
        if mode == "acc":
            success = 0
            for uid_str, pdata in participants.items():
                rec = _get_existing_account(int(uid_str))
                if not rec:
                    continue
                rec["balance"] = int(rec.get("balance", 0) or 0) + amount
                success += 1
                try:
                    await context.bot.send_message(
                        chat_id=int(uid_str),
                        text=(
                            "✅ Internal Event Reward masuk.\n\n"
                            f"Event : {event.get('synopsis', '-')}\n"
                            f"Masuk : {_normalize_price_text(amount)} ✦𝕷\n"
                            f"Balance : {_normalize_price_text(rec.get('balance', 0))} ✦𝕷"
                        ),
                    )
                except Exception:
                    pass
            event["status"] = "approved"
            event["approved_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
            event["approved_by"] = int(getattr(actor, "id", 0) or 0)
            save_accounts()
            result_text = f"Reward internal event terkirim ke {success} participant."
        elif mode == "reject":
            event["status"] = "rejected"
            result_text = "Reward internal event ditolak."
        else:
            return False, "Mode approval tidak valid."

    for key, value in list(approval_map.items()):
        if value.get("kind") == kind and value.get("uid") == (info or {}).get("uid") and value.get("event_id") == (info or {}).get("event_id"):
            approval_map.pop(key, None)
    save_state()
    if reply_message:
        try:
            await reply_message.reply_text(result_text)
        except Exception:
            pass
    return True, result_text

# =========================================================
# Asmoday Invite Link Room
# =========================================================
def _resort_link_send_time(booking: dict):
    now = _now()

    checkin_str = booking.get("checkin")
    if not checkin_str:
        return now

    try:
        checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d").date()
    except Exception:
        return now

    checkin_dt = datetime.combine(
        checkin_date,
        datetime.min.time()
    ).replace(hour=14, minute=0, second=0, microsecond=0)

    # same day dan sudah lewat jam check-in -> kirim langsung
    if checkin_date == now.date() and now >= checkin_dt:
        return now

    # same day sebelum 14:00, atau future day -> kirim jam 14:00
    return checkin_dt

async def resort_booking_link_watcher(context: ContextTypes.DEFAULT_TYPE):
    now = _now()
    changed = False

    for booking in ROOM_BOOKINGS:
        if booking.get("status") not in ("confirmed", "link_ready"):
            continue

        if booking.get("link_sent_at"):
            continue

        send_after = _parse_dt(booking.get("link_send_after"))

        # fallback untuk booking lama yang belum punya jadwal kirim
        if not send_after:
            send_after = _resort_link_send_time(booking)
            booking["link_send_after"] = send_after.strftime("%Y-%m-%d %H:%M:%S")
            changed = True

        if now < send_after:
            continue

        guest_uid = int(booking.get("guest_uid", 0) or 0)
        room_link = booking.get("room_link") or "-"
        if not guest_uid or room_link == "-":
            continue

        try:
            await context.bot.send_message(
                chat_id=guest_uid,
                text=(
                    "𖠷 ╱ LETHÉA RESORT\n\n"
                    f"Jejak reservasi untuk room {booking.get('room_name', '-')} kini telah dibukakan.\n"
                    f"Booking ID : {booking.get('booking_id', '-')}\n"
                    f"Link room : {room_link}"
                ),
                disable_web_page_preview=True,
            )
            booking["link_sent_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            booking["status"] = "link_sent"
            changed = True
        except Exception as e:
            print(f"[resort_booking_link_watcher] failed: {e}")

    if changed:
        save_room_data()

# =========================================================
# Resort Checkout Warning
# =========================================================
def _resort_checkout_warning_time(booking: dict):
    checkout_str = booking.get("checkout")
    if not checkout_str:
        return None

    try:
        checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d").date()
    except Exception:
        return None

    # checkout jam 11:00, warning 30 menit sebelumnya = 10:30
    checkout_dt = datetime.combine(
        checkout_date,
        datetime.min.time()
    ).replace(hour=11, minute=0, second=0, microsecond=0)

    return checkout_dt - timedelta(minutes=30)


async def resort_checkout_warning_watcher(context: ContextTypes.DEFAULT_TYPE):
    now = _now()
    changed = False

    for booking in ROOM_BOOKINGS:
        status = (booking.get("status") or "").lower()

        # hanya booking yang masih hidup
        if status not in {"confirmed", "link_sent"}:
            continue

        if booking.get("checkout_warning_sent_at"):
            continue

        warn_at = _resort_checkout_warning_time(booking)
        if not warn_at:
            continue

        if now < warn_at:
            continue

        guest_uid = int(booking.get("guest_uid", 0) or 0)
        if not guest_uid:
            continue

        try:
            await context.bot.send_message(
                chat_id=guest_uid,
                text=(
                    "𖠷 ╱ LETHÉA RESORT\n\n"
                    f"Jejak tinggalmu di room {booking.get('room_name', '-')} akan segera menutup tirainya.\n"
                    "Harap bersiap untuk checkout pada pukul 11:00.\n\n"
                    f"Booking ID : {booking.get('booking_id', '-')}\n"
                    f"Link room : {booking.get('room_link') or '-'}"
                ),
                disable_web_page_preview=True,
            )
            booking["checkout_warning_sent_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            changed = True
        except Exception as e:
            print(f"[resort_checkout_warning_watcher] failed: {e}")

    if changed:
        save_room_data()

# ========================================================
# RESORT BOOKING ADMIN PANEL
# ========================================================

def _resort_booking_guest_label(booking: dict) -> str:
    guest_name = (booking.get("guest_name") or "").strip()
    guest_username = (booking.get("guest_username") or "").strip().lstrip("@")

    if guest_name and guest_username:
        return f"{guest_name} (@{guest_username})"
    if guest_name:
        return guest_name
    if guest_username:
        return f"@{guest_username}"

    guest_uid = int(booking.get("guest_uid", 0) or 0)
    rec = _get_existing_account(guest_uid) if guest_uid else None
    if rec:
        username = (rec.get("username") or "").strip().lstrip("@")
        name = (rec.get("name") or "").strip()
        if name and username and username != "-":
            return f"{name} (@{username})"
        if name:
            return name
        if username and username != "-":
            return f"@{username}"
        return f"Account {rec.get('acc_no', '-')}"
    return f"UID {guest_uid}" if guest_uid else "-"


def _resort_booking_status_label(status: str) -> str:
    mapping = {
        "pending_payment": "Pending Payment",
        "pending_admin": "Menunggu ACC Admin",
        "confirmed": "Confirmed",
        "link_sent": "Link Sent",
        "rejected": "Rejected",
        "cancelled": "Cancelled",
        "done": "Done",
        "checked_out": "Checked Out",
    }
    return mapping.get((status or "").lower(), status or "-")


def _resort_checkout_notify_text(booking: dict) -> str:
    return (
        "𖠷 ╱ RESORT CHECKOUT NOTICE\n\n"
        f"Nama Pelanggan : {_resort_booking_guest_label(booking)}\n"
        f"Room : {booking.get('room_name') or '-'}\n"
        f"Checkout : {booking.get('checkout') or '-'}\n"
        f"Link Group : {booking.get('room_link') or '-'}"
    )


def _resort_admin_booking_keyboard(booking: dict):
    status = (booking.get("status") or "").lower()
    if status in {"cancelled", "rejected", "checked_out", "done"}:
        return None

    booking_id = booking.get("booking_id") or "-"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Booking", callback_data=f"resortadmincancel:{booking_id}")]
    ])


def _resort_booking_card_text(booking: dict) -> str:
    return (
        "𖠷 ╱ RESORT BOOKING\n\n"
        f"Nama Pelanggan : {_resort_booking_guest_label(booking)}\n"
        f"Booking ID : {booking.get('booking_id') or '-'}\n"
        f"Check-in : {booking.get('checkin') or '-'}\n"
        f"Check-out : {booking.get('checkout') or '-'}\n"
        f"Room : {booking.get('room_name') or '-'}\n"
        f"Link : {booking.get('room_link') or '-'}\n"
        f"Status : {_resort_booking_status_label(booking.get('status'))}"
    )


async def booking_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    if not _can_manage_staff(update.effective_user):
        await update.message.reply_text("Hanya Currathor atau Owner.")
        return

    if not ROOM_BOOKINGS:
        await update.message.reply_text("Belum ada data booking resort.")
        return

    items = sorted(
        ROOM_BOOKINGS,
        key=lambda x: (
            x.get("checkin") or "",
            x.get("checkout") or "",
            x.get("booking_id") or "",
        )
    )

    shown = 0
    for booking in items:
        status = (booking.get("status") or "").lower()

        # skip yang memang sudah final tidak aktif
        if status in {"rejected"}:
            continue

        shown += 1
        await update.message.reply_text(
            _resort_booking_card_text(booking),
            reply_markup=_resort_admin_booking_keyboard(booking),
            disable_web_page_preview=True,
        )

    if shown == 0:
        await update.message.reply_text("Belum ada booking resort yang aktif/tercatat.")


async def resort_admin_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()

    if not _can_manage_staff(query.from_user):
        await query.answer("Hanya Currathor atau Owner.", show_alert=True)
        return

    parts = (query.data or "").split(":", 1)
    if len(parts) != 2:
        return

    booking_id = parts[1]
    booking = next((x for x in ROOM_BOOKINGS if x.get("booking_id") == booking_id), None)
    if not booking:
        await query.answer("Booking tidak ditemukan.", show_alert=True)
        return

    status = (booking.get("status") or "").lower()
    if status in {"cancelled", "rejected", "checked_out", "done"}:
        await query.answer("Booking ini sudah tidak aktif.", show_alert=True)
        return

    booking["status"] = "cancelled"
    booking["cancelled_by_admin_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
    booking["cancelled_by_admin_uid"] = int(query.from_user.id)

    # hentikan semua jadwal / jejak link
    booking["link_send_after"] = None
    booking["link_sent_at"] = None
    booking["checkout_notified_at"] = None

    # batalkan bill kalau masih ada referensi bill resort
    bill_ref = next((x for x in PENDING_BILLS.values() if x.get("resort_booking_id") == booking.get("booking_id")), None)
    if bill_ref and (bill_ref.get("status") or "").lower() not in {"cancelled", "rejected"}:
        bill_ref["status"] = "cancelled"
        save_payment_data()

    # lepas booking angel yang terkait supaya availability ikut balik
    if booking.get("angel_uid"):
        try:
            profile = _ensure_angel_profile(int(booking.get("angel_uid")))
            for item in profile.get("bookings", []):
                if item.get("resort_booking_id") == booking.get("booking_id"):
                    item["status"] = "cancelled"
            save_angel_data()
        except Exception as e:
            print(f"[resort_admin_cancel_callback] angel cleanup error: {e}")

    save_room_data()

    try:
        await context.bot.send_message(
            chat_id=int(booking.get("guest_uid")),
            text=(
                "ⓘ Jejak reservasi resortmu telah dibatalkan oleh pengurus.\n\n"
                f"Booking ID : {booking.get('booking_id') or '-'}\n"
                f"Room : {booking.get('room_name') or '-'}\n"
                f"Tanggal : {booking.get('checkin') or '-'} s/d {booking.get('checkout') or '-'}\n\n"
                "Pembatalan ini tidak mengembalikan dana yang telah terpatri."
            ),
        )
    except Exception as e:
        print(f"[resort_admin_cancel_callback] guest notify error: {e}")

    try:
        await query.edit_message_text(
            _resort_booking_card_text(booking) + "\n\nBooking dibatalkan oleh admin. Tanggal kembali available.",
            disable_web_page_preview=True,
        )
    except Exception:
        pass


async def resort_checkout_watcher(context: ContextTypes.DEFAULT_TYPE):
    today = _now().strftime("%Y-%m-%d")
    changed = False

    for booking in ROOM_BOOKINGS:
        status = (booking.get("status") or "").lower()

        if status not in {"confirmed", "link_sent"}:
            continue

        if booking.get("checkout") != today:
            continue

        if booking.get("checkout_notified_at"):
            continue

        try:
            await context.bot.send_message(
                chat_id=FORWARD_PUBLIC_CHAT_ID,
                text=_resort_checkout_notify_text(booking),
                disable_web_page_preview=True,
            )
            booking["checkout_notified_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
            changed = True
        except Exception as e:
            print(f"[resort_checkout_watcher] failed: {e}")

    if changed:
        save_room_data()

# ========================================================
# BLACKJACK
# ========================================================
BLACKJACK_MAX_PLAYERS = 8


def _blackjack_room_key(chat_id: int) -> str:
    return str(chat_id)


def _blackjack_card_value(card: str) -> int:
    rank = card[:-1]
    if rank in {"J", "Q", "K"}:
        return 10
    if rank == "A":
        return 11
    return int(rank)


def _blackjack_hand_totals(cards):
    total = sum(_blackjack_card_value(c) for c in cards)
    aces = sum(1 for c in cards if c[:-1] == "A")
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    soft = any(c[:-1] == "A" for c in cards) and total <= 21 and sum(_blackjack_card_value(c) for c in cards) != total
    return total, soft


def _blackjack_is_blackjack(cards):
    total, _ = _blackjack_hand_totals(cards)
    return len(cards) == 2 and total == 21


def _blackjack_can_split(cards):
    return len(cards) == 2 and _blackjack_card_value(cards[0]) == _blackjack_card_value(cards[1])


def _blackjack_draw(room: dict):
    deck = room.setdefault("deck", [])
    if not deck:
        import random
        deck[:] = _new_deck()
        random.shuffle(deck)
    return deck.pop(0)


def _blackjack_player_ids(room: dict):
    return list(room.get("player_order") or [])


def _blackjack_player_name(room: dict, uid: str) -> str:
    p = room.get("players", {}).get(str(uid)) or {}
    return p.get("name") or f"Player {uid}"


def _blackjack_format_hand(hand: dict, hide_second: bool = False) -> str:
    cards = list(hand.get("cards") or [])
    if hide_second and len(cards) >= 2:
        shown = [cards[0], "??"]
        return " ".join(shown)
    return _format_cards(cards)


def _blackjack_active_hand(room: dict, uid: str):
    player = room.get("players", {}).get(str(uid)) or {}
    hands = player.get("hands") or []
    idx = int(player.get("active_hand_index", 0) or 0)
    if 0 <= idx < len(hands):
        return hands[idx], idx
    return None, idx


def _blackjack_advance_hand(room: dict, uid: str):
    player = room.get("players", {}).get(str(uid)) or {}
    hands = player.get("hands") or []
    idx = int(player.get("active_hand_index", 0) or 0)
    while idx < len(hands) and hands[idx].get("done"):
        idx += 1
    player["active_hand_index"] = idx
    if idx >= len(hands):
        player["finished"] = True
        return None
    return str(uid)


def _blackjack_next_turn_uid(room: dict):
    order = [str(x) for x in room.get("player_order") or []]
    current = str(room.get("current_turn_uid") or "")
    if current and current in order:
        start = order.index(current)
    else:
        start = -1
    for offset in range(1, len(order) + 1):
        uid = order[(start + offset) % len(order)]
        player = room.get("players", {}).get(uid) or {}
        if not player.get("finished"):
            return uid
    return None


def _blackjack_round_ready(room: dict) -> bool:
    for uid in _blackjack_player_ids(room):
        p = room.get("players", {}).get(str(uid)) or {}
        if int(p.get("bet", 0)) <= 0:
            return False
    return bool(_blackjack_player_ids(room))


def _blackjack_action_keyboard(chat_id: int, room: dict, uid: str):
    player = room.get("players", {}).get(str(uid)) or {}
    hand, hand_index = _blackjack_active_hand(room, uid)
    if not hand:
        return None
    rows = [[InlineKeyboardButton("Hit", callback_data=f"blackjackact:{chat_id}:hit:{hand_index}"), InlineKeyboardButton("Stand", callback_data=f"blackjackact:{chat_id}:stand:{hand_index}")]]
    cards = hand.get("cards") or []
    if len(cards) == 2 and not hand.get("acted_once"):
        if int(player.get("stack", 0)) >= int(hand.get("bet", 0)):
            rows[0].append(InlineKeyboardButton("Double", callback_data=f"blackjackact:{chat_id}:double:{hand_index}"))
        extra = []
        if not hand.get("split_done") and _blackjack_can_split(cards) and int(player.get("stack", 0)) >= int(hand.get("bet", 0)):
            extra.append(InlineKeyboardButton("Split", callback_data=f"blackjackact:{chat_id}:split:{hand_index}"))
        extra.append(InlineKeyboardButton("Surrender", callback_data=f"blackjackact:{chat_id}:surrender:{hand_index}"))
        rows.append(extra)
    return InlineKeyboardMarkup(rows)


def _blackjack_waiting_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join", callback_data="blackjack:join"), InlineKeyboardButton("Leave", callback_data="blackjack:leave")], [InlineKeyboardButton("Start", callback_data="blackjack:start"), InlineKeyboardButton("Close Table", callback_data="blackjack:cancel")]])


def _blackjack_next_round_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Next Round", callback_data="blackjack:nextround"), InlineKeyboardButton("Close Table", callback_data="blackjack:close")]])


def _blackjack_status_text(room: dict) -> str:
    dealer_cards = room.get("dealer_hand", {}).get("cards") or []
    hide = room.get("stage") in {"betting", "player_turn"}
    lines = [
        "‹🃏:۰  𝗕𝗟𝗔𝗖𝗞𝗝𝗔𝗖𝗞",
        "— — • — • — — • — • — — • — • — —",
        f"⌦ Dealer : Asmoday",
        f"⌦ Stage  : {(room.get('stage') or 'waiting').replace('_', ' ').title()}",
        f"⌦ Pot    : {_normalize_price_text(room.get('pot', 0))}",
        "",
        f"⌦ Dealer Hand : {_blackjack_format_hand({'cards': dealer_cards}, hide_second=hide) if dealer_cards else '-'}",
    ]
    if dealer_cards and not hide:
        total, _ = _blackjack_hand_totals(dealer_cards)
        lines.append(f"⌦ Dealer Total : {total}")
    lines.extend(["", "› Player Seats"])
    for uid in _blackjack_player_ids(room):
        p = room.get("players", {}).get(str(uid)) or {}
        label = f"{p.get('name')} · bet {_normalize_price_text(p.get('bet', 0))} · stack {_normalize_price_text(p.get('stack', 0))}"
        if str(uid) == str(room.get("current_turn_uid") or "") and room.get("stage") == "player_turn":
            label += " · acting"
        lines.append(f"› {label}")
        for idx, hand in enumerate(p.get("hands") or []):
            total, _ = _blackjack_hand_totals(hand.get("cards") or [])
            suffix = []
            if hand.get("blackjack"):
                suffix.append("Blackjack")
            if hand.get("bust"):
                suffix.append("Bust")
            if hand.get("surrendered"):
                suffix.append("Surrender")
            if hand.get("done") and not suffix:
                suffix.append("Stand")
            extra = f" · {' / '.join(suffix)}" if suffix else ""
            lines.append(f"  · Hand {idx + 1} : {_format_cards(hand.get('cards') or [])} · {total}{extra}")
    if room.get("stage") == "waiting":
        lines.extend(["", "› 2–8 pemain dapat duduk di meja.", "› Masing-masing bertaruh melawan Asmoday, bukan sesama pemain."])
    return "\n".join(lines)


async def _blackjack_refresh_message(context, room: dict):
    message_id = room.get("message_id")
    if not message_id:
        return
    reply_markup = None
    if room.get("stage") == "waiting":
        reply_markup = _blackjack_waiting_keyboard()
    elif room.get("stage") == "player_turn" and room.get("current_turn_uid"):
        reply_markup = _blackjack_action_keyboard(room.get("chat_id"), room, str(room.get("current_turn_uid")))
    text_value = _blackjack_status_text(room)
    markup_value = reply_markup.to_dict() if reply_markup else None
    if room.get("_last_render_text") == text_value and room.get("_last_render_markup") == markup_value:
        return
    try:
        await context.bot.edit_message_text(chat_id=room.get("chat_id"), message_id=message_id, text=text_value, reply_markup=reply_markup)
        room["_last_render_text"] = text_value
        room["_last_render_markup"] = markup_value
    except Exception as e:
        if "message is not modified" in str(e).lower():
            room["_last_render_text"] = text_value
            room["_last_render_markup"] = markup_value
            return
        print(f"[_blackjack_refresh_message] error: {e}")


async def _blackjack_send_room_message(context, room: dict, text: str, *, reply_markup=None):
    kwargs = {"chat_id": room.get("chat_id"), "text": text, "reply_to_message_id": room.get("message_id")}
    if room.get("thread_id"):
        kwargs["message_thread_id"] = room.get("thread_id")
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    return await context.bot.send_message(**kwargs)


def _blackjack_intro_text() -> str:
    return (
        "‹🃏:۰  𝗕𝗟𝗔𝗖𝗞𝗝𝗔𝗖𝗞 — 𝗚𝗔𝗠𝗘 𝗙𝗟𝗢𝗪\n"
        "— — • — • — — • — • — — • — • — —\n"
        "Each player stands against Asmoday alone.\n"
        "The target is simple: approach 21 without crossing it.\n\n"
        "› Hit      : ambil 1 kartu tambahan\n"
        "› Stand    : berhenti pada total saat ini\n"
        "› Double   : gandakan bet, ambil tepat 1 kartu, lalu selesai\n"
        "› Split    : jika dua kartu awal bernilai sama, pecah jadi dua hand\n"
        "› Surrender: mundur lebih awal dan hanya kehilangan setengah bet\n\n"
        "Asmoday akan membuka satu kartu dealer, menyembunyikan satu kartu lain,\n"
        "lalu memanggil pemain satu per satu hingga seluruh meja selesai bergerak."
    )


async def _blackjack_take_from_stack(room: dict, uid: str, amount: int) -> int:
    amount = max(0, int(amount or 0))
    if amount <= 0:
        return 0
    player = room.get("players", {}).get(str(uid)) or {}
    paid = min(int(player.get("stack", 0)), amount)
    player["stack"] = int(player.get("stack", 0)) - paid
    room["pot"] = int(room.get("pot", 0)) + paid
    rec = _get_existing_account(int(uid))
    if rec:
        rec["balance"] = int(rec.get("balance", 0)) - paid
    return paid


def _blackjack_finish_hand_flags(hand: dict):
    total, _ = _blackjack_hand_totals(hand.get("cards") or [])
    hand["blackjack"] = _blackjack_is_blackjack(hand.get("cards") or []) and not hand.get("split_child")
    hand["bust"] = total > 21
    if hand["bust"]:
        hand["done"] = True


def _blackjack_prepare_round(room: dict):
    import random
    deck = _new_deck()
    random.shuffle(deck)
    room["deck"] = deck
    room["pot"] = 0
    room["dealer_hand"] = {"cards": []}
    room["stage"] = "betting"
    room["current_turn_uid"] = None
    room["intro_sent"] = room.get("intro_sent", False)
    for uid in _blackjack_player_ids(room):
        rec = _get_existing_account(int(uid))
        p = room["players"][str(uid)]
        p["stack"] = int(rec.get("balance", 0) if rec else p.get("stack", 0))
        p["bet"] = 0
        p["hands"] = []
        p["finished"] = False
        p["active_hand_index"] = 0


async def _blackjack_begin_player_turns(context, room: dict):
    room["stage"] = "player_turn"
    order = _blackjack_player_ids(room)
    room["current_turn_uid"] = str(order[0]) if order else None
    for uid in order:
        _blackjack_advance_hand(room, str(uid))
    room["current_turn_uid"] = _blackjack_next_turn_uid(room)
    await _blackjack_refresh_message(context, room)
    if room.get("current_turn_uid"):
        uid = str(room.get("current_turn_uid"))
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday calls\n\n› {_blackjack_player_name(room, uid)}, meja menunggumu.", reply_markup=_blackjack_action_keyboard(room.get('chat_id'), room, uid))
    else:
        await _blackjack_dealer_phase(context, room)


async def _blackjack_deal_initial(context, room: dict):
    for uid in _blackjack_player_ids(room):
        cards = [_blackjack_draw(room), _blackjack_draw(room)]
        hand = {"cards": cards, "bet": int(room["players"][str(uid)].get("bet", 0)), "done": False, "bust": False, "blackjack": False, "doubled": False, "surrendered": False, "acted_once": False, "split_child": False}
        _blackjack_finish_hand_flags(hand)
        if hand.get("blackjack"):
            hand["done"] = True
        room["players"][str(uid)]["hands"] = [hand]
        room["players"][str(uid)]["active_hand_index"] = 0
        room["players"][str(uid)]["finished"] = False
    room["dealer_hand"] = {"cards": [_blackjack_draw(room), _blackjack_draw(room)]}
    await _blackjack_refresh_message(context, room)
    await _blackjack_send_room_message(context, room, "‹🃏:۰  Asmoday deals\n\n› Semua kartu awal telah diletakkan di atas meja.\n› Satu kartu dealer terbuka. Satu lagi tetap tersembunyi.")
    await _blackjack_begin_player_turns(context, room)


async def _blackjack_advance_turn(context, room: dict):
    current_uid = str(room.get("current_turn_uid") or "")
    if current_uid:
        if _blackjack_advance_hand(room, current_uid) is not None:
            room["current_turn_uid"] = current_uid
        else:
            room["current_turn_uid"] = _blackjack_next_turn_uid(room)
    else:
        room["current_turn_uid"] = _blackjack_next_turn_uid(room)
    await _blackjack_refresh_message(context, room)
    if room.get("current_turn_uid"):
        uid = str(room.get("current_turn_uid"))
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday calls\n\n› {_blackjack_player_name(room, uid)}, giliranmu berikutnya.", reply_markup=_blackjack_action_keyboard(room.get('chat_id'), room, uid))
    else:
        await _blackjack_dealer_phase(context, room)


async def _blackjack_dealer_phase(context, room: dict):
    room["stage"] = "dealer_turn"
    await _blackjack_refresh_message(context, room)
    dealer_cards = room.get("dealer_hand", {}).get("cards") or []
    await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday reveals\n\n› Dealer Hand : {_format_cards(dealer_cards)}")
    while True:
        total, _ = _blackjack_hand_totals(dealer_cards)
        if total >= 17:
            break
        card = _blackjack_draw(room)
        dealer_cards.append(card)
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday acts\n\n› Dealer draws {card}.")
    await _blackjack_resolve_round(context, room)


async def _blackjack_resolve_round(context, room: dict):
    room["stage"] = "resolved"
    dealer_cards = room.get("dealer_hand", {}).get("cards") or []
    dealer_total, _ = _blackjack_hand_totals(dealer_cards)
    dealer_blackjack = _blackjack_is_blackjack(dealer_cards)
    dealer_bust = dealer_total > 21
    lines = ["‹🃏:۰  𝗕𝗟𝗔𝗖𝗞𝗝𝗔𝗖𝗞 — 𝗥𝗘𝗦𝗨𝗟𝗧", "— — • — • — — • — • — — • — • — —", f"⌦ Dealer : Asmoday", f"⌦ Dealer Hand : {_format_cards(dealer_cards)} · {dealer_total}", ""]
    for uid in _blackjack_player_ids(room):
        player = room.get("players", {}).get(str(uid)) or {}
        player_name = player.get("name")
        for idx, hand in enumerate(player.get("hands") or []):
            total, _ = _blackjack_hand_totals(hand.get("cards") or [])
            bet = int(hand.get("bet", 0))
            outcome = "Dealer Wins"
            payout = 0
            if hand.get("surrendered"):
                payout = bet // 2
                outcome = "Surrender"
            elif hand.get("bust"):
                outcome = "Bust"
            else:
                player_blackjack = hand.get("blackjack")
                if player_blackjack and not dealer_blackjack:
                    payout = bet * 2
                    outcome = "Blackjack"
                elif dealer_bust:
                    payout = bet * 2
                    outcome = "Win"
                elif dealer_blackjack and not player_blackjack:
                    outcome = "Dealer Blackjack"
                elif player_blackjack and dealer_blackjack:
                    payout = bet
                    outcome = "Push"
                elif total > dealer_total:
                    payout = bet * 2
                    outcome = "Win"
                elif total == dealer_total:
                    payout = bet
                    outcome = "Push"
                else:
                    outcome = "Dealer Wins"
            if payout > 0:
                rec = _get_existing_account(int(uid))
                if rec:
                    rec["balance"] = int(rec.get("balance", 0)) + payout
            lines.append(f"› {player_name} · Hand {idx + 1}")
            lines.append(f"  · Cards : {_format_cards(hand.get('cards') or [])}")
            lines.append(f"  · Total : {total}")
            lines.append(f"  · Result : {outcome}")
            lines.append("")
    save_accounts()
    await _blackjack_refresh_message(context, room)
    await _blackjack_send_room_message(context, room, "\n".join(lines).strip(), reply_markup=_blackjack_next_round_keyboard())


async def blackjack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Blackjack hanya bisa dibuka di group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu sebelum buka meja Blackjack.")
        return
    room_key = _blackjack_room_key(chat.id)
    if room_key in BLACKJACK_ROOMS:
        await update.message.reply_text("Masih ada meja Blackjack aktif di grup ini.")
        return
    room = {"chat_id": chat.id, "thread_id": getattr(update.effective_message, "message_thread_id", None), "host_id": user.id, "stage": "waiting", "player_order": [str(user.id)], "players": {str(user.id): {"name": user.full_name or user.username or f"User {user.id}", "stack": int(rec.get("balance", 0)), "bet": 0, "hands": [], "finished": False, "active_hand_index": 0}}, "dealer_hand": {"cards": []}, "pot": 0, "deck": [], "message_id": None, "intro_sent": False}
    sent = await update.message.reply_text(_blackjack_status_text(room), reply_markup=_blackjack_waiting_keyboard(), message_thread_id=getattr(update.effective_message, "message_thread_id", None))
    room["message_id"] = sent.message_id
    BLACKJACK_ROOMS[room_key] = room
    await _blackjack_send_room_message(context, room, "‹🃏:۰  Asmoday opens the table\n\n› Blackjack telah dibuka.\n› Pemain menghadapi dealer, bukan sesama pemain.\n› Tekan Join untuk duduk, lalu Start untuk membuka ronde pertama.")


async def blackjack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    room = BLACKJACK_ROOMS.get(_blackjack_room_key(chat_id))
    if not room:
        await query.answer("Meja Blackjack tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    uid = str(user.id)
    if action == "join":
        if room.get("stage") != "waiting":
            await query.answer("Ronde sudah berjalan.", show_alert=True)
            return
        if uid in room.get("players", {}):
            return
        if len(room.get("player_order", [])) >= BLACKJACK_MAX_PLAYERS:
            await query.answer("Kursi meja sudah penuh.", show_alert=True)
            return
        rec = _get_existing_account(user.id)
        if not _has_gamble_access(rec):
            await query.answer("Kamu butuh account number yang valid.", show_alert=True)
            return
        room["players"][uid] = {"name": user.full_name or user.username or f"User {user.id}", "stack": int(rec.get("balance", 0)), "bet": 0, "hands": [], "finished": False, "active_hand_index": 0}
        room["player_order"].append(uid)
        await _blackjack_refresh_message(context, room)
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday notes\n\n› {room['players'][uid]['name']} mengambil kursi di meja Blackjack.")
        return
    if action == "leave":
        if room.get("stage") != "waiting":
            await query.answer("Ronde sudah berjalan.", show_alert=True)
            return
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Tutup meja jika ingin batal.", show_alert=True)
            return
        if uid in room.get("players", {}):
            room["players"].pop(uid, None)
            room["player_order"] = [x for x in room.get("player_order", []) if str(x) != uid]
            await _blackjack_refresh_message(context, room)
        return
    if action == "cancel" or action == "close":
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa menutup meja.", show_alert=True)
            return
        BLACKJACK_ROOMS.pop(_blackjack_room_key(chat_id), None)
        await query.edit_message_text("‹🃏:۰  Asmoday menutup meja Blackjack.")
        return
    if action == "start" or action == "nextround":
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa memulai ronde.", show_alert=True)
            return
        if len(room.get("player_order", [])) < 1:
            await query.answer("Belum ada pemain di meja.", show_alert=True)
            return
        _blackjack_prepare_round(room)
        await _blackjack_refresh_message(context, room)
        if not room.get("intro_sent"):
            room["intro_sent"] = True
            await _blackjack_send_room_message(context, room, _blackjack_intro_text())
        await _blackjack_send_room_message(context, room, "‹🃏:۰  Asmoday calls\n\n› Kirim nominal bet masing-masing dengan angka biasa.\n› Setelah seluruh bet masuk, kartu akan dibagikan.")
        return


async def blackjack_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 4:
        return
    _, room_chat_id_raw, action, hand_index_raw = parts
    room = BLACKJACK_ROOMS.get(_blackjack_room_key(int(room_chat_id_raw)))
    if not room or room.get("stage") != "player_turn":
        await query.answer("Aksi Blackjack tidak tersedia.", show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid != str(room.get("current_turn_uid") or ""):
        await query.answer("Bukan giliranmu.", show_alert=True)
        return
    player = room.get("players", {}).get(uid) or {}
    hand, idx = _blackjack_active_hand(room, uid)
    if not hand:
        return
    if int(hand_index_raw) != idx:
        await query.answer("Hand ini sudah bergeser.", show_alert=True)
        return
    if action == "hit":
        card = _blackjack_draw(room)
        hand["cards"].append(card)
        hand["acted_once"] = True
        _blackjack_finish_hand_flags(hand)
        total, _ = _blackjack_hand_totals(hand.get("cards") or [])
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday deals\n\n› {player.get('name')} menerima {card}.\n› Total kini {total}.")
        if hand.get("bust"):
            await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday declares\n\n› {player.get('name')} melewati angka 21.")
            await _blackjack_advance_turn(context, room)
        else:
            await _blackjack_refresh_message(context, room)
        return
    if action == "stand":
        hand["done"] = True
        hand["acted_once"] = True
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday records\n\n› {player.get('name')} menahan hand ini apa adanya.")
        await _blackjack_advance_turn(context, room)
        return
    if action == "double":
        bet = int(hand.get("bet", 0))
        if int(player.get("stack", 0)) < bet or len(hand.get("cards") or []) != 2 or hand.get("acted_once"):
            await query.answer("Double down tidak valid sekarang.", show_alert=True)
            return
        paid = await _blackjack_take_from_stack(room, uid, bet)
        hand["bet"] = int(hand.get("bet", 0)) + paid
        card = _blackjack_draw(room)
        hand["cards"].append(card)
        hand["acted_once"] = True
        hand["doubled"] = True
        hand["done"] = True
        _blackjack_finish_hand_flags(hand)
        save_accounts()
        total, _ = _blackjack_hand_totals(hand.get("cards") or [])
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday records\n\n› {player.get('name')} menggandakan bet lalu menerima {card}.\n› Total akhir hand ini {total}.")
        await _blackjack_advance_turn(context, room)
        return
    if action == "split":
        bet = int(hand.get("bet", 0))
        if hand.get("acted_once") or not _blackjack_can_split(hand.get("cards") or []) or int(player.get("stack", 0)) < bet:
            await query.answer("Split tidak valid untuk hand ini.", show_alert=True)
            return
        await _blackjack_take_from_stack(room, uid, bet)
        c1, c2 = hand["cards"]
        hand1 = {"cards": [c1, _blackjack_draw(room)], "bet": bet, "done": False, "bust": False, "blackjack": False, "doubled": False, "surrendered": False, "acted_once": False, "split_child": True, "split_done": True}
        hand2 = {"cards": [c2, _blackjack_draw(room)], "bet": bet, "done": False, "bust": False, "blackjack": False, "doubled": False, "surrendered": False, "acted_once": False, "split_child": True, "split_done": True}
        _blackjack_finish_hand_flags(hand1)
        _blackjack_finish_hand_flags(hand2)
        player["hands"][idx:idx+1] = [hand1, hand2]
        player["active_hand_index"] = idx
        save_accounts()
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday divides\n\n› {player.get('name')} memecah hand menjadi dua jalur taruhan.")
        await _blackjack_refresh_message(context, room)
        return
    if action == "surrender":
        if hand.get("acted_once") or len(hand.get("cards") or []) != 2:
            await query.answer("Surrender hanya tersedia di awal hand.", show_alert=True)
            return
        hand["surrendered"] = True
        hand["done"] = True
        hand["acted_once"] = True
        await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday records\n\n› {player.get('name')} meninggalkan hand ini dan hanya mempertaruhkan setengah dari betnya.")
        await _blackjack_advance_turn(context, room)
        return


async def blackjack_bet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private" or not msg or not msg.text:
        return
    room = BLACKJACK_ROOMS.get(_blackjack_room_key(chat.id))
    if not room or room.get("stage") != "betting":
        return
    uid = str(user.id)
    if uid not in room.get("players", {}):
        return
    raw = (msg.text or "").strip().replace(",", "").replace(".", "")
    if not raw.isdigit():
        return
    bet = int(raw)
    if bet <= 0:
        return
    player = room["players"][uid]
    if int(player.get("bet", 0)) > 0:
        return
    if bet > int(player.get("stack", 0)):
        await msg.reply_text(f"Stack kamu tidak cukup. Tersisa {_normalize_price_text(player.get('stack', 0))}.")
        return
    await _blackjack_take_from_stack(room, uid, bet)
    player["bet"] = bet
    save_accounts()
    await _blackjack_refresh_message(context, room)
    await _blackjack_send_room_message(context, room, f"‹🃏:۰  Asmoday accepts\n\n› Bet {_blackjack_player_name(room, uid)} : {_normalize_price_text(bet)}")
    if _blackjack_round_ready(room):
        await _blackjack_deal_initial(context, room)


# =========================================================
# DICE POKER
# =========================================================
# =========================================================
# DICE POKER
# =========================================================
DICE_POKER_HAND_LABELS = {
    7: "Five of a Kind",
    6: "Four of a Kind",
    5: "Full House",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Dice",
}

def _dice_poker_room_key(chat_id: int) -> str:
    return str(chat_id)


def _format_luxen(amount: int) -> str:
    try:
        return f"{int(amount):,} Luxen"
    except Exception:
        return f"{amount} Luxen"


def _roll_dice(n: int):
    import random
    return [random.randint(1, 6) for _ in range(n)]


def _format_dice(dice):
    return " ".join(f"🎲{x}" for x in dice)


def _dice_counts(dice):
    counts = {}
    for d in dice:
        counts[d] = counts.get(d, 0) + 1
    return counts


def _evaluate_dice_poker_hand(dice):
    """
    return (rank_index, tiebreak_list, label)
    urutan rank:
    7 Five of a Kind
    6 Four of a Kind
    5 Full House
    4 Straight
    3 Three of a Kind
    2 Two Pair
    1 One Pair
    0 High Dice
    """
    dice = sorted(dice)
    counts = _dice_counts(dice)
    freq = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    values_desc = sorted(dice, reverse=True)

    # Straight
    if dice == [1, 2, 3, 4, 5]:
        return (4, [5], "Straight")
    if dice == [2, 3, 4, 5, 6]:
        return (4, [6], "Straight")

    # Five of a kind
    if freq[0][1] == 5:
        v = freq[0][0]
        return (7, [v], "Five of a Kind")

    # Four of a kind
    if freq[0][1] == 4:
        four = freq[0][0]
        kicker = max(v for v in dice if v != four)
        return (6, [four, kicker], "Four of a Kind")

    # Full house
    if len(freq) == 2 and freq[0][1] == 3 and freq[1][1] == 2:
        return (5, [freq[0][0], freq[1][0]], "Full House")

    # Three of a kind
    if freq[0][1] == 3:
        trip = freq[0][0]
        kickers = sorted([v for v in dice if v != trip], reverse=True)
        return (3, [trip] + kickers, "Three of a Kind")

    # Two pair
    pair_values = sorted([v for v, c in counts.items() if c == 2], reverse=True)
    if len(pair_values) == 2:
        kicker = max(v for v, c in counts.items() if c == 1)
        return (2, pair_values + [kicker], "Two Pair")

    # One pair
    if len(pair_values) == 1:
        pair = pair_values[0]
        kickers = sorted([v for v in dice if v != pair], reverse=True)
        return (1, [pair] + kickers, "One Pair")

    # High dice
    return (0, values_desc, "High Dice")


def _dice_poker_compare(a_dice, b_dice):
    a_score = _evaluate_dice_poker_hand(a_dice)
    b_score = _evaluate_dice_poker_hand(b_dice)
    if a_score[:2] > b_score[:2]:
        return 1, a_score, b_score
    if a_score[:2] < b_score[:2]:
        return -1, a_score, b_score
    return 0, a_score, b_score


def _dice_poker_turn_uid(room: dict):
    order = room.get("turn_order") or []
    if not order:
        return None
    idx = int(room.get("turn_index", 0)) % len(order)
    return order[idx]


def _dice_poker_next_turn(room: dict):
    order = room.get("turn_order") or []
    if not order:
        return
    room["turn_index"] = (int(room.get("turn_index", 0)) + 1) % len(order)


def _dice_poker_all_finished(room: dict) -> bool:
    for p in room.get("players", {}).values():
        if not p.get("finished"):
            return False
    return True


def _dice_poker_status_text(room: dict):
    players = room.get("players", {})
    lines = [
        "‹🎲:۰ 𝗗𝗜𝗖𝗘 𝗣𝗢𝗞𝗘𝗥",
        "— — • — • — — • — • — — • — • — —",
        f"• [] Status : {(room.get('status') or 'waiting').upper()}",
        f"• [] Host : {room.get('host_name', '-')}",
        "",
        "———— ╱╱ Player List :",
    ]

    if not players:
        lines.append("› -")
    else:
        turn_uid = _dice_poker_turn_uid(room)
        for uid, p in players.items():
            marks = []
            if str(uid) == str(room.get("host_id")):
                marks.append("Host")
            if str(uid) == str(turn_uid) and room.get("status") == "playing":
                marks.append("Turn")
            if p.get("finished"):
                marks.append("Locked")
            mark_text = f" [{' | '.join(marks)}]" if marks else ""
            lines.append(
                f"› {p.get('name', 'Player')}{mark_text} | "
                f"Roll {p.get('roll_count', 0)}/3 | "
                f"{p.get('final_label') or '-'}"
            )

    if room.get("status") == "waiting":
        lines.extend([
            "",
            "‹🎲:۰  𝗗𝗜𝗖𝗘 𝗣𝗢𝗞𝗘𝗥 — 𝗖𝗔𝗥𝗔 𝗕𝗘𝗥𝗠𝗔𝗜𝗡\n"
            "— — • — • — — • — • — — • — • — —\n"
            "Dice Poker adalah permainan kombinasi dadu. Tujuannya adalah membentuk kombinasi dadu terkuat dari 5 dadu yang dimiliki.\n\n"
            "⌦ Setiap pemain menerima 5 dadu\n"
            "⌦ Setiap pemain memiliki maksimal 3 kali roll dalam satu ronde\n\n"
            "› Pada roll pertama, semua dadu dilempar secara otomatis.\n"
            "› Setelah melihat hasil, pemain dapat memilih dadu mana yang ingin disimpan.\n"
            "› Dadu yang tidak disimpan dapat dilempar ulang.\n"
            "› Pemain dapat melakukan hingga 2 kali reroll tambahan (total 3 roll).\n\n"
            "𝗖𝗮𝗿𝗮 𝗺𝗲𝗻𝗮𝗻𝗴𝗸𝗮𝗻 𝗸𝗼𝗺𝗯𝗶𝗻𝗮𝘀𝗶:\n"
            "› Setelah semua pemain selesai roll, hasil akhir dibandingkan.\n"
            "› Kombinasi terkuat menentukan pemenang ronde.\n\n"
            "𝗨𝗿𝘂𝘁𝗮𝗻 𝗸𝗼𝗺𝗯𝗶𝗻𝗮𝘀𝗶:\n"
            "› Five of a Kind (5 angka sama)\n"
            "› Four of a Kind (4 angka sama)\n"
            "› Full House (3 + 2)\n"
            "› Straight (1-2-3-4-5 atau 2-3-4-5-6)\n"
            "› Three of a Kind (3 angka sama)\n"
            "› Two Pair\n"
            "› One Pair\n"
            "› High Dice (nilai tertinggi)\n\n"
            "𝗝𝗶𝗸𝗮 𝘁𝗲𝗿𝗷𝗮𝗱𝗶 𝘀𝗲𝗿𝗶:\n"
            "› Dibandingkan nilai dadu tertinggi dalam kombinasi.\n"
            "› Jika masih sama, bandingkan urutan dadu berikutnya.\n\n"
            "𝗣𝗲𝗺𝗲𝗻𝗮𝗻𝗴 𝗿𝗼𝗻𝗱𝗲:\n"
            "› Pemain dengan kombinasi terkuat mengambil round pot.\n"
            "› Jika seri, pot dibagi rata.\n\n"
            "𝗖𝗮𝘁𝗮𝘁𝗮𝗻:\n"
            "› Tidak semua roll harus diulang — menyimpan kombinasi yang tepat adalah kunci.\n"
            "› Terlalu serakah dapat merusak kombinasi yang sudah kuat.\n"
            "› Mengetahui kapan berhenti lebih penting daripada terus mengejar hasil sempurna.\n\n"
            "Asmoday tidak menghargai keberuntungan semata. Ia menilai siapa yang tahu kapan harus berhenti."
        ])

    elif room.get("status") == "betting":
        lines.extend([
            "",
            "Kirim nominal betting dengan angka biasa.",
        ])
    elif room.get("status") == "playing":
        turn_uid = _dice_poker_turn_uid(room)
        if turn_uid and str(turn_uid) in players:
            lines.extend([
                "",
                f"• [] Turn : {players[str(turn_uid)].get('name', 'Player')}",
            ])

    return "\n".join(lines)


def _dice_poker_waiting_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Join", callback_data="dicepoker:join"),
            InlineKeyboardButton("Leave", callback_data="dicepoker:leave"),
        ],
        [
            InlineKeyboardButton("Start", callback_data="dicepoker:start"),
            InlineKeyboardButton("Cancel", callback_data="dicepoker:cancel"),
        ],
    ])


def _dice_poker_turn_keyboard(room_chat_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Roll", callback_data=f"dicepokerturn:{room_chat_id}:roll"),
            InlineKeyboardButton("Stop", callback_data=f"dicepokerturn:{room_chat_id}:stop"),
        ]
    ])


async def _dice_poker_send_room_message(context, room: dict, text: str, *, reply_to_room: bool = True, reply_markup=None):
    kwargs = {"chat_id": room.get("chat_id"), "text": text}
    thread_id = room.get("thread_id")
    if thread_id:
        kwargs["message_thread_id"] = thread_id
    if reply_to_room and room.get("message_id"):
        kwargs["reply_to_message_id"] = room.get("message_id")
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    return await context.bot.send_message(**kwargs)


async def _dice_poker_refresh_message(context, chat_id: int, room: dict):
    message_id = room.get("message_id")
    if not message_id:
        return

    reply_markup = None
    if room.get("status") == "waiting":
        reply_markup = _dice_poker_waiting_keyboard()
    elif room.get("status") == "playing":
        turn_uid = _dice_poker_turn_uid(room)
        if turn_uid:
            reply_markup = _dice_poker_turn_keyboard(chat_id)

    text_value = _dice_poker_status_text(room)
    markup_value = reply_markup.to_dict() if reply_markup else None
    if room.get("_last_render_text") == text_value and room.get("_last_render_markup") == markup_value:
        return

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text_value,
            reply_markup=reply_markup,
        )
        room["_last_render_text"] = text_value
        room["_last_render_markup"] = markup_value
    except Exception as e:
        if "message is not modified" in str(e).lower():
            room["_last_render_text"] = text_value
            room["_last_render_markup"] = markup_value
            return
        print(f"[_dice_poker_refresh_message] error: {e}")


async def _dice_poker_dm_state(context, uid: int, room: dict):
    p = room.get("players", {}).get(str(uid))
    if not p:
        return

    locked = p.get("locked_idx", [])
    dice = p.get("dice") or []
    roll_count = int(p.get("roll_count", 0))
    lock_text = ", ".join(str(i + 1) for i in locked) if locked else "-"

    text = (
        f"Dice : {_format_dice(dice)}\n"
        f"Roll : {roll_count}/3\n"
        f"Locked Slot : {lock_text}\n\n"
        "Kirim slot yang mau di-keep. Contoh: 1 3 5\n"
        "Atau kirim:\n"
        "reroll\n"
        "stop"
    )

    try:
        await context.bot.send_message(chat_id=int(uid), text=text)
    except Exception as e:
        print(f"[_dice_poker_dm_state] failed uid={uid}: {e}")


async def _dice_poker_finish(context, chat_id: int, room: dict):
    players = room.get("players", {})
    results = []

    for uid, p in players.items():
        score = _evaluate_dice_poker_hand(p.get("dice") or [])
        p["final_label"] = score[2]
        p["final_score"] = score
        results.append((uid, p, score))

    results.sort(key=lambda x: x[2][:2], reverse=True)
    top_score = results[0][2][:2]
    winners = [item for item in results if item[2][:2] == top_score]

    lines = [
        "‹🎲:۰ 𝐒𝐡𝐨𝐰𝐝𝐨𝐰𝐧 !",
        "",
    ]

    for uid, p, score in results:
        lines.append(
            f"• {p.get('name')}\n"
            f"⌦  Dice : {_format_dice(p.get('dice') or [])}\n"
            f"⌦  Hand : {score[2]}"
        )
        lines.append("")

    if len(winners) == 1:
        lines.append(f"Pemenang : {winners[0][1].get('name')}")
    else:
        lines.append("Pemenang : " + ", ".join(x[1].get("name") for x in winners) + " (Tie)")

    room["status"] = "resolved"
    await _dice_poker_refresh_message(context, chat_id, room)
    await _dice_poker_send_room_message(context, room, "\n".join(lines).strip())
    DICE_POKER_ROOMS.pop(_dice_poker_room_key(chat_id), None)


async def _dice_poker_begin_game(context, chat_id: int, room: dict):
    room["status"] = "playing"
    order = list(room.get("players", {}).keys())
    room["turn_order"] = order
    room["turn_index"] = 0

    for uid, p in room.get("players", {}).items():
        p["dice"] = _roll_dice(5)
        p["roll_count"] = 1
        p["locked_idx"] = []
        p["finished"] = False
        p["final_label"] = None

    await _dice_poker_refresh_message(context, chat_id, room)

    first_uid = _dice_poker_turn_uid(room)
    first_name = room["players"][str(first_uid)].get("name") if first_uid else "-"

    await _dice_poker_send_room_message(
        context,
        room,
        f"Semua betting sudah masuk. Roll pertama dibagikan. Sekarang giliran {first_name}.",
        reply_markup=_dice_poker_turn_keyboard(chat_id),
    )

    for uid in room.get("players", {}).keys():
        await _dice_poker_dm_state(context, int(uid), room)


# DICE POKER COMMAND
async def dice_poker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await update.message.reply_text("Dice Poker hanya bisa dibuka di group.")
        return

    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu sebelum buka room Dice Poker.")
        return

    room_key = _dice_poker_room_key(chat.id)
    if room_key in DICE_POKER_ROOMS:
        await update.message.reply_text("Masih ada room Dice Poker yang aktif di grup ini.")
        return

    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "host_name": user.full_name or user.username or f"User {user.id}",
        "status": "waiting",
        "players": {
            str(user.id): {
                "name": user.full_name or user.username or f"User {user.id}",
                "dice": [],
                "roll_count": 0,
                "locked_idx": [],
                "finished": False,
                "final_label": None,
                "bet": None,
            }
        },
        "message_id": None,
        "turn_order": [],
        "turn_index": 0,
        "pot": 0,
        "max_players": 6,  # backend only, tidak perlu ditulis di UI
    }

    sent = await update.message.reply_text(
        _dice_poker_status_text(room),
        reply_markup=_dice_poker_waiting_keyboard(),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    await update.message.reply_text(
        "Asmoday membuka meja Dice Poker. Saat siap, host bisa mulai game dari tombol Start.",
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
        reply_to_message_id=sent.message_id,
    )
    room["message_id"] = sent.message_id
    DICE_POKER_ROOMS[room_key] = room


async def dice_poker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    query = update.callback_query
    await query.answer()

    user = query.from_user
    chat_id = query.message.chat_id
    room = DICE_POKER_ROOMS.get(_dice_poker_room_key(chat_id))

    if not room:
        await query.answer("Room tidak ditemukan atau sudah selesai.", show_alert=True)
        return

    action = (query.data or "").split(":", 1)[1]
    uid = str(user.id)

    if action == "join":
        rec = _get_existing_account(user.id)
        if not _has_gamble_access(rec):
            await query.answer("Nomor account perlu kau miliki sebelum ikut bermain.", show_alert=True)
            return
        if room.get("status") != "waiting":
            await query.answer("Game sudah dimulai.", show_alert=True)
            return
        if uid in room["players"]:
            return
        if len(room["players"]) >= int(room.get("max_players", 6)):
            await query.answer("Slot Dice Poker sudah penuh.", show_alert=True)
            return

        room["players"][uid] = {
            "name": user.full_name or user.username or f"User {user.id}",
            "dice": [],
            "roll_count": 0,
            "locked_idx": [],
            "finished": False,
            "final_label": None,
            "bet": None,
        }
        await _dice_poker_refresh_message(context, chat_id, room)
        return

    if action == "leave":
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Cancel room jika mau batal.", show_alert=True)
            return
        if room.get("status") != "waiting":
            await query.answer("Game sudah dimulai. Tidak bisa leave sekarang.", show_alert=True)
            return
        if uid in room["players"]:
            room["players"].pop(uid, None)
            await _dice_poker_refresh_message(context, chat_id, room)
        return

    if action == "cancel":
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa membatalkan room.", show_alert=True)
            return
        DICE_POKER_ROOMS.pop(_dice_poker_room_key(chat_id), None)
        await query.edit_message_text("Room Dice Poker dibatalkan.")
        return

    if action == "start":
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa mulai.", show_alert=True)
            return
        if len(room.get("players", {})) < 2:
            await query.answer("Minimal harus ada 2 pemain.", show_alert=True)
            return

        room["status"] = "betting"
        room["pot"] = 0

        for p in room.get("players", {}).values():
            p["bet"] = None
            p["dice"] = []
            p["roll_count"] = 0
            p["locked_idx"] = []
            p["finished"] = False
            p["final_label"] = None
            p["final_score"] = None

        await _dice_poker_refresh_message(context, chat_id, room)
        await _dice_poker_send_room_message(
            context,
            room,
            "Kirim nominal betting dengan angka biasa."
        )
        return


async def dice_poker_turn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    query = update.callback_query
    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return

    _, room_chat_id_raw, action = parts
    try:
        room_chat_id = int(room_chat_id_raw)
    except Exception:
        await query.answer("Room tidak valid.", show_alert=True)
        return

    room = DICE_POKER_ROOMS.get(_dice_poker_room_key(room_chat_id))
    if not room or room.get("status") != "playing":
        await query.answer("Fase permainan sudah lewat.", show_alert=True)
        return

    uid = str(query.from_user.id)
    turn_uid = str(_dice_poker_turn_uid(room) or "")
    if uid != turn_uid:
        await query.answer("Bukan giliranmu.", show_alert=True)
        return

    p = room["players"].get(uid)
    if not p:
        return

    if action == "roll":
        if int(p.get("roll_count", 0)) >= 3:
            await query.answer("Kamu sudah mencapai roll terakhir. Pilih stop atau finalize melalui pesan pribadi.", show_alert=True)
            return
        await query.answer("Atur keep / reroll lewat pesan pribadi Asmoday.", show_alert=True)
        await _dice_poker_dm_state(context, int(uid), room)
        return

    if action == "stop":
        p["finished"] = True
        p["final_label"] = _evaluate_dice_poker_hand(p.get("dice") or [])[2]
        await _dice_poker_send_room_message(context, room, f"🔒 {p.get('name')} mengunci hasilnya.")

        if _dice_poker_all_finished(room):
            await _dice_poker_finish(context, room_chat_id, room)
            return

        _dice_poker_next_turn(room)
        await _dice_poker_refresh_message(context, room_chat_id, room)
        next_uid = _dice_poker_turn_uid(room)
        if next_uid:
            await _dice_poker_send_room_message(
                context,
                room,
                f"Sekarang giliran {room['players'][str(next_uid)].get('name')}.",
                reply_markup=_dice_poker_turn_keyboard(room_chat_id),
            )
            await _dice_poker_dm_state(context, int(next_uid), room)


async def dice_poker_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    if update.effective_chat.type != "private":
        return

    msg = update.effective_message
    text = (msg.text or "").strip().lower()
    if not text:
        return

    uid = str(update.effective_user.id)

    active_room = None
    for room in DICE_POKER_ROOMS.values():
        if room.get("status") != "playing":
            continue
        if uid not in room.get("players", {}):
            continue
        if str(_dice_poker_turn_uid(room) or "") != uid:
            continue
        active_room = room
        break

    if not active_room:
        return

    p = active_room["players"][uid]
    roll_count = int(p.get("roll_count", 0))
    if roll_count >= 3:
        await msg.reply_text("Kamu sudah tidak punya roll lagi. Kirim 'stop' untuk finalize.")
        return

    if text == "stop":
        p["finished"] = True
        p["final_label"] = _evaluate_dice_poker_hand(p.get("dice") or [])[2]

        await msg.reply_text(f"Hasilmu dikunci: {_format_dice(p.get('dice') or [])} | {p['final_label']}")
        await _dice_poker_send_room_message(context, active_room, f"🔒 {p.get('name')} mengunci hasilnya.")

        if _dice_poker_all_finished(active_room):
            await _dice_poker_finish(context, active_room["chat_id"], active_room)
            return

        _dice_poker_next_turn(active_room)
        await _dice_poker_refresh_message(context, active_room["chat_id"], active_room)
        next_uid = _dice_poker_turn_uid(active_room)
        if next_uid:
            await _dice_poker_send_room_message(
                context,
                active_room,
                f"Sekarang giliran {active_room['players'][str(next_uid)].get('name')}.",
                reply_markup=_dice_poker_turn_keyboard(active_room["chat_id"]),
            )
            await _dice_poker_dm_state(context, int(next_uid), active_room)
        return

    old_dice = list(p.get("dice") or [])
    if len(old_dice) != 5:
        await msg.reply_text("Data dice tidak valid.")
        return

    if text == "reroll":
        locked_idx = []
    else:
        nums = re.findall(r"\d+", text)
        if not nums:
            await msg.reply_text("Kirim slot yang mau di-keep. Contoh: 1 3 5 | atau kirim 'reroll' | atau 'stop'")
            return

        locked_idx = sorted(set(int(x) - 1 for x in nums if 1 <= int(x) <= 5))
        if not locked_idx and text != "reroll":
            await msg.reply_text("Slot valid hanya 1 sampai 5.")
            return

    new_dice = old_dice[:]
    reroll_targets = [i for i in range(5) if i not in locked_idx]
    rerolled = _roll_dice(len(reroll_targets))
    for i, val in zip(reroll_targets, rerolled):
        new_dice[i] = val

    p["dice"] = new_dice
    p["locked_idx"] = locked_idx
    p["roll_count"] = roll_count + 1

    label = _evaluate_dice_poker_hand(new_dice)[2]
    p["final_label"] = label if int(p["roll_count"]) >= 3 else None

    await msg.reply_text(
        f"Dice baru: {_format_dice(new_dice)}\n"
        f"Roll: {p['roll_count']}/3\n"
        f"Hand saat ini: {label}"
    )

    perfect_rank = _evaluate_dice_poker_hand(new_dice)[0]
    if perfect_rank == 7:
        p["finished"] = True
        p["final_label"] = "Five of a Kind"
        await msg.reply_text("Perfect roll tercapai. Hasil otomatis dikunci.")

    elif int(p["roll_count"]) >= 3:
        p["finished"] = True
        p["final_label"] = label
        await msg.reply_text("Ini roll terakhir. Hasil otomatis dikunci.")

    await _dice_poker_send_room_message(
        context,
        active_room,
        f"{p.get('name')} menyelesaikan aksi roll-nya.",
    )

    if _dice_poker_all_finished(active_room):
        await _dice_poker_finish(context, active_room["chat_id"], active_room)
        return

    if p.get("finished"):
        _dice_poker_next_turn(active_room)
        await _dice_poker_refresh_message(context, active_room["chat_id"], active_room)
        next_uid = _dice_poker_turn_uid(active_room)
        if next_uid:
            await _dice_poker_send_room_message(
                context,
                active_room,
                f"Sekarang giliran {active_room['players'][str(next_uid)].get('name')}.",
                reply_markup=_dice_poker_turn_keyboard(active_room["chat_id"]),
            )
            await _dice_poker_dm_state(context, int(next_uid), active_room)
    else:
        await _dice_poker_dm_state(context, int(uid), active_room)


async def dice_poker_bet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not msg.text or chat.type == "private":
        return

    room = DICE_POKER_ROOMS.get(_dice_poker_room_key(chat.id))
    if not room:
        return

    if room.get("status") != "betting":
        return

    uid = str(user.id)
    p = room.get("players", {}).get(uid)
    if not p:
        return

    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await msg.reply_text("Kamu harus punya account number dulu untuk ikut betting.")
        return

    bet = _parse_bet_amount(msg.text)
    if bet is None:
        return

    balance = int((rec or {}).get("balance", 0) or 0)
    if bet > balance:
        await msg.reply_text(f"Saldo kamu tidak cukup. Saldo sekarang: {balance}")
        return

    if p.get("bet") is not None:
        await msg.reply_text("Bet kamu sudah diterima. Tunggu pemain lain selesai betting.")
        return

    p["bet"] = bet
    room["pot"] = sum(int(player.get("bet", 0) or 0) for player in room.get("players", {}).values())

    await msg.reply_text(_asmoday_bet_ack_text(p.get('name'), bet))
    await _dice_poker_refresh_message(context, chat.id, room)

    if all(player.get("bet") is not None for player in room.get("players", {}).values()):
        await _dice_poker_begin_game(context, chat.id, room)


# =========================================================
# BOORAY
# =========================================================
BOORAY_MAX_PLAYERS = 8


def _booray_room_key(chat_id: int) -> str:
    return str(chat_id)


def _booray_player_ids(room: dict):
    return [str(x) for x in room.get("player_order") or []]


def _booray_player_name(room: dict, uid: str) -> str:
    player = room.get("players", {}).get(str(uid)) or {}
    return player.get("name") or f"Player {uid}"


def _booray_draw(room: dict):
    deck = room.setdefault("deck", [])
    if not deck:
        import random
        deck[:] = _new_deck()
        random.shuffle(deck)
    return deck.pop(0)


def _booray_round_players(room: dict):
    return [uid for uid in _booray_player_ids(room) if (room.get("players", {}).get(str(uid)) or {}).get("in_round")]


def _booray_card_rows(cards):
    rows = []
    row = []
    for card in cards:
        row.append(card)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def _booray_waiting_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join", callback_data="booray:join"), InlineKeyboardButton("Leave", callback_data="booray:leave")],
        [InlineKeyboardButton("Start", callback_data="booray:start"), InlineKeyboardButton("Close Table", callback_data="booray:cancel")],
    ])


def _booray_next_round_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Next Round", callback_data="booray:nextround"), InlineKeyboardButton("Close Table", callback_data="booray:close")]
    ])


def _booray_decision_keyboard(chat_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Stay", callback_data=f"booraydecide:{chat_id}:stay"), InlineKeyboardButton("Fold", callback_data=f"booraydecide:{chat_id}:fold")]
    ])


def _booray_valid_cards(room: dict, uid: str):
    player = room.get("players", {}).get(str(uid)) or {}
    hand = list(player.get("hand") or [])
    lead_suit = room.get("lead_suit")
    if not lead_suit:
        return hand
    suited = [card for card in hand if card[-1] == lead_suit]
    return suited or hand


def _booray_play_keyboard(room: dict, uid: str):
    valid_cards = _booray_valid_cards(room, uid)
    rows = []
    for row_cards in _booray_card_rows(valid_cards):
        rows.append([InlineKeyboardButton(card, callback_data=f"boorayplay:{room.get('chat_id')}:{card}") for card in row_cards])
    return InlineKeyboardMarkup(rows)


def _booray_status_text(room: dict) -> str:
    lines = [
        "‹🃏:۰  𝗕𝗢𝗢𝗥𝗔𝗬",
        "— — • — • — — • — • — — • — • — —",
        "⌦ Dealer : Asmoday",
        f"⌦ Stage : {(room.get('stage') or 'waiting').replace('_', ' ').title()}",
        f"⌦ Round : {int(room.get('round_no', 0))}",
        f"⌦ Ante : {_format_luxen(room.get('ante', 0))}",
        f"⌦ Round Pot : {_format_luxen(room.get('current_round_pot', room.get('pot', 0)))}",
        f"⌦ Carry Pot : {_format_luxen(room.get('carry_pot', 0))}",
    ]
    trump_card = room.get("trump_card")
    if trump_card:
        lines.append(f"⌦ Trump : {trump_card} · Suit {trump_card[-1]}")
    if room.get("lead_suit"):
        lines.append(f"⌦ Lead Suit : {room.get('lead_suit')}")
    if room.get("current_turn_uid"):
        lines.append(f"⌦ Acting : {_booray_player_name(room, room.get('current_turn_uid'))}")
    lines.extend(["", "› Table"])
    for uid in _booray_player_ids(room):
        player = room.get("players", {}).get(str(uid)) or {}
        status = []
        if player.get("decision") == "stay":
            status.append("Stay")
        elif player.get("decision") == "fold":
            status.append("Fold")
        if player.get("in_round"):
            status.append(f"{int(player.get('tricks', 0))} trick")
        line = f"› {player.get('name')} · stack {_format_luxen(player.get('stack', 0))}"
        if status:
            line += " · " + " / ".join(status)
        lines.append(line)
    if room.get("current_trick"):
        lines.extend(["", "› Current Trick"])
        for uid, card in room.get("current_trick"):
            lines.append(f"· {_booray_player_name(room, uid)} : {card}")
    if room.get("stage") == "waiting":
        lines.extend(["", "› Ante ditentukan host saat meja dibuka.", "› Setiap ronde terdiri dari 5 trick.", "› Pemain yang ikut ronde tetapi gagal mengambil 1 trick pun akan Boorayed."])
    return "\n".join(lines)


async def _booray_refresh_message(context, room: dict):
    message_id = room.get("message_id")
    if not message_id:
        return
    reply_markup = _booray_waiting_keyboard() if room.get("stage") == "waiting" else None
    text_value = _booray_status_text(room)
    markup_value = reply_markup.to_dict() if reply_markup else None
    if room.get("_last_render_text") == text_value and room.get("_last_render_markup") == markup_value:
        return
    try:
        await context.bot.edit_message_text(chat_id=room.get("chat_id"), message_id=message_id, text=text_value, reply_markup=reply_markup)
        room["_last_render_text"] = text_value
        room["_last_render_markup"] = markup_value
    except Exception as e:
        if "message is not modified" in str(e).lower():
            room["_last_render_text"] = text_value
            room["_last_render_markup"] = markup_value
            return
        print(f"[_booray_refresh_message] error: {e}")


async def _booray_send_room_message(context, room: dict, text: str, *, reply_markup=None):
    kwargs = {"chat_id": room.get("chat_id"), "text": text, "reply_to_message_id": room.get("message_id")}
    if room.get("thread_id"):
        kwargs["message_thread_id"] = room.get("thread_id")
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    return await context.bot.send_message(**kwargs)


async def _booray_send_private_prompt(context, room: dict, uid: str, text: str, *, reply_markup=None):
    try:
        await context.bot.send_message(chat_id=int(uid), text=text, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"[_booray_send_private_prompt] failed uid={uid}: {e}")
        await _booray_send_room_message(context, room, f"Asmoday gagal menjangkau {_booray_player_name(room, uid)} lewat DM. Minta dia /start bot lalu mulai lagi.")
        return False


def _booray_intro_text(room: dict) -> str:
    return (
        "‹🃏:۰  𝗕𝗢𝗢𝗥𝗔𝗬 — 𝗖𝗔𝗥𝗔 𝗕𝗘𝗥𝗠𝗔𝗜𝗡\n"
        "— — • — • — — • — • — — • — • — —\n"
        "Booray adalah permainan trick-taking. Tujuan utamanya bukan menyapu semua trick, melainkan jangan sampai kalah total.\n\n"
        f"⌦ Ante ronde ini : {_format_luxen(room.get('ante', 0))} dari setiap pemain duduk\n"
        "⌦ Setiap pemain menerima 5 kartu private\n"
        "⌦ 1 kartu dibuka sebagai Trump\n\n"
        "› Sebelum trick dimulai, setiap pemain memilih Stay atau Fold.\n"
        "› Fold berarti keluar dari ronde dengan aman. Ante tetap hangus, tapi kamu tidak bisa terkena Booray.\n"
        "› Stay berarti ikut seluruh ronde dan wajib menanggung risikonya.\n\n"
        "𝗖𝗮𝗿𝗮 𝗺𝗲𝗻𝗮𝗻𝗴𝗸𝗮𝗻 𝘁𝗿𝗶𝗰𝗸:\n"
        "› Pemain pertama bebas membuka kartu apa saja; suit kartu itu menjadi Lead Suit.\n"
        "› Jika kamu punya Lead Suit, kamu wajib mengikuti suit tersebut.\n"
        "› Jika kamu tidak punya, kamu boleh buang kartu apa pun.\n"
        "› Jika ada Trump yang dimainkan, Trump tertinggi menang. Jika tidak ada Trump, kartu tertinggi dari Lead Suit yang menang.\n\n"
        "𝗔𝗽𝗮 𝗶𝘁𝘂 𝗕𝗼𝗼𝗿𝗮𝘆?\n"
        "› Pemain yang memilih Stay tetapi menutup ronde dengan 0 trick dinyatakan Boorayed.\n\n"
        "𝗣𝗲𝗻𝗮𝗹𝘁𝘆 𝗕𝗼𝗼𝗿𝗮𝘆:\n"
        "› Pemain yang Boorayed harus membayar sebesar round pot saat itu.\n"
        "› Pembayaran ini tidak masuk ke pemenang ronde sekarang; ia menjadi Carry Pot untuk ronde berikutnya.\n"
        "› Karena itu, meja bisa makin lama makin mahal.\n\n"
        "𝗣𝗲𝗺𝗲𝗻𝗮𝗻𝗴 𝗿𝗼𝗻𝗱𝗲:\n"
        "› Pemain dengan trick terbanyak mengambil round pot saat ini.\n"
        "› Jika seri, round pot dibagi rata.\n\n"
        "Asmoday tidak mencari keberanian kosong. Ia hanya menilai siapa yang sanggup menghindari kehancuran penuh."
    )


async def _booray_take_from_stack(room: dict, uid: str, amount: int) -> int:
    amount = max(0, int(amount or 0))
    if amount <= 0:
        return 0
    player = room.get("players", {}).get(str(uid)) or {}
    paid = min(int(player.get("stack", 0)), amount)
    player["stack"] = int(player.get("stack", 0)) - paid
    rec = _get_existing_account(int(uid))
    if rec:
        rec["balance"] = int(rec.get("balance", 0)) - paid
    room["pot"] = int(room.get("pot", 0)) + paid
    return paid


def _booray_credit_balance(uid: str, amount: int):
    amount = int(amount or 0)
    if amount <= 0:
        return
    rec = _get_existing_account(int(uid))
    if rec:
        rec["balance"] = int(rec.get("balance", 0)) + amount


async def _booray_cancel_for_dm_failure(context, room: dict, failed_names=None):
    failed_names = failed_names or []
    for uid in _booray_player_ids(room):
        player = room.get("players", {}).get(uid) or {}
        paid = int(player.get("round_paid", 0) or 0)
        if paid > 0:
            _booray_credit_balance(uid, paid)
            player["stack"] = int(player.get("stack", 0) or 0) + paid
            player["round_paid"] = 0
    save_accounts()
    chat_id = room.get("chat_id")
    BOORAY_ROOMS.pop(_booray_room_key(chat_id), None)
    names = ", ".join(failed_names) if failed_names else "salah satu pemain"
    await _booray_send_room_message(
        context,
        room,
        f"Meja Booray dibatalkan karena Asmoday tidak bisa mengirim DM ke {names}. Ante ronde ini sudah dikembalikan. Semua pemain wajib /start bot dulu sebelum membuka meja ulang."
    )


async def _booray_prepare_round(room: dict):
    import random
    room["round_no"] = int(room.get("round_no", 0)) + 1
    deck = _new_deck()
    random.shuffle(deck)
    room["deck"] = deck
    room["pot"] = int(room.get("carry_pot", 0))
    room["trick_no"] = 0
    room["lead_suit"] = None
    room["current_trick"] = []
    room["current_turn_uid"] = None
    room["current_round_pot"] = int(room.get("carry_pot", 0))
    room["carry_pot"] = 0
    order = _booray_player_ids(room)
    if order:
        room["round_leader_index"] = (int(room.get("round_leader_index", -1)) + 1) % len(order)
    else:
        room["round_leader_index"] = 0
    for uid in order:
        rec = _get_existing_account(int(uid))
        player = room.get("players", {}).get(uid) or {}
        player["stack"] = int(rec.get("balance", 0) if rec else player.get("stack", 0))
        paid = await _booray_take_from_stack(room, uid, int(room.get("ante", 0)))
        player["round_paid"] = int(paid)
        room["current_round_pot"] = int(room.get("current_round_pot", 0)) + paid
        player["hand"] = [room["deck"].pop(0) for _ in range(5)]
        player["tricks"] = 0
        player["decision"] = None
        player["in_round"] = False
    room["trump_card"] = room["deck"].pop(0) if room["deck"] else None
    room["stage"] = "decision"


def _booray_all_decided(room: dict) -> bool:
    for uid in _booray_player_ids(room):
        if (room.get("players", {}).get(uid) or {}).get("decision") not in {"stay", "fold"}:
            return False
    return True


def _booray_active_order_for_trick(room: dict):
    active = [uid for uid in _booray_player_ids(room) if (room.get("players", {}).get(uid) or {}).get("in_round")]
    leader = str(room.get("leader_uid") or "")
    if leader in active:
        idx = active.index(leader)
        return active[idx:] + active[:idx]
    return active


def _booray_trick_winner(room: dict):
    trick = room.get("current_trick") or []
    if not trick:
        return None, None
    trump = room.get("trump_card", "")[-1:] or ""
    lead_suit = room.get("lead_suit") or trick[0][1][-1]
    trump_cards = [(uid, card) for uid, card in trick if card[-1] == trump]
    relevant = trump_cards if trump_cards else [(uid, card) for uid, card in trick if card[-1] == lead_suit]
    winner_uid, winner_card = max(relevant, key=lambda item: _card_rank(item[1]))
    return winner_uid, winner_card


async def _booray_begin_play(context, room: dict):
    room["stage"] = "player_turn"
    room["trick_no"] = 1
    active = _booray_round_players(room)
    if not active:
        room["stage"] = "resolved"
        room["carry_pot"] = int(room.get("current_round_pot", 0))
        await _booray_refresh_message(context, room)
        await _booray_send_room_message(context, room, f"Tidak ada satu pun pemain yang memilih Stay. Round pot {_format_luxen(room.get('current_round_pot', 0))} dibawa ke ronde berikutnya.", reply_markup=_booray_next_round_keyboard())
        return
    leader_index = int(room.get("round_leader_index", 0)) % len(_booray_player_ids(room))
    proposed = _booray_player_ids(room)[leader_index] if _booray_player_ids(room) else active[0]
    room["leader_uid"] = proposed if proposed in active else active[0]
    room["current_turn_uid"] = room["leader_uid"]
    room["lead_suit"] = None
    room["current_trick"] = []
    await _booray_refresh_message(context, room)
    await _booray_send_room_message(context, room, f"Trump ronde ini adalah {room.get('trump_card')}. Trick pertama dibuka oleh {_booray_player_name(room, room.get('leader_uid'))}.")
    await _booray_prompt_turn(context, room)


async def _booray_prompt_turn(context, room: dict):
    uid = room.get("current_turn_uid")
    if not uid:
        return
    valid_cards = _booray_valid_cards(room, uid)
    note = "Buka dengan kartu apa saja." if not room.get("lead_suit") else f"Ikuti suit {room.get('lead_suit')} jika kamu memilikinya."
    text = (
        "‹🃏:۰  𝗕𝗢𝗢𝗥𝗔𝗬 — 𝗚𝗜𝗟𝗜𝗥𝗔𝗡𝗠𝗨\n"
        "— — • — • — — • — • — — • — • — —\n"
        f"⌦ Trump : {room.get('trump_card')}\n"
        f"⌦ Trick : {room.get('trick_no', 1)}\n\n"
        f"{note}\n\n"
        f"› Kartu valid : {' '.join(valid_cards)}"
    )
    await _booray_send_room_message(context, room, f"Asmoday memanggil {_booray_player_name(room, uid)} untuk meletakkan satu kartu.")
    ok = await _booray_send_private_prompt(context, room, uid, text, reply_markup=_booray_play_keyboard(room, uid))
    if not ok:
        await _booray_cancel_for_dm_failure(context, room, [_booray_player_name(room, uid)])


async def _booray_after_play(context, room: dict):
    order = _booray_active_order_for_trick(room)
    if len(room.get("current_trick") or []) < len(order):
        played = {uid for uid, _ in room.get("current_trick") or []}
        for uid in order:
            if uid not in played:
                room["current_turn_uid"] = uid
                await _booray_refresh_message(context, room)
                await _booray_prompt_turn(context, room)
                return
    winner_uid, winner_card = _booray_trick_winner(room)
    if winner_uid:
        room["players"][str(winner_uid)]["tricks"] = int(room["players"][str(winner_uid)].get("tricks", 0)) + 1
    await _booray_send_room_message(context, room, f"Trick {room.get('trick_no')} jatuh kepada {_booray_player_name(room, winner_uid)} dengan {winner_card}.")
    if int(room.get("trick_no", 0)) >= 5:
        await _booray_resolve_round(context, room)
        return
    room["trick_no"] = int(room.get("trick_no", 0)) + 1
    room["leader_uid"] = winner_uid
    room["current_turn_uid"] = winner_uid
    room["lead_suit"] = None
    room["current_trick"] = []
    await _booray_refresh_message(context, room)
    await _booray_send_room_message(context, room, f"Trick {room.get('trick_no')} dimulai. Leader kini {_booray_player_name(room, winner_uid)}.")
    await _booray_prompt_turn(context, room)


async def _booray_resolve_round(context, room: dict):
    room["stage"] = "resolved"
    active = _booray_round_players(room)
    if not active:
        room["carry_pot"] = int(room.get("current_round_pot", 0))
        await _booray_refresh_message(context, room)
        await _booray_send_room_message(context, room, f"Tidak ada pemain aktif tersisa. Round pot {_format_luxen(room.get('current_round_pot', 0))} menjadi carry pot.", reply_markup=_booray_next_round_keyboard())
        return
    top = max(int((room.get("players", {}).get(uid) or {}).get("tricks", 0)) for uid in active)
    winners = [uid for uid in active if int((room.get("players", {}).get(uid) or {}).get("tricks", 0)) == top]
    boorayed = [uid for uid in active if int((room.get("players", {}).get(uid) or {}).get("tricks", 0)) == 0]
    prize = int(room.get("current_round_pot", 0))
    share = prize // len(winners) if winners else 0
    remainder = prize % len(winners) if winners else 0
    for i, uid in enumerate(winners):
        _booray_credit_balance(uid, share + (1 if i < remainder else 0))
    penalty_base = prize
    room["carry_pot"] = 0
    for uid in boorayed:
        paid = await _booray_take_from_stack(room, uid, penalty_base)
        room["carry_pot"] = int(room.get("carry_pot", 0)) + paid
    save_accounts()
    lines = [
        "‹🃏:۰  𝗕𝗢𝗢𝗥𝗔𝗬 — 𝗛𝗔𝗦𝗜𝗟 𝗥𝗢𝗡𝗗𝗘",
        "— — • — • — — • — • — — • — • — —",
        f"⌦ Trump : {room.get('trump_card')}",
        f"⌦ Round Pot : {_format_luxen(prize)}",
        f"⌦ Carry Pot Berikutnya : {_format_luxen(room.get('carry_pot', 0))}",
        "",
    ]
    for uid in active:
        player = room.get("players", {}).get(uid) or {}
        tricks = int(player.get("tricks", 0))
        outcome = "Aman"
        if uid in boorayed:
            outcome = f"Boorayed · penalty {_format_luxen(penalty_base)}"
        if uid in winners:
            outcome += " · Pemenang ronde"
        lines.append(f"› {player.get('name')} · {tricks} trick · {outcome}")
    await _booray_refresh_message(context, room)
    await _booray_send_room_message(context, room, "\n".join(lines), reply_markup=_booray_next_round_keyboard())


async def booray_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Booray hanya bisa dibuka di group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu sebelum buka meja Booray.")
        return
    if not context.args or not str(context.args[0]).replace(',', '').isdigit():
        await update.message.reply_text("Format: /booray <ante>")
        return
    ante = int(str(context.args[0]).replace(',', ''))
    if ante <= 0:
        await update.message.reply_text("Ante harus lebih dari 0.")
        return
    room_key = _booray_room_key(chat.id)
    if room_key in BOORAY_ROOMS:
        await update.message.reply_text("Masih ada meja Booray aktif di grup ini.")
        return
    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "stage": "waiting",
        "player_order": [str(user.id)],
        "players": {str(user.id): {"name": user.full_name or user.username or f"User {user.id}", "stack": int(rec.get("balance", 0)), "hand": [], "decision": None, "in_round": False, "tricks": 0}},
        "pot": 0,
        "current_round_pot": 0,
        "carry_pot": 0,
        "ante": ante,
        "deck": [],
        "message_id": None,
        "intro_sent": False,
        "round_no": 0,
        "round_leader_index": -1,
    }
    sent = await update.message.reply_text(_booray_status_text(room), reply_markup=_booray_waiting_keyboard(), message_thread_id=getattr(update.effective_message, "message_thread_id", None))
    room["message_id"] = sent.message_id
    BOORAY_ROOMS[room_key] = room
    await _booray_send_room_message(context, room, f"Asmoday membuka meja Booray. Ante ditetapkan host sebesar {_format_luxen(ante)}. Setiap ronde, seluruh pemain duduk otomatis membayar ante itu ke round pot.")


async def booray_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    room = BOORAY_ROOMS.get(_booray_room_key(chat_id))
    if not room:
        await query.answer("Meja Booray tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    uid = str(user.id)
    if action == "join":
        if room.get("stage") != "waiting":
            await query.answer("Ronde sudah berjalan.", show_alert=True)
            return
        if uid in room.get("players", {}):
            return
        if len(room.get("player_order", [])) >= BOORAY_MAX_PLAYERS:
            await query.answer("Kursi meja sudah penuh.", show_alert=True)
            return
        rec = _get_existing_account(user.id)
        if not _has_gamble_access(rec):
            await query.answer("Kamu butuh account number yang valid.", show_alert=True)
            return
        room["players"][uid] = {"name": user.full_name or user.username or f"User {user.id}", "stack": int(rec.get("balance", 0)), "hand": [], "decision": None, "in_round": False, "tricks": 0}
        room["player_order"].append(uid)
        await _booray_refresh_message(context, room)
        await _booray_send_room_message(context, room, f"Asmoday mencatat {_booray_player_name(room, uid)} duduk di meja Booray.")
        return
    if action == "leave":
        if room.get("stage") != "waiting":
            await query.answer("Ronde sudah berjalan.", show_alert=True)
            return
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Tutup meja jika ingin batal.", show_alert=True)
            return
        if uid in room.get("players", {}):
            room["players"].pop(uid, None)
            room["player_order"] = [x for x in room.get("player_order", []) if str(x) != uid]
            await _booray_refresh_message(context, room)
        return
    if action in {"cancel", "close"}:
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa menutup meja.", show_alert=True)
            return
        BOORAY_ROOMS.pop(_booray_room_key(chat_id), None)
        await query.edit_message_text("Asmoday menutup meja Booray.")
        return
    if action in {"start", "nextround"}:
        if user.id != room.get("host_id") and not _is_admin(user):
            await query.answer("Hanya host atau admin yang bisa memulai ronde.", show_alert=True)
            return
        for puid in list(_booray_player_ids(room)):
            rec = _get_existing_account(int(puid))
            if rec:
                room["players"][puid]["stack"] = int(rec.get("balance", 0))
        host_uid = str(room.get("host_id"))
        if int((room.get("players", {}).get(host_uid) or {}).get("stack", 0)) < int(room.get("ante", 0)):
            await query.answer("Saldo host tidak cukup untuk membayar ante ronde berikutnya.", show_alert=True)
            return
        removed = []
        for puid in list(_booray_player_ids(room)):
            if puid == host_uid:
                continue
            if int((room.get("players", {}).get(puid) or {}).get("stack", 0)) < int(room.get("ante", 0)):
                removed.append(_booray_player_name(room, puid))
                room["players"].pop(puid, None)
                room["player_order"] = [x for x in room.get("player_order", []) if str(x) != puid]
        if removed:
            await _booray_send_room_message(context, room, f"Asmoday mengeluarkan pemain yang tidak sanggup membayar ante ronde berikutnya: {', '.join(removed)}.")
        if len(room.get("player_order", [])) < 2:
            await _booray_refresh_message(context, room)
            await query.answer("Booray butuh minimal 2 pemain yang mampu membayar ante.", show_alert=True)
            return
        await _booray_prepare_round(room)
        save_accounts()
        await _booray_refresh_message(context, room)
        if not room.get("intro_sent"):
            room["intro_sent"] = True
            await _booray_send_room_message(context, room, _booray_intro_text(room))
        await _booray_send_room_message(context, room, f"Asmoday membuka ronde {room.get('round_no')}. Trump Card: {room.get('trump_card')}. Round pot saat ini {_format_luxen(room.get('current_round_pot', 0))}. Kini semua pemain harus menentukan Stay atau Fold.")
        dm_failed = []
        for puid in _booray_player_ids(room):
            player = room.get("players", {}).get(puid) or {}
            ok = await _booray_send_private_prompt(
                context,
                room,
                puid,
                (
                    "‹🃏:۰  𝗕𝗢𝗢𝗥𝗔𝗬 — 𝗣𝗥𝗜𝗩𝗔𝗧𝗘 𝗛𝗔𝗡𝗗\n"
                    "— — • — • — — • — • — — • — • — —\n"
                    f"⌦ Trump : {room.get('trump_card')}\n"
                    f"⌦ Ante terpotong : {_format_luxen(room.get('ante', 0))}\n"
                    f"⌦ Kartu kamu : {' '.join(player.get('hand') or [])}\n\n"
                    "Pilih Stay jika mau ikut berebut trick. Pilih Fold jika ingin selamat dan melepas ronde ini tanpa risiko Booray tambahan."
                ),
                reply_markup=_booray_decision_keyboard(chat_id),
            )
            if not ok:
                dm_failed.append(_booray_player_name(room, puid))
        if dm_failed:
            await _booray_cancel_for_dm_failure(context, room, dm_failed)
        return


async def booray_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return
    _, room_chat_id_raw, action = parts
    room = BOORAY_ROOMS.get(_booray_room_key(int(room_chat_id_raw)))
    if not room or room.get("stage") != "decision":
        await query.answer("Fase keputusan telah lewat.", show_alert=True)
        return
    uid = str(query.from_user.id)
    player = room.get("players", {}).get(uid)
    if not player or player.get("decision") in {"stay", "fold"}:
        return
    if action not in {"stay", "fold"}:
        return
    player["decision"] = action
    player["in_round"] = action == "stay"
    await _booray_refresh_message(context, room)
    try:
        await query.edit_message_text(f"Keputusanmu dikunci: {action.title()}")
    except Exception:
        pass
    await _booray_send_room_message(context, room, f"Asmoday mencatat {_booray_player_name(room, uid)} memilih {action.title()}.")
    if not _booray_all_decided(room):
        return
    active = _booray_round_players(room)
    if len(active) == 0:
        room["stage"] = "resolved"
        room["carry_pot"] = int(room.get("current_round_pot", 0))
        save_accounts()
        await _booray_refresh_message(context, room)
        await _booray_send_room_message(context, room, f"Seluruh meja memilih Fold. Round pot {_format_luxen(room.get('current_round_pot', 0))} berubah menjadi carry pot untuk ronde berikutnya.", reply_markup=_booray_next_round_keyboard())
        return
    if len(active) == 1:
        winner = active[0]
        prize = int(room.get("current_round_pot", 0))
        _booray_credit_balance(winner, prize)
        room["stage"] = "resolved"
        room["carry_pot"] = 0
        save_accounts()
        await _booray_refresh_message(context, room)
        await _booray_send_room_message(context, room, f"Hanya {_booray_player_name(room, winner)} yang memilih Stay. Ia mengambil round pot {_format_luxen(prize)} tanpa perlu memainkan satu trick pun.", reply_markup=_booray_next_round_keyboard())
        return
    await _booray_begin_play(context, room)


async def booray_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":", 2)
    if len(parts) != 3:
        return
    _, room_chat_id_raw, card = parts
    room = BOORAY_ROOMS.get(_booray_room_key(int(room_chat_id_raw)))
    if not room or room.get("stage") != "player_turn":
        await query.answer("Fase kartu sudah lewat.", show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid != str(room.get("current_turn_uid") or ""):
        await query.answer("Bukan giliranmu.", show_alert=True)
        return
    player = room.get("players", {}).get(uid) or {}
    valid_cards = _booray_valid_cards(room, uid)
    if card not in valid_cards or card not in list(player.get("hand") or []):
        await query.answer("Kartu itu tidak valid untuk dimainkan sekarang.", show_alert=True)
        return
    player["hand"].remove(card)
    if not room.get("lead_suit"):
        room["lead_suit"] = card[-1]
    room.setdefault("current_trick", []).append((uid, card))
    await _booray_refresh_message(context, room)
    try:
        await query.edit_message_text(f"Kartu terkunci: {card}")
    except Exception:
        pass
    await _booray_send_room_message(context, room, f"{_booray_player_name(room, uid)} meletakkan {card} ke meja.")
    await _booray_after_play(context, room)

# =========================================================
# THIRTY-ONE
# =========================================================
THIRTYONE_VALUES = {"A": 11, "K": 10, "Q": 10, "J": 10}

def _thirtyone_room_key(chat_id: int) -> str:
    return str(chat_id)

def _thirtyone_card_value(card: str) -> int:
    rank = card[:-1]
    if rank in THIRTYONE_VALUES:
        return THIRTYONE_VALUES[rank]
    return int(rank)

def _thirtyone_best_score(cards):
    if len(cards) == 3 and len({c[:-1] for c in cards}) == 1:
        return 30.5, 'Three of a Kind'
    best = 0
    best_suit = '-'
    for suit in CARD_SUITS:
        total = sum(_thirtyone_card_value(c) for c in cards if c.endswith(suit))
        if total > best:
            best = total
            best_suit = suit
    return best, best_suit

def _format_luxen(amount) -> str:
    try:
        return f"{int(amount):,}✦𝕷"
    except Exception:
        return f"{amount}✦𝕷"

def _thirtyone_short_intro_text() -> str:
    return (
        "♠ ♡ ♣ ♢ ·  𝗧𝗛𝗜𝗥𝗧𝗬–𝗢𝗡𝗘\n"
        "— — • — • — — • — • — — • — • — —\n\n"
        "𝗚𝗢𝗔𝗟 𝗢𝗙 𝗧𝗛𝗘 𝗚𝗔𝗠𝗘 :\n"
        "Bangun nilai tertinggi dalam satu suit. Target sempurna adalah 31.\n"
        "Kamu tidak mencari banyak kartu—kamu mencari satu jalur yang paling kuat.\n\n"
        "𝗚𝗔𝗠𝗘 𝗙𝗟𝗢𝗪 :\n"
        "Asmoday membagikan 3 kartu tertutup ke tiap pemain, lalu membuka 3 kartu di tengah meja.\n"
        "Sisa deck menjadi draw pile, tetapi ronde ini bergerak melalui keputusanmu di atas tiga kartu tengah itu.\n\n"
        "𝗣𝗔𝗗𝗔 𝗚𝗜𝗟𝗜𝗥𝗔𝗡𝗠𝗨 :\n"
        "• Swap  : ambil 1 kartu tengah, lalu buang 1 kartu dari tanganmu.\n"
        "• Swap All : ambil semua 3 kartu tengah dan ganti seluruh tanganmu.\n"
        "• Pass  : lewat tanpa perubahan.\n"
        "• Knock : akhiri ronde; semua pemain lain hanya mendapat 1 giliran terakhir.\n\n"
        "𝗣𝗘𝗡𝗜𝗟𝗔𝗜𝗔𝗡 :\n"
        "Hanya satu suit terbaik yang dihitung. A = 11, J/Q/K = 10, angka sesuai nilainya.\n"
        "31 menang instan. Tiga kartu dengan rank yang sama dihitung 30½ dan hanya kalah dari 31.\n\n"
        "𝗔𝗞𝗛𝗜𝗥 𝗥𝗢𝗡𝗗𝗘 :\n"
        "Setelah knock atau 31 tercapai, semua tangan dibuka. Nilai tertinggi mengambil pot. Nilai terendah jatuh di ronde ini.\n\n"
        "Asmoday menyarankan satu hal: jangan mengetuk terlalu cepat hanya karena meja terlihat tenang."
    )

def _thirtyone_status_text(room: dict) -> str:
    lines = [
        "♠ ♡ ♣ ♢ ·  𝗧𝗛𝗜𝗥𝗧𝗬–𝗢𝗡𝗘",
        "",
        f"⌦ Dealer : Asmoday",
        f"⌦ State : {(room.get('status') or 'waiting').title()}",
        f"⌦ Round : {room.get('round_no', 0)}",
        f"⌦ Pot : {_format_luxen(room.get('pot', 0))}",
    ]
    center = room.get('center_cards') or []
    if center:
        lines.append(f"⌦ Center : {' '.join(center)}")
    lines.append("")
    lines.append("⌦ Table :")
    players = room.get('players', {})
    if not players:
        lines.append("› -")
    else:
        turn_uid = room.get('turn_uid')
        for uid, p in players.items():
            marks = []
            if str(uid) == str(room.get('host_id')):
                marks.append('Host')
            if str(uid) == str(turn_uid) and room.get('status') == 'action':
                marks.append('Turn')
            if p.get('knocked'):
                marks.append('Knock')
            best_score, best_suit = p.get('best_score', 0), p.get('best_suit', '-')
            best_label = 'Three of a Kind' if best_suit == 'Three of a Kind' else f'{best_score} · {best_suit}'
            mark_text = f" [{' · '.join(marks)}]" if marks else ''
            lines.append(f"› {p.get('name')}{mark_text} · Bet {_format_luxen(p.get('bet', 0))} · Best {best_label}")
    if room.get('status') == 'waiting':
        lines.extend(["", "Asmoday menunggu pemain lain untuk duduk di meja."])
    elif room.get('status') == 'betting':
        lines.extend(["", "Asmoday membuka betting. Semua pemain kirim nominal dengan angka biasa."])
    elif room.get('status') == 'action' and room.get('turn_uid'):
        current = players.get(str(room.get('turn_uid'))) or {}
        lines.extend(["", f"Giliran : {current.get('name', '-')}"])
    elif room.get('status') == 'finished':
        lines.extend(["", "Ronde selesai. Asmoday menunggu keputusan meja berikutnya."])
    return "\n".join(lines)

def _thirtyone_waiting_keyboard(room: dict):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join", callback_data="thirtyone:join"), InlineKeyboardButton("Leave", callback_data="thirtyone:leave")],
        [InlineKeyboardButton("Start", callback_data="thirtyone:start"), InlineKeyboardButton("Cancel", callback_data="thirtyone:cancel")],
    ])

def _thirtyone_action_keyboard(room: dict):
    center = room.get('center_cards') or []
    rows = []
    if center:
        rows.append([InlineKeyboardButton(f"Swap {i+1}", callback_data=f"thirtyoneact:swap:{i}") for i in range(len(center))])
    rows.append([InlineKeyboardButton("Swap All", callback_data="thirtyoneact:swapall:0"), InlineKeyboardButton("Pass", callback_data="thirtyoneact:pass:0")])
    rows.append([InlineKeyboardButton("Knock", callback_data="thirtyoneact:knock:0")])
    return InlineKeyboardMarkup(rows)

def _thirtyone_next_round_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Next Round", callback_data="thirtyone:nextround"), InlineKeyboardButton("Close Table", callback_data="thirtyone:close")]])

async def _thirtyone_send_room_message(context, room: dict, text: str, *, reply_markup=None, reply_to_room=True):
    kwargs = {"chat_id": room.get("chat_id"), "text": text}
    if room.get('thread_id'):
        kwargs['message_thread_id'] = room['thread_id']
    if reply_to_room and room.get('message_id'):
        kwargs['reply_to_message_id'] = room['message_id']
    if reply_markup is not None:
        kwargs['reply_markup'] = reply_markup
    return await context.bot.send_message(**kwargs)

async def _thirtyone_refresh_message(context, room: dict):
    if not room.get('message_id'):
        return
    markup = None
    if room.get('status') == 'waiting':
        markup = _thirtyone_waiting_keyboard(room)
    elif room.get('status') == 'action':
        markup = _thirtyone_action_keyboard(room)
    try:
        await context.bot.edit_message_text(chat_id=room['chat_id'], message_id=room['message_id'], text=_thirtyone_status_text(room), reply_markup=markup)
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            print(f"[_thirtyone_refresh_message] {e}")

async def _thirtyone_dm_hand(context, uid: str, room: dict):
    p = room.get('players', {}).get(str(uid)) or {}
    score, suit = _thirtyone_best_score(p.get('hand', []))
    p['best_score'], p['best_suit'] = score, suit
    suit_label = suit if suit == 'Three of a Kind' else f"Suit {suit}"
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=(
                "♠ ♡ ♣ ♢ ·  𝗧𝗛𝗜𝗥𝗧𝗬–𝗢𝗡𝗘 — 𝗣𝗥𝗜𝗩𝗔𝗧𝗘 𝗛𝗔𝗡𝗗\n\n"
                f"Kartu : {' '.join(p.get('hand', []))}\n"
                f"Best : {score} · {suit_label}\n\n"
                "Asmoday menunggumu memilih: Swap, Swap All, Pass, atau Knock."
            )
        )
    except Exception:
        await _thirtyone_send_room_message(context, room, f"Asmoday gagal mengirim kartu ke {p.get('name')}. Pastikan dia sudah /start bot.")

def _thirtyone_reset_round(room: dict):
    _choice_poker_shuffle_deck(room)
    room['round_no'] = int(room.get('round_no', 0)) + 1
    room['status'] = 'action'
    room['center_cards'] = _draw_cards(room, 3)
    room['turn_order'] = list(room.get('players', {}).keys())
    room['turn_index'] = 0
    room['turn_uid'] = room['turn_order'][0] if room['turn_order'] else None
    room['knock_uid'] = None
    room['final_turns_left'] = 0
    for uid, p in room.get('players', {}).items():
        p['hand'] = _draw_cards(room, 3)
        p['knocked'] = False
        p['best_score'], p['best_suit'] = _thirtyone_best_score(p['hand'])

def _thirtyone_advance_turn(room: dict):
    order = room.get('turn_order') or []
    if not order:
        room['turn_uid'] = None
        return
    room['turn_index'] = (int(room.get('turn_index', 0)) + 1) % len(order)
    room['turn_uid'] = order[room['turn_index']]

async def _thirtyone_start_round(context, room: dict):
    _thirtyone_reset_round(room)
    await _thirtyone_send_room_message(context, room, _thirtyone_short_intro_text())
    await _thirtyone_send_room_message(
        context,
        room,
        (
            f"Asmoday membuka tiga kartu tengah: {' '.join(room.get('center_cards', []))}.\n\n"
            "Cara membaca meja ini sederhana, tetapi tidak lunak.\n"
            "Bangun total tertinggi dalam satu suit. Campuran suit tidak digabung.\n"
            "Jika kamu puas dengan tanganmu, knock akan menutup ronde setelah semua lawan memperoleh satu giliran terakhir.\n"
            "Jika seseorang menyentuh 31 tepat, ronde berakhir seketika tanpa belas kasihan."
        )
    )
    for uid in room.get('players', {}):
        await _thirtyone_dm_hand(context, uid, room)
    await _thirtyone_refresh_message(context, room)
    current = room.get('players', {}).get(str(room.get('turn_uid'))) or {}
    await _thirtyone_send_room_message(context, room, f"Asmoday membuka ronde {room['round_no']}. Giliran pertama jatuh kepada {current.get('name', '-')}.", reply_markup=_thirtyone_action_keyboard(room))

async def _thirtyone_finish_round(context, room: dict, instant_uid=None):
    room['status'] = 'finished'
    players = room.get('players', {})
    active = list(players.keys())
    scores = {}
    for uid in active:
        p = players[uid]
        p['best_score'], p['best_suit'] = _thirtyone_best_score(p.get('hand', []))
        scores[uid] = p['best_score']
    if instant_uid and str(instant_uid) in scores:
        winners = [str(instant_uid)]
    else:
        high = max(scores.values()) if scores else 0
        winners = [uid for uid, v in scores.items() if v == high]
    low = min(scores.values()) if scores else 0
    losers = [uid for uid, v in scores.items() if v == low]
    pot = int(room.get('pot', 0))
    share = pot // len(winners) if winners else 0
    for uid in winners:
        rec = _get_existing_account(int(uid))
        if rec:
            rec['balance'] = int(rec.get('balance', 0)) + share
    save_accounts()
    lines = [
        "♠ ♡ ♣ ♢ ·  𝗧𝗛𝗜𝗥𝗧𝗬–𝗢𝗡𝗘 — 𝗛𝗔𝗦𝗜𝗟 𝗥𝗢𝗡𝗗𝗘",
        "",
        f"⌦ Pot : {_format_luxen(pot)}",
        f"⌦ Winner Share : {_format_luxen(share)}" if winners else "⌦ Winner Share : 0✦𝕷",
        "",
    ]
    for uid in active:
        p = players.get(uid) or {}
        label = f"{p.get('best_score')}"
        if p.get('best_suit') == 'Three of a Kind':
            label += ' · Three of a Kind'
        else:
            label += f" · Suit {p.get('best_suit')}"
        outcome = []
        if uid in winners:
            outcome.append('Pemenang ronde')
        if uid in losers:
            outcome.append('Nilai terendah')
        lines.append(f"› {p.get('name')} · {' '.join(p.get('hand', []))} · {label}" + (f" · {' / '.join(outcome)}" if outcome else ''))
    winner_names = ', '.join((players.get(uid) or {}).get('name', '-') for uid in winners) if winners else '-'
    lines.extend([
        "",
        "Asmoday menurunkan vonis tanpa ragu.",
        f"⌦ {winner_names} mengamankan {_format_luxen(share if len(winners)==1 else pot)} pada ronde ini." if winners else "⌦ Tidak ada pemenang yang tercatat.",
        "⌦ Nilai tertinggi mendekati 31 mengambil meja; nilai terendah jatuh paling dulu.",
    ])
    await _thirtyone_refresh_message(context, room)
    await _thirtyone_send_room_message(context, room, "\n".join(lines), reply_markup=_thirtyone_next_round_keyboard())

async def thirtyone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == 'private':
        await update.message.reply_text('Thirty-One hanya bisa dibuka di group.')
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text('Kamu harus punya account number dulu sebelum buka meja Thirty-One.')
        return
    key = _thirtyone_room_key(chat.id)
    if key in THIRTYONE_ROOMS:
        await update.message.reply_text('Masih ada meja Thirty-One yang aktif di grup ini.')
        return
    room = {
        'chat_id': chat.id,
        'thread_id': getattr(update.effective_message, 'message_thread_id', None),
        'host_id': user.id,
        'host_name': user.full_name or user.username or f'User {user.id}',
        'status': 'waiting',
        'round_no': 0,
        'players': {str(user.id): {'name': user.full_name or user.username or f'User {user.id}', 'bet': None, 'hand': [], 'best_score': 0, 'best_suit': '-', 'folded_round': False}},
        'message_id': None,
        'pot': 0,
        'center_cards': [],
    }
    sent = await update.message.reply_text(_thirtyone_status_text(room), reply_markup=_thirtyone_waiting_keyboard(room), message_thread_id=room['thread_id'])
    room['message_id'] = sent.message_id
    THIRTYONE_ROOMS[key] = room
    await _thirtyone_send_room_message(context, room, 'Asmoday membuka meja Thirty-One. Host sudah duduk; pemain lain dapat bergabung sekarang.')

async def thirtyone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    room = THIRTYONE_ROOMS.get(_thirtyone_room_key(query.message.chat_id))
    if not room:
        await query.answer('Meja tidak ditemukan.', show_alert=True)
        return
    action = (query.data or '').split(':', 1)[1]
    uid = str(query.from_user.id)
    if action == 'join':
        if room.get('status') != 'waiting':
            await query.answer('Ronde sudah berjalan.', show_alert=True)
            return
        if uid in room.get('players', {}):
            return
        rec = _get_existing_account(query.from_user.id)
        if not _has_gamble_access(rec):
            await query.answer('Butuh account number untuk ikut meja ini.', show_alert=True)
            return
        room['players'][uid] = {'name': query.from_user.full_name or query.from_user.username or uid, 'bet': None, 'hand': [], 'best_score': 0, 'best_suit': '-', 'folded_round': False}
        await _thirtyone_refresh_message(context, room)
        return
    if action == 'leave':
        if room.get('status') != 'waiting':
            await query.answer('Ronde sudah berjalan.', show_alert=True)
            return
        if uid == str(room.get('host_id')):
            await query.answer('Host tidak bisa leave. Tutup meja kalau mau batal.', show_alert=True)
            return
        room.get('players', {}).pop(uid, None)
        await _thirtyone_refresh_message(context, room)
        return
    if action == 'cancel' or action == 'close':
        if int(query.from_user.id) != int(room.get('host_id')) and not _is_admin(query.from_user):
            await query.answer('Hanya host atau admin yang bisa menutup meja.', show_alert=True)
            return
        THIRTYONE_ROOMS.pop(_thirtyone_room_key(query.message.chat_id), None)
        try:
            await query.edit_message_text('Asmoday menutup meja Thirty-One.')
        except Exception:
            pass
        return
    if action == 'start':
        if room.get('status') != 'waiting':
            return
        if int(query.from_user.id) != int(room.get('host_id')) and not _is_admin(query.from_user):
            await query.answer('Hanya host atau admin yang bisa memulai.', show_alert=True)
            return
        if len(room.get('players', {})) < 2:
            await query.answer('Minimal dua pemain.', show_alert=True)
            return
        room['status'] = 'betting'
        await _thirtyone_refresh_message(context, room)
        await _thirtyone_send_room_message(context, room, 'Asmoday membuka betting. Semua pemain kirim nominal bet dengan angka biasa di group ini.')
        return
    if action == 'nextround':
        if room.get('status') != 'finished':
            await query.answer('Ronde belum selesai.', show_alert=True)
            return
        room['status'] = 'betting'
        room['pot'] = 0
        for p in room.get('players', {}).values():
            p['bet'] = None
        await _thirtyone_refresh_message(context, room)
        await _thirtyone_send_room_message(context, room, 'Asmoday membuka betting untuk ronde berikutnya. Kirim nominal baru.')
        return

async def thirtyone_swap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    query = update.callback_query
    await query.answer()
    parts = (query.data or '').split(':')
    if len(parts) != 3:
        return
    _, action, idx_text = parts
    room = THIRTYONE_ROOMS.get(_thirtyone_room_key(query.message.chat_id))
    if not room or room.get('status') != 'action':
        await query.answer('Fase aksi tidak aktif.', show_alert=True)
        return
    uid = str(query.from_user.id)
    if uid != str(room.get('turn_uid')):
        await query.answer('Bukan giliranmu.', show_alert=True)
        return
    p = room.get('players', {}).get(uid)
    if not p:
        return
    if action == 'swapall':
        old_hand = list(p.get('hand', []))
        p['hand'] = list(room.get('center_cards', []))
        room['center_cards'] = old_hand
        await _thirtyone_send_room_message(context, room, f"Asmoday mencatat {p['name']} menukar seluruh tangan dengan tiga kartu tengah.")
    elif action == 'swap':
        try:
            idx = int(idx_text)
        except Exception:
            await query.answer('Pilihan kartu tidak valid.', show_alert=True)
            return
        center = room.get('center_cards', [])
        if idx < 0 or idx >= len(center):
            await query.answer('Pilihan kartu tidak valid.', show_alert=True)
            return
        taken = center[idx]
        discarded = p['hand'].pop(0)
        p['hand'].append(taken)
        center[idx] = discarded
        await _thirtyone_send_room_message(context, room, f"Asmoday melihat {p['name']} menukar satu kartu dari tengah.")
    elif action == 'pass':
        await _thirtyone_send_room_message(context, room, f"{p['name']} memilih diam dan melewatkan giliran.")
    elif action == 'knock':
        room['knock_uid'] = uid
        p['knocked'] = True
        others = [x for x in room.get('turn_order', []) if x != uid]
        room['final_turns_left'] = len(others)
        await _thirtyone_send_room_message(context, room, f"Asmoday menerima knock dari {p['name']}. Semua pemain lain hanya mendapat satu giliran terakhir.")
    p['best_score'], p['best_suit'] = _thirtyone_best_score(p['hand'])
    await _thirtyone_dm_hand(context, uid, room)
    if p['best_score'] == 31:
        await _thirtyone_finish_round(context, room, instant_uid=uid)
        return
    if room.get('knock_uid'):
        _thirtyone_advance_turn(room)
        if room.get('turn_uid') == room.get('knock_uid'):
            await _thirtyone_finish_round(context, room)
            return
        room['final_turns_left'] = max(0, int(room.get('final_turns_left', 0)) - 1)
        if room['final_turns_left'] <= 0:
            await _thirtyone_finish_round(context, room)
            return
    else:
        _thirtyone_advance_turn(room)
    await _thirtyone_refresh_message(context, room)

async def thirtyone_bet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return

    if update.effective_chat.type == "private" or not update.effective_message or not update.effective_message.text:
        return

    room = THIRTYONE_ROOMS.get(_thirtyone_room_key(update.effective_chat.id))
    if not room or room.get("status") != "betting":
        return

    uid = str(update.effective_user.id)
    if uid not in room.get("players", {}):
        return

    raw = (update.effective_message.text or "").strip().replace(",", "").replace(".", "")
    if not raw.isdigit():
        return

    bet = int(raw)
    if bet <= 0:
        return

    rec = _get_existing_account(update.effective_user.id)
    balance = int((rec or {}).get("balance", 0))
    if bet > balance:
        await update.effective_message.reply_text(
            f"Saldo kamu tidak cukup. Saldo sekarang: {_format_luxen(balance)}"
        )
        return

    room["players"][uid]["bet"] = bet

    name = room["players"][uid].get("name", "Player")

    await update.effective_message.reply_text(
        "\n".join([
            "",
            f"{name} menempatkan taruhan.",
            f"Jumlah: {_format_luxen(bet)}",
            "",
        ]),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )

    await _thirtyone_refresh_message(context, room)

    if all((p.get("bet") or 0) > 0 for p in room.get("players", {}).values()):
        room["pot"] = 0

        for pid, p in room.get("players", {}).items():
            prec = _get_existing_account(int(pid))
            if prec:
                prec["balance"] = max(0, int(prec.get("balance", 0)) - int(p.get("bet", 0)))
            room["pot"] += int(p.get("bet", 0))

        save_accounts()

        await _thirtyone_send_room_message(
            context,
            room,
            "\n".join([
                "‹🃏:۰ ALL BETS LOCKED",
                "— — • — • — — • — • — — • — • — —",
                "",
                f"Total Pot: {_format_luxen(room.get('pot', 0))}",
                "",
                "Semua taruhan telah diterima.",
                "Asmoday mulai membagikan kartu.",
            ]),
        )

        await _thirtyone_start_round(context, room)


# =========================================================
# HANDLERS & APP SETUP
# =========================================================

# =========================================================
# FEATURE: CHESS
# =========================================================
def _chess_room_key(chat_id: int) -> str:
    return str(chat_id)


def _chess_bet_label(amount: int) -> str:
    return f"{_normalize_price_text(amount)} ✦𝕷" if int(amount or 0) > 0 else "No Bet"


def _chess_render_board(board) -> str:
    piece_map = {
        "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
        "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
    }
    rows = []
    for rank in range(8, 0, -1):
        cells = []
        for file_idx in range(8):
            sq = chess.square(file_idx, rank - 1)
            piece = board.piece_at(sq)
            if piece:
                cells.append(piece_map.get(piece.symbol(), piece.symbol()))
            else:
                cells.append("·")
        rows.append(f"{rank} " + " ".join(cells))
    rows.append("  a b c d e f g h")
    return "\n".join(rows)




def _chess_norm_asset_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _chess_asset_dirs():
    base_dirs = []
    try:
        base_dirs.append(Path(CHESS_ASSET_DIR).expanduser())
    except Exception:
        pass
    base_dirs.extend([
        Path.home() / "Documents" / "Oxana" / "chess",
        Path.home() / "documents" / "oxana" / "chess",
        Path.cwd() / "Documents" / "Oxana" / "chess",
        Path.cwd() / "documents" / "oxana" / "chess",
        Path.cwd() / "document" / "oxana" / "chess",
        Path(__file__).resolve().parent / "Documents" / "Oxana" / "chess",
        Path(__file__).resolve().parent / "documents" / "oxana" / "chess",
        Path(__file__).resolve().parent / "document" / "oxana" / "chess",
        ASSETS_DIR / "Chess",
        ASSETS_DIR / "chess",
        Path(__file__).resolve().parent / "Chess",
        Path(__file__).resolve().parent / "chess",
    ])
    seen = set()
    out = []
    for d in base_dirs:
        try:
            key = str(d.resolve())
        except Exception:
            key = str(d)
        if key in seen:
            continue
        seen.add(key)
        if d.exists() and d.is_dir():
            out.append(d)
    return out


def _chess_find_asset(candidates):
    exts = {".png", ".webp", ".jpg", ".jpeg"}
    normalized_targets = {_chess_norm_asset_name(Path(c).stem) for c in candidates}
    for folder in _chess_asset_dirs():
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
        by_norm = {_chess_norm_asset_name(p.stem): p for p in files}
        for target in normalized_targets:
            if target in by_norm:
                return by_norm[target]
        # fallback: allow target words to be contained in asset names
        for target in normalized_targets:
            for norm_name, path in by_norm.items():
                if target and (target in norm_name or norm_name in target):
                    return path
    return None


def _chess_board_asset_path():
    return _chess_find_asset([
        "board", "chess_board", "chessboard", "dark_gothic_board", "asmoday_board", "papan", "papan_catur"
    ])


_CHESS_PIECE_ASSET_CANDIDATES = {
    "P": ["white_pawn", "wp", "pawn_white", "pion_white", "pion_putih", "whitepion"],
    "R": ["white_rook", "wr", "rook_white", "benteng_white", "benteng_putih"],
    "N": ["white_knight", "wn", "knight_white", "kuda_white", "kuda_putih"],
    "B": ["white_bishop", "wb", "bishop_white", "gajah_white", "gajah_putih"],
    "Q": ["white_queen", "wq", "queen_white", "ratu_white", "ratu_putih"],
    "K": ["white_king", "wk", "king_white", "raja_white", "raja_putih"],
    "p": ["black_pawn", "bp", "pawn_black", "pion_black", "pion_hitam", "blackpion"],
    "r": ["black_rook", "br", "rook_black", "benteng_black", "benteng_hitam"],
    "n": ["black_knight", "bn", "knight_black", "kuda_black", "kuda_hitam"],
    "b": ["black_bishop", "bb", "bishop_black", "gajah_black", "gajah_hitam"],
    "q": ["black_queen", "bq", "queen_black", "ratu_black", "ratu_hitam"],
    "k": ["black_king", "bk", "king_black", "raja_black", "raja_hitam"],
}


def _chess_piece_asset_path(symbol: str):
    return _chess_find_asset(_CHESS_PIECE_ASSET_CANDIDATES.get(symbol, [symbol]))


def _chess_render_board_image(board, last_move_uci: str = None):
    if not CHESS_IMAGE_AVAILABLE:
        return None, "Pillow belum tersedia. Install dulu dengan: pip install pillow"

    board_path = _chess_board_asset_path()
    if not board_path:
        dirs = ", ".join(str(p) for p in _chess_asset_dirs()) or CHESS_ASSET_DIR
        return None, f"Asset board tidak ditemukan. Pastikan ada board.png di folder: {dirs}"

    try:
        base = Image.open(board_path).convert("RGBA")
    except Exception as e:
        return None, f"Asset board gagal dibuka: {e}"

    board_w, board_h = base.size

    # Design board kamu:
    # fullboard 512x512px, grid/kotak aktif 437.6466px, 1 kotak 54.7058px.
    # Rumus di bawah otomatis menyesuaikan kalau gambar board di-resize.
    try:
        grid_size_cfg = float(globals().get("CHESS_BOARD_GRID_SIZE", 0) or 0)
    except Exception:
        grid_size_cfg = 0

    if grid_size_cfg > 0:
        ref_full = 512.0
        scale_ratio = min(board_w, board_h) / ref_full
        playable = grid_size_cfg * scale_ratio
        margin_x = (board_w - playable) / 2.0
        margin_y = (board_h - playable) / 2.0
    else:
        margin = max(0.0, float(CHESS_BOARD_MARGIN or 0))
        margin_x = margin
        margin_y = margin
        playable = min(board_w - (margin_x * 2), board_h - (margin_y * 2))
        if playable <= 0:
            margin_x = 0.0
            margin_y = 0.0
            playable = min(board_w, board_h)

    square = playable / 8.0
    if square <= 0:
        return None, "Ukuran board terlalu kecil untuk dirender."

    def _square_box(sq):
        file_idx = chess.square_file(sq)
        rank_idx = chess.square_rank(sq)
        x0 = margin_x + file_idx * square
        y0 = margin_y + (7 - rank_idx) * square
        x1 = x0 + square
        y1 = y0 + square
        return x0, y0, x1, y1

    # Highlight langkah terakhir. Dipakai setelah square float supaya kotaknya tidak geser.
    if last_move_uci:
        try:
            move = chess.Move.from_uci(last_move_uci)
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            line_w = max(2, int(round(square / 24)))
            for sq in (move.from_square, move.to_square):
                x0, y0, x1, y1 = _square_box(sq)
                draw.rectangle(
                    [int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))],
                    fill=(120, 0, 0, 58),
                    outline=(190, 25, 25, 145),
                    width=line_w,
                )
            base = Image.alpha_composite(base, overlay)
        except Exception:
            pass

    piece_cache = {}
    missing = []
    try:
        scale = float(CHESS_PIECE_SCALE or 0.85)
    except Exception:
        scale = 0.85
    scale = max(0.45, min(1.20, scale))
    piece_size = max(1, int(round(square * scale)))

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece:
            continue

        sym = piece.symbol()
        if sym not in piece_cache:
            p_path = _chess_piece_asset_path(sym)
            if not p_path:
                missing.append(sym)
                piece_cache[sym] = None
            else:
                try:
                    piece_cache[sym] = Image.open(p_path).convert("RGBA")
                except Exception:
                    missing.append(sym)
                    piece_cache[sym] = None

        piece_img = piece_cache.get(sym)
        if piece_img is None:
            continue

        piece_img = piece_img.resize((piece_size, piece_size), Image.LANCZOS)
        x0, y0, x1, y1 = _square_box(sq)
        x = int(round(x0 + ((square - piece_size) / 2.0)))
        y = int(round(y0 + ((square - piece_size) / 2.0)))
        base.alpha_composite(piece_img, (x, y))

    bio = BytesIO()
    bio.name = "asmoday_chess_board.png"
    base.convert("RGBA").save(bio, format="PNG", optimize=True)
    bio.seek(0)

    err = None
    if missing:
        missing_unique = ", ".join(sorted(set(missing)))
        err = f"Beberapa asset bidak belum ditemukan: {missing_unique}"
    return bio, err

def _chess_room_status_text(room: dict) -> str:
    white_uid = room.get("white_uid")
    black_uid = room.get("black_uid")
    white_name = (room.get("players", {}).get(str(white_uid)) or {}).get("name", "-")
    black_name = (room.get("players", {}).get(str(black_uid)) or {}).get("name", "-")
    host_name = room.get("host_name", "-")
    bet = int(room.get("bet", 0) or 0)
    lines = [
        "♟️ ╱ CHESS COURT",
        "",
        f"Host : {host_name}",
        f"Bet : {_chess_bet_label(bet)}",
        f"Status : {(room.get('status') or 'waiting').title()}",
        "",
        "Players:",
    ]
    order = room.get("player_order", [])
    if not order:
        lines.append("› -")
    else:
        for idx, uid in enumerate(order, start=1):
            pdata = room.get("players", {}).get(str(uid)) or {}
            role = []
            if str(uid) == str(white_uid):
                role.append("White")
            if str(uid) == str(black_uid):
                role.append("Black")
            role_text = f" [{' / '.join(role)}]" if role else ""
            lines.append(f"› {idx}. {pdata.get('name', 'Player')}{role_text}")
    if room.get("status") == "waiting":
        lines.extend([
            "",
            "‹♟️:۰  𝗖𝗛𝗘𝗦𝗦 — 𝗚𝗔𝗠𝗘 𝗙𝗟𝗢𝗪",
            "— — • — • — — • — • — — • — • — —",
            "Each match is conducted in a 1 vs 1 format.",
            "One player initiates the room, the other accepts the duel.",
            "",
            "› Create   : /chess atau /chess <bet>",
            "› Join     : /joinchess untuk memasuki room",
            "› Start    : /chessstart untuk memulai permainan",
            "› Move     : gunakan format UCI (e2e4, g8f6, e7e8q)",
            "",
            "If a wager is applied, both players must hold sufficient balance",
            "before the match is permitted to begin.",
        ])
    return "\n".join(lines)


def _chess_waiting_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join", callback_data="chess:join"), InlineKeyboardButton("Leave", callback_data="chess:leave")],
        [InlineKeyboardButton("Start", callback_data="chess:start"), InlineKeyboardButton("Close", callback_data="chess:close")],
    ])


async def _chess_refresh_message(context, room: dict):
    if not room.get("message_id"):
        return
    markup = _chess_waiting_keyboard() if room.get("status") == "waiting" else None
    try:
        await context.bot.edit_message_text(
            chat_id=room.get("chat_id"),
            message_id=room.get("message_id"),
            text=_chess_room_status_text(room),
            reply_markup=markup,
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[_chess_refresh_message] error: {e}")


async def _chess_send_room_message(context, room: dict, text: str):
    kwargs = {"chat_id": room.get("chat_id"), "text": text}
    if room.get("thread_id"):
        kwargs["message_thread_id"] = room.get("thread_id")
    if room.get("message_id"):
        kwargs["reply_to_message_id"] = room.get("message_id")
    return await context.bot.send_message(**kwargs)


def _chess_stockfish_ready() -> bool:
    return bool(CHESS_LIB_AVAILABLE and STOCKFISH_PATH and Path(STOCKFISH_PATH).exists())


def _chess_best_move(board):
    if not _chess_stockfish_ready():
        return None
    engine = None
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        try:
            engine.configure({"Skill Level": 20})
        except Exception:
            pass
        result = engine.play(board, chess.engine.Limit(depth=15))
        return result.move
    except Exception as e:
        print(f"[_chess_best_move] error: {e}")
        return None
    finally:
        try:
            if engine:
                engine.quit()
        except Exception:
            pass


async def _chess_notify_forneus_hint(context, room: dict):
    turn_uid = int(room.get("turn_uid") or 0)
    if not turn_uid or turn_uid != int(FORNEUS_UID or 0):
        return
    if not CHESS_LIB_AVAILABLE:
        try:
            await context.bot.send_message(chat_id=turn_uid, text="♟️ Asmoday tak dapat membaca papan, karena python-chess belum terpasang pada server ini.")
        except Exception:
            pass
        return
    board = room.get("board")
    if not board:
        return
    best_move = _chess_best_move(board)
    if not best_move:
        try:
            await context.bot.send_message(chat_id=turn_uid, text="♟️ Asmoday tak dapat memanggil Stockfish saat ini. Pastikan STOCKFISH_PATH benar dan binary aktif.")
        except Exception:
            pass
        return
    try:
        san = board.san(best_move)
    except Exception:
        san = best_move.uci()
    side = "White" if board.turn == chess.WHITE else "Black"
    msg = (
        "♟️ Asmoday whispers...\n\n"
        f"Kamu sedang memegang sisi {side}.\n"
        f"Langkah terbaik saat ini : {best_move.uci()}\n"
        f"Notation : {san}\n\n"
        "Ikuti langkah ini bila ingin menapak ke jalur kemenangan."
    )
    try:
        await context.bot.send_message(chat_id=turn_uid, text=msg)
    except Exception as e:
        print(f"[_chess_notify_forneus_hint] DM failed: {e}")


async def _chess_send_board(context, room: dict, note: str = None):
    board = room.get("board")
    if not board:
        return
    white_uid = room.get("white_uid")
    black_uid = room.get("black_uid")
    white_name = (room.get("players", {}).get(str(white_uid)) or {}).get("name", "-")
    black_name = (room.get("players", {}).get(str(black_uid)) or {}).get("name", "-")
    turn_uid = room.get("turn_uid")
    turn_name = (room.get("players", {}).get(str(turn_uid)) or {}).get("name", "-")

    caption_lines = [
        "♟️ 𝗔𝗦𝗠𝗢𝗗𝗔𝗬’𝗦 𝗖𝗛𝗘𝗦𝗦𝗕𝗢𝗔𝗥𝗗",
        "",
        f"White : {white_name}",
        f"Black : {black_name}",
        f"Bet : {_chess_bet_label(int(room.get('bet', 0) or 0))}",
    ]
    if note:
        caption_lines.extend(["", note])
    if board.is_check():
        caption_lines.append("Status : Check")
    caption_lines.extend([
        "",
        f"Turn : {turn_name}",
        "Kirim langkah dengan format seperti e2e4 atau e7e8q.",
    ])
    caption = "\n".join(caption_lines)

    img, img_err = _chess_render_board_image(board, room.get("last_move"))
    if img:
        kwargs = {
            "chat_id": room.get("chat_id"),
            "photo": img,
            "caption": caption,
        }
        if room.get("thread_id"):
            kwargs["message_thread_id"] = room.get("thread_id")
        if room.get("message_id"):
            kwargs["reply_to_message_id"] = room.get("message_id")
        try:
            await context.bot.send_photo(**kwargs)
        except Exception as e:
            print(f"[_chess_send_board] send_photo error: {e}")
            img = None

    if not img:
        lines = [
            "♟️ CHESS MATCH",
            "",
            f"White : {white_name}",
            f"Black : {black_name}",
            f"Bet : {_chess_bet_label(int(room.get('bet', 0) or 0))}",
            "",
            _chess_render_board(board),
            "",
        ]
        if note:
            lines.append(note)
            lines.append("")
        if img_err:
            lines.append(f"Image board belum dapat dirender: {img_err}")
            lines.append("")
        if board.is_check():
            lines.append("Status : Check")
        lines.append(f"Turn : {turn_name}")
        lines.append("Kirim langkah dengan format seperti e2e4 atau e7e8q.")
        await _chess_send_room_message(context, room, "\n".join(lines))

    await _chess_notify_forneus_hint(context, room)

def _chess_parse_bet_arg(context) -> int:
    if not getattr(context, "args", None):
        return 0
    raw = (context.args[0] or "").replace(",", "").replace(".", "").strip()
    if not raw or not raw.isdigit():
        return -1
    amount = int(raw)
    return amount if amount >= 0 else -1


async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not CHESS_LIB_AVAILABLE:
        await update.message.reply_text("python-chess belum terpasang di server ini. Install dulu dengan: pip install python-chess")
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("Chess hanya bisa dibuka di group.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu sebelum buka room Chess.")
        return
    room_key = _chess_room_key(chat.id)
    if room_key in CHESS_ROOMS:
        await update.message.reply_text("Masih ada room Chess aktif di grup ini.")
        return
    bet = _chess_parse_bet_arg(context)
    if bet < 0:
        await update.message.reply_text("Format: /chess atau /chess <nominal_bet>")
        return
    room = {
        "chat_id": chat.id,
        "thread_id": getattr(update.effective_message, "message_thread_id", None),
        "host_id": user.id,
        "host_name": user.full_name or user.username or f"User {user.id}",
        "status": "waiting",
        "bet": int(bet or 0),
        "players": {
            str(user.id): {"name": user.full_name or user.username or f"User {user.id}", "joined_at": _now().strftime("%Y-%m-%d %H:%M:%S")}
        },
        "player_order": [str(user.id)],
        "white_uid": None,
        "black_uid": None,
        "turn_uid": None,
        "board": chess.Board(),
        "message_id": None,
        "stake_locked": False,
    }
    sent = await update.message.reply_text(
        _chess_room_status_text(room),
        reply_markup=_chess_waiting_keyboard(),
        message_thread_id=getattr(update.effective_message, "message_thread_id", None),
    )
    room["message_id"] = sent.message_id
    CHESS_ROOMS[room_key] = room
    flow_text = (
        "♟️ Asmoday membuka meja Chess.\n\n"
        "Gameflow :\n"
        "› Room ini khusus 1 vs 1.\n"
        "› Lawan masuk dengan /joinchess.\n"
        "› Host memulai duel dengan /chessstart.\n"
        "› Move dikirim dengan format UCI seperti e2e4, b8c6, atau e7e8q.\n"
        "› Jika host membuka room memakai nominal bet, saldo kedua pemain akan dikunci saat duel dimulai.\n"
        "› Pemenang menerima total pot. Jika seri, saldo dikembalikan.\n"
    )
    await _chess_send_room_message(context, room, flow_text)


async def join_chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    if not CHESS_LIB_AVAILABLE:
        await update.message.reply_text("python-chess belum terpasang di server ini. Install dulu dengan: pip install python-chess")
        return
    chat = update.effective_chat
    user = update.effective_user
    room = CHESS_ROOMS.get(_chess_room_key(chat.id))
    if not room:
        await update.message.reply_text("Belum ada room Chess aktif di grup ini. Gunakan /chess dulu.")
        return
    if room.get("status") != "waiting":
        await update.message.reply_text("Duel sudah dimulai. Tunggu room berikutnya.")
        return
    uid = str(user.id)
    if uid in room.get("players", {}):
        await update.message.reply_text("Kamu sudah ada di room Chess ini.")
        return
    if len(room.get("player_order", [])) >= 2:
        await update.message.reply_text("Room Chess ini sudah penuh. Chess hanya 1 vs 1.")
        return
    rec = _get_existing_account(user.id)
    if not _has_gamble_access(rec):
        await update.message.reply_text("Kamu harus punya account number dulu untuk ikut room Chess.")
        return
    room["players"][uid] = {"name": user.full_name or user.username or f"User {user.id}", "joined_at": _now().strftime("%Y-%m-%d %H:%M:%S")}
    room["player_order"].append(uid)
    await _chess_refresh_message(context, room)
    await _chess_send_room_message(context, room, f"{room['players'][uid]['name']} duduk di meja Chess. Host bisa mulai duel dengan /chessstart.")


async def _chess_start_room(context, room: dict, actor):
    if room.get("status") != "waiting":
        return False, "Duel Chess sudah dimulai."
    if len(room.get("player_order", [])) != 2:
        return False, "Room Chess harus berisi tepat 2 pemain."
    import random
    order = room.get("player_order", [])[:]
    random.shuffle(order)
    white_uid, black_uid = int(order[0]), int(order[1])
    bet = int(room.get("bet", 0) or 0)
    if bet > 0:
        for uid in (white_uid, black_uid):
            rec = _get_existing_account(uid)
            bal = int((rec or {}).get("balance", 0))
            if bal < bet:
                name = (room.get("players", {}).get(str(uid)) or {}).get("name", f"UID {uid}")
                return False, f"Saldo {name} tidak cukup untuk bet {_normalize_price_text(bet)}."
        for uid in (white_uid, black_uid):
            rec = _get_existing_account(uid)
            rec["balance"] = int(rec.get("balance", 0)) - bet
        save_accounts()
        room["stake_locked"] = True
    room["white_uid"] = white_uid
    room["black_uid"] = black_uid
    room["turn_uid"] = white_uid
    room["board"] = chess.Board()
    room["status"] = "playing"
    await _chess_refresh_message(context, room)
    for uid in (white_uid, black_uid):
        color = "White" if uid == white_uid else "Black"
        other_uid = black_uid if uid == white_uid else white_uid
        other_name = (room.get("players", {}).get(str(other_uid)) or {}).get("name", "-")
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    "♟️ Asmoday membuka duel Chess-mu.\n\n"
                    f"Sisi : {color}\n"
                    f"Lawan : {other_name}\n"
                    f"Bet : {_chess_bet_label(bet)}\n\n"
                    "Gerakkan bidak di group dengan format seperti e2e4 atau e7e8q.\n"
                )
            )
        except Exception as e:
            print(f"[_chess_start_room] DM info failed uid={uid}: {e}")
    await _chess_send_board(context, room, note="Asmoday memulai duel. White bergerak lebih dulu.")
    return True, None


async def chess_start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    room = CHESS_ROOMS.get(_chess_room_key(update.effective_chat.id))
    if not room:
        await update.message.reply_text("Belum ada room Chess aktif.")
        return
    if update.effective_user.id != room.get("host_id") and not _is_admin(update.effective_user):
        await update.message.reply_text("Hanya host atau admin yang bisa memulai duel Chess.")
        return
    ok, err = await _chess_start_room(context, room, update.effective_user)
    if not ok and err:
        await update.message.reply_text(err)


async def chess_close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    room = CHESS_ROOMS.get(_chess_room_key(update.effective_chat.id))
    if not room:
        await update.message.reply_text("Belum ada room Chess aktif.")
        return
    if update.effective_user.id != room.get("host_id") and not _is_admin(update.effective_user):
        await update.message.reply_text("Hanya host atau admin yang bisa menutup room Chess.")
        return
    if room.get("stake_locked") and room.get("status") == "playing":
        white_uid = int(room.get("white_uid") or 0)
        black_uid = int(room.get("black_uid") or 0)
        bet = int(room.get("bet", 0) or 0)
        for uid in (white_uid, black_uid):
            rec = _get_existing_account(uid)
            if rec:
                rec["balance"] = int(rec.get("balance", 0)) + bet
        save_accounts()
    CHESS_ROOMS.pop(_chess_room_key(update.effective_chat.id), None)
    await update.message.reply_text("Asmoday menutup room Chess.")


async def chess_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await _ensure_not_banned(update, context):
        return
    await query.answer()
    room = CHESS_ROOMS.get(_chess_room_key(query.message.chat_id))
    if not room:
        await query.answer("Room Chess tidak ditemukan.", show_alert=True)
        return
    action = (query.data or "").split(":", 1)[1]
    if action == "join":
        class DummyUpdate:
            effective_chat = query.message.chat
            effective_user = query.from_user
            message = query.message
        fake = DummyUpdate()
        # Inline version of join to avoid duplication side effects
        if room.get("status") != "waiting":
            await query.answer("Duel sudah dimulai.", show_alert=True)
            return
        uid = str(query.from_user.id)
        if uid in room.get("players", {}):
            return
        if len(room.get("player_order", [])) >= 2:
            await query.answer("Room Chess sudah penuh.", show_alert=True)
            return
        rec = _get_existing_account(query.from_user.id)
        if not _has_gamble_access(rec):
            await query.answer("Kamu harus punya account number dulu.", show_alert=True)
            return
        room["players"][uid] = {"name": query.from_user.full_name or query.from_user.username or f"User {query.from_user.id}", "joined_at": _now().strftime("%Y-%m-%d %H:%M:%S")}
        room["player_order"].append(uid)
        await _chess_refresh_message(context, room)
        await _chess_send_room_message(context, room, f"{room['players'][uid]['name']} duduk di meja Chess. Host bisa mulai duel dengan /chessstart.")
        return
    if action == "leave":
        if room.get("status") != "waiting":
            await query.answer("Duel sudah dimulai. Tidak bisa leave sekarang.", show_alert=True)
            return
        uid = str(query.from_user.id)
        if uid == str(room.get("host_id")):
            await query.answer("Host tidak bisa leave. Tutup room bila ingin batal.", show_alert=True)
            return
        if uid in room.get("players", {}):
            room["players"].pop(uid, None)
            room["player_order"] = [x for x in room.get("player_order", []) if str(x) != uid]
            await _chess_refresh_message(context, room)
        return
    if action == "start":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya host atau admin yang bisa memulai.", show_alert=True)
            return
        ok, err = await _chess_start_room(context, room, query.from_user)
        if not ok and err:
            await query.answer(err, show_alert=True)
        return
    if action == "close":
        if query.from_user.id != room.get("host_id") and not _is_admin(query.from_user):
            await query.answer("Hanya host atau admin yang bisa menutup.", show_alert=True)
            return
        if room.get("stake_locked") and room.get("status") == "playing":
            white_uid = int(room.get("white_uid") or 0)
            black_uid = int(room.get("black_uid") or 0)
            bet = int(room.get("bet", 0) or 0)
            for uid in (white_uid, black_uid):
                rec = _get_existing_account(uid)
                if rec:
                    rec["balance"] = int(rec.get("balance", 0)) + bet
            save_accounts()
        CHESS_ROOMS.pop(_chess_room_key(query.message.chat_id), None)
        try:
            await query.edit_message_text("Asmoday menutup room Chess.")
        except Exception:
            pass


async def _chess_finish(context, room: dict, result_text: str, winner_uid: int = None, is_draw: bool = False):
    bet = int(room.get("bet", 0) or 0)
    white_uid = int(room.get("white_uid") or 0)
    black_uid = int(room.get("black_uid") or 0)
    if room.get("stake_locked") and bet > 0:
        if is_draw or not winner_uid:
            for uid in (white_uid, black_uid):
                rec = _get_existing_account(uid)
                if rec:
                    rec["balance"] = int(rec.get("balance", 0)) + bet
        else:
            rec = _get_existing_account(int(winner_uid))
            if rec:
                rec["balance"] = int(rec.get("balance", 0)) + (bet * 2)
        save_accounts()
    room["status"] = "finished"
    await _chess_send_room_message(context, room, result_text)
    CHESS_ROOMS.pop(_chess_room_key(room.get("chat_id")), None)


async def chess_move_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _ensure_not_banned(update, context):
        return
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not CHESS_LIB_AVAILABLE or chat.type == "private" or not msg or not msg.text:
        return
    room = CHESS_ROOMS.get(_chess_room_key(chat.id))
    if not room or room.get("status") != "playing":
        return
    if int(room.get("turn_uid") or 0) != int(user.id):
        return
    raw = (msg.text or "").strip().lower()
    if len(raw) not in (4, 5):
        return
    try:
        move = chess.Move.from_uci(raw)
    except Exception:
        return
    board = room.get("board")
    if not board or move not in board.legal_moves:
        await msg.reply_text("Langkah tidak sah. Gunakan format seperti e2e4 atau e7e8q.")
        return
    mover_name = (room.get("players", {}).get(str(user.id)) or {}).get("name", user.full_name or user.username or f"User {user.id}")
    try:
        san = board.san(move)
    except Exception:
        san = raw
    board.push(move)
    room["last_move"] = move.uci()
    note = f"{mover_name} memainkan {raw} ({san})."
    if board.is_checkmate():
        await _chess_send_board(context, room, note=note + " Checkmate tercapai.")
        await _chess_finish(context, room, f"♟️ CHECKMATE! {mover_name} menang dan mengambil seluruh pot {_chess_bet_label(int(room.get('bet', 0) or 0) * 2) if int(room.get('bet', 0) or 0) > 0 else ''}.", winner_uid=user.id, is_draw=False)
        return
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
        await _chess_send_board(context, room, note=note + " Duel berakhir seri.")
        await _chess_finish(context, room, "♟️ Duel Chess berakhir seri. Pot dikembalikan kepada kedua pihak.", winner_uid=None, is_draw=True)
        return
    next_uid = int(room.get("black_uid") if int(user.id) == int(room.get("white_uid")) else room.get("white_uid"))
    room["turn_uid"] = next_uid
    await _chess_send_board(context, room, note=note)




# wrap approval supaya Curated Dining bisa di-ACC tanpa mengganggu flow lain
_curated_or_old_process_approval_action = _process_approval_action

async def _process_approval_action(context, actor, chat_id: int, target_message, mode: str, reply_message=None):
    info = approval_map.get((chat_id, target_message.message_id)) if target_message else None
    if not info or info.get("kind") != "curated_dining":
        return await _curated_or_old_process_approval_action(context, actor, chat_id, target_message, mode, reply_message)
    if chat_id != FORWARD_PUBLIC_CHAT_ID:
        return False, "Approval hanya bisa dilakukan di grup pengurus."
    if not _is_admin(actor):
        return False, "Hanya Deittee atau Currathor."
    item = _find_curated(info.get("curated_id"))
    if not item or not item.get("booking") or item["booking"].get("booking_id") != info.get("booking_id"):
        return False, "Data Curated Dining tidak ditemukan."
    booking = item.get("booking") or {}
    guest_uid = int(booking.get("guest_uid", 0) or 0)
    guest_rec = _get_existing_account(guest_uid)
    if mode == "acc":
        if not guest_rec:
            return False, "Account guest tidak ditemukan."
        amount = int(item.get("price", 0) or 0)
        balance = int(guest_rec.get("balance", 0) or 0)
        if balance < amount:
            item["status"] = "open"; item["booking"] = None
            save_curated_dining_data(); await _curated_refresh_public_message(context, item)
            try: await context.bot.send_message(chat_id=guest_uid, text="ⓘ Curated Dining belum dapat disahkan sebab saldo belum mencukupi. Slot kembali available.")
            except Exception: pass
            return False, "Saldo guest tidak cukup. Slot kembali available."
        guest_rec["balance"] = balance - amount
        save_accounts()
        payouts = await _credit_currathors(context, int(amount * 50 / 100), f"Bagi hasil 50% Curated Dining dari {booking.get('guest_display')}")
        item["status"] = "confirmed"; booking["status"] = "confirmed"
        booking["confirmed_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
        booking["currathor_payouts"] = {str(k): int(v) for k, v in (payouts or {}).items()}
        booking["guest_balance_deducted_at"] = _now().strftime("%Y-%m-%d %H:%M:%S")
        save_curated_dining_data(); await _curated_refresh_public_message(context, item)
        try:
            await context.bot.send_message(chat_id=guest_uid, text=("✅ Curated Dining reservation approved.\n\n" f"Curated ID : {item.get('id')}\n" f"Total : {_normalize_price_text(amount)} ✦𝕷\n" f"Balance : {_normalize_price_text(guest_rec.get('balance', 0))} ✦𝕷"))
        except Exception:
            pass
        result_text = f"Curated Dining {item.get('id')} disahkan untuk {booking.get('guest_display')}."
    elif mode == "reject":
        item["status"] = "open"; item["booking"] = None
        save_curated_dining_data(); await _curated_refresh_public_message(context, item)
        try: await context.bot.send_message(chat_id=guest_uid, text="Curated Dining reservation tidak memperoleh restu. Slot kembali available.")
        except Exception: pass
        result_text = "Curated Dining ditolak. Slot kembali available."
    else:
        return False, "Mode approval tidak valid."
    for key, value in list(approval_map.items()):
        if value.get("kind") == "curated_dining" and value.get("booking_id") == info.get("booking_id"):
            approval_map.pop(key, None)
    save_state()
    if reply_message:
        try: await reply_message.reply_text(result_text)
        except Exception: pass
    return True, result_text

def main():
    load_state()
    load_accounts()
    load_pending()
    load_started_users()
    load_menu_data()
    load_angel_data()
    load_payment_data()
    load_shift_data()
    load_staff_interview_data()
    load_room_data()    
    load_curated_dining_data()
    load_custom_command_data()
    load_cnit_claims()
    load_cnit_book()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("registration", registration_cmd))
    app.add_handler(CommandHandler("registrationstaff", registration_staff_cmd))
    app.add_handler(CommandHandler("oprecstaff", oprec_staff_cmd))
    app.add_handler(CommandHandler("renewal", renewal_cmd))
    app.add_handler(CommandHandler("upgradevip", upgrade_vip_cmd))
    app.add_handler(CommandHandler("starttalk", starttalk))
    app.add_handler(CommandHandler("stoptalk", stoptalk))
    app.add_handler(CommandHandler("myacc", my_acc))
    app.add_handler(CommandHandler("changeidcphoto", change_pict_cmd))
    app.add_handler(CommandHandler("changepict", change_pict_cmd))
    app.add_handler(CommandHandler("mybalance", my_balance))
    app.add_handler(CommandHandler("mystafflog", my_cnit_cmd))
    app.add_handler(CommandHandler("setnitroid", set_nitro_id_cmd))
    app.add_handler(CommandHandler("claimcnit", claim_cnit_cmd))
    app.add_handler(CommandHandler("confirmcnit", confirm_cnit_cmd))
    app.add_handler(CommandHandler("rejectcnit", reject_cnit_cmd))
    app.add_handler(CommandHandler("changecodename", change_codename))
    app.add_handler(CommandHandler("changefullname", change_fullname))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("where_forward", where_forward))
    app.add_handler(CommandHandler("getid", get_id))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("letheamenu", lethea_menu_cmd))
    app.add_handler(CommandHandler("createmenu", create_menu_cmd))
    app.add_handler(CommandHandler("createroom", create_room_cmd))
    app.add_handler(CommandHandler("listroom", list_room_cmd))
    app.add_handler(CommandHandler("bookinglist", booking_list_cmd))
    app.add_handler(CommandHandler("delroom", del_room_cmd))
    app.add_handler(CommandHandler("rollmenu", roll_menu_cmd))
    app.add_handler(CommandHandler("listmenu", list_menu_cmd))
    app.add_handler(CommandHandler("infomenu", info_menu_cmd))
    app.add_handler(CommandHandler("delmenu", del_menu_cmd))
    app.add_handler(CommandHandler("addpriceall", add_price_all_cmd))
    app.add_handler(CommandHandler("addprice", add_price_cmd))
    app.add_handler(CommandHandler("sendbill", send_bill_cmd))
    app.add_handler(CommandHandler("inputangel", input_angel_cmd))
    app.add_handler(CommandHandler("rentangel", rent_angel_cmd))
    app.add_handler(CommandHandler("reserveresort", reserver_resort_cmd))
    app.add_handler(CommandHandler("tarot", tarot_cmd))
    app.add_handler(CommandHandler("angelprice", angel_price_cmd))
    app.add_handler(CommandHandler("angeloff", angel_off_cmd))
    app.add_handler(CommandHandler("myangelbook", my_angel_book_cmd))
    app.add_handler(CommandHandler("listangel", list_angel_cmd))
    app.add_handler(CommandHandler("openwarung", open_warung_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("openbar", open_bar_cmd))
    app.add_handler(CommandHandler("openresort", open_resort_cmd))
    app.add_handler(CommandHandler("opencurated", open_curated_cmd))
    app.add_handler(CommandHandler("listcurated", list_curated_cmd))
    app.add_handler(CommandHandler("closecurated", close_curated_cmd))
    app.add_handler(CommandHandler("delcurated", del_curated_cmd))
    app.add_handler(CommandHandler("addcmd", addcmd_cmd))
    app.add_handler(CommandHandler("listcmd", listcmd_cmd))
    app.add_handler(CommandHandler("delcmd", delcmd_cmd))
    app.add_handler(InlineQueryHandler(curated_inline_query_router))
    app.add_handler(CallbackQueryHandler(open_warung_callback, pattern=r"^openwarung:"))
    app.add_handler(CommandHandler("closebar", close_bar_cmd))
    app.add_handler(CommandHandler("openshift", open_shift_cmd))
    app.add_handler(CommandHandler("shiftresortopen", open_shift_resort_cmd))
    app.add_handler(CommandHandler("closeshift", close_shift_cmd))

    # gamble handlers
    app.add_handler(CommandHandler("choicepoker", choice_poker_cmd))
    app.add_handler(CommandHandler("thirtyone", thirtyone_cmd))
    app.add_handler(CommandHandler("poker", poker_cmd))
    app.add_handler(CommandHandler("blackjack", blackjack_cmd))
    app.add_handler(CommandHandler("booray", booray_cmd))
    app.add_handler(CommandHandler("dicepoker", dice_poker_cmd))
    app.add_handler(CommandHandler("symphony", alluringsymphony_cmd))
    app.add_handler(CommandHandler("alluringsymphony", alluringsymphony_cmd))
    app.add_handler(CommandHandler("alluring", alluringsymphony_cmd))
    app.add_handler(CommandHandler("baccarat", baccarat_cmd))
    app.add_handler(CommandHandler("baccaratbet", baccarat_bet_cmd))
    app.add_handler(CommandHandler("jugement", jugement_cmd))
    app.add_handler(CommandHandler("judgment", jugement_cmd))
    app.add_handler(CommandHandler("jugdment", jugement_cmd))
    app.add_handler(CommandHandler("joinjudgment", join_jugement_cmd))
    app.add_handler(CommandHandler("bet", jugement_bet_cmd))
    app.add_handler(CommandHandler("take", jugement_take_cmd))
    app.add_handler(CommandHandler("pass", jugement_pass_cmd))
    app.add_handler(CommandHandler("lock", jugement_lock_cmd))
    app.add_handler(CommandHandler("chess", chess_cmd))
    app.add_handler(CommandHandler("joinchess", join_chess_cmd))
    app.add_handler(CommandHandler("chessstart", chess_start_cmd))
    app.add_handler(CommandHandler("chessclose", chess_close_cmd))

    # admin handlers
    app.add_handler(CommandHandler("addstaff", add_staff))
    app.add_handler(CommandHandler("editrole", edit_role))
    app.add_handler(CommandHandler("delstaff", del_staff))
    app.add_handler(CommandHandler("ban", ban_user_cmd))
    app.add_handler(CommandHandler("unban", unban_user_cmd))
    app.add_handler(CommandHandler("addsaldo", add_saldo))
    app.add_handler(CommandHandler("minsaldo", min_saldo))
    app.add_handler(CommandHandler("listacc", list_acc))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("deladmin", del_admin))
    app.add_handler(CommandHandler("listadmin", list_admin))
    app.add_handler(CommandHandler("delacc", del_acc))
    app.add_handler(CommandHandler("acc", acc_pending))
    app.add_handler(CommandHandler("reject", reject_pending))
    app.add_handler(CommandHandler("addcnit", add_cnit_cmd))
    app.add_handler(CommandHandler("dellcnit", del_cnit_cmd))
    app.add_handler(CommandHandler("cnitbook", cnit_book_cmd))
    app.add_handler(CommandHandler("botfee", bot_fee_cmd))
    app.add_handler(CommandHandler("mybill", my_bill_cmd))
    app.add_handler(CommandHandler("paymentbill", payment_bill_cmd))

    for _tag_cmd in TAG_COMMAND_ROLE_MAP.keys():
        app.add_handler(CommandHandler(_tag_cmd, tag_command))

    app.add_handler(CommandHandler("topup", topup_cmd))
    app.add_handler(CommandHandler("openevent", openevent_cmd))
    app.add_handler(CommandHandler("closeevent", closeevent_cmd))

    app.add_handler(CallbackQueryHandler(semi_app_nav_callback, pattern=r"^nav:"))
    app.add_handler(CallbackQueryHandler(semi_app_action_callback, pattern=r"^navaction:"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(registration_callback, pattern=r"^reg:"))
    app.add_handler(CallbackQueryHandler(registration_callback, pattern=r"^renew:"))
    app.add_handler(CallbackQueryHandler(registration_callback, pattern=r"^upgrade:"))
    app.add_handler(CallbackQueryHandler(registration_callback, pattern=r"^regconfirm:"))
    app.add_handler(CallbackQueryHandler(registration_callback, pattern=r"^proofdone:"))
    app.add_handler(CallbackQueryHandler(staff_interview_callback, pattern=r"^staffiv:"))
    app.add_handler(CallbackQueryHandler(proof_edit_callback, pattern=r"^proofedit:"))
    app.add_handler(CallbackQueryHandler(approval_callback, pattern=r"^approve:"))
    app.add_handler(CallbackQueryHandler(choice_poker_callback, pattern=r"^choicepoker:"))
    app.add_handler(CallbackQueryHandler(thirtyone_callback, pattern=r"^thirtyone:"))
    app.add_handler(CallbackQueryHandler(thirtyone_swap_callback, pattern=r"^thirtyoneact:"))
    app.add_handler(CallbackQueryHandler(poker_callback, pattern=r"^poker:"))
    app.add_handler(CallbackQueryHandler(blackjack_callback, pattern=r"^blackjack:"))
    app.add_handler(CallbackQueryHandler(booray_callback, pattern=r"^booray:"))
    app.add_handler(CallbackQueryHandler(booray_decision_callback, pattern=r"^booraydecide:"))
    app.add_handler(CallbackQueryHandler(booray_play_callback, pattern=r"^boorayplay:"))
    app.add_handler(CallbackQueryHandler(blackjack_action_callback, pattern=r"^blackjackact:"))
    app.add_handler(CallbackQueryHandler(poker_action_callback, pattern=r"^pokeract:"))
    app.add_handler(CallbackQueryHandler(choice_poker_swap_callback, pattern=r"^choicepokerswap:"))
    app.add_handler(CallbackQueryHandler(choice_poker_action_callback, pattern=r"^choicepokeract:"))
    app.add_handler(CallbackQueryHandler(choice_poker_choice_callback, pattern=r"^choicepokerchoice:"))
    app.add_handler(CallbackQueryHandler(chess_callback, pattern=r"^chess:"))
    app.add_handler(CallbackQueryHandler(dice_poker_callback, pattern=r"^dicepoker:"))
    app.add_handler(CallbackQueryHandler(dice_poker_turn_callback, pattern=r"^dicepokerturn:"))
    app.add_handler(CallbackQueryHandler(symphony_callback, pattern=r"^symphony:"))
    app.add_handler(CallbackQueryHandler(symphony_play_callback, pattern=r"^symphonyplay:"))
    app.add_handler(CallbackQueryHandler(symphony_piano_callback, pattern=r"^symphonypiano:"))
    app.add_handler(CallbackQueryHandler(baccarat_callback, pattern=r"^baccarat:"))
    app.add_handler(CallbackQueryHandler(jugement_callback, pattern=r"^jugement:"))
    app.add_handler(CallbackQueryHandler(jugement_action_callback, pattern=r"^jugementact:"))
    app.add_handler(CallbackQueryHandler(staff_role_callback, pattern=r"^staffrole:"))
    app.add_handler(CallbackQueryHandler(menu_create_callback, pattern=r"^menucreate:"))
    app.add_handler(CallbackQueryHandler(room_create_callback, pattern=r"^roomcreate:"))
    app.add_handler(CallbackQueryHandler(curated_create_callback, pattern=r"^curatedcreate:"))
    app.add_handler(CallbackQueryHandler(curated_reserve_callback, pattern=r"^curatedreserve:"))
    app.add_handler(CallbackQueryHandler(addcmd_callback, pattern=r"^addcmd:"))
    app.add_handler(CallbackQueryHandler(payment_bill_callback, pattern=r"^paybill:"))
    app.add_handler(CallbackQueryHandler(topup_callback, pattern=r"^topup:"))
    app.add_handler(CallbackQueryHandler(event_admin_callback, pattern=r"^eventadmin:"))
    app.add_handler(CallbackQueryHandler(event_join_callback, pattern=r"^eventjoin:"))
    app.add_handler(CallbackQueryHandler(cnit_claim_callback, pattern=r"^cnitclaim:"))
    app.add_handler(CallbackQueryHandler(open_shift_mode_callback, pattern=r"^openshiftmode:"))
    app.add_handler(CallbackQueryHandler(angel_input_callback, pattern=r"^angelinput:"))
    app.add_handler(CallbackQueryHandler(angel_view_callback, pattern=r"^angelview:"))
    app.add_handler(CallbackQueryHandler(resort_reservation_callback, pattern=r"^resortreserve:"))
    app.add_handler(CallbackQueryHandler(angel_calendar_callback, pattern=r"^angelcal:"))
    app.add_handler(CallbackQueryHandler(tarot_callback, pattern=r"^tarot:"))
    app.add_handler(CallbackQueryHandler(angel_off_calendar_callback, pattern=r"^angeloffcal:"))
    app.add_handler(CallbackQueryHandler(shift_join_callback, pattern=r"^shiftjoin:"))
    app.add_handler(CallbackQueryHandler(shift_recap_callback, pattern=r"^shiftrecap:"))
    app.add_handler(CallbackQueryHandler(resort_admin_cancel_callback, pattern=r"^resortadmincancel:"))

    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, event_open_text_router, block=True), group=-31)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_text_router, block=True), group=-30)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, bang_game_router, block=False), group=-13)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, open_bar_link_router, block=False), group=-8)
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, change_pict_image_router, block=True), group=-20)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & (filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, addcmd_media_router, block=True), group=-19)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, addcmd_text_router, block=True), group=-19)
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, curated_create_photo_router, block=True), group=-19)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, curated_create_text_router, block=True), group=-18)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, curated_booking_text_router, block=True), group=-17)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, angel_input_image_router, block=False), group=-7)
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, create_menu_image_router, block=False), group=-6)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, angel_input_text_router, block=False), group=-5)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, create_menu_text_router, block=False), group=-4)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, create_room_text_router, block=False), group=-3)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, choice_poker_bet_router, block=False), group=-9)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, chess_move_router, block=False), group=-12)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, thirtyone_bet_router, block=False), group=-10)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, poker_bet_router, block=False), group=-10)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, blackjack_bet_router, block=False), group=-10)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, dice_poker_bet_router, block=False), group=-10)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, dice_poker_text_router, block=False), group=-10)
    app.add_handler(MessageHandler(filters.Chat(FORWARD_PUBLIC_CHAT_ID) & filters.TEXT & ~filters.COMMAND, approval_text_router, block=False), group=-2)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, talk_admin_reply_router), group=-1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tarot_text_router, block=False), group=0)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, angel_booking_text_router, block=False), group=1)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, resort_reservation_text_router, block=False), group=2)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, registration_text_router, block=False), group=3)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & (filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, registration_proof_router, block=False), group=4)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, menu_text_router, block=False), group=5)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, talk_user_router, block=False), group=6)
    app.add_handler(MessageHandler(filters.COMMAND, custom_command_router, block=True), group=20)

    if app.job_queue:
        app.job_queue.run_repeating(membership_expiry_watcher, interval=3600, first=30)
        app.job_queue.run_repeating(resort_booking_link_watcher, interval=60, first=10)
        app.job_queue.run_repeating(resort_checkout_warning_watcher, interval=60, first=15)
        app.job_queue.run_repeating(resort_checkout_watcher, interval=300, first=15)
    app.add_error_handler(error_handler)
    print("Asmoday is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
