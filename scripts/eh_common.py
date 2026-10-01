# -*- coding: utf-8 -*-
"""event-hosting-sop 公共库：JSON 读取、中文字体、输出目录、HTML 基础能力。

统一数据结构（由 assets/信息采集表.html 导出）：
{
  "meta": {"tool":"event-hosting-sop","schema":1},
  "event": { 赛事各字段... }
}
所有 builder 只依赖本文件，且不访问网络 / 不需要凭证。
"""
import os
import json
import html as _html

# ------- 视觉常量（与品牌一致，微信编辑器安全色） -------
BLUE = "#1a365d"
BLUE2 = "#2c5282"
ORANGE = "#ed8936"
LIGHT = "#eaf0f6"
INK = "#2d3748"
MUTED = "#718096"
RED = "#c0392b"
WHITE = "#ffffff"


# ------- 数据读取 -------
def load_info(path):
    """读取信息采集表导出的 JSON，返回 event 字典。兼容直接传 event 字典。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "event" in data:
        return data["event"]
    return data


def save_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def ensure_dir(path):
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    os.makedirs(path, exist_ok=True)
    return path


# ------- 取值兜底 -------
def g(d, key, default=""):
    """安全取字典值，None 也转成 default。"""
    if not isinstance(d, dict):
        return default
    v = d.get(key)
    return v if v not in (None, "") else default


def esc(v):
    return _html.escape(str("" if v is None else v))


def money(v):
    try:
        return f"{int(round(float(v))):,}"
    except (TypeError, ValueError):
        return "0"


def nl2br(v):
    return esc(v).replace("\n", "<br>")


# ------- 中文字体（matplotlib） -------
def pick_font():
    from matplotlib import font_manager as fm
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                fm.fontManager.addfont(path)
                return fm.FontProperties(fname=path).get_name()
            except Exception:
                pass
    return "sans-serif"


def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = [pick_font()]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


# ------- HTML 页面骨架（屏幕阅读用：策划方案 / 报名后台等） -------
def page_shell(title, body, extra_css="", lang="zh-CN"):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
  :root{{--blue:{BLUE};--blue2:{BLUE2};--orange:{ORANGE};--light:{LIGHT};
    --ink:{INK};--muted:{MUTED};--line:#d7e0ea;--bg:#f4f7fb;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    font-size:15px;line-height:1.75;}}
  .wrap{{max-width:860px;margin:0 auto;padding:28px 18px 60px;}}
  h1,h2,h3{{color:var(--blue);line-height:1.4;}}
  h2{{font-size:19px;margin:34px 0 12px;padding-left:11px;border-left:5px solid var(--orange);}}
  h3{{font-size:16px;margin:22px 0 8px;}}
  p{{margin:8px 0;}}
  table{{border-collapse:collapse;width:100%;margin:12px 0;background:#fff;font-size:14px;}}
  th,td{{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top;}}
  th{{background:var(--blue);color:#fff;font-weight:600;}}
  tr:nth-child(even) td{{background:#f8fafd;}}
  .card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin:14px 0;}}
  .muted{{color:var(--muted);font-size:13px;}}
  .tag{{display:inline-block;background:var(--light);color:var(--blue2);border-radius:20px;
    padding:2px 12px;font-size:12.5px;margin:2px 4px 2px 0;}}
  .banner{{background:var(--blue);color:#fff;border-radius:12px;padding:26px 24px;margin-bottom:8px;}}
  .banner h1{{color:#fff;margin:0 0 6px;font-size:24px;}}
  .banner p{{margin:0;opacity:.9;}}
  ul,ol{{margin:8px 0;padding-left:22px;}}
  li{{margin:4px 0;}}
  .note{{background:#fff8f0;border:1px solid #f3d9bd;border-radius:8px;padding:12px 16px;
    color:#8a5a23;font-size:13.5px;margin:14px 0;}}
  {extra_css}
</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>"""


# ------- 便捷摘要 -------
def event_summary(e):
    v = e.get("venue", {})
    p = e.get("participants", {})
    sports = "、".join(s.get("name", "") for s in e.get("sports", []) if s.get("name"))
    return {
        "name": g(e, "name", "未命名赛事"),
        "sports": sports or "综合",
        "date": g(e, "date", "日期待定"),
        "venue": g(v, "name", "场地待定"),
        "athletes": g(p, "athletes", 0),
        "budget": g(e, "budget", 0),
    }
