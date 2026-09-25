from __future__ import annotations

from typing import Any
import math

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1350
MARGIN = 64


def _text(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _rgb(v, fallback=(40, 40, 40)):
    if isinstance(v, (list, tuple)) and len(v) >= 3:
        try:
            return tuple(max(0, min(255, int(x))) for x in v[:3])
        except Exception:
            return fallback
    s = _text(v).replace("#", "")
    if len(s) == 6:
        try:
            return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            pass
    return fallback


def _font(size: int, bold=False):
    paths = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _theme(design):
    t = design.get("theme", {}) if isinstance(design, dict) else {}
    return {
        "bg": _rgb(t.get("background_color", t.get("background")), (248, 249, 251)),
        "primary": _rgb(t.get("primary_color", t.get("primary")), (35, 72, 90)),
        "secondary": _rgb(t.get("secondary_color", t.get("secondary")), (100, 110, 120)),
        "accent": _rgb(t.get("accent_color", t.get("accent")), (245, 170, 70)),
        "text": _rgb(t.get("text_color", t.get("text")), (30, 30, 35)),
    }


def _wrap(draw, text, font, width):
    words = _text(text).split()
    if not words:
        return ""
    lines, cur = [], ""
    for word in words:
        test = word if not cur else cur + " " + word
        if draw.textbbox((0, 0), test, font=font)[2] <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def _items(slide, design, planner_data):
    candidates = []
    for obj in (
        slide.get("visual_data"),
        slide.get("structured_data"),
        slide.get("items"),
        slide.get("cards"),
        slide.get("timeline_items"),
        slide.get("diagram_nodes"),
        (design.get("visual_strategy", {}) if isinstance(design, dict) else {}).get("visual_data"),
        planner_data.get("visual_data") if isinstance(planner_data, dict) else None,
    ):
        if isinstance(obj, list) and obj:
            candidates = obj
            break
        if isinstance(obj, dict):
            for key in ("items", "data", "points", "nodes", "steps", "milestones", "cards"):
                value = obj.get(key)
                if isinstance(value, list) and value:
                    candidates = value
                    break
        if candidates:
            break

    if candidates:
        return candidates

    # Safe fallback: planner sections are real content, not invented data.
    sections = planner_data.get("sections") if isinstance(planner_data, dict) else None
    if isinstance(sections, list):
        out = []
        for s in sections:
            if isinstance(s, dict):
                out.append({
                    "label": s.get("title") or s.get("heading") or s.get("name") or "",
                    "description": s.get("description") or s.get("content") or s.get("body") or "",
                })
        if out:
            return out
    return []


def _draw_header(draw, slide, colors, y=64):
    # Reserve a visual area for the main compositor's separately rendered title.
    return y + 130


def _draw_cards(image, slide, design, planner_data):
    colors = _theme(design); draw = ImageDraw.Draw(image)
    items = _items(slide, design, planner_data)
    if not items:
        return False
    cols = 2 if len(items) <= 6 else 3
    rows = max(1, math.ceil(len(items) / cols))
    top = _draw_header(draw, slide, colors, 55)
    gap = 24
    card_w = (WIDTH - 2*MARGIN - gap*(cols-1)) // cols
    card_h = min(300, (HEIGHT - top - MARGIN - gap*(rows-1)) // rows)
    for i, item in enumerate(items[:9]):
        r, c = divmod(i, cols)
        x = MARGIN + c*(card_w+gap); y = top + r*(card_h+gap)
        draw.rounded_rectangle((x,y,x+card_w,y+card_h), radius=28, fill=(255,255,255), outline=colors["accent"], width=3)
        label = _text(item.get("title") or item.get("label") or item.get("name") or f"{i+1:02d}") if isinstance(item, dict) else _text(item)
        body = _text(item.get("description") or item.get("content") or item.get("body") or item.get("value") or "") if isinstance(item, dict) else ""
        lf = _font(30, True); bf = _font(23, False)
        draw.text((x+24,y+24), _wrap(draw,label,lf,card_w-48), font=lf, fill=colors["primary"], spacing=5)
        if body:
            draw.multiline_text((x+24,y+92), _wrap(draw,body,bf,card_w-48), font=bf, fill=colors["text"], spacing=8)
    return True


def _draw_timeline(image, slide, design, planner_data):
    colors = _theme(design); draw = ImageDraw.Draw(image)
    items = _items(slide, design, planner_data)
    if not items:
        return False
    top = _draw_header(draw, slide, colors, 55)
    xline = WIDTH//2
    bottom = HEIGHT - MARGIN
    draw.line((xline, top, xline, bottom), fill=colors["primary"], width=8)
    count = min(len(items), 8)
    step = (bottom-top) / max(1, count-1)
    for i,item in enumerate(items[:8]):
        y = int(top+i*step)
        draw.ellipse((xline-14,y-14,xline+14,y+14), fill=colors["accent"], outline=colors["primary"], width=3)
        side = -1 if i%2==0 else 1
        box_w = 390
        x = xline - 36 - box_w if side < 0 else xline + 36
        label = _text(item.get("date") or item.get("year") or item.get("title") or item.get("label") or f"Stage {i+1}") if isinstance(item,dict) else _text(item)
        body = _text(item.get("description") or item.get("content") or item.get("body") or "") if isinstance(item,dict) else ""
        lf=_font(28,True); bf=_font(21)
        draw.rounded_rectangle((x,y-55,x+box_w,y+55), radius=22, fill=(255,255,255), outline=colors["secondary"], width=2)
        draw.text((x+20,y-43), _wrap(draw,label,lf,box_w-40), font=lf, fill=colors["primary"])
        if body:
            draw.text((x+20,y+2), _wrap(draw,body,bf,box_w-40), font=bf, fill=colors["text"])
    return True


def _numeric_points(items):
    points=[]
    for i,item in enumerate(items):
        if not isinstance(item,dict): continue
        label=item.get("label") or item.get("name") or item.get("x") or str(i+1)
        val=item.get("value", item.get("y"))
        try: val=float(val)
        except Exception: continue
        points.append((str(label),val))
    return points


def _draw_graph(image, slide, design, planner_data):
    colors=_theme(design); draw=ImageDraw.Draw(image)
    items=_items(slide,design,planner_data)
    points=_numeric_points(items)
    if len(points)<2:
        return False
    top=_draw_header(draw,slide,colors,55)
    left=MARGIN+35; right=WIDTH-MARGIN; bottom=HEIGHT-MARGIN
    chart_top=top+40; chart_bottom=bottom-60
    maxv=max(v for _,v in points); minv=min(v for _,v in points)
    if maxv==minv: maxv=minv+1
    draw.line((left,chart_top,left,chart_bottom),fill=colors["secondary"],width=3)
    draw.line((left,chart_bottom,right,chart_bottom),fill=colors["secondary"],width=3)
    slot=(right-left)/len(points)
    bar_w=max(24,int(slot*0.55))
    for i,(label,val) in enumerate(points):
        x=int(left+(i+0.5)*slot)
        h=int((val-minv)/(maxv-minv)*(chart_bottom-chart_top-30))+30
        y=chart_bottom-h
        draw.rounded_rectangle((x-bar_w//2,y,x+bar_w//2,chart_bottom),radius=12,fill=colors["primary"])
        vf=_font(22,True); lf=_font(19)
        draw.text((x-bar_w,y-34), f"{val:g}",font=vf,fill=colors["text"])
        lab=_wrap(draw,label,lf,int(slot-8))
        bbox=draw.multiline_textbbox((0,0),lab,font=lf,spacing=3)
        draw.multiline_text((x-(bbox[2]-bbox[0])/2,chart_bottom+14),lab,font=lf,fill=colors["text"],align="center",spacing=3)
    return True


def _draw_diagram(image, slide, design, planner_data):
    colors=_theme(design); draw=ImageDraw.Draw(image)
    items=_items(slide,design,planner_data)
    if not items: return False
    top=_draw_header(draw,slide,colors,55)
    usable=HEIGHT-top-MARGIN; n=min(len(items),7); box_h=min(120,int((usable-(n-1)*24)/n)); y=top
    for i,item in enumerate(items[:7]):
        label=_text(item.get("title") or item.get("label") or item.get("name") or f"Step {i+1}") if isinstance(item,dict) else _text(item)
        body=_text(item.get("description") or item.get("content") or item.get("body") or "") if isinstance(item,dict) else ""
        x=150 if i%2==0 else 300; w=WIDTH-300
        draw.rounded_rectangle((x,y,x+w,y+box_h),radius=24,fill=(255,255,255),outline=colors["primary"],width=3)
        lf=_font(28,True); bf=_font(20)
        draw.text((x+24,y+18),_wrap(draw,label,lf,w-48),font=lf,fill=colors["primary"])
        if body: draw.text((x+24,y+58),_wrap(draw,body,bf,w-48),font=bf,fill=colors["text"])
        if i<n-1:
            cx=x+w//2; draw.line((cx,y+box_h,cx,y+box_h+18),fill=colors["secondary"],width=5)
            draw.polygon([(cx-10,y+box_h+12),(cx+10,y+box_h+12),(cx,y+box_h+28)],fill=colors["secondary"])
        y += box_h+24
    return True


def _draw_event_poster(image, slide, design, planner_data):
    colors = _theme(design)
    draw = ImageDraw.Draw(image)
    # Decorative poster frame only. Actual headline/body/CTA are rendered
    # by the main compositor so text is never duplicated or embedded in AI art.
    draw.rounded_rectangle(
        (48, 48, WIDTH - 48, HEIGHT - 48),
        radius=36,
        outline=colors["primary"],
        width=5,
        fill=(255, 255, 255),
    )
    draw.rounded_rectangle(
        (76, 76, WIDTH - 76, 150),
        radius=28,
        fill=colors["primary"],
    )
    draw.ellipse((90, 190, 260, 360), fill=colors["accent"])
    draw.ellipse((WIDTH - 260, HEIGHT - 360, WIDTH - 90, HEIGHT - 190), fill=colors["secondary"])
    return True


def _draw_infographic(image, slide, design, planner_data):
    # Infographic uses cards but intentionally allows a larger hierarchy.
    return _draw_cards(image, slide, design, planner_data)


def render_structured_visual(image, visual_type: str, slide: dict, design: dict, planner_data: dict | None = None):
    """Render non-AI visual types. Returns True when a meaningful visual was rendered."""
    planner_data = planner_data or {}
    vt = _text(visual_type).lower()
    if vt == "graph": return _draw_graph(image, slide, design, planner_data)
    if vt == "timeline": return _draw_timeline(image, slide, design, planner_data)
    if vt == "cards": return _draw_cards(image, slide, design, planner_data)
    if vt == "infographic": return _draw_infographic(image, slide, design, planner_data)
    if vt == "diagram": return _draw_diagram(image, slide, design, planner_data)
    if vt == "event_poster": return _draw_event_poster(image, slide, design, planner_data)
    return False
