# -*- coding: utf-8 -*-
"""小型体育赛事办赛工具包生成器：产出 6 张表 xlsx + 时间轴 png。

两种用法：
1) 旧模式（独立参数）：--sport/--scale/--venue/--budget/--date
2) JSON 模式（流水线）：--info 赛事信息.json，按真实信息预填 6 张表与时间轴
"""
import argparse, os, sys
from datetime import datetime, timedelta

from eh_common import load_info, g as _g

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---------- 中文字体（自动探测） ----------
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
                name = fm.FontProperties(fname=path).get_name()
                return name
            except Exception:
                pass
    return "sans-serif"

plt.rcParams["font.sans-serif"] = [pick_font()]
plt.rcParams["axes.unicode_minus"] = False

BLUE = "1A365D"; ORANGE_C = "ED8936"; LIGHT = "EAF0F6"; WHITE = "FFFFFF"
LIGHT_H = "#EAF0F6"
BLUEH = "#1a365d"; ORANGEH = "#ed8936"; GRAYH = "#666666"

thin = Side(style="thin", color="C9D3DD")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
head_font = Font(name="微软雅黑", size=11, bold=True, color=WHITE)
cell_font = Font(name="微软雅黑", size=10, color="333333")
note_font = Font(name="微软雅黑", size=10, italic=True, color="888888")
head_fill = PatternFill("solid", fgColor=BLUE)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)


def build_sheet(ws, title, note, headers, rows, widths, sample_rows=99):
    cols = len(headers)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
    c = ws.cell(row=1, column=1, value=title)
    c.font = Font(name="微软雅黑", size=14, bold=True, color=BLUE)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
    c = ws.cell(row=2, column=1, value=note)
    c.font = note_font
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 22
    hr = 3
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=hr, column=j, value=h)
        c.font = head_font; c.fill = head_fill; c.alignment = center; c.border = border
    ws.row_dimensions[hr].height = 26
    r = hr + 1
    for i, row in enumerate(rows):
        for j, v in enumerate(row, 1):
            c = ws.cell(row=r, column=j, value=v)
            c.font = cell_font; c.alignment = left; c.border = border
            if i < sample_rows:
                c.fill = PatternFill("solid", fgColor="FFF4E6")
        ws.row_dimensions[r].height = 30
        r += 1
    for _ in range(12):
        for j in range(1, cols + 1):
            c = ws.cell(row=r, column=j, value="")
            c.border = border; c.font = cell_font; c.alignment = left
        ws.row_dimensions[r].height = 26
        r += 1
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(row=hr + 1, column=1)


