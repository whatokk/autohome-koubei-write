# -*- coding: utf-8 -*-
"""
口碑「口吻指纹」分析 —— 检验多篇之间【人设】之外，【写作口吻】是否也真的分开了

人设（地域/职业/家庭/前车）只是"谁在说"；口吻是"怎么说话"。
同一批口碑里 6 个人设如果都是同一种腔调，读者一眼就看出是一个模子写的。

本脚本把每篇的口吻拆成可量化维度：
  自称 · 语气助词 · 口头禅 · 方言/地域词 · 网络用语 · 句长 · 标点习惯 · 数字口语化 · 句子起手式

用法:
    python voice_fingerprint.py <口碑目录>
"""
import os
import re
import sys
import glob
import json
import statistics
import collections

# 口吻特征词典（可按车型/地域扩充）
DIM = {
    "自称": ["我", "咱", "俺", "本人", "自己"],
    "语气助词": ["吧", "呢", "嘛", "啊", "呀", "啦", "哈", "哟", "嘞", "呗", "咯", "哦", "诶", "喽"],
    "口头禅": ["真的", "说实话", "其实", "反正", "就是", "挺", "确实", "感觉", "基本上",
               "说白了", "讲真", "不瞒你说", "说白了", "有一说一", "讲道理"],
    # 注意：「老」（老车/老小区/老城区）、「搞」、「弄」是通用词，几乎所有篇都会用，
    # 留在表里只会产生噪音、把真实口吻差异冲淡，已剔除。
    # 同理「中」不作山东方言标记 —— 单字会命中「中控/中午/其中」，噪音更大。
    "方言地域": ["巴适", "安逸", "得劲", "忒", "贼", "倍儿", "耍", "俺们", "咱们",
                 "中不中", "得儿", "好正", "靓", "几好", "抵", "正嘢"],
    # 「秒」「直接」曾是本表成员，但会命中「零百7.3秒」「直接规划路线」这类普通中文，
    # 属误判，已剔除；只保留真正的网络化表达。
    "网络用语": ["真香", "绝了", "无语", "妥妥", "上头", "拉满", "拿捏", "破防", "秒杀", "秒变"],
    "数字口语化": ["一个礼拜", "礼拜", "半个月", "十来", "好几", "两千多", "小两千", "半个", "一箱", "一两"],
    "情绪标点": ["！", "？", "…", "——", "~"],
    "起手式": ["其实", "说", "要说", "先说", "反正", "我", "这车", "开", "提", "买"],
}


def body_of(path):
    s = open(path, encoding="utf-8").read()
    b = s.split("---\n")[-1]
    return b.split("\n", 1)[1] if "\n" in b else b


def analyze(txt):
    han = len(re.findall(r'[\u4e00-\u9fff]', txt))
    sents = [s.strip() for s in re.split(r'[。！？!?\n]', txt) if len(s.strip()) > 1]
    lens = [len(re.findall(r'[\u4e00-\u9fff]', s)) for s in sents]
    out = {
        "字数": han,
        "句数": len(sents),
        "平均句长": round(statistics.mean(lens), 1) if lens else 0,
        "句长离散度": round(statistics.pstdev(lens), 1) if len(lens) > 1 else 0,
        "最长句": max(lens) if lens else 0,
    }
    for k, words in DIM.items():
        hits = {w: txt.count(w) for w in words if txt.count(w)}
        out[k] = hits
        out[k + "_总数"] = sum(hits.values())
        out[k + "_密度"] = round(sum(hits.values()) / max(1, han) * 1000, 1)  # 每千字
    # 标点按千字归一化，否则长文天然标点多、会被误读成"口吻不同"
    out["情绪标点_密度"] = round(out["情绪标点_总数"] / max(1, han) * 1000, 1)
    # 句子起手式分布
    starts = collections.Counter(s[:2] for s in sents)
    out["高频起手"] = " ".join(f"{k}×{v}" for k, v in starts.most_common(5))
    return out


def main():
    root = sys.argv[1]
    files = sorted(f for f in glob.glob(os.path.join(root, "*.md"))
                   if os.path.basename(f)[:1].isdigit())
    rows = {os.path.basename(f): analyze(body_of(f)) for f in files}

    print("=== 口吻指纹逐篇 ===\n")
    # 展示维度（含字数，供人工看）
    keys = ["字数", "平均句长", "句长离散度", "自称_密度", "语气助词_密度", "口头禅_密度",
            "方言地域_密度", "网络用语_密度", "数字口语化_密度", "情绪标点_总数"]
    for n, r in rows.items():
        print(f"[{n}] " + " | ".join(f"{k.replace('_密度','')}={r[k]}" for k in keys))
        print(f"    自称 {r['自称']}")
        print(f"    语气助词 {r['语气助词']}")
        print(f"    方言/地域 {r['方言地域']}")
        print(f"    高频起手 {r['高频起手']}\n")

    # 计分维度：只取真正的「口吻」特征。
    # 特意排除「字数」—— 长短不同不等于口吻不同，把它算进来会得出错误结论。
    # 标点用千字密度而非总数，避免长文天然占优。
    VOICE = ["平均句长", "句长离散度", "语气助词_密度", "口头禅_密度", "方言地域_密度",
             "网络用语_密度", "数字口语化_密度", "情绪标点_密度"]

    print("=== 篇间口吻差异（越小越像；同批次建议 ≥3 个维度拉开）===")
    print("   计分维度：" + "、".join(v.replace("_密度", "") for v in VOICE) + "\n")
    names = list(rows)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra, rb = rows[a], rows[b]
            diffs = []
            for k in VOICE:
                va, vb = ra[k], rb[k]
                if va == 0 and vb == 0:
                    continue
                base = max(va, vb) or 1
                diffs.append(abs(va - vb) / base)
            score = round(statistics.mean(diffs), 3) if diffs else 0
            flag = "⚠ 口吻接近" if score < 0.35 else ("~ 一般" if score < 0.55 else "✓ 已分开")
            print(f"  {a} × {b}: {score}  {flag}")

    json.dump(rows, open(os.path.join(root, "_voice_fingerprint.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {os.path.join(root, '_voice_fingerprint.json')}")


if __name__ == "__main__":
    main()
