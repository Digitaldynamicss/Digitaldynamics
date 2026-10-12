"""The three scenes, transitions and the caption layer.

Every scene is a pure function of time: `Reel.frame(t)` returns the RGBA
frame for any t in [0, duration), so single frames can be previewed without
rendering the whole reel (see `render.py --still`)."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gfx
from gfx import (W, H, SS, rgb, prog, clamp, lerp, ease_out_cubic, ease_out_back,
                 ease_in_out_cubic, ease_in_cubic, text, pill, place, hstack, emoji)

CAPTION_Y = 1440      # caption pill centre; everything critical sits above y≈1500
BRAND_Y = 196         # just below the Reels top UI


class Reel:
    def __init__(self, cfg):
        self.cfg = cfg
        self.c = cfg["colors"]
        self.txt = cfg["text"]
        self.brand = cfg["brand"]
        sc = cfg["scenes"]
        self.t_models = sc["models"]["start"]
        self.t_cta = sc["cta"]["start"]
        self.t_end = sc["cta"]["endcard_at"]
        self.photos_used = {}
        self._build_static()
        self._build_captions()

    # ================================================================ static layers
    def _build_static(self):
        c = self.c
        # --- scene 1: showroom gate at night
        photo = gfx.load_asset("showroom.jpg", "showroom.png")
        self.photos_used["showroom"] = photo is not None
        if photo is not None:
            bg = gfx.cover(photo, W, H)
            shade = gfx.vgradient(W, H, [(0, "#000000"), (0.45, "#000000"), (1, "#000000")])
            arr = np.asarray(bg).astype(float)[..., :3] * 0.45 + shade * 0.0
            self.bg_hook = gfx.np_to_img(arr * gfx.vignette(W, H, 0.6))
        else:
            arr = gfx.vgradient(W, H, [(0, "#040405"), (0.40, "#0B0C0F"), (0.66, "#15161A"),
                                      (0.67, "#1C1D22"), (1, "#060607")])
            gx0, gx1, gy0, gy1 = 290, 790, 740, 1300
            gate = np.zeros_like(arr)
            gate[gy0:gy1, gx0:gx1] = gfx.vgradient(gx1 - gx0, gy1 - gy0, [(0, "#3A3430"), (0.55, "#A88E78"), (1, "#E8D2BC")])
            arr = arr + gate
            arr += gfx.radial(W, H, 540, 1180, 520, 360, "#FFE7CC", 0.55, 1.6)
            arr += gfx.radial(W, H, 540, 1300, 900, 260, "#FFD8B0", 0.35, 1.5)      # light spill on floor
            arr += gfx.radial(W, H, 0, 900, 520, 900, c["red"], 0.35, 2.0)
            arr += gfx.radial(W, H, W, 900, 520, 900, c["red"], 0.35, 2.0)
            for x in (gx0 - 14, gx1 + 14):                                          # red LED pillars
                arr += gfx.radial(W, H, x, (gy0 + gy1) / 2, 26, 420, c["red"], 1.4, 1.2)
            arr += gfx.radial(W, H, 540, gy0 - 14, 300, 18, c["red"], 1.4, 1.2)
            # floor perspective lines
            img = gfx.np_to_img(arr * gfx.vignette(W, H, 0.5) + gfx.noise_grain(W, H, 4))
            d = ImageDraw.Draw(img)
            for k in range(-8, 9):
                d.line((540 + k * 40, 1300, 540 + k * 260, H), fill=(255, 255, 255, 14), width=2)
            self.bg_hook = img
        self.headlight = gfx.glow_dot(150, "#FFF6E8", 0.95)
        self.streak = Image.new("RGBA", (900, 6), (255, 255, 255, 0))
        ImageDraw.Draw(self.streak).rectangle((0, 1, 900, 4), fill=(255, 245, 230, 150))
        self.streak = self.streak.filter(ImageFilter.GaussianBlur(1.5))

        # --- scene 2: warm "home" and urban "style" environments
        arr = gfx.vgradient(W, H, [(0, "#0C0605"), (0.45, "#2A0F0B"), (0.62, "#6B2A12"), (0.63, "#1A0D09"), (1, "#070404")])
        arr += gfx.radial(W, H, 300, 1190, 700, 260, "#F09A45", 0.55, 1.6)
        for k, (x, y, r) in enumerate([(120, 640, 70), (420, 560, 46), (840, 700, 90), (640, 880, 38), (220, 980, 54), (960, 1000, 40)]):
            arr += gfx.radial(W, H, x, y, r, r, "#FFB060", 0.22, 1.1)
        home = gfx.np_to_img(arr * gfx.vignette(W, H, 0.55) + gfx.noise_grain(W, H, 4, 2))
        d = ImageDraw.Draw(home)
        roof = [(0, 1210), (0, 1120), (90, 1060), (180, 1120), (180, 1090), (300, 1010), (420, 1090), (420, 1130),
                (520, 1130), (520, 1070), (640, 1070), (700, 1030), (760, 1070), (760, 1120), (900, 1040), (1080, 1140), (1080, 1210)]
        d.polygon(roof, fill=(14, 8, 6, 255))
        for x, y in [(60, 1140), (110, 1140), (250, 1080), (320, 1080), (560, 1095), (600, 1095), (840, 1110), (950, 1120)]:
            d.rectangle((x, y, x + 26, y + 30), fill=(255, 190, 110, 200))
        self.bg_home = home

        arr = gfx.vgradient(W, H, [(0, "#040508"), (0.5, "#0B0E14"), (0.62, "#161A22"), (0.63, "#0B0C10"), (1, "#030304")])
        arr += gfx.radial(W, H, 800, 1190, 700, 220, c["red"], 0.55, 1.6)
        arr += gfx.radial(W, H, 980, 500, 400, 700, "#2A3A5A", 0.5, 2.0)
        city = gfx.np_to_img(arr * gfx.vignette(W, H, 0.5) + gfx.noise_grain(W, H, 4, 3))
        d = ImageDraw.Draw(city)
        rng = np.random.default_rng(7)
        x = 0
        while x < W:
            bw = int(rng.integers(60, 130)); bh = int(rng.integers(160, 520))
            d.rectangle((x, 1210 - bh, x + bw, 1210), fill=(9, 10, 14, 255))
            for wy in range(1210 - bh + 20, 1190, 34):
                for wx in range(x + 12, x + bw - 14, 26):
                    if rng.random() < 0.28:
                        col = (255, 70, 70, 170) if rng.random() < 0.25 else (200, 215, 255, 110)
                        d.rectangle((wx, wy, wx + 10, wy + 14), fill=col)
            x += bw + int(rng.integers(4, 14))
        streaks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(streaks)
        for k in range(7):
            y0 = 380 + k * 95
            sd.line((W, y0, 0, y0 + 260), fill=(215, 20, 26, 120 - k * 12), width=4)
        city.alpha_composite(streaks.filter(ImageFilter.GaussianBlur(2)))
        city.alpha_composite(streaks)
        self.bg_city = city

        # --- scene 3: gift burst + end card
        arr = gfx.vgradient(W, H, [(0, "#120203"), (0.5, "#3A0507"), (1, "#0A0102")])
        arr += gfx.radial(W, H, 540, 980, 700, 700, c["red"], 0.8, 1.4)
        self.bg_gift = gfx.np_to_img(arr * gfx.vignette(W, H, 0.5) + gfx.noise_grain(W, H, 4, 4))
        gp = gfx.load_asset("gift_handover.jpg", "gift_handover.png")
        self.photos_used["gift_handover"] = gp is not None
        if gp is not None:
            g = np.asarray(gfx.cover(gp, W, H)).astype(float)[..., :3]
            shade = gfx.vgradient(W, H, [(0, "#000000"), (1, "#000000")])
            self.bg_gift = gfx.np_to_img(g * 0.55 * gfx.vignette(W, H, 0.6))
        rays = Image.new("RGBA", (2400, 2400), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rays)
        for k in range(14):
            a0 = k * math.tau / 14
            pts = [(1200, 1200), (1200 + 1700 * math.cos(a0 - 0.07), 1200 + 1700 * math.sin(a0 - 0.07)),
                   (1200 + 1700 * math.cos(a0 + 0.07), 1200 + 1700 * math.sin(a0 + 0.07))]
            rd.polygon(pts, fill=(255, 220, 200, 22))
        self.rays = rays.filter(ImageFilter.GaussianBlur(6))
        self.gift_box = self._draw_gift()

        if photo is not None:
            ec = np.asarray(gfx.cover(photo, W, H).filter(ImageFilter.GaussianBlur(6))).astype(float)[..., :3] * 0.32
        else:
            ec = gfx.vgradient(W, H, [(0, "#0A0A0C"), (0.55, "#141418"), (1, "#050506")])
            # abstract showroom facade: glass front glowing behind the content
            fac = np.zeros_like(ec)
            fac[300:1060, 110:970] = gfx.vgradient(860, 760, [(0, "#2A2420"), (1, "#5A4636")]) * 0.5
            fac_img = gfx.np_to_img(fac).filter(ImageFilter.GaussianBlur(40))
            ec = ec + np.asarray(fac_img).astype(float)[..., :3]
            ec += gfx.radial(W, H, 540, 260, 520, 60, c["red"], 0.9, 1.3)
        ec += gfx.radial(W, H, 540, 640, 620, 260, c["whatsapp"], 0.16, 1.6)
        end = gfx.np_to_img(ec * gfx.vignette(W, H, 0.45) + gfx.noise_grain(W, H, 3, 5))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shade.putalpha(gfx.linear_alpha_mask(W, H, 0.25, 0.75))
        end.alpha_composite(shade)
        self.bg_end = end

        # bikes (supplied photos are the source of truth when present)
        shine, used = gfx.bike_photo_or_drawing(["shine_dlx.png", "shine_dlx.jpg"], "commuter")
        self.photos_used["shine_dlx"] = used
        hornet, used = gfx.bike_photo_or_drawing(["cb125_hornet.png", "cb125_hornet.jpg"], "naked")
        self.photos_used["cb125_hornet"] = used
        self.shine_static, self.hornet_static = shine, hornet.transpose(Image.FLIP_LEFT_RIGHT)
        hero = gfx.load_asset("hero_bike.png", "hero_bike.jpg")
        self.photos_used["hero_bike"] = hero is not None
        self.hero_photo = gfx.contain(hero, gfx.BIKE_W, gfx.BIKE_H) if hero is not None else None
        self.shadow = gfx.ground_shadow(1000, 120)

        logo = gfx.load_asset("logo.png")
        self.photos_used["logo"] = logo is not None
        if logo is not None:
            self.brand_bug = gfx.contain(logo, 360, 90)
        else:
            mark = Image.new("RGBA", (22, 22), rgb(c["red"]))
            self.brand_bug = hstack([mark, text(f'{self.brand["dealer"]}  ·  {self.brand["city"]}', "bold", 28, "#FFFFFF", 5, 0.6)], 14)

    def _draw_gift(self):
        c = self.c
        w, h = 520, 520
        im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        s = SS
        d.rounded_rectangle((60 * s, 210 * s, 460 * s, 500 * s), 18 * s, fill=rgb(c["red"]))           # box
        d.rectangle((60 * s, 210 * s, 160 * s, 500 * s), fill=rgb("#B00F15"))                          # shading
        d.rounded_rectangle((35 * s, 160 * s, 485 * s, 240 * s), 16 * s, fill=rgb("#E8242A"))         # lid
        d.rectangle((225 * s, 160 * s, 295 * s, 500 * s), fill=rgb("#FFFFFF"))                        # ribbon
        d.rectangle((225 * s, 240 * s, 295 * s, 256 * s), fill=rgb("#D9D9DE"))
        for sign in (-1, 1):                                                                          # bow loops
            d.ellipse(((260 + sign * 95 - 85) * s, 70 * s, (260 + sign * 95 + 85) * s, 175 * s), fill=rgb("#FFFFFF"))
            d.ellipse(((260 + sign * 95 - 45) * s, 100 * s, (260 + sign * 95 + 45) * s, 150 * s), fill=rgb("#B00F15"))
        d.ellipse((228 * s, 120 * s, 292 * s, 175 * s), fill=rgb("#F2F2F5"))
        im = im.resize((w, h), Image.LANCZOS)
        glow = gfx.glow_dot(330, "#FF6A50", 0.55)
        out = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
        out.alpha_composite(glow, (20, 20))
        out.alpha_composite(im, (90, 90))
        return out

    # ================================================================ captions
    def _build_captions(self):
        self.captions = []
        for vo in self.cfg["voiceover"]:
            parts = vo["subtitle"]
            weights = [len(p) for p in parts]
            total, t0 = sum(weights), vo["start"]
            span = vo["end"] - vo["start"]
            for p, wgt in zip(parts, weights):
                t1 = t0 + span * wgt / total
                self.captions.append((t0, t1, p))
                t0 = t1

    def caption_img(self, s):
        key = ("cap", s)
        if key not in _cache:
            line = text(s, "semi", 44, "#FFFFFF", 0, 0.0, max_w=900)
            _cache[key] = pill(line, (0, 0, 0, 165), 30, 16, 22)
        return _cache[key]

    def draw_captions(self, canvas, t):
        for t0, t1, s in self.captions:
            if t0 - 0.02 <= t < t1:
                a = min(prog(t, t0 - 0.02, 0.08), 1 - prog(t, t1 - 0.06, 0.06)) if t1 - t0 > 0.2 else 1
                y = CAPTION_Y + 10 * (1 - ease_out_cubic(prog(t, t0 - 0.02, 0.12)))
                place(canvas, self.caption_img(s), W / 2, y, 1, max(a, 0.0))

    # ================================================================ scene 1: price hook (0-3s)
    def scene_hook(self, t):
        T = self.txt["hook"]
        canvas = gfx.zoom(self.bg_hook, 1.0 + 0.07 * ease_in_out_cubic(prog(t, 0, 3.0)), 0.5, 0.65).copy()

        # bike rolls out of the lit gate towards camera
        p = ease_out_cubic(prog(t, 0.0, 1.9))
        x = lerp(300, 540, p)
        s = lerp(0.50, 0.95, p)
        ground = lerp(1300, 1372, p)
        cy = ground - (575 - 300) * s
        dist = (x - 300) + (s - 0.5) * 900
        angle = math.degrees(dist / (gfx.R_WHEEL * s))
        b = self.hero_photo if self.hero_photo is not None else gfx.bike("commuter", angle)
        speed = 1 - p
        place(canvas, self.shadow, x, ground, s * 1.05, 0.9)
        place(canvas, gfx.reflection(b, 0.22), x, ground + (600 - 575) * s + 300 * s - 6, s, 1)
        if speed > 0.08:   # motion trail
            for k in (3, 2, 1):
                place(canvas, b, x - k * 26 * speed * 2.2, cy, s, 0.10 * k * speed)
            for k, yy in enumerate((cy - 60 * s, cy + 20 * s, cy + 110 * s)):
                place(canvas, self.streak, x - 520 * s - 80 * k, yy, s, 0.7 * speed)
        place(canvas, b, x, cy, s, 1)
        if self.hero_photo is None:  # headlight bloom
            hx, hy = x + (765 - 500) * s, cy + (205 - 300) * s
            place(canvas, self.headlight, hx, hy, s * 1.1, 0.9)

        self.draw_brand(canvas, t, 0.0)
        # headline stack
        a = ease_out_cubic(prog(t, 0.08, 0.25))
        place(canvas, text(T["pre"], "xbold", 76, "#FFFFFF", 6, 0.6), W / 2, 330 + 40 * (1 - a), 1, a)

        price = text(T["price"], "display", 300, "#FFFFFF", 0, 0.5, max_w=840)
        slab_p = ease_out_cubic(prog(t, 0.16, 0.28))
        if slab_p > 0:
            sw, sh = price.width + 70, int(price.height * 0.86)
            slab = _skew_slab(int(sw * slab_p) + 1, sh, self.c["red"])
            place(canvas, slab, W / 2 - sw / 2 + slab.width / 2, 528, 1, 1)
        pp = prog(t, 0.22, 0.42)
        if pp > 0:
            sc = lerp(0.55, 1.0, ease_out_back(pp, 2.2))
            pr = _shine(price, prog(t, 1.25, 0.55))
            place(canvas, pr, W / 2, 522, sc, min(1, pp * 3))

        a = ease_out_cubic(prog(t, 0.55, 0.3))
        place(canvas, text(T["line1"], "xbold", 80, "#FFFFFF", 2, 0.7, max_w=960), W / 2 - 60 * (1 - a), 735, 1, a)
        a = prog(t, 0.75, 0.35)
        place(canvas, text(T["line2"], "black", 124, "#FFFFFF", 0, 0.7, max_w=960), W / 2, 862, lerp(1.25, 1, ease_out_cubic(a)), min(1, a * 2.5))
        return canvas

    # ================================================================ scene 2: model discounts (3-10s)
    def column(self, which, lt, t_in):
        """One model column (≈540px wide) as a layer; lt is scene-local time, t_in its entrance."""
        T = self.txt[which]
        layer = Image.new("RGBA", (620, 1340), (0, 0, 0, 0))
        cx = 310
        def at(off):
            return lt - t_in - off
        a = ease_out_cubic(clamp(at(0.05) / 0.25))
        tag = pill(text(T["tag"], "bold", 32, "#111111", 4), "#FFFFFF", 26, 12)
        place(layer, tag, cx, 70 + 20 * (1 - a), 1, a)
        a = ease_out_cubic(clamp(at(0.12) / 0.25))
        place(layer, text(T["make"], "xbold", 46, "#C9CCD2", 12, 0.5), cx, 160 + 20 * (1 - a), 1, a)
        for i, line in enumerate(T["model"]):
            a = ease_out_cubic(clamp(at(0.18 + i * 0.08) / 0.28))
            place(layer, text(line, "black", 100, "#FFFFFF", 0, 0.6, max_w=560), cx - 50 * (1 - a), 245 + i * 104, 1, a)
        # bike slides in with spinning wheels
        bp = ease_out_cubic(clamp(at(0.1) / 0.6))
        dirn = 1 if which == "shine" else -1
        if which == "shine":
            base = self.shine_static if self.photos_used["shine_dlx"] else gfx.bike("commuter", (1 - bp) * -420)
        else:
            base = self.hornet_static if self.photos_used["cb125_hornet"] else gfx.bike("naked", (1 - bp) * -420).transpose(Image.FLIP_LEFT_RIGHT)
        bs = 0.56
        bx = cx - dirn * 260 * (1 - bp)
        ground = 840
        place(layer, self.shadow, bx, ground, bs * 1.05, 0.85 * bp)
        place(layer, base, bx, ground - 275 * bs, bs, bp)
        # discount: the hero of the column
        pp = clamp(at(0.85) / 0.4)
        if pp > 0:
            amt = text(T["amount"], "display", 150, "#FFFFFF", 0, 0.6, max_w=455)
            place(layer, amt, cx, 975, lerp(0.5, 1, ease_out_back(pp, 2.4)), min(1, pp * 3))
            sp = ease_out_cubic(clamp(at(1.0) / 0.3))
            suf = pill(text(T["suffix"], "black", 56, "#FFFFFF", 2), self.c["red"], 30, 14, 12)
            place(layer, suf, cx, 1110 + 30 * (1 - sp), 1, sp)
        return layer

    def scene_models(self, t):
        lt = t - self.t_models
        split = ease_in_out_cubic(prog(lt, 3.25, 0.55))
        canvas = gfx.zoom(self.bg_home, 1.04 + 0.04 * prog(lt, 0, 7), 0.3, 0.6).copy()
        if split > 0:
            city = gfx.zoom(self.bg_city, 1.08 - 0.04 * prog(lt, 3.2, 3.8), 0.7, 0.6)
            div = lerp(W + 140, 540, split)          # divider x at mid-height
            mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mask).polygon([(div + 60, 0), (W, 0), (W, H), (div - 60, H)], fill=255)
            canvas.paste(city, (0, 0), mask)
        # entrance from the red wipe: Shine column content
        shine_x = lerp(540, 270, split)
        shine_s = lerp(1.0, 0.92, split)
        col = self.column("shine", lt, 0.05)
        dim = 0.32 * (ease_out_cubic(prog(lt, 3.6, 0.4)) - ease_out_cubic(prog(lt, 5.4, 0.4)))
        place(canvas, col, shine_x, 230 + 670 * shine_s, shine_s, 1 - dim)
        if split > 0:
            hcol = self.column("hornet", lt, 3.45)
            place(canvas, hcol, lerp(W + 330, 810, split), 230 + 670 * 0.92, 0.92, 1)
            div = lerp(W + 140, 540, split)
            line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(line).line((div + 60, 0, div - 60, H), fill=rgb(self.c["red"]), width=8)
            canvas.alpha_composite(line.filter(ImageFilter.GaussianBlur(10)))
            canvas.alpha_composite(line)
        self.draw_brand(canvas, t, 0.0)
        return canvas

    # ================================================================ scene 3: gift + CTA (10-15s)
    def scene_cta(self, t):
        lt = t - self.t_cta
        end_lt = t - self.t_end
        if end_lt < 0.32:
            canvas = self.gift_frame(lt)
            if end_lt > 0:
                e = ease_out_cubic(prog(end_lt, 0, 0.32))
                card = self.end_card(end_lt)
                place(canvas, card, W / 2, H / 2 + H * (1 - e), 1, 1)
            return canvas
        return self.end_card(end_lt)

    def gift_frame(self, lt):
        canvas = self.bg_gift.copy()
        place(canvas, self.rays, W / 2, 1000, 1, 0.9 * ease_out_cubic(prog(lt, 0, 0.4)), rot=lt * 14)
        p = prog(lt, 0.0, 0.5)
        if p > 0:
            s = lerp(0.3, 1.0, ease_out_back(p, 2.0)) * (1 + 0.015 * math.sin(lt * 7))
            place(canvas, self.gift_box, W / 2, 1010 + 6 * math.sin(lt * 5), s, min(1, p * 3))
        for k, (gx, gy, ph) in enumerate([(300, 820, 0.2), (800, 760, 0.45), (760, 1240, 0.7), (280, 1180, 0.9)]):
            tw = clamp(math.sin((lt - ph) * 6) * 1.2)
            if lt > ph:
                place(canvas, _sparkle(), gx, gy, 0.6 + 0.4 * tw, tw)
        a = prog(lt, 0.03, 0.35)
        place(canvas, text("ASSURED", "black", 136, "#FFFFFF", 4, 0.6), W / 2, 420, lerp(1.3, 1, ease_out_cubic(a)), min(1, a * 2.5))
        a = prog(lt, 0.15, 0.4)
        words = self.txt["gift"].split(" ", 1)[-1]
        gift = hstack([text(words, "black", 180, "#FFFFFF", 4, 0.6), emoji("🎁", 150)], 26)
        place(canvas, gift, W / 2, 590, lerp(0.6, 1, ease_out_back(a, 2.0)), min(1, a * 3))
        return canvas

    def end_card(self, lt):
        c = self.c
        canvas = gfx.zoom(self.bg_end, 1.06 - 0.06 * ease_out_cubic(prog(lt, 0, 3.8))).copy()
        # assured gift reminder
        a = ease_out_cubic(prog(lt, 0.0, 0.3))
        badge = pill(hstack([emoji("🎁", 46), text(self.txt["gift"], "black", 46, "#FFFFFF", 3)], 14), c["red"], 30, 14)
        place(canvas, badge, W / 2, 280 - 30 * (1 - a), 1, a)
        # CTA pill (WhatsApp-style green)
        a = ease_out_cubic(prog(lt, 0.04, 0.3))
        cta = pill(hstack([emoji("📞", 50), text(self.txt["cta"], "black", 52, "#06210F", 1)], 16), c["whatsapp"], 38, 20)
        place(canvas, cta, W / 2 - 80 * (1 - a), 450, 1, a)
        # the phone number: largest element on the card
        pp = prog(lt, 0.08, 0.4)
        if pp > 0:
            num = text(self.brand["phone"], "display", 200, "#FFFFFF", 4, 0.7, max_w=940)
            pulse = 1 + 0.022 * max(0.0, math.sin((lt - 0.6) * math.tau / 1.0)) if lt > 0.6 else 1
            place(canvas, num, W / 2, 640, lerp(0.5, 1, ease_out_back(pp, 2.0)) * pulse, min(1, pp * 3))
            bar_w = int(num.width * 0.8 * ease_out_cubic(prog(lt, 0.35, 0.4)))
            if bar_w > 2:
                bar = Image.new("RGBA", (bar_w, 10), rgb(c["whatsapp"]))
                place(canvas, bar, W / 2, 760, 1, 1)
        a = ease_out_cubic(prog(lt, 0.22, 0.35))
        place(canvas, text(self.brand["dealer"], "black", 96, "#FFFFFF", 2, 0.6, max_w=980), W / 2, 870 + 30 * (1 - a), 1, a)
        place(canvas, text(self.brand["city"], "xbold", 50, c["red"], 20, 0.6), W / 2, 960 + 30 * (1 - a), 1, a)
        # both bikes as a quiet recap
        bp = ease_out_cubic(prog(lt, 0.35, 0.5))
        for img, x in ((self.shine_static, 300), (self.hornet_static, 780)):
            place(canvas, self.shadow, x, 1240, 0.42, 0.8 * bp)
            place(canvas, img, x + (1 if x > 540 else -1) * 120 * (1 - bp), 1240 - 275 * 0.40, 0.40, bp)
        a = ease_out_cubic(prog(lt, 0.4, 0.3))
        place(canvas, text(self.txt["tnc"], "bold", 32, "#E6E6EA", 3), W / 2, 1300, 1, a)
        place(canvas, text(self.txt["finance"], "medium", 30, "#C9CBD1", 0), W / 2, 1345, 1, a)
        return canvas

    # ================================================================ chrome + transitions
    def draw_brand(self, canvas, t, start):
        place(canvas, self.brand_bug, W / 2, BRAND_Y, 1, 0.92 * ease_out_cubic(prog(t, start, 0.3)))

    def frame(self, t):
        if t < self.t_models:
            canvas = self.scene_hook(t)
        elif t < self.t_cta:
            canvas = self.scene_models(t)
        else:
            canvas = self.scene_cta(t)

        # red skewed wipe hook -> models
        tw = t - self.t_models
        if -0.3 < tw < 0.3:
            y = lerp(H + 1400, -1400, (tw + 0.3) / 0.6)
            place(canvas, _wipe_band(self.c), W / 2, y, 1, 1)
        # flash/zoom models -> gift
        tf = t - self.t_cta
        if -0.22 < tf < 0.25:
            a = 1 - abs(tf) / (0.22 if tf < 0 else 0.25)
            canvas = gfx.zoom(canvas, 1 + 0.12 * a * (1 if tf < 0 else 0.6))
            ov = Image.new("RGBA", (W, H), rgb(self.c["red"], int(235 * ease_in_cubic(a))))
            canvas = canvas.copy()
            canvas.alpha_composite(ov)
        self.draw_captions(canvas, t)
        return canvas


# ---------------------------------------------------------------- small cached helpers
_cache = {}


def _skew_slab(w, h, color):
    key = ("slab", w, h, color)
    if key not in _cache:
        k = int(h * 0.22)
        im = Image.new("RGBA", ((w + k) * SS, h * SS), (0, 0, 0, 0))
        ImageDraw.Draw(im).polygon([(k * SS, 0), ((w + k) * SS, 0), (w * SS, h * SS), (0, h * SS)], fill=rgb(color))
        _cache[key] = im.resize((w + k, h), Image.LANCZOS)
    return _cache[key]


def _shine(img, p):
    """Diagonal light sweep across an image's opaque pixels (p: 0..1)."""
    if p <= 0 or p >= 1:
        return img
    w, h = img.size
    xs = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.35
    centre = lerp(-0.3 * w, 1.4 * w, p)
    band = np.clip(1 - np.abs(xs - centre) / (w * 0.08), 0, 1) * 0.85
    arr = np.asarray(img).astype(float)
    a = arr[..., 3] / 255
    arr[..., :3] = arr[..., :3] * (1 - band[..., None] * a[..., None]) + 255 * band[..., None] * a[..., None] * 0.0 + \
        np.array([255, 225, 215]) * band[..., None] * a[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def _sparkle():
    if "sparkle" not in _cache:
        n = 60
        im = Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = n * SS / 2
        d.polygon([(c, 0), (c + 5 * SS, c - 5 * SS), (n * SS, c), (c + 5 * SS, c + 5 * SS), (c, n * SS),
                   (c - 5 * SS, c + 5 * SS), (0, c), (c - 5 * SS, c - 5 * SS)], fill=(255, 245, 235, 255))
        _cache["sparkle"] = im.resize((n, n), Image.LANCZOS)
    return _cache["sparkle"]


def _wipe_band(c):
    if "wipe" not in _cache:
        h = 2400
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(0, 300), (W, 0), (W, h - 300), (0, h)], fill=rgb(c["red"]))
        d.polygon([(0, 300), (W, 0), (W, 40), (0, 340)], fill=rgb("#FFFFFF", 200))
        d.polygon([(0, h - 40), (W, h - 340), (W, h - 300), (0, h)], fill=rgb(c["black"]))
        _cache["wipe"] = im
    return _cache["wipe"]
