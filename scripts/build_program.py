# -*- coding: utf-8 -*-
"""阶段五：生成《赛事秩序册》——A4 可打印 HTML（浏览器内 Ctrl/Cmd+P 另存为 PDF）。

内容：封面 / 组织机构 / 竞赛规程 / 赛程总表 / 分组循环编排（自动生成）/
      淘汰赛对阵表 / 参赛队及运动员名单（报名确认后可更新）/ 场馆信息。

无队伍名单时用「队伍1..」占位，报名名单确认后重新生成即可替换。
"""
import argparse
import os
from datetime import datetime
from itertools import combinations

from eh_common import load_info, g, esc, ensure_dir, nl2br, money


def round_robin(n, names=None):
    """单循环编排：返回每轮比赛 [(A,B)]，使用贝格尔轮转，奇数队补 bye。"""
    names = names or [f"队伍{i + 1}" for i in range(n)]
    teams = list(names)
    if len(teams) % 2 == 1:
        teams = teams + [None]  # 轮空
    half = len(teams) // 2
    rounds = []
    arr = teams[:]
    for _ in range(len(teams) - 1):
        left, right = arr[:half], arr[half:]
        pairs = []
        for i in range(half):
            a, b = left[i], right[half - 1 - i]
            if a and b:
                pairs.append((a, b))
        rounds.append(pairs)
        # 固定位置轮转
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    return rounds


def fmt_time(t):
    return t if t else ""


