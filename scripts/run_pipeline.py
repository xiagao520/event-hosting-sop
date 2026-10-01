# -*- coding: utf-8 -*-
"""赛事全流程流水线串联器。

阶段：
  form      信息采集表（静态页，路径提示，无需运行）
  plan      ② 赛事策划方案  └─ 确认关卡 ─┐
  promo     ③ 海报 + 报名登记系统         │（plan 确认后）
  kit       ④ 6 张执行表 + 时间轴         │
  program   ⑤ 赛事秩序册                  ┘

用法：
  # 第一步：仅生成策划方案，交用户确认
  python run_pipeline.py --info 赛事信息.json
  # 用户确认方案后，生成海报+报名+6张表+秩序册
  python run_pipeline.py --info 赛事信息.json --confirmed
  # 只重跑某一阶段
  python run_pipeline.py --info 赛事信息.json --stage program
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(mod, info, out_name):
    cmd = [sys.executable, os.path.join(HERE, mod), "--info", info]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {mod}\n{r.stderr}", file=sys.stderr)
        return None
    line = next((l for l in r.stdout.splitlines() if ":" in l), "")
    return line.split(":", 1)[1].strip() if line else "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True, help="赛事信息.json")
    ap.add_argument("--confirmed", action="store_true",
                    help="用户已确认策划方案，继续生成后续物料")
    ap.add_argument("--stage", default="",
                    choices=["plan", "promo", "kit", "program", "all"],
                    help="只运行指定阶段")
    args = ap.parse_args()

    info = os.path.abspath(args.info)
    base = os.path.dirname(info)
    produced = {}

    def do_plan():
        produced["策划方案"] = run("build_plan.py", info, "plan")

    def do_promo():
        produced["宣传海报"] = run("build_poster.py", info, "poster")
        produced["报名系统"] = run("build_registration.py", info, "reg")

    def do_kit():
        # generate_kit 默认输出到信息同目录/办赛工具包
        cmd = [sys.executable, os.path.join(HERE, "generate_kit.py"), "--info", info]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
        for l in r.stdout.splitlines():
            if l.startswith("XLSX:"):
                produced["6张表"] = l.split(":", 1)[1].strip()
            if l.startswith("PNG:"):
                produced["时间轴"] = l.split(":", 1)[1].strip()

    def do_program():
        produced["秩序册"] = run("build_program.py", info, "program")

    # 单阶段模式
    if args.stage:
        {"plan": do_plan, "promo": do_promo, "kit": do_kit,
         "program": do_program, "all": lambda: [do_plan(), do_promo(), do_kit(), do_program()]
         }[args.stage]()
    elif args.confirmed:
        do_promo(); do_kit(); do_program()
    else:
        # 默认：先出策划方案，停在确认关卡
        do_plan()
        print("GATE: 策划方案已生成，请用户审阅确认；确认后加 --confirmed 继续。")

    for k, v in produced.items():
        if v:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
