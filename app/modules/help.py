from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import help_keyboard, start_keyboard
from app.utils.formatters import bullet_list, join_lines

router = Router()


def build_help_text() -> str:
    sections = bullet_list(
        [
            "/start - bot စတင်မိတ်ဆက်",
            "/help - command list",
            "/ping - bot response speed",
            "/id - user/chat id ကြည့်ရန်",
            "/json - replied message json ကြည့်ရန်",
            "/notes - saved notes ကြည့်ရန်",
            "/warns - warns system",
            "/settings - chat settings",
        ]
    )
    return join_lines(
        "<b>Help Menu</b>",
        "",
        "ဒီ bot မှာပါဝင်မယ့် base commands တွေက:",
        sections,
        "",
        "Module အလိုက် help buttons တွေကိုလည်း အောက်မှာနှိပ်ကြည့်နိုင်ပါတယ်။",
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.reply(build_help_text(), reply_markup=help_keyboard(), disable_web_page_preview=True)


@router.callback_query(F.data == "help:open")
async def help_open_cb(query: CallbackQuery) -> None:
    if query.message:
        await query.message.edit_text(build_help_text(), reply_markup=help_keyboard(), disable_web_page_preview=True)
    await query.answer()


@router.callback_query(F.data == "help:back")
async def help_back_cb(query: CallbackQuery) -> None:
    text = join_lines("<b>Main Menu</b>", "", "Help menu ကနေ main menu ကိုပြန်ရောက်ပါပြီ။")
    if query.message:
        await query.message.edit_text(text, reply_markup=start_keyboard(), disable_web_page_preview=True)
    await query.answer()


@router.callback_query(F.data == "help:admin")
async def help_admin_cb(query: CallbackQuery) -> None:
    text = join_lines(
        "<b>Admin Help</b>",
        "",
        bullet_list([
            "/ban - user ban",
            "/unban - user unban",
            "/mute - user mute",
            "/unmute - user unmute",
            "/warn - user warn",
            "/del - replied message delete",
        ]),
    )
    if query.message:
        await query.message.edit_text(text, reply_markup=help_keyboard())
    await query.answer()


@router.callback_query(F.data == "help:greetings")
async def help_greetings_cb(query: CallbackQuery) -> None:
    text = join_lines(
        "<b>Greetings Help</b>",
        "",
        bullet_list([
            "/welcome - welcome status/view",
            "/setwelcome - custom welcome text",
            "/cleanwelcome - old welcome cleanup",
        ]),
    )
    if query.message:
        await query.message.edit_text(text, reply_markup=help_keyboard())
    await query.answer()


@router.callback_query(F.data == "help:notes")
async def help_notes_cb(query: CallbackQuery) -> None:
    text = join_lines(
        "<b>Notes Help</b>",
        "",
        bullet_list([
            "/save <name> <text> - note သိမ်းရန်",
            "/get <name> - note ပြန်ခေါ်ရန်",
            "/notes - notes list",
            "/clear <name> - note ဖျက်ရန်",
        ]),
    )
    if query.message:
        await query.message.edit_text(text, reply_markup=help_keyboard())
    await query.answer()


@router.callback_query(F.data == "help:warns")
async def help_warns_cb(query: CallbackQuery) -> None:
    text = join_lines(
        "<b>Warns Help</b>",
        "",
        bullet_list([
            "/warn - replied user ကို warn ပေးရန်",
            "/warns - current warns info",
            "/resetwarns - warns reset",
        ]),
    )
    if query.message:
        await query.message.edit_text(text, reply_markup=help_keyboard())
    await query.answer()


@router.callback_query(F.data == "help:close")
@router.callback_query(F.data == "close")
async def help_close_cb(query: CallbackQuery) -> None:
    if query.message:
        try:
            await query.message.delete()
        except Exception:
            pass
    await query.answer("ပိတ်လိုက်ပါပြီ။")
