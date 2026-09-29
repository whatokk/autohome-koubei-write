# -*- coding: utf-8 -*-
"""
口碑文案 × 官方配置 核对脚本（汽车之家写作流水线的强制收尾步骤）

作用：把写完的口碑 Markdown 逐篇扫一遍，比对一个「配置声明字典」，
     把每个数字/术语标成：
       OK    与官方一致
       ERR   与官方冲突（必须改）
       MED   属媒体口径（官方配置页查不到，可保留但不要写成"官方/标配"）
       SEL   选装项被写成了标配（本车型高频翻车点）

用法:
    python check_against_config.py <口碑目录或md文件> <规则json>

规则 json 结构（见 references/核对规则示例.json）：
{
  "specname": "...",
  "ok":   [{"pat": "675公里", "note": "CLTC 675km"}],
  "err":  [{"pat": "12\\.3寸", "fix": "10.25寸", "note": "液晶仪表官方 10.25 英寸"}],
  "med":  [{"pat": "1000V", "note": "电压仅见媒体稿，官方配置页无"}],
  "sel":  [{"pat": "帝瓦雷音响(都有|都给到)", "fix": "帝瓦雷是 6000 元选装", "note": "..."}]
}
"""
import os
import re
import sys
import glob
import json


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    target, rulefile = sys.argv[1], sys.argv[2]
    rules = json.load(open(rulefile, encoding="utf-8"))

    files = sorted(glob.glob(os.path.join(target, "*.md"))) if os.path.isdir(target) else [target]
    files = [f for f in files if os.path.basename(f)[:1].isdigit()] or files

    tot = {"OK": 0, "ERR": 0, "MED": 0, "SEL": 0}
    print(f"=== 核对规则：{rules.get('specname','')} ===\n")
    for f in files:
        txt = open(f, encoding="utf-8").read()
        hits = []
        for kind in ("ok", "err", "med", "sel"):
            for r in rules.get(kind, []):
                for m in re.finditer(r["pat"], txt):
                    hits.append((kind, m.group(0), r.get("note", ""), r.get("fix", "")))
        c = {k: 0 for k in tot}
        for kind, *_ in hits:
            c[kind.upper() if kind != "ok" else "OK"] += 1
        for k in tot:
            tot[k] += c[k]
        flag = "✗ 有问题" if c["ERR"] or c["SEL"] else ("△ 待确认" if c["MED"] else "✓ 通过")
        print(f"[{os.path.basename(f)}] {flag}  OK {c['OK']} / ERR {c['ERR']} / 选装误写 {c['SEL']} / 媒体口径 {c['MED']}")
        for kind, s, note, fix in hits:
            if kind == "ok":
                continue
            tag = {"err": "✗ 错误", "sel": "✗ 选装误写", "med": "△ 媒体口径"}[kind]
            print(f"    {tag}：「{s}」{(' → 应改为 ' + fix) if fix else ''}　{note}")

    print(f"\n=== 合计 OK {tot['OK']} / ERR {tot['ERR']} / 选装误写 {tot['SEL']} / 媒体口径 {tot['MED']} ===")
    if tot["ERR"] or tot["SEL"]:
        print("→ 存在硬伤，必须修完再交付")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
