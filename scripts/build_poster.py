# -*- coding: utf-8 -*-
"""阶段三：读取 赛事信息.json，用 Pillow 生成竖版赛事宣传海报 PNG（无需联网/字体文件自动探测）。"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

from eh_common import load_info, g, money, ensure_dir

W, H = 1080, 1620
BLUE = (26, 54, 93)
BLUE_D = (16, 36, 66)
BLUE2 = (44, 82, 130)
ORANGE = (237, 137, 54)
ORANGE_L = (246, 173, 110)
LIGHT = (234, 240, 246)
WHITE = (255, 255, 255)
GOLD = (240, 196, 90)
GRAY = (150, 165, 185)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def ctext(d, cx, y, text, fnt, fill, anchor_center=True):
    if anchor_center:
        d.text((cx, y), text, font=fnt, fill=fill, anchor="ma")
    else:
        d.text((cx, y), text, font=fnt, fill=fill)


def wrap_cn(text, fnt, max_w):
    """按像素宽度对中文文本换行。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        test = cur + ch
        if font_metrics(fnt, test)[0] > max_w and cur:
            lines.append(cur); cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def font_metrics(fnt, text):
    # 用临时图测量，避免重复建图
    box = fnt.getbbox(text)
    return box[2] - box[0], box[3] - box[1]


def vgradient(img, top, bottom):
    """竖向渐变背景。"""
    base = Image.new("RGB", (1, H), top)
    px = base.load()
    for y in range(H):
        t = y / H
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    img.paste(base.resize((W, H)), (0, 0))


def draw_trophy(d, cx, cy, scale=1.0):
    """用几何图形画一个简约奖杯。"""
    s = scale
    gold = GOLD
    # 杯身
    d.rounded_rectangle([cx - 70*s, cy - 90*s, cx + 70*s, cy + 30*s], 18*s, fill=gold)
    # 杯盖球
    d.ellipse([cx - 16*s, cy - 122*s, cx + 16*s, cy - 90*s], fill=gold)
    # 把手
    d.arc([cx - 120*s, cy - 80*s, cx - 60*s, cy + 10*s], 270, 90, fill=gold, width=int(12*s))
    d.arc([cx + 60*s, cy - 80*s, cx + 120*s, cy + 10*s], 90, 270, fill=gold, width=int(12*s))
    # 支柱与底座
    d.rectangle([cx - 14*s, cy + 30*s, cx + 14*s, cy + 62*s], fill=gold)
    d.rounded_rectangle([cx - 58*s, cy + 62*s, cx + 58*s, cy + 92*s], 8*s, fill=gold)


def build_poster(e, out_path):
    img = Image.new("RGB", (W, H), BLUE_D)
    vgradient(img, BLUE, BLUE_D)
    d = ImageDraw.Draw(img)

    # 顶部装饰条
    d.rectangle([0, 0, W, 14], fill=ORANGE)

    f_kicker = font(40)
    f_title = font(70)
    f_slogan = font(42)
    f_label = font(34)
    f_val = font(40)
    f_small = font(30)
    f_org = font(32)

    cx = W // 2
    y = 90

    # 主办徽记式文字
    kicker = g(e, "organizer", "诚邀参赛")
    ctext(d, cx, y, f"【 {kicker} 】", f_kicker, ORANGE_L)
    y += 80

    # 奖杯
    draw_trophy(d, cx, y + 120, 1.15)
    y += 270

    # 标题（自动换行）
    title = g(e, "name", "体育赛事")
    lines = wrap_cn(title, f_title, W - 160)
    if len(lines) > 3:  # 标题过长则缩小字号
        f_title = font(64)
        lines = wrap_cn(title, f_title, W - 160)
    for ln in lines:
        ctext(d, cx, y, ln, f_title, WHITE)
        y += 92
    y += 6

    # 口号
    slogan = g(e, "slogan")
    if slogan:
        ctext(d, cx, y, f"「 {slogan} 」", f_slogan, GOLD)
        y += 66

    # 橙色分隔
    d.rounded_rectangle([cx - 60, y, cx + 60, y + 8], 4, fill=ORANGE)
    y += 44

    # 信息块（标签+值）
    v = e.get("venue", {})
    p = e.get("participants", {})
    sports = " / ".join(s.get("name", "") for s in e.get("sports", []) if s.get("name"))
    date_str = g(e, "date")
    if g(e, "time_start"):
        date_str += f"  {g(e,'time_start')}" + (f"-{g(e,'time_end')}" if g(e, "time_end") else "")

    blocks = [
        ("比赛项目", sports or "综合"),
        ("比赛时间", date_str),
        ("比赛地点", g(v, "name")),
        ("参赛规模", f"{g(p,'athletes','—')}人 / {g(p,'teams','—')}队"),
    ]
    box_x0, box_x1 = 90, W - 90
    f_block = font(38)
    for label, val in blocks:
        # 白色实心信息条
        d.rounded_rectangle([box_x0, y, box_x1, y + 78], 14, fill=WHITE)
        d.rounded_rectangle([box_x0, y, box_x0 + 150, y + 78], 14, fill=ORANGE)
        d.rectangle([box_x0 + 120, y, box_x0 + 150, y + 78], fill=ORANGE)
        ctext(d, box_x0 + 75, y + 18, label, f_label, WHITE)
        d.text((box_x0 + 175, y + 18), str(val), font=f_block, fill=BLUE)
        y += 94

    y += 6
    # 费用 / 奖项
    fee = float(g(e, "fee", 0) or 0)
    fee_txt = "免费参赛" if fee == 0 else f"报名费 {money(fee)} 元/人"
    ctext(d, cx, y, fee_txt + "    |    " + g(e, "awards", "现场颁奖"), f_small, GOLD)
    y += 60

    # 底部：二维码占位 + 联系方式
    contact = e.get("contact", {})
    qr = 200
    qx0, qy0 = box_x0, y
    qx1, qy1 = qx0 + qr, qy0 + qr
    d.rounded_rectangle([qx0 - 8, qy0 - 8, qx1 + 8, qy1 + 8], 12, fill=WHITE)
    # 虚线感占位：内部边框
    d.rectangle([qx0, qy0, qx1, qy1], outline=(180, 190, 205), width=3)
    ctext(d, qx0 + qr // 2, qy0 + 60, "扫码报名", f_label, BLUE)
    ctext(d, qx0 + qr // 2, qy0 + 112, "(粘贴报名二维码)", f_small, GRAY)

    # 右侧联系信息
    tx = qx1 + 40
    d.text((tx, qy0 + 6), f"报名咨询：{g(contact,'name','')}", font=f_org, fill=WHITE)
    d.text((tx, qy0 + 56), f"电话：{g(contact,'phone','')}", font=f_org, fill=LIGHT)
    d.text((tx, qy0 + 106), f"微信：{g(contact,'wechat','')}", font=f_org, fill=LIGHT)

    # 底部主办信息条
    d.rectangle([0, H - 70, W, H], fill=BLUE2)
    org_line = g(e, "organizer", "")
    if g(e, "undertaker"):
        org_line += f"  ·  承办 {g(e,'undertaker')}"
    ctext(d, cx, H - 56, org_line, f_small, LIGHT)

    img.save(out_path, "PNG")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    e = load_info(args.info)
    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        base = os.path.dirname(os.path.abspath(args.info))
        out_path = os.path.join(base, "赛事宣传海报.png")
    ensure_dir(os.path.dirname(out_path))
    build_poster(e, out_path)
    print("POSTER:", out_path)


if __name__ == "__main__":
    main()