def build_html(e):
    v = e.get("venue", {})
    p = e.get("participants", {})
    contact = e.get("contact", {})
    co = e.get("co_organizers", [])
    sports = e.get("sports", [])

    org_rows = [("主办方", g(e, "organizer"))]
    if g(e, "undertaker"):
        org_rows.append(("承办方", g(e, "undertaker")))
    for c in co:
        org_rows.append((g(c, "role", "协办方"), g(c, "name")))
    org_rows.append(("报名咨询",
                     f"{g(contact,'name','')} {g(contact,'phone','')} 微信{g(contact,'wechat','')}"))
    org_html = "".join(f"<tr><th>{esc(k)}</th><td>{esc(val)}</td></tr>" for k, val in org_rows)

    date_time = g(e, "date")
    if g(e, "time_start"):
        date_time += f" {fmt_time(g(e,'time_start'))}" + (f"—{fmt_time(g(e,'time_end'))}" if g(e, "time_end") else "")

    # ---- 竞赛规程 ----
    rules_blocks = []
    for s in sports:
        groups = "、".join(s.get("groups", [])) or "不分组"
        rules_blocks.append(f"""
        <h4>{esc(g(s,'name'))}（组别：{esc(groups)}）</h4>
        <p><b>赛制：</b>{esc(g(s,'format', g(e,'format')))}</p>
        <p><b>队伍人数：</b>{esc(g(s,'team_size','按各项目规则'))}</p>
        <p><b>竞赛规则：</b>{esc(g(s,'rules','按主办方公布的竞赛规则执行'))}</p>""")

    fee = float(g(e, "fee", 0) or 0)
    fee_str = "免费" if fee == 0 else f"{money(g(e, 'fee'))} 元/人"

    # ---- 分组循环编排（每组默认 4 队演示；无报名数据时占位）----
    schedule_sections = []
    for s in sports:
        sport_name = g(s, "name")
        groups = s.get("groups", []) or ["不分组"]
        for grp in groups:
            rounds = round_robin(4)  # 报名确认后可按实际队数更新
            sec = [f'<div class="grp-title">{esc(sport_name)} · {esc(grp)} 组（单循环）</div>']
            sec.append("<table class='sched'><tr><th style='width:70px'>轮次</th>"
                       "<th>对阵</th><th style='width:90px'>比分</th><th style='width:90px'>场地</th></tr>")
            for ri, pairs in enumerate(rounds, 1):
                for pi, (a, b) in enumerate(pairs):
                    first = "rowspan" if pi == 0 else ""
                    cell = f"<td rowspan='{len(pairs)}'><b>第{ri}轮</b></td>" if pi == 0 else ""
                    sec.append(f"<tr>{cell}<td>{esc(a)} VS {esc(b)}</td>"
                               f"<td>∶</td><td>{'1号场' if (ri+pi)%2==0 else '2号场'}</td></tr>")
            sec.append("</table>")
            # 小组积分表
            sec.append("<table class='score'><tr><th>名次</th><th>队名</th><th>胜</th><th>负</th>"
                       "<th>积分</th><th>净胜</th></tr>")
            for i in range(1, 5):
                sec.append(f"<tr><td>{i}</td><td class='fill'>队伍{i}</td><td></td><td></td><td></td><td></td></tr>")
            sec.append("</table>")
            schedule_sections.append("".join(sec))

    # ---- 淘汰赛对阵（八强模板）----
    ko_rows = ""
    ko_pairs = [("A1", "B2"), ("C1", "D2"), ("B1", "A2"), ("D1", "C2")]
    for i, (a, b) in enumerate(ko_pairs, 1):
        ko_rows += (f"<tr><td>QF{i}</td><td>{a}</td><td>VS</td><td>{b}</td>"
                    f"<td class='fill'>胜者</td><td>比分</td></tr>")

    # ---- 参赛名单（占位，报名确认后更新）----
    roster = """
      <table class='roster'>
        <tr><th>序号</th><th>队名/俱乐部</th><th>运动员名单（号码 姓名）</th><th>领队/教练</th><th>联系电话</th></tr>
    """
    for i in range(1, 9):
        roster += (f"<tr><td>{i}</td><td class='fill'>队伍{i}</td>"
                   "<td class='fill'></td><td></td><td></td></tr>")
    roster += "</table>"

    body = f"""
<div class="book">

  <!-- 封面 -->
  <section class="cover">
    <div class="cover-org">{esc(g(e,'organizer'))}</div>
    <div class="cover-title">{esc(g(e,'name'))}</div>
    <div class="cover-slogan">{esc(g(e,'slogan',''))}</div>
    <div class="cover-meta">
      <p>秩序册</p>
      <p>{esc(g(e,'date'))}</p>
      <p>{esc(g(v,'name'))}</p>
    </div>
  </section>

  <!-- 一 组织机构 -->
  <section>
    <h2>一、组织机构</h2>
    <table class='org'>{org_html}</table>
    <h3>赛事工作机构</h3>
    <table class='org'>
      <tr><th>竞赛组</th><td>负责赛程编排、裁判调度、成绩记录</td></tr>
      <tr><th>场地器材组</th><td>负责场地布置、器材保障与收尾</td></tr>
      <tr><th>安全医疗组</th><td>负责安全检查、现场急救与应急处置</td></tr>
      <tr><th>宣传接待组</th><td>负责影像拍摄、媒体接待与签到引导</td></tr>
      <tr><th>后勤保障组</th><td>负责餐饮、饮水、证书奖牌及物资</td></tr>
    </table>
  </section>

  <!-- 二 竞赛规程 -->
  <section>
    <h2>二、竞赛规程</h2>
    <h3>（一）比赛时间与地点</h3>
    <p>时间：{esc(date_time)}</p>
    <p>地点：{esc(g(v,'name'))} {esc(g(v,'address'))}</p>
    <h3>（二）参赛单位与规模</h3>
    <p>面向 {esc(g(p,'age_range','符合年龄要求'))} 的运动员，预计参赛 {esc(g(p,'athletes','—'))} 人、
       {esc(g(p,'teams','—'))} 队。</p>
    <h3>（三）竞赛项目与办法</h3>
    {''.join(rules_blocks)}
    <h3>（四）计分与晋级办法</h3>
    <p>{esc(g(e,'scoring','胜2分负1分；同积分先比相互战绩，再比净胜分。'))}</p>
    <p>{esc(g(e,'schedule_plan','各组单循环取前2名，交叉淘汰决出冠亚季军。'))}</p>
    <h3>（五）录取名次与奖励</h3>
    <p>{esc(g(e,'awards','各组别录取冠亚季军，颁发奖杯与证书。'))}</p>
    <h3>（六）报名与报到</h3>
    <p>报名费：{fee_str}。
       报名咨询 {esc(g(contact,'name',''))} 电话 {esc(g(contact,'phone',''))} 微信 {esc(g(contact,'wechat',''))}。
       各队于比赛开始前 30 分钟到签到处报到、核验身份。</p>
    <h3>（七）安全与纪律</h3>
    <ul>
      <li>参赛者须身体健康、适合参加本项目，签署健康承诺与风险告知；</li>
      <li>主办方统一为参赛人员购买赛事意外险；</li>
      <li>遵守赛场纪律、尊重裁判，服从工作人员安排；</li>
      <li>装备须符合各项目安全要求。</li>
    </ul>
    <h3>（八）其他</h3>
    <p>{esc(g(e,'extra','本规程解释权归主办方所有，未尽事宜另行通知。'))}</p>
  </section>

  <!-- 三 赛程总表 -->
  <section>
    <h2>三、赛程总表</h2>
    <table class='sched'>
      <tr><th>时间</th><th>项目/组别</th><th>内容</th><th>场地</th></tr>
      <tr><td>08:30</td><td>全部</td><td>签到、核验、领取号码</td><td>签到处</td></tr>
      <tr><td>09:00</td><td>各组</td><td>小组赛开始</td><td>1/2号场</td></tr>
      <tr><td>10:30</td><td>晋级队</td><td>交叉淘汰赛</td><td>1号场</td></tr>
      <tr><td>11:30</td><td>决赛队</td><td>决赛</td><td>1号场</td></tr>
      <tr><td>11:50</td><td>全部</td><td>颁奖、合影</td><td>主舞台</td></tr>
    </table>
    <p class='tip'>※ 上表为参考总表，具体时间以现场广播/裁判组通知为准。</p>
  </section>

  <!-- 四 分组与编排 -->
  <section>
    <h2>四、分组循环编排与积分表</h2>
    <p class='tip'>每组队伍数、队名为报名确认后更新；当前为占位编排，可直接在打印前填写或重新生成。</p>
    {''.join(schedule_sections)}
  </section>

  <!-- 五 淘汰赛 -->
  <section>
    <h2>五、淘汰赛对阵表</h2>
    <table class='ko'>
      <tr><th>场次</th><th>对阵</th><th></th><th></th><th>晋级</th><th>比分</th></tr>
      {ko_rows}
      <tr><td>SF1</td><td>QF1胜者</td><td>VS</td><td>QF2胜者</td><td class='fill'></td><td></td></tr>
      <tr><td>SF2</td><td>QF3胜者</td><td>VS</td><td>QF4胜者</td><td class='fill'></td><td></td></tr>
      <tr><td>决赛</td><td>SF1胜者</td><td>VS</td><td>SF2胜者</td><td class='fill'>冠军</td><td></td></tr>
    </table>
  </section>

  <!-- 六 参赛名单 -->
  <section>
    <h2>六、参赛队及运动员名单</h2>
    {roster}
  </section>

  <!-- 七 场馆信息 -->
  <section>
    <h2>七、场馆与服务信息</h2>
    <table class='org'>
      <tr><th>场地名称</th><td>{esc(g(v,'name'))}</td></tr>
      <tr><th>详细地址</th><td>{esc(g(v,'address','—'))}</td></tr>
      <tr><th>场地条件</th><td>{esc(g(v,'courts','—'))}</td></tr>
      <tr><th>场地联系</th><td>{esc(g(v,'contact','—'))}</td></tr>
    </table>
    <p class='tip'>请提前规划出行；现场设医疗点、饮水点与休息区，听从引导、注意安全。</p>
  </section>

</div>
"""

    css = """
  *{box-sizing:border-box;}
  body{margin:0;background:#9aa7b5;font-family:"PingFang SC","Microsoft YaHei",sans-serif;color:#222;}
  .book{max-width:820px;margin:0 auto;background:#fff;padding:40px 46px;}
  section{margin-bottom:18px;}
  h2{font-size:20px;color:#1a365d;border-left:7px solid #ed8936;padding-left:12px;margin:26px 0 14px;}
  h3{font-size:15.5px;color:#2c5282;margin:18px 0 8px;}
  h4{font-size:14.5px;color:#1a365d;margin:14px 0 6px;}
  p{margin:6px 0;font-size:14px;line-height:1.8;}
  ul{margin:6px 0;padding-left:22px;} li{font-size:14px;line-height:1.8;}
  table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px;}
  th,td{border:1px solid #b9c6d3;padding:7px 9px;text-align:left;vertical-align:middle;}
  th{background:#1a365d;color:#fff;font-weight:600;}
  .org th{width:120px;background:#2c5282;}
  .grp-title{background:#eaf0f6;color:#1a365d;font-weight:700;padding:8px 12px;border-radius:6px;
    margin:16px 0 8px;font-size:14px;}
  table.sched th,table.ko th{background:#2c5282;text-align:center;}
  table.sched td,table.ko td{text-align:center;}
  table.score{width:60%;} table.score th,table.score td{text-align:center;}
  .fill{background:#fbfcfe;}
  .tip{color:#8a94a3;font-size:12.5px;}
  .roster td:nth-child(3){text-align:left;}
  /* 封面 */
  .cover{height:1000px;display:flex;flex-direction:column;justify-content:center;
    align-items:center;text-align:center;border:3px solid #ed8936;padding:40px;}
  .cover-org{font-size:18px;color:#2c5282;letter-spacing:2px;}
  .cover-title{font-size:46px;font-weight:800;color:#1a365d;margin:40px 0 16px;line-height:1.35;}
  .cover-slogan{font-size:22px;color:#ed8936;margin-bottom:80px;}
  .cover-meta p{font-size:18px;color:#333;margin:10px 0;}
  /* 打印 */
  @media print{
    body{background:#fff;}
    .book{padding:0;max-width:none;}
    section{page-break-inside:avoid;}
    .cover{page-break-after:always;}
    h2{page-break-after:avoid;}
    table{page-break-inside:avoid;}
  }
"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>秩序册-{esc(g(e,'name'))}</title><style>{css}</style></head>
<body>{body}</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    e = load_info(args.info)
    htmlstr = build_html(e)
    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        base = os.path.dirname(os.path.abspath(args.info))
        out_path = os.path.join(base, "赛事秩序册.html")
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(htmlstr)
    print("PROGRAM:", out_path)


if __name__ == "__main__":
    main()
