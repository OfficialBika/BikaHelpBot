from __future__ import annotations

import io
import os
import textwrap
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


def contains_myanmar(text: str) -> bool:
    return any(
        "\u1000" <= ch <= "\u109f" or "\uaa60" <= ch <= "\uaa7f"
        for ch in text
    )


def load_font(
    size: int,
    prefer_myanmar: bool = True,
    bold: bool = False,
):
    candidates: list[str] = []

    if prefer_myanmar:
        if bold and getattr(settings, "WELCOME_CARD_FONT_MYANMAR_BOLD", ""):
            candidates.append(settings.WELCOME_CARD_FONT_MYANMAR_BOLD)
        if getattr(settings, "WELCOME_CARD_FONT_MYANMAR", ""):
            candidates.append(settings.WELCOME_CARD_FONT_MYANMAR)

    if bold and getattr(settings, "WELCOME_CARD_FONT_LATIN_BOLD", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN_BOLD)

    if getattr(settings, "WELCOME_CARD_FONT_LATIN", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN)

    if getattr(settings, "WELCOME_CARD_FONT_LATIN_ALT", ""):
        candidates.append(settings.WELCOME_CARD_FONT_LATIN_ALT)

    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass

    return ImageFont.load_default()


def pick_font_for_text(text: str, size: int, bold: bool = False):
    return load_font(
        size=size,
        prefer_myanmar=contains_myanmar(text),
        bold=bold,
    )


def crop_to_circle(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.fit(
        image.convert("RGBA"),
        (size, size),
        method=Image.LANCZOS,
    )

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)

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
                continue

            if current:
                lines.append(current)
                current = word
                continue

            rough = max(1, max_width // max(10, font.size // 2))
            broken = textwrap.wrap(word, width=rough)
            if broken:
                lines.extend(broken[:-1])
                current = broken[-1]
            else:
                current = word

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

    # Left circle position
    circle_x = 52
    circle_y = 326
    circle_size = 355

    # Right text box area
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

    title_font = pick_font_for_text(final_text, 44, bold=True)
    body_font = pick_font_for_text(final_text, 36, bold=False)

    # If first line should look slightly stronger, we still render the full body with body font
    # to keep Myanmar shaping consistent and line spacing stable.
    wrapped = wrap_text(draw, final_text, body_font, text_w)
    lines = wrapped.splitlines()

    line_heights: list[int] = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line if line else "A", font=body_font)
        h = bbox[3] - bbox[1]
        line_heights.append(max(h, body_font.size + 8))

    total_height = sum(line_heights) + max(0, (len(lines) - 1) * 10)
    start_y = text_y + max(0, (text_h - total_height) // 2)

    current_y = start_y
    for idx, line in enumerate(lines):
        content = line if line else " "
        font_to_use = body_font

        # Make very first visible line slightly stronger if desired
        if idx == 0 and content.strip():
            font_to_use = title_font

        bbox = draw.textbbox((0, 0), content, font=font_to_use)
        line_width = bbox[2] - bbox[0]
        x = text_x + (text_w - line_width) // 2

        # Soft shadow/glow
        shadow_fill = (40, 25, 15, 180)
        text_fill = (255, 245, 230, 255)

        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + ox, current_y + oy), content, font=font_to_use, fill=shadow_fill)

        draw.text((x, current_y), content, font=font_to_use, fill=text_fill)

        current_y += line_heights[idx] + 10

    out_dir = ensure_output_dir()
    safe_name = fullname[:30].replace(" ", "_").replace("/", "_")
    output_path = out_dir / f"welcome_card_{safe_name}.png"
    base.save(output_path, format="PNG")
    return output_path
