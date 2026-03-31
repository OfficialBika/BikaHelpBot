from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

CARD_TEXT_TEMPLATE = (
    "{fullname} ရေ\n\n"
    "{group_name} မှ\n"
    "လှိုက်လှဲစွာ ကြိုဆိုပါတယ်။\n\n"
    "Group ထဲမှာ ပျော်ပျော်ပါးပါး\n"
    "အတူတူ စကားပြောလိုက်ကြရအောင်။"
)


def ensure_output_dir() -> Path:
    out_dir = Path(settings.WELCOME_CARD_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def contains_myanmar(text: str) -> bool:
    return any("\u1000" <= ch <= "\u109F" or "\uAA60" <= ch <= "\uAA7F" for ch in text)


def safe_truetype(path: str | None, size: int):
    if not path:
        return None
    if not os.path.exists(path):
        return None
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:
        return None


def load_font(size: int, prefer_myanmar: bool = True, bold: bool = False):
    candidates: list[str] = []

    # Myanmar first
    if prefer_myanmar:
        if bold and getattr(settings, "WELCOME_CARD_FONT_MYANMAR_BOLD", ""):
            candidates.append(settings.WELCOME_CARD_FONT_MYANMAR_BOLD)
        if getattr(settings, "WELCOME_CARD_FONT_MYANMAR", ""):
            candidates.append(settings.WELCOME_CARD_FONT_MYANMAR)

    # Latin fallbacks
    if bold and getattr(settings, "WELCOME_CARD_FONT_LATIN_BOLD", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN_BOLD)

    if getattr(settings, "WELCOME_CARD_FONT_LATIN", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN)

    if getattr(settings, "WELCOME_CARD_FONT_LATIN_ALT", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN_ALT)

    for path in candidates:
        font = safe_truetype(path, size=size)
        if font is not None:
            return font

    return ImageFont.load_default()


def pick_font_for_text(text: str, size: int, bold: bool = False):
    return load_font(
        size=size,
        prefer_myanmar=contains_myanmar(text),
        bold=bold,
    )


def crop_to_circle(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.fit(image.convert("RGBA"), (size, size), method=Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)
    return output


def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    lines: list[str] = []

    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if text_width(draw, candidate, font) <= max_width:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = word
                continue

            # very long word fallback
            temp = ""
            for ch in word:
                test = temp + ch
                if text_width(draw, test, font) <= max_width:
                    temp = test
                else:
                    if temp:
                        lines.append(temp)
                    temp = ch
            current = temp

        if current:
            lines.append(current)

    return "\n".join(lines)


async def fetch_user_profile_image(bot, user_id: int) -> Optional[Image.Image]:
    try:
        photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
        if not photos.photos:
            return None

        file_id = photos.photos[0][-1].file_id
        file = await bot.get_file(file_id)

        bio = io.BytesIO()
        await bot.download_file(file.file_path, destination=bio)
        bio.seek(0)

        return Image.open(bio).convert("RGBA")
    except Exception as exc:
        logger.warning("Failed to fetch profile image for %s: %s", user_id, exc)
        return None


def render_card(
    fullname: str,
    group_name: str,
    profile_image: Optional[Image.Image] = None,
    custom_text: str | None = None,
) -> Path:
    template_path = Path(settings.WELCOME_CARD_TEMPLATE)
    if not template_path.exists():
        raise FileNotFoundError(f"Welcome card template not found: {template_path}")

    base = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    # Layout
    circle_x = 36
    circle_y = 346
    circle_size = 350

    text_x = 425
    text_y = 250
    text_w = 890
    text_h = 470

    if profile_image is not None:
        profile_circle = crop_to_circle(profile_image, circle_size)
        base.alpha_composite(profile_circle, (circle_x, circle_y))

    final_text = (custom_text or CARD_TEXT_TEMPLATE).format(
        fullname=fullname,
        group_name=group_name,
    )

    # Important: use Myanmar-capable body font for whole block
    body_font = pick_font_for_text(final_text, 36, bold=False)

    wrapped = wrap_text(draw, final_text, body_font, text_w)
    lines = wrapped.splitlines()

    line_gap = 12
    heights: list[int] = []
    for line in lines:
        h = text_height(draw, line if line else "A", body_font)
        heights.append(max(h, body_font.size + 6))

    total_height = sum(heights) + (len(lines) - 1) * line_gap if lines else 0
    start_y = text_y + max(0, (text_h - total_height) // 2)

    current_y = start_y
    shadow_fill = (35, 24, 16, 180)
    text_fill = (255, 245, 230, 255)

    for idx, line in enumerate(lines):
        content = line if line else " "
        w = text_width(draw, content, body_font)
        x = text_x + (text_w - w) // 2

        # soft shadow
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + ox, current_y + oy), content, font=body_font, fill=shadow_fill)

        draw.text((x, current_y), content, font=body_font, fill=text_fill)
        current_y += heights[idx] + line_gap

    out_dir = ensure_output_dir()
    safe_name = fullname[:30].replace(" ", "_").replace("/", "_")
    output_path = out_dir / f"welcome_card_{safe_name}.png"
    base.save(output_path, format="PNG")
    return output_path
