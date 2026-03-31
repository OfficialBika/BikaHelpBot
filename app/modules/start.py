from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.keyboards.inline import start_keyboard
from app.keyboards.reply import private_main_keyboard
from app.modules.helper_funcs.formatting import mention_html
from app.utils.formatters import join_lines

router = Router()
settings = get_settings()


@router.message(CommandStart())
async def start_cmd(message: Message) -> None:
    mention = mention_html(message.from_user)
    text = join_lines(
        f"ဟယ်လို {mention} 👋",
        f"ကျွန်မက <b>{settings.BOT_NAME}</b> ပါ။",
        "",
        "ဒီ bot က group management အတွက် build လုပ်ထားတာပါ။",
        "အဓိက command တွေကို /help နဲ့ကြည့်နိုင်ပါတယ်။",
    )

    if message.chat.type == "private":
        await message.answer(text, reply_markup=private_main_keyboard(), disable_web_page_preview=True)
        await message.answer("အောက်က inline menu ကိုလည်း သုံးနိုင်ပါတယ်။", reply_markup=start_keyboard())
    else:
        await message.reply(text, reply_markup=start_keyboard(), disable_web_page_preview=True)


@router.callback_query(F.data == "start:open")
async def start_open_cb(query: CallbackQuery) -> None:
    mention = mention_html(query.from_user)
    text = join_lines(
        f"ဟယ်လို {mention} 👋",
        f"<b>{settings.BOT_NAME}</b> ကိုအသုံးပြုနေပါတယ်။",
        "",
        "အကူအညီလိုရင် /help ကိုနှိပ်ပါ။",
    )
    if query.message:
        await query.message.edit_text(text, reply_markup=start_keyboard(), disable_web_page_preview=True)
    await query.answer()
