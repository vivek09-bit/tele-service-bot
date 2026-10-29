"""
Telegram Sales & Services Bot
Handles service catalogs, pricing inquiries, contact routing, and keyword matching.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Base directory & data loading
BASE_DIR = Path(__file__).resolve().parent
SERVICES_FILE = BASE_DIR / "services.json"


def load_services_data() -> Dict[str, Any]:
    """Loads services and company configuration from services.json."""
    if not SERVICES_FILE.exists():
        logger.error("services.json not found at %s", SERVICES_FILE)
        return {"company": {}, "services": []}
    try:
        with open(SERVICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Error loading services.json: %s", e)
        return {"company": {}, "services": []}


DATA = load_services_data()
COMPANY = DATA.get("company", {})
SERVICES: List[Dict[str, Any]] = DATA.get("services", [])

# Fallback contact info from .env or services.json
PROFILE = DATA.get("profile") or DATA.get("company", {})
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", PROFILE.get("email", "contact@example.com"))
CONTACT_PHONE = os.getenv("CONTACT_PHONE", PROFILE.get("phone", "+1 (555) 000-0000"))
CONTACT_TELEGRAM = os.getenv("CONTACT_TELEGRAM", PROFILE.get("telegram", "@SupportBot"))
CONTACT_WEBSITE = os.getenv("CONTACT_WEBSITE", PROFILE.get("website", "https://example.com"))
NAME = PROFILE.get("name", "Personal Assistant")
TAGLINE = PROFILE.get("tagline", "Quality Services & Solutions")


def get_service_by_id(service_id: str) -> Optional[Dict[str, Any]]:
    """Helper to find service item by its unique ID."""
    for s in SERVICES:
        if s.get("id") == service_id:
            return s
    return None


# ---------------------------------------------------------
# UI Builders (Keyboards & Messages)
# ---------------------------------------------------------


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Builds the primary navigation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📂 View Services", callback_data="menu_services"),
            InlineKeyboardButton("💰 Pricing & Rates", callback_data="menu_pricing"),
        ],
        [
            InlineKeyboardButton("📞 Contact Me", callback_data="menu_contact"),
            InlineKeyboardButton("💬 Chat / Hire Me", callback_data="inquire_general"),
        ],
        [
            InlineKeyboardButton("🌐 Portfolio / Website", url=CONTACT_WEBSITE if CONTACT_WEBSITE.startswith("http") else f"https://{CONTACT_WEBSITE}")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_services_keyboard() -> InlineKeyboardMarkup:
    """Builds buttons for each service in the catalog."""
    keyboard = []
    # Two buttons per row for clean display
    row = []
    for s in SERVICES:
        icon = s.get("icon", "🔹")
        title = s.get("title", "Service")
        btn = InlineKeyboardButton(f"{icon} {title}", callback_data=f"service_{s.get('id')}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Navigation footer
    keyboard.append([
        InlineKeyboardButton("💰 Pricing Guide", callback_data="menu_pricing"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(keyboard)


def build_service_detail_keyboard(service_id: str) -> InlineKeyboardMarkup:
    """Builds action buttons for a single service view."""
    keyboard = [
        [
            InlineKeyboardButton("💬 Inquire / Order This", callback_data=f"inquire_{service_id}"),
        ],
        [
            InlineKeyboardButton("⬅️ Back to Services", callback_data="menu_services"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to main menu button."""
    keyboard = [
        [
            InlineKeyboardButton("📂 View Services", callback_data="menu_services"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------
# Message Content Formatters
# ---------------------------------------------------------


def format_welcome_message(first_name: str = "there") -> str:
    """Formats the main greeting text."""
    return (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"I am the personal assistant bot for <b>{NAME}</b>.\n"
        f"<i>{TAGLINE}</i>\n\n"
        f"How can I help you today? Choose an option below or send a message to ask about my services, rates, or availability:"
    )


def format_pricing_message() -> str:
    """Formats the pricing breakdown for all services."""
    lines = [f"<b>💰 Services & Pricing Guide — {NAME}</b>\n"]
    for s in SERVICES:
        icon = s.get("icon", "🔹")
        title = s.get("title", "Service")
        pricing = s.get("pricing", "Contact for custom quote")
        turnaround = s.get("turnaround", "Variable")
        lines.append(f"{icon} <b>{title}</b>")
        lines.append(f"  • <b>Rate:</b> {pricing}")
        lines.append(f"  • <b>Turnaround:</b> {turnaround}\n")

    lines.append("<i>Need a customized quote, retainer, or specific project scope? Message me directly!</i>")
    return "\n".join(lines)


def format_contact_message() -> str:
    """Formats the contact info."""
    clean_telegram = CONTACT_TELEGRAM.lstrip("@")
    return (
        f"<b>📞 Get in Touch with {NAME}</b>\n\n"
        f"I am available for freelance projects, consulting, and collaborations.\n\n"
        f"📧 <b>Email:</b> {CONTACT_EMAIL}\n"
        f"📱 <b>Phone/WhatsApp:</b> {CONTACT_PHONE}\n"
        f"💬 <b>Telegram:</b> <a href=\"https://t.me/{clean_telegram}\">{CONTACT_TELEGRAM}</a>\n"
        f"🌐 <b>Portfolio:</b> <a href=\"{CONTACT_WEBSITE}\">{CONTACT_WEBSITE}</a>\n\n"
        f"Feel free to reach out via your preferred channel!"
    )


def format_service_detail(service: Dict[str, Any]) -> str:
    """Formats comprehensive information about a single service."""
    icon = service.get("icon", "🔹")
    title = service.get("title", "Service")
    full_desc = service.get("full_desc", service.get("short_desc", ""))
    pricing = service.get("pricing", "Custom quote")
    turnaround = service.get("turnaround", "TBD")
    deliverables = service.get("deliverables", [])

    deliverables_text = "\n".join([f"  ✅ {item}" for item in deliverables]) if deliverables else "  ✅ Custom deliverables based on project scope"

    return (
        f"{icon} <b>{title}</b>\n\n"
        f"<b>Overview:</b>\n{full_desc}\n\n"
        f"<b>Key Deliverables:</b>\n{deliverables_text}\n\n"
        f"⏱ <b>Typical Turnaround:</b> {turnaround}\n"
        f"💵 <b>Investment / Rate:</b> {pricing}\n\n"
        f"<i>Interested or have questions? Click below to discuss your project!</i>"
    )


# ---------------------------------------------------------
# Telegram Event Handlers
# ---------------------------------------------------------


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    name = user.first_name if user else "there"
    text = format_welcome_message(name)
    reply_markup = build_main_menu_keyboard()

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    help_text = (
        f"<b>💡 How to use {NAME}'s Assistant Bot:</b>\n\n"
        f"• <b>/start</b> - Open main menu\n"
        f"• <b>/services</b> - Browse available services & skills\n"
        f"• <b>/pricing</b> - View pricing & rates guide\n"
        f"• <b>/contact</b> - Get direct contact information\n"
        f"• <b>/help</b> - Show this help guide\n\n"
        f"You can also simply type keywords such as <i>'web'</i>, <i>'bot'</i>, <i>'seo'</i>, or <i>'rate'</i>, and I'll find what you need!"
    )
    if update.message:
        await update.message.reply_text(
            help_text,
            reply_markup=build_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /services command."""
    text = (
        f"<b>📂 My Core Services & Offerings</b>\n\n"
        f"Select a service below for detailed specifications, deliverables, and rates:"
    )
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=build_services_keyboard(),
            parse_mode=ParseMode.HTML,
        )


async def pricing_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /pricing command."""
    text = format_pricing_message()
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /contact command."""
    text = format_contact_message()
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispatches button clicks from inline keyboards."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""
    user = update.effective_user
    user_name = user.first_name if user else "there"

    # Navigation actions
    if data == "menu_main":
        text = format_welcome_message(user_name)
        await query.edit_message_text(
            text=text,
            reply_markup=build_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    elif data == "menu_services":
        text = (
            f"<b>📂 My Core Services & Offerings</b>\n\n"
            f"Select a service below for detailed specifications, deliverables, and rates:"
        )
        await query.edit_message_text(
            text=text,
            reply_markup=build_services_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    elif data == "menu_pricing":
        text = format_pricing_message()
        await query.edit_message_text(
            text=text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    elif data == "menu_contact":
        text = format_contact_message()
        await query.edit_message_text(
            text=text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    elif data.startswith("service_"):
        service_id = data.replace("service_", "")
        service = get_service_by_id(service_id)
        if service:
            text = format_service_detail(service)
            await query.edit_message_text(
                text=text,
                reply_markup=build_service_detail_keyboard(service_id),
                parse_mode=ParseMode.HTML,
            )
        else:
            await query.edit_message_text(
                text="⚠️ Service details could not be found.",
                reply_markup=build_services_keyboard(),
            )

    elif data.startswith("inquire_"):
        service_id = data.replace("inquire_", "")
        clean_telegram = CONTACT_TELEGRAM.lstrip("@")
        service_title = "My Services"

        if service_id != "general":
            service = get_service_by_id(service_id)
            if service:
                service_title = service.get("title", service_title)

        inquiry_text = (
            f"💼 <b>Inquiry: {service_title}</b>\n\n"
            f"Thanks for reaching out! Let's discuss your project goals. You can contact me directly:\n\n"
            f"👉 <b>Telegram:</b> <a href=\"https://t.me/{clean_telegram}\">{CONTACT_TELEGRAM}</a>\n"
            f"📧 <b>Email:</b> {CONTACT_EMAIL}\n"
            f"📱 <b>Phone:</b> {CONTACT_PHONE}\n\n"
            f"Or send a message right here with your requirements and timeline!"
        )

        inquiry_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"💬 Direct Message ({CONTACT_TELEGRAM})",
                    url=f"https://t.me/{clean_telegram}",
                )
            ],
            [
                InlineKeyboardButton("⬅️ Back to Services", callback_data="menu_services"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            ],
        ])

        await query.edit_message_text(
            text=inquiry_text,
            reply_markup=inquiry_keyboard,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles free-form user messages using keyword search across services and intents.
    """
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip().lower()

    # Direct intent matches
    if any(k in user_text for k in ["contact", "email", "phone", "call", "reach", "talk", "agent", "human", "support"]):
        text = format_contact_message()
        await update.message.reply_text(
            text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    if any(k in user_text for k in ["price", "pricing", "cost", "how much", "quote", "rate", "fee"]):
        text = format_pricing_message()
        await update.message.reply_text(
            text,
            reply_markup=build_back_to_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    if any(k in user_text for k in ["hello", "hi", "hey", "start", "menu"]):
        user = update.effective_user
        name = user.first_name if user else "there"
        await update.message.reply_text(
            format_welcome_message(name),
            reply_markup=build_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    # Match service keywords
    matched_services = []
    for s in SERVICES:
        keywords = s.get("keywords", [])
        title = s.get("title", "").lower()
        short_desc = s.get("short_desc", "").lower()

        # Score matching
        score = 0
        for kw in keywords:
            if kw in user_text:
                score += 2
        for word in user_text.split():
            if len(word) > 2 and (word in title or word in short_desc):
                score += 1

        if score > 0:
            matched_services.append((score, s))

    # Sort matches by score descending
    matched_services.sort(key=lambda x: x[0], reverse=True)

    if matched_services:
        best_match = matched_services[0][1]
        reply_header = f"🔍 <i>Found information related to your question:</i>\n\n"
        detail_text = format_service_detail(best_match)
        keyboard = build_service_detail_keyboard(best_match.get("id"))

        await update.message.reply_text(
            reply_header + detail_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    else:
        # Fallback guidance
        fallback_text = (
            f"🤔 I'm not sure I understood your question completely.\n\n"
            f"Would you like to browse my services or chat with me directly?"
        )
        await update.message.reply_text(
            fallback_text,
            reply_markup=build_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs unhandled exceptions."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    """Initializes and runs the Telegram Bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token.strip() == "" or token == "your_telegram_bot_token_here":
        print("\n" + "=" * 60)
        print("❌ ERROR: TELEGRAM_BOT_TOKEN is missing or not set in .env!")
        print("Please create/update .env file with your bot token from @BotFather:")
        print("TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        print("=" * 60 + "\n")
        return

    logger.info("Initializing %s's Assistant Bot...", NAME)

    application = ApplicationBuilder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("services", services_command))
    application.add_handler(CommandHandler("pricing", pricing_command))
    application.add_handler(CommandHandler("contact", contact_command))

    # Callback query handlers (Inline button clicks)
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Text message handler (Keyword matching & questions)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    # Error handling
    application.add_error_handler(error_handler)

    logger.info("Bot started successfully. Polling for updates...")
    application.run_polling()


if __name__ == "__main__":
    main()