def make_excel(out_path, sport, scale, venue, budget, event_name="", date="", organizers=None):
    # 预算按总预算参考拆分（自有场馆省场地费，商场场馆场地费更低但宣传略高）
    b = float(budget)
    in_mall = "商场" in venue
    organizers = organizers or []
    venue_ratio = 0.05 if in_mall else 0.0
    rows_budget = [
        ["场地", "场地租赁", round(b * (venue_ratio or 0.0)), "", "", "自有/商场可省"],
        ["场地", "舞台/背景板", round(b * 0.12), "", "", "可复用桁架"],
        ["人员", "裁判/教练", round(b * 0.14), "", "", "按项目定人数"],
        ["人员", "现场工作人员", round(b * 0.08), "", "", "签到/引导"],
        ["物料", "号码布/证书/奖牌", round(b * 0.08), "", "", "按参赛规模"],
        ["宣传", "海报/拍摄/直播", round(b * (0.12 if in_mall else 0.09)), "", "", "本地摄影"],
        ["保险", "赛事意外险(全员)", round(b * 0.05), "", "", "必买"],
        ["餐饮", "工作人员/饮用水", round(b * 0.05), "", "", ""],
        ["机动", "应急备用金", round(b * 0.10), "", "", "约10%"],
    ]

    title_prefix = f"{event_name} · " if event_name else ""
    wb = Workbook()
    ws = wb.active; ws.title = "①赛事预算表"
    build_sheet(ws, f"{title_prefix}{sport}赛事预算表", f"参考总预算 {budget:,.0f} 元按比例拆分，橙色为示例，可直接改。建议留10%机动费。",
                ["费用类别", "明细项目", "预算金额(元)", "实际金额(元)", "差额", "备注/供应商"],
                rows_budget, [12, 20, 14, 14, 10, 18])

    # 倒排工期：若给出比赛日期，把真实日期填入“责任人”前的说明；负责人默认主办方
    default_owner = organizers[0] if organizers else ""
    nodes = [("D-21天", "确定方案/规模/场地", "方案定稿、场地意向"),
             ("D-21天", "报批/对接相关部门", "材料提交"),
             ("D-14天", "开放报名、发布海报", "报名通道上线"),
             ("D-10天", "拉赞助/对接商户", "至少3家联动"),
             ("D-7天", "确定裁判/工作人员", "排班表确认"),
             ("D-5天", "购买保险", "全员名单投保"),
             ("D-3天", "物料到位、设备调试", "清点签收"),
             ("D-1天", "现场踩点、流程彩排", "动线确认"),
             ("D日", "正式比赛", "安全完赛"),
             ("D+2天", "数据整理、客户跟进", "跟进完成")]
    rows_timeline = []
    try:
        d0 = datetime.strptime(date, "%Y-%m-%d") if date else None
    except (ValueError, TypeError):
        d0 = None
    for label, task, deliver in nodes:
        off = int(label.replace("D", "").replace("天", "")) if label != "D日" else 0
        date_note = ""
        if d0:
            date_note = (d0 + timedelta(days=off)).strftime("%m-%d")
        rows_timeline.append([label, task, (f"{date_note} · {deliver}" if date_note else deliver),
                              default_owner, ""])
    ws = wb.create_sheet("②倒排工期表")
    build_sheet(ws, f"{title_prefix}办赛倒排工期表", "以比赛日为 D 日倒推，责任人落实到人。",
                ["时间节点", "任务事项", "交付标准/对应日期", "责任人", "完成状态"],
                rows_timeline, [12, 24, 22, 14, 12])

    ws = wb.create_sheet("③人员分工表")
    build_sheet(ws, "现场人员分工表", "可一人兼多岗，关键环节不能空缺。",
                ["岗位", "人数", "核心职责", "关键动作", "负责人/电话"],
                [["总指挥", 1, "全场调度、突发决策", "持对讲机、控流程", ""],
                 ["签到组", 2, "签到、发号码布、引导", "核对名单、分流", ""],
                 ["裁判组", "按项目", "执裁、计时、计分", "公平、记录成绩", ""],
                 ["场地组", 2, "设备、场地、秩序", "提前布置、收尾", ""],
                 ["安全医疗", 1, "急救、突发处置", "药箱、联系医院", ""],
                 ["宣传组", 1, "拍照、直播、素材", "抓高光镜头", ""],
                 ["接待组", 1, "家长/嘉宾接待答疑", "稳定情绪、引座", ""]],
                [12, 8, 22, 22, 16])

    ws = wb.create_sheet("④物料清单")
    build_sheet(ws, "赛事物料清单", "赛前一天逐项打勾。",
                ["分类", "物料名称", "数量", "是否到位", "负责人", "备注"],
                [["赛事", "号码布/队标", "", "☐", "", ""],
                 ["赛事", "计分板/计时器/口哨", "", "☐", "", ""],
                 ["奖项", "奖牌/证书/奖品", "", "☐", "", ""],
                 ["宣传", "背景板/横幅/指引牌", "", "☐", "", ""],
                 ["宣传", "相机/稳定器/充电宝", "", "☐", "", ""],
                 ["后勤", "桌椅/帐篷/音响/麦克风", "", "☐", "", ""],
                 ["后勤", "饮用水/纸杯", "", "☐", "", ""],
                 ["医疗", "急救箱/冰袋/消毒用品", "", "☐", "", ""],
                 ["文书", "签到表/免责书/流程单", "", "☐", "", ""]],
                [10, 26, 8, 10, 12, 16])

    ws = wb.create_sheet("⑤安全检查表")
    build_sheet(ws, "安全检查表（赛前必过）", "任何一项不达标，宁可延期。",
                ["检查项", "检查要点", "是否合格", "整改措施", "复查人"],
                [["场地安全", "地面平整、无尖锐物、防滑", "☐合格 ☐不合格", "", ""],
                 ["器材安全", "器材稳固、无破损、符合年龄", "☐合格 ☐不合格", "", ""],
                 ["医疗保障", "急救箱、急救员、就近医院路线", "☐合格 ☐不合格", "", ""],
                 ["保险", "所有参赛者已投保意外险", "☐合格 ☐不合格", "", ""],
                 ["人员配置", "师生比达标、关键区域有人盯", "☐合格 ☐不合格", "", ""],
                 ["天气预案", "高温/雷雨应对、遮阴或室内方案", "☐合格 ☐不合格", "", ""],
                 ["疏散通道", "通道畅通、标识清晰", "☐合格 ☐不合格", "", ""],
                 ["应急联络", "负责人/医院/急救电话齐全", "☐合格 ☐不合格", "", ""],
                 ["免责告知", "健康承诺/风险告知已签署", "☐合格 ☐不合格", "", ""]],
                [12, 30, 16, 18, 10])

    ws = wb.create_sheet("⑥赛后跟进表")
    build_sheet(ws, "赛后48小时跟进表", "比赛结束才是转化开始。",
                ["队伍/孩子姓名", "家长联系方式", "现场表现/高光", "跟进话术要点", "跟进结果", "下一步"],
                [["示例：张某", "138****0000", "高光表现", "发照片+肯定+邀请体验", "", "体验课"],
                 ["示例：李某", "139****1111", "敢拼/进步", "鼓励+成长建议", "", "社群"]],
                [16, 16, 18, 22, 14, 12])

    wb.save(out_path)


