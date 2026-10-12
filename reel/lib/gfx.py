"""Drawing primitives shared by every scene: fonts, cached text, easing,
compositing, gradients/glows and the stylised motorcycle illustrations."""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2  # supersampling factor for vector-style drawings

FONT_DIR = "/usr/share/fonts/opentype/inter"
FONTS = {
    "black": f"{FONT_DIR}/Inter-Black.otf",
    "xbold": f"{FONT_DIR}/Inter-ExtraBold.otf",
    "bold": f"{FONT_DIR}/Inter-Bold.otf",
    "semi": f"{FONT_DIR}/Inter-SemiBold.otf",
    "medium": f"{FONT_DIR}/Inter-Medium.otf",
    "display": f"{FONT_DIR}/InterDisplay-Black.otf",
}
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


# ---------------------------------------------------------------- colours

def rgb(hex_color, a=255):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---------------------------------------------------------------- easing

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def prog(t, start, dur):
    """0..1 progress of a tween that starts at `start` and lasts `dur`."""
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_out_cubic(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_in_cubic(x):
    return x ** 3


def ease_out_back(x, s=1.70158):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def lerp(a, b, x):
    return a + (b - a) * x


# ---------------------------------------------------------------- assets

def load_asset(*names):
    """Return the first supplied asset found in reel/assets/, or None."""
    for n in names:
        p = os.path.join(ASSET_DIR, n)
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
    return None


def cover(img, w, h):
    """Scale+crop an image to fully cover w x h."""
    s = max(w / img.width, h / img.height)
    im = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def contain(img, w, h):
    s = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


# ---------------------------------------------------------------- text

@lru_cache(maxsize=None)
def font(kind, size):
    return ImageFont.truetype(FONTS[kind], size)


@lru_cache(maxsize=None)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)


@lru_cache(maxsize=None)
def text(s, kind, size, color="#FFFFFF", tracking=0, shadow=0.0, max_w=None):
    """Render a single line of text to a tight RGBA image (cached).
    `tracking` is extra letter-spacing in px; `shadow` is drop-shadow opacity.
    `max_w` shrinks the font until the line fits."""
    if max_w:
        while size > 10:
            probe = text(s, kind, size, color, tracking, 0.0)
            if probe.width <= max_w:
                break
            size -= 2
    f = font(kind, size)
    pad = int(size * 0.35) + 8
    widths = [f.getlength(c) for c in s]
    tw = int(sum(widths) + tracking * max(0, len(s) - 1))
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, cw in zip(s, widths):
            d.text((x, pad), c, font=f, fill=rgb(color))
            x += cw + tracking
    else:
        d.text((pad, pad), s, font=f, fill=rgb(color))
    if shadow > 0:
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(size * 0.08))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * shadow)))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        base.alpha_composite(sh, (0, int(size * 0.04)))
        base.alpha_composite(im)
        im = base
    bb = im.getchannel("A").getbbox()
    m = 6
    return im.crop((max(0, bb[0] - m), max(0, bb[1] - m), min(im.width, bb[2] + m), min(im.height, bb[3] + m)))


def hstack(imgs, gap=0, valign="center"):
    w = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    h = max(i.height for i in imgs)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i in imgs:
        y = (h - i.height) // 2 if valign == "center" else h - i.height
        out.alpha_composite(i, (x, y))
        x += i.width + gap
    return out


def pill(content, fill, pad_x=34, pad_y=18, radius=None, outline=None):
    """Put an RGBA image inside a rounded rectangle."""
    w, h = content.width + pad_x * 2, content.height + pad_y * 2
    r = radius if radius is not None else h // 2
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=rgb(fill) if isinstance(fill, str) else fill,
                                          outline=outline, width=3 * SS if outline else 0)
    out = big.resize((w, h), Image.LANCZOS)
    out.alpha_composite(content, (pad_x, pad_y))
    return out


# ---------------------------------------------------------------- compositing

