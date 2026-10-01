# 赛事一站式筹办流水线 · Event Hosting SOP

一个面向小型体育赛事的 **Coze 技能（Skill）**，也是一套可独立运行的 Python 工具。按「信息采集 → 策划方案（确认）→ 宣传海报 + 报名系统 → 6 张执行表 → 赛事秩序册」五步，把一场小赛的筹办物料全部生成，纯本地运行、**不联网、无需密钥**。

适合篮球、足球、游泳、跆拳道、羽毛球、亲子运动会等各类群众性 / 青少年赛事，尤其适合几十到一两百人、半天时长的活动。

## ✨ 能生成什么

| 阶段 | 产物 |
|---|---|
| ① 信息采集 | 离线网页表单 `assets/信息采集表.html` → 导出 `赛事信息.json` |
| ② 策划方案 | `赛事策划方案.html`（概述 / 组织机构 / 赛制 / 倒排时间轴 / 预算拆分 / 安全） |
| ③ 海报 + 报名 | `赛事宣传海报.png`、`赛事报名登记系统.html`（含名单管理与 CSV 导出） |
| ④ 执行表 | `办赛实操工具包_6张表.xlsx`（预算 / 倒排工期 / 人员分工 / 物料 / 安全检查 / 赛后跟进）+ `办赛全流程时间轴.png` |
| ⑤ 秩序册 | `赛事秩序册.html`（封面 / 规程 / 赛程 / 单循环自动编排 / 淘汰对阵 / 名单，A4 打印导出 PDF） |

## 🚀 方式一：作为 Coze 技能使用

安装本技能后，在对话中直接描述需求，例如：

> 帮我办一场青少年篮球邀请赛，60 人 12 队，万象城中庭，预算 12000，10 月 25 日。

Agent 会先给你信息采集表、生成策划方案，确认后产出海报、报名系统、6 张表和秩序册。

## 💻 方式二：直接运行脚本

需要 Python 3，依赖：

```bash
pip install openpyxl matplotlib pillow
```

跑完整流水线：

```bash
cd scripts

# 1) 生成策划方案，先审阅
python run_pipeline.py --info ../examples/样例_篮球邀请赛.json

# 2) 确认方案后，生成海报+报名+6张表+秩序册
python run_pipeline.py --info ../examples/样例_篮球邀请赛.json --confirmed

# 只重跑某一阶段：plan / promo / kit / program / all
python run_pipeline.py --info <路径>/赛事信息.json --stage program
```

### 单独生成 6 张表（旧用法，无需 JSON）

```bash
python generate_kit.py --sport "篮球" --scale "60人" \
  --venue "商场中庭" --budget 12000 --date 2026-10-25 --out "办赛工具包_篮球"
```

## 📌 使用提示

- **报名系统**为单文件纯前端，名单存于本机浏览器，适合一台设备集中登记并导出 CSV；多人多设备实时汇总需另接后端。管理后台默认密码 `eh2026`。
- **秩序册**中队伍数 / 队名默认占位，报名确认后用真实信息重跑 `--stage program` 更新；浏览器内 Ctrl/Cmd + P 另存为 PDF。
- **海报**二维码为占位框，可把真实报名二维码贴入。
- 保险全员购买；安全检查不通过宁可延期；赛后 48 小时内必须跟进。

## 📁 目录结构

```
event-hosting-sop/
├── SKILL.md                 技能定义
├── assets/信息采集表.html    ① 信息采集表单
├── examples/                样例 赛事信息.json
└── scripts/
    ├── eh_common.py         公共库
    ├── build_plan.py        ② 策划方案
    ├── build_poster.py      ③ 海报
    ├── build_registration.py③ 报名系统
    ├── generate_kit.py      ④ 6张表+时间轴
    ├── build_program.py     ⑤ 秩序册
    └── run_pipeline.py      流水线串联器
```

## ⚠️ 免责声明

全部产物为运营参考模板，不构成法律或保险专业意见；报批、保险与场地要求以当地规定为准。

## 📄 License

[MIT](LICENSE)