def make_timeline(out_path, sport):
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=150)
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.text(6, 4.85, f"一场{sport}小型赛事，照着这张图办", ha="center", va="center",
            fontsize=20, fontweight="bold", color=BLUEH)
    stages = [("D-21天", "定方案\n定场地\n去报批"), ("D-14天", "开放报名\n发海报"),
              ("D-10天", "拉赞助\n对接商户"), ("D-5天", "买保险\n排人员"),
              ("D-1天", "物料到位\n踩点彩排"), ("D日", "安全\n完赛"),
              ("D+2天", "发照片\n跟进转化")]
    n = len(stages); x0, x1 = 0.6, 11.4
    gap = (x1 - x0) / (n - 1); yb = 2.6
    ax.annotate("", xy=(x1 + 0.25, yb), xytext=(x0 - 0.25, yb),
                arrowprops=dict(arrowstyle="-|>", color=ORANGEH, lw=3))
    for i, (day, text) in enumerate(stages):
        x = x0 + i * gap
        ax.scatter([x], [yb], s=320, color=BLUEH, zorder=5, edgecolors="white", linewidths=2)
        ax.text(x, yb + 0.55, day, ha="center", va="bottom", fontsize=11,
                fontweight="bold", color=ORANGEH)
        ax.plot([x, x], [yb - 0.12, 1.57], color="#b8c4d0", lw=1.2, ls="--")
        box = FancyBboxPatch((x - 0.62, 0.9), 1.24, 0.72,
                             boxstyle="round,pad=0.02,rounding_size=0.08",
                             fc=LIGHT_H, ec=BLUEH, lw=1.3)
        ax.add_patch(box)
        ax.text(x, 1.26, text, ha="center", va="center", fontsize=9.5, color=BLUEH)
    ax.text(6, 0.18, "关键提醒：保险全员买 · 安全检查不通过宁可延期 · 赛后48小时内必须跟进",
            ha="center", va="center", fontsize=11, color="#c0392b", fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", default="", help="赛事信息.json；提供后从其中读取参数")
    ap.add_argument("--sport", default="综合运动会")
    ap.add_argument("--scale", default="50人")
    ap.add_argument("--venue", default="自有场馆")
    ap.add_argument("--budget", type=float, default=10000)
    ap.add_argument("--date", default="")
    ap.add_argument("--out", default="办赛工具包_output")
    args = ap.parse_args()

    event_name = ""
    organizers = []
    if args.info:
        e = load_info(args.info)
        v = e.get("venue", {})
        p = e.get("participants", {})
        sports = "、".join(s.get("name", "") for s in e.get("sports", []) if s.get("name"))
        args.sport = sports or "综合运动会"
        args.scale = f"{_g(p, 'athletes', 50)}人"
        args.venue = _g(v, "name", "自有场馆")
        args.budget = float(_g(e, "budget", 10000) or 10000)
        args.date = _g(e, "date", "")
        event_name = _g(e, "name", "")
        if _g(e, "organizer"):
            organizers.append(_g(e, "organizer"))
        if not args.out or args.out == "办赛工具包_output":
            args.out = os.path.join(os.path.dirname(os.path.abspath(args.info)), "办赛工具包")

    cwd = os.getcwd()
    out_dir = args.out if os.path.isabs(args.out) else os.path.join(cwd, args.out)
    os.makedirs(out_dir, exist_ok=True)

    xlsx_path = os.path.join(out_dir, "办赛实操工具包_6张表.xlsx")
    png_path = os.path.join(out_dir, "办赛全流程时间轴.png")
    # 时间轴上的运动项目取首个主项目，避免太长
    timeline_sport = args.sport.split("、")[0]
    make_excel(xlsx_path, args.sport, args.scale, args.venue, args.budget,
               event_name=event_name, date=args.date, organizers=organizers)
    make_timeline(png_path, timeline_sport)

    print("XLSX:", xlsx_path)
    print("PNG:", png_path)


if __name__ == "__main__":
    main()