def place(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Composite `img` centred at (cx, cy) with scale/opacity/rotation."""
    if img is None or alpha <= 0.003 or scale <= 0.01:
        return
    im = img
    if abs(scale - 1.0) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    # alpha_composite needs the source fully inside: crop if necessary
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, im.width, im.height):
        im = im.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(im, (x + sx0, y + sy0))


def with_alpha(img, alpha):
    im = img.copy()
    im.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    return im


def zoom(img, s, ox=0.5, oy=0.5):
    """Scale a full frame about an origin (fractions) and crop back to size."""
    if abs(s - 1) < 1e-4:
        return img
    w, h = img.size
    big = img.resize((int(w * s), int(h * s)), Image.BICUBIC)
    x = int((big.width - w) * ox)
    y = int((big.height - h) * oy)
    return big.crop((x, y, x + w, y + h))


# ---------------------------------------------------------------- backgrounds

def np_to_img(arr):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])
    return Image.fromarray(arr, "RGBA")


def vgradient(w, h, stops):
    """stops: [(pos 0..1, '#hex'), ...]"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3))
    pos = [s[0] for s in stops]
    cols = np.array([rgb(s[1])[:3] for s in stops], float)
    for c in range(3):
        out[:, c] = np.interp(ys, pos, cols[:, c])
    return np.repeat(out[:, None, :], w, axis=1)


def radial(w, h, cx, cy, rx, ry, color, strength=1.0, power=2.0):
    """Additive radial glow layer as float array (h, w, 3)."""
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
    k = np.clip(1 - d, 0, 1) ** power * strength
    c = np.array(rgb(color)[:3], float)
    return k[..., None] * c


def noise_grain(w, h, amount=6, seed=1):
    rng = np.random.default_rng(seed)
    return rng.normal(0, amount, (h, w, 1))


def vignette(w, h, strength=0.55):
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - w / 2) / (w * 0.75)) ** 2 + ((ys - h / 2) / (h * 0.7)) ** 2)
    return np.clip(1 - strength * d ** 2, 0, 1)[..., None]


def glow_dot(radius, color, strength=1.0):
    size = radius * 2
    arr = radial(size, size, radius, radius, radius, radius, color, strength, 2.2)
    a = np.clip(arr.max(axis=2), 0, 255)
    img = np.dstack([np.full((size, size), c) for c in rgb(color)[:3]] + [a])
    return Image.fromarray(img.astype(np.uint8), "RGBA")


def linear_alpha_mask(w, h, top=1.0, bottom=0.0):
    a = np.linspace(top, bottom, h)[:, None] * np.ones((1, w))
    return Image.fromarray((a * 255).astype(np.uint8), "L")


# ---------------------------------------------------------------- motorcycles
# Stylised side-profile illustrations used until official photos are supplied.
# They are deliberately generic graphics (no logos, badges or decals) so they
# never misrepresent a specific model.

BIKE_W, BIKE_H = 1000, 600
R_WHEEL = 150
REAR, FRONT = (215, 425), (790, 425)

STYLES = {
    "commuter": dict(body="#C8102E", body_dark="#7D0A1D", trim="#1A1A1E", metal="#B8BCC4",
                     rim="#2A2B30", rim_stripe=None, spokes=5, fork="#C9CDD4"),
    "naked": dict(body="#D7141A", body_dark="#5E080B", trim="#121214", metal="#8C9099",
                  rim="#141416", rim_stripe="#D7141A", spokes=6, fork="#C8A24A"),
}


def _poly(d, pts, fill, s=SS):
    d.polygon([(x * s, y * s) for x, y in pts], fill=fill)


def _line(d, pts, fill, width, s=SS):
    d.line([(x * s, y * s) for x, y in pts], fill=fill, width=int(width * s), joint="curve")
    for x, y in (pts[0], pts[-1]):
        r = width * s / 2
        d.ellipse((x * s - r, y * s - r, x * s + r, y * s + r), fill=fill)


