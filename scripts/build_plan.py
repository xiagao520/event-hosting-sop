# -*- coding: utf-8 -*-
"""阶段二：读取 赛事信息.json，生成《赛事策划方案》HTML，供用户审阅确认。"""
import argparse
import os
from datetime import datetime, timedelta

from eh_common import (load_info, g, esc, money, page_shell, ensure_dir,
                       BLUE, ORANGE)


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def budget_rows(budget, venue_type):
    b = float(budget or 0)
    in_mall = "商场" in str(venue_type)
    venue_ratio = 0.05 if in_mall else 0.0
    promo = 0.12 if in_mall else 0.09
    return [
        ("场地租赁", b * venue_ratio, "自有/商场可省"),
        ("舞台/背景板", b * 0.12, "可复用桁架"),
        ("裁判/教练", b * 0.14, "按项目定人数"),
        ("现场工作人员", b * 0.08, "签到/引导"),
        ("号码布/证书/奖牌", b * 0.08, "按参赛规模"),
        ("海报/拍摄/直播", b * promo, "本地摄影"),
        ("赛事意外险(全员)", b * 0.05, "必买"),
        ("餐饮/饮用水", b * 0.05, ""),
        ("应急备用金", b * 0.10, "约10%"),
    ]


def build_html(e):
    v = e.get("venue", {})
    p = e.get("participants", {})
    contact = e.get("contact", {})
    sports = e.get("sports", [])
    co = e.get("co_organizers", [])
    d = parse_date(g(e, "date"))

    # 组织单位
    org_lines = [f"<b>主办方：</b>{esc(g(e, 'organizer'))}"]
    if g(e, "undertaker"):
        org_lines.append(f"<b>承办方：</b>{esc(g(e, 'undertaker'))}")
    for c in co:
        org_lines.append(f"<b>{esc(g(c, 'role', '协办方'))}：</b>{esc(g(c, 'name'))}")

    # 项目与组别
    sport_cards = []
    for s in sports:
        groups = "".join(f'<span class="tag">{esc(x)}</span>' for x in s.get("groups", []))
        rows = [
            ("赛制", g(s, "format", g(e, "format"))),
            ("团体人数", g(s, "team_size", "—")),
            ("报名费", ("免费" if float(g(s, "fee", 0) or 0) == 0 else f"{money(g(s,'fee'))} 元/人")),
            ("规则要点", g(s, "rules", "按主办方公布的竞赛规则执行")),
        ]
        rhtml = "".join(f"<tr><th style='width:110px'>{esc(k)}</th><td>{esc(val)}</td></tr>"
                        for k, val in rows)
        sport_cards.append(f"""
        <div class="card">
          <h3 style="margin-top:0">{esc(g(s, 'name'))}</h3>
          <div style="margin:6px 0 10px">{groups or '<span class="muted">未分组</span>'}</div>
          <table>{rhtml}</table>
        </div>""")

    # 时间轴（倒排）
    timeline = []
    if d:
        nodes = [(-21, "确定方案 / 场地 / 报批"), (-14, "发布海报、开放报名"),
                 (-10, "对接商户 / 赞助联动"), (-7, "确定裁判与工作人员排班"),
                 (-5, "全员名单投保"), (-3, "物料到位、设备调试"),
                 (-1, "现场踩点、流程彩排"), (0, "正式比赛"), (2, "数据整理、客户跟进")]
        timeline.append("<table><tr><th style='width:130px'>时间节点</th><th>关键任务</th></tr>")
        for off, task in nodes:
            day = (d + timedelta(days=off)).strftime("%m-%d")
            label = "D日" if off == 0 else f"D{off:+d}天"
            timeline.append(
                f"<tr><td><b>{label}</b><span class='muted'>（{day}）</span></td><td>{esc(task)}</td></tr>")
        timeline.append("</table>")
    timeline_html = "".join(timeline) or '<p class="muted">未提供比赛日期，时间轴将在确定日期后生成。</p>'

    # 预算
    brows = budget_rows(g(e, "budget", 0), g(v, "type"))
    btotal = sum(x[1] for x in brows)
    bhtml = "<table><tr><th>费用项目</th><th style='width:140px'>参考金额(元)</th><th>说明</th></tr>"
    for name, amt, note in brows:
        bhtml += f"<tr><td>{esc(name)}</td><td>{money(amt)}</td><td class='muted'>{esc(note)}</td></tr>"
    bhtml += (f"<tr><th>合计</th><th>{money(btotal)}</th><th class='muted'>"
              f"以总预算 {money(g(e,'budget',0))} 元为基准</th></tr></table>")

    fee_text = "免费" if float(g(e, "fee", 0) or 0) == 0 else f"{money(g(e, 'fee'))} 元/人"

    datetime_str = g(e, "date")
    if g(e, "time_start"):
        datetime_str += f" {esc(g(e,'time_start'))}" + (f"–{esc(g(e,'time_end'))}" if g(e, "time_end") else "")

    body = f"""
<div class="banner">
  <h1>赛事策划方案（待确认）</h1>
  <p>{esc(g(e, 'name'))}</p>
</div>
<p class="muted">本方案由办赛流水线根据信息采集表自动生成，请逐项审阅；确认后将生成宣传海报、报名登记系统、6张执行表与赛事秩序册。</p>

<h2>一、活动概述</h2>
<div class="card">
  <table>
    <tr><th style="width:110px">赛事名称</th><td>{esc(g(e, 'name'))}</td></tr>
    <tr><th>主题口号</th><td>{esc(g(e, 'slogan', '—'))}</td></tr>
    <tr><th>比赛时间</th><td>{esc(datetime_str)}</td></tr>
    <tr><th>比赛地点</th><td>{esc(g(v, 'name'))}
        <span class="muted">{esc(g(v, 'address'))}</span></td></tr>
    <tr><th>场地条件</th><td>{esc(g(v, 'courts', '—'))}（{esc(g(v, 'type'))}）</td></tr>
    <tr><th>参赛规模</th><td>约 {esc(g(p, 'athletes', '—'))} 名运动员 ·
        {esc(g(p, 'teams', '—'))} 支队伍 · 预计观众 {esc(g(p, 'audience', '—'))} 人 ·
        年龄 {esc(g(p, 'age_range', '—'))}</td></tr>
    <tr><th>报名费</th><td>{fee_text}</td></tr>
  </table>
</div>

<h2>二、组织机构</h2>
<div class="card">
  {"<br>".join(org_lines)}
</div>

<h2>三、竞赛项目与赛制设计</h2>
{"".join(sport_cards)}
<div class="card">
  <h3 style="margin-top:0">赛制与计分办法</h3>
  <p><b>总体赛制：</b>{esc(g(e, 'format'))}</p>
  <p><b>计分办法：</b>{esc(g(e, 'scoring', '—'))}</p>
  <p><b>赛程编排：</b>{esc(g(e, 'schedule_plan', '—'))}</p>
  <p><b>奖项设置：</b>{esc(g(e, 'awards', '—'))}</p>
</div>

<h2>四、宣传与报名安排</h2>
<div class="card">
  <p>方案确认后，将生成赛事<b>宣传海报</b>与<b>线上报名登记页</b>，报名页采集：姓名、性别、年龄、组别、队伍、监护人及联系方式、健康承诺等，并支持导出名单用于编排和保险投保。</p>
  <p><b>报名咨询：</b>{esc(g(contact, 'name', '—'))} · {esc(g(contact, 'phone', '—'))}
     · 微信 {esc(g(contact, 'wechat', '—'))}</p>
</div>

<h2>五、筹备时间轴（倒排）</h2>
{timeline_html}

<h2>六、预算参考拆分</h2>
{bhtml}

<h2>七、安全与风险保障</h2>
<div class="card">
  <ul>
    <li>为<b>全体参赛人员</b>购买赛事意外险，赛前一天完成全员投保；</li>
    <li>赛前进行场地、器材、通道、医疗 9 项安全检查，任一项不达标宁可延期；</li>
    <li>配备急救箱、急救员，提前确认就近医院路线与应急联络；</li>
    <li>制定高温 / 雷雨等极端天气的室内或顺延预案；</li>
    <li>签署健康承诺与风险告知，明确参赛身体条件要求。</li>
  </ul>
</div>

<h2>八、其他说明</h2>
<div class="card">{esc(g(e, 'extra', '—')) or '<span class="muted">无</span>'}</div>

<div class="note">✅ 请重点确认：赛事名称、时间地点、组别赛制、规模与预算。如需修改，直接在信息采集表调整后重新生成本方案；确认无误后即可进入「海报 + 报名系统」环节。</div>
"""
    return page_shell(f"赛事策划方案-{g(e,'name')}", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True, help="赛事信息.json 路径")
    ap.add_argument("--out", default="", help="输出HTML路径，默认在信息同目录")
    args = ap.parse_args()

    e = load_info(args.info)
    htmlstr = build_html(e)
    if args.out:
        out_path = args.out
    else:
        base = os.path.dirname(os.path.abspath(args.info))
        out_path = os.path.join(base, "赛事策划方案.html")
    out_path = os.path.abspath(out_path)
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(htmlstr)
    print("PLAN:", out_path)


if __name__ == "__main__":
    main()
