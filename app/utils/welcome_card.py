from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import get_settings

settings = get_settings()

CARD_TEXT_TEMPLATE = (
    "{fullname} ရေ\n\n"
    "{group_name} မှ\n"
    "လှိုက်လှဲစွာ ကြိုဆိုပါတယ်။\n\n"
    "Group ထဲမှာ စကားတွေပြောရင်း\n"
    "ဘဝရဲ့ ပျော်စရာအချိန်လေးတွေအဖြစ်\n"
    "အတူတူ ဖန်တီးလိုက်ကြရအောင်။"
)


def ensure_output_dir() -> Path:
    out_dir = Path(settings.WELCOME_CARD_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def load_font(size: int, prefer_myanmar: bool = True):
    candidates = []
    if prefer_myanmar:
        candidates.append(settings.WELCOME_CARD_FONT_MYANMAR)
    candidates.append(settings.WELCOME_CARD_FONT_LATIN)

    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def contains_myanmar(text: str) -> bool:
    return any("\u1000" <= ch <= "\u109f" or "\uaa60" <= ch <= "\uaa7f" for ch in text)


def pick_font_for_text(text: str, size: int):
    return load_font(size=size, prefer_myanmar=contains_myanmar(text))


def crop_to_circle(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.fit(image.convert("RGBA"), (size, size), method=Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)
    return output


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.rstrip()
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = f"{current} {word}".strip() if current else word
            bbox = draw.textbbox((0, 0), test, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                    current = word
                else:
                    lines.append(word)
                    current = ""
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
    except Exception:
        return None


def render_card(fullname: str, group_name: str, profile_image: Optional[Image.Image] = None, custom_text: str | None = None) -> Path:
    template_path = Path(settings.WELCOME_CARD_TEMPLATE)
    if not template_path.exists():
        raise FileNotFoundError(f"Welcome card template not found: {template_path}")

    base = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    circle_x, circle_y, circle_size = 52, 326, 355
    text_x, text_y, text_w, text_h = 425, 250, 890, 470

    if profile_image is not None:
        base.alpha_composite(crop_to_circle(profile_image, circle_size), (circle_x, circle_y))

    final_text = (custom_text or CARD_TEXT_TEMPLATE).format(fullname=fullname, group_name=group_name)
    body_font = pick_font_for_text(final_text, 36)
    wrapped = wrap_text(draw, final_text, body_font, text_w)

    lines = wrapped.splitlines()
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line if line else "A", font=body_font)
        h = bbox[3] - bbox[1]
        line_heights.append(max(h, body_font.size + 8))
    total_height = sum(line_heights) + max(0, (len(lines) - 1) * 10)
    start_y = text_y + max(0, (text_h - total_height) // 2)

    current_y = start_y
    for idx, line in enumerate(lines):
        content = line if line else " "
        bbox = draw.textbbox((0, 0), content, font=body_font)
        line_width = bbox[2] - bbox[0]
        x = text_x + (text_w - line_width) // 2
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + ox, current_y + oy), content, font=body_font, fill=(30, 20, 10, 180))
        draw.text((x, current_y), content, font=body_font, fill=(255, 245, 230, 255))
        current_y += line_heights[idx] + 10

    out_dir = ensure_output_dir()
    safe_name = ''.join(ch if ch.isalnum() else '_' for ch in fullname[:20]) or 'user'
    output_path = out_dir / f"welcome_card_{safe_name}.png"
    base.save(output_path, format="PNG")
    return output_path