def _ellipse(d, cx, cy, rx, ry, fill, s=SS, outline=None, width=0):
    d.ellipse(((cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s), fill=fill, outline=outline, width=int(width * s))


@lru_cache(maxsize=None)
def wheel(style, front):
    st = STYLES[style]
    r = R_WHEEL
    size = (r * 2 + 8) * SS
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2 / SS
    _ellipse(d, c, c, r, r, rgb("#0D0D0F"))                       # tyre
    _ellipse(d, c, c, r - 6, r - 6, None, outline=rgb("#2B2C31"), width=3)  # sidewall
    _ellipse(d, c, c, r - 34, r - 34, rgb(st["rim"]))            # rim
    if st["rim_stripe"]:
        _ellipse(d, c, c, r - 38, r - 38, None, outline=rgb(st["rim_stripe"]), width=4)
    _ellipse(d, c, c, r - 46, r - 46, rgb("#08080A"))
    if front:  # brake disc
        _ellipse(d, c, c, 66, 66, rgb("#7E828A"))
        _ellipse(d, c, c, 52, 52, rgb("#08080A"))
        for k in range(10):
            a = k * math.tau / 10
            _ellipse(d, c + 59 * math.cos(a), c + 59 * math.sin(a), 3.5, 3.5, rgb("#3A3C42"))
    n = st["spokes"]
    for k in range(n):
        a = k * math.tau / n
        x1, y1 = c + 22 * math.cos(a), c + 22 * math.sin(a)
        x2, y2 = c + (r - 40) * math.cos(a), c + (r - 40) * math.sin(a)
        if style == "naked":  # split Y-spokes
            for da in (-0.09, 0.09):
                _line(d, [(x1, y1), (c + (r - 40) * math.cos(a + da), c + (r - 40) * math.sin(a + da))], rgb(st["rim"]), 7)
        else:
            _line(d, [(x1, y1), (x2, y2)], rgb(st["metal"]), 10)
    _ellipse(d, c, c, 26, 26, rgb(st["metal"]))
    _ellipse(d, c, c, 10, 10, rgb("#222222"))
    return im.resize((size // SS, size // SS), Image.LANCZOS)


@lru_cache(maxsize=None)
def bike_body(style):
    st = STYLES[style]
    im = Image.new("RGBA", (BIKE_W * SS, BIKE_H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body, dark, trim, metal = rgb(st["body"]), rgb(st["body_dark"]), rgb(st["trim"]), rgb(st["metal"])
    if style == "commuter":
        _line(d, [REAR, (455, 395)], rgb("#26272C"), 22)                         # swingarm
        _poly(d, [(250, 360), (450, 372), (452, 398), (260, 392)], rgb("#1C1D21"))  # chain guard
        _poly(d, [(390, 318), (575, 318), (600, 372), (565, 470), (420, 470), (380, 400)], rgb("#33353B"))  # engine
        for k in range(5):
            _line(d, [(430, 340 + k * 22), (560, 340 + k * 22)], rgb("#4A4D55"), 5)
        _line(d, [(260, 255), (245, 395)], rgb("#2A2B30"), 18)                     # rear shock
        _line(d, [(520, 450), (430, 470), (330, 462)], metal, 16)                  # exhaust pipe
        _poly(d, [(150, 438), (340, 446), (345, 476), (150, 476), (132, 458)], metal)  # muffler
        _poly(d, [(160, 448), (340, 454), (342, 463), (160, 462)], rgb("#E6E8EC"))
        _poly(d, [(330, 270), (470, 268), (470, 380), (360, 370)], body)            # side panel
        _poly(d, [(110, 262), (330, 248), (345, 300), (170, 300)], body)            # tail
        _poly(d, [(95, 262), (125, 258), (128, 280), (98, 284)], rgb("#FF2B2B"))   # tail lamp
        _poly(d, [(160, 236), (470, 226), (478, 262), (175, 274)], trim)           # flat long seat
        _poly(d, [(440, 210), (590, 190), (655, 238), (640, 300), (470, 300)], body)  # tank
        _poly(d, [(470, 222), (585, 205), (615, 230), (480, 244)], with_rgb(body, 1.35))
        _poly(d, [(480, 270), (630, 262), (640, 300), (470, 300)], dark)
        _line(d, [(700, 175), (790, 425)], rgb(st["fork"]), 20)                    # fork
        _line(d, [(670, 135), (705, 150), (735, 130)], rgb("#222222"), 10)            # handlebar
        _poly(d, [(690, 150), (765, 160), (790, 230), (745, 262), (700, 240)], body)  # headlamp cowl
        _ellipse(d, 765, 205, 24, 30, rgb("#F4F6FF"))
        _poly(d, [(680, 290), (770, 270), (880, 300), (900, 330), (840, 318), (760, 300)], body)  # front fender
    else:  # naked street
        _line(d, [REAR, (470, 385)], rgb("#202125"), 26)
        _poly(d, [(395, 300), (585, 305), (610, 360), (580, 470), (430, 475), (390, 395)], rgb("#2B2D33"))
        for k in range(4):
            _line(d, [(440, 330 + k * 26), (570, 330 + k * 26)], rgb("#43464E"), 6)
        _poly(d, [(430, 470), (600, 460), (610, 500), (450, 505)], rgb("#18191C"))  # underbelly exhaust
        _poly(d, [(520, 478), (610, 470), (612, 492), (522, 498)], metal)
        _line(d, [(400, 330), (600, 300)], rgb("#C8A24A"), 9)                      # frame accent
        _line(d, [(250, 245), (380, 330)], rgb("#2A2B30"), 16)                     # subframe
        _line(d, [(300, 255), (265, 395)], rgb("#C8A24A"), 14)                     # rear shock
        _poly(d, [(80, 200), (250, 230), (360, 262), (350, 290), (150, 260)], body)  # raised sharp tail
        _poly(d, [(70, 196), (110, 200), (108, 216), (75, 214)], rgb("#FF2B2B"))
        _poly(d, [(150, 214), (300, 240), (430, 250), (430, 272), (260, 266), (160, 238)], trim)  # stepped seat
        _poly(d, [(420, 215), (560, 170), (660, 200), (690, 255), (630, 320), (520, 330), (430, 285)], body)  # muscular tank
        _poly(d, [(440, 225), (555, 185), (640, 205), (560, 228)], with_rgb(body, 1.4))
        _poly(d, [(560, 250), (690, 255), (630, 330), (540, 335)], dark)            # shroud
        _poly(d, [(590, 268), (660, 272), (620, 318), (575, 316)], trim)
        _line(d, [(705, 165), (790, 425)], rgb(st["fork"]), 26)                    # USD fork
        _line(d, [(705, 165), (735, 265)], rgb("#202125"), 28)
        _line(d, [(660, 140), (700, 148), (740, 135)], rgb("#222222"), 10)
        _poly(d, [(715, 160), (775, 170), (800, 215), (770, 250), (730, 238)], trim)  # angular LED headlight
        _poly(d, [(770, 190), (795, 212), (775, 240), (760, 214)], rgb("#E9F2FF"))
        _poly(d, [(700, 300), (790, 268), (870, 285), (880, 300), (790, 296)], trim)   # short fender
    im = im.resize((BIKE_W, BIKE_H), Image.LANCZOS)
    # soft top-light: brighten upper surfaces of the body
    arr = np.asarray(im).astype(float)
    light = np.linspace(1.25, 0.85, BIKE_H)[:, None, None]
    arr[..., :3] = np.clip(arr[..., :3] * light, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def with_rgb(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (c[3],)


def bike(style, wheel_angle=0.0):
    """Full bike image (BIKE_W x BIKE_H) with wheels rotated by `wheel_angle` degrees."""
    im = Image.new("RGBA", (BIKE_W, BIKE_H), (0, 0, 0, 0))
    for centre, front in ((REAR, False), (FRONT, True)):
        wimg = wheel(style, front)
        if wheel_angle:
            wimg = wimg.rotate(-wheel_angle, Image.BICUBIC)
        im.alpha_composite(wimg, (int(centre[0] - wimg.width / 2), int(centre[1] - wimg.height / 2)))
    im.alpha_composite(bike_body(style))
    return im


def bike_photo_or_drawing(asset_names, style, wheel_angle=0.0):
    """Supplied cut-out photo if present (source of truth), else the illustration."""
    photo = load_asset(*asset_names)
    if photo is not None:
        return contain(photo, BIKE_W, BIKE_H), True
    return bike(style, wheel_angle), False


def ground_shadow(w, h, alpha=0.75):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((w * 0.08, h * 0.25, w * 0.92, h * 0.75), fill=(0, 0, 0, int(255 * alpha)))
    return im.filter(ImageFilter.GaussianBlur(h * 0.18))


def reflection(img, strength=0.28):
    ref = img.transpose(Image.FLIP_TOP_BOTTOM)
    mask = linear_alpha_mask(ref.width, ref.height, strength, 0.0)
    a = np.asarray(ref.getchannel("A")).astype(float) * (np.asarray(mask).astype(float) / 255)
    ref = ref.copy()
    ref.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return ref.filter(ImageFilter.GaussianBlur(2))
