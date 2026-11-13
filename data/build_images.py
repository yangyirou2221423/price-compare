"""Generate abstract product artwork for the demo catalogue (no third-party images)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "src" / "static" / "products"
OUT.mkdir(parents=True, exist_ok=True)

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"

PRODUCTS = [
    ("p001", "星海", "X1 Pro", "手机", (14, 27, 44), (53, 84, 120), "phone"),
    ("p002", "灵越", "Air 14", "轻薄本", (17, 48, 54), (38, 103, 104), "laptop"),
    ("p003", "声阔", "Pods Pro", "耳机", (55, 30, 52), (122, 65, 100), "earbuds"),
    ("p004", "净界", "Air Pro", "空气净化", (20, 56, 47), (52, 116, 91), "purifier"),
    ("p005", "云鲸", "J6", "扫地机器人", (22, 44, 66), (49, 94, 136), "robot"),
    ("p006", "极光", "P3", "投影仪", (35, 35, 72), (76, 72, 139), "projector"),
    ("p007", "星环", "S2", "智能手表", (73, 47, 17), (151, 105, 40), "watch"),
    ("p008", "松下", "XQG100", "洗衣机", (40, 47, 55), (91, 104, 116), "washer"),
    ("p009", "追风", "Hurricane", "吹风机", (70, 34, 27), (154, 80, 58), "dryer"),
    ("p010", "星海", "Pad Air 11", "平板", (20, 49, 73), (52, 107, 150), "tablet"),
    ("p011", "战刃", "Blade 16", "游戏本", (44, 22, 26), (116, 48, 48), "laptop"),
    ("p012", "简物", "Box Mini", "收纳盒", (58, 50, 36), (137, 116, 78), "box"),
]


def gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (size, size), top)
    draw = ImageDraw.Draw(image)
    for y in range(size):
        t = y / max(1, size - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (size, y)], fill=color)
    return image.convert("RGBA")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size, index=0)


def draw_device(draw: ImageDraw.ImageDraw, kind: str, white) -> None:
    cx, cy = 360, 360
    if kind == "phone":
        draw.rounded_rectangle((232, 150, 488, 560), radius=52, outline=white, width=7)
        draw.rounded_rectangle((252, 190, 468, 522), radius=34, outline=(255, 255, 255, 120), width=3)
        draw.rounded_rectangle((322, 168, 398, 184), radius=8, fill=white)
        draw.ellipse((340, 535, 380, 575), outline=white, width=3)
    elif kind == "laptop":
        draw.rounded_rectangle((190, 190, 530, 430), radius=22, outline=white, width=7)
        draw.polygon([(150, 470), (570, 470), (610, 515), (110, 515)], outline=white, width=6)
        draw.line([(300, 500), (420, 500)], fill=white, width=4)
    elif kind == "tablet":
        draw.rounded_rectangle((200, 160, 520, 560), radius=36, outline=white, width=7)
        draw.rounded_rectangle((226, 196, 494, 524), radius=18, outline=(255, 255, 255, 110), width=3)
        draw.ellipse((348, 538, 372, 562), outline=white, width=3)
    elif kind == "earbuds":
        draw.rounded_rectangle((230, 320, 490, 500), radius=70, outline=white, width=7)
        draw.ellipse((280, 245, 360, 325), outline=white, width=7)
        draw.ellipse((360, 245, 440, 325), outline=white, width=7)
        draw.line([(300, 320), (300, 255)], fill=white, width=5)
        draw.line([(420, 320), (420, 255)], fill=white, width=5)
    elif kind == "purifier":
        draw.rounded_rectangle((250, 150, 470, 560), radius=48, outline=white, width=7)
        for y in range(230, 500, 34):
            draw.line([(290, y), (430, y)], fill=(255, 255, 255, 120), width=4)
        draw.ellipse((330, 510, 390, 570), outline=white, width=4)
    elif kind == "robot":
        draw.ellipse((190, 270, 530, 610), outline=white, width=8)
        draw.ellipse((250, 330, 470, 550), outline=(255, 255, 255, 130), width=4)
        draw.ellipse((330, 180, 390, 240), outline=white, width=6)
        draw.arc((300, 410, 420, 510), 20, 160, fill=white, width=5)
    elif kind == "projector":
        draw.rounded_rectangle((180, 260, 540, 470), radius=40, outline=white, width=7)
        draw.ellipse((240, 300, 370, 430), outline=white, width=6)
        draw.ellipse((275, 335, 335, 395), outline=white, width=4)
        for x in range(410, 500, 22):
            draw.line([(x, 320), (x, 410)], fill=(255, 255, 255, 120), width=3)
        draw.line([(250, 470), (220, 535)], fill=white, width=6)
        draw.line([(470, 470), (500, 535)], fill=white, width=6)
    elif kind == "watch":
        draw.rounded_rectangle((260, 180, 460, 500), radius=52, outline=white, width=7)
        draw.rounded_rectangle((290, 220, 430, 460), radius=34, outline=(255, 255, 255, 130), width=3)
        draw.rounded_rectangle((310, 110, 410, 190), radius=22, outline=white, width=5)
        draw.rounded_rectangle((310, 490, 410, 570), radius=22, outline=white, width=5)
        draw.line([(360, 340), (360, 290)], fill=white, width=5)
        draw.line([(360, 340), (400, 365)], fill=white, width=5)
    elif kind == "washer":
        draw.rounded_rectangle((220, 150, 500, 560), radius=26, outline=white, width=7)
        draw.ellipse((275, 285, 445, 455), outline=white, width=7)
        draw.ellipse((310, 320, 410, 420), outline=(255, 255, 255, 130), width=3)
        draw.line([(260, 220), (460, 220)], fill=white, width=4)
        draw.ellipse((270, 195, 300, 225), outline=white, width=3)
    elif kind == "dryer":
        draw.ellipse((225, 230, 405, 410), outline=white, width=8)
        draw.ellipse((275, 280, 355, 360), outline=(255, 255, 255, 130), width=4)
        draw.rounded_rectangle((330, 380, 430, 555), radius=34, outline=white, width=7)
        draw.line([(380, 400), (380, 520)], fill=(255, 255, 255, 120), width=3)
    elif kind == "box":
        draw.rounded_rectangle((190, 300, 530, 520), radius=20, outline=white, width=7)
        draw.line([(190, 360), (530, 360)], fill=white, width=5)
        draw.line([(360, 300), (360, 520)], fill=white, width=5)
        draw.rounded_rectangle((300, 390, 420, 420), radius=12, outline=white, width=4)
    else:
        draw.ellipse((220, 220, 500, 500), outline=white, width=8)


def build_one(slug, brand, model, category, top, bottom, kind) -> None:
    size = 720
    image = gradient(size, top, bottom)
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Soft glow and grid.
    draw.ellipse((-120, -120, 460, 460), fill=(255, 255, 255, 18))
    draw.ellipse((420, 360, 900, 840), fill=(255, 255, 255, 12))
    for x in range(0, size, 60):
        draw.line([(x, 0), (x, size)], fill=(255, 255, 255, 12), width=1)
    for y in range(0, size, 60):
        draw.line([(0, y), (size, y)], fill=(255, 255, 255, 12), width=1)

    white = (255, 252, 244, 235)
    draw_device(draw, kind, white)

    # Type.
    draw.text((48, 44), brand, font=font(46, True), fill=white)
    draw.text((48, 104), model, font=font(26), fill=(255, 255, 255, 175))
    tag_font = font(22, True)
    tag_text = category
    box = draw.textbbox((0, 0), tag_text, font=tag_font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.rounded_rectangle((48, 622, 48 + tw + 40, 622 + th + 22), radius=18, fill=(255, 255, 255, 32))
    draw.text((68, 630), tag_text, font=tag_font, fill=white)
    draw.text((584, 638), "DEMO", font=font(18, True), fill=(255, 255, 255, 120))

    composed = Image.alpha_composite(image, overlay).convert("RGB")
    composed.save(OUT / f"{slug}.png", optimize=True)


def main() -> None:
    for item in PRODUCTS:
        build_one(*item)
    print(f"wrote {len(PRODUCTS)} images to {OUT}")


if __name__ == "__main__":
    main()
