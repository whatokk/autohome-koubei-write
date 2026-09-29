# -*- coding: utf-8 -*-
"""
汽车之家「官方配置事实库」生成器（唯一写作依据）

2026-09-24 摸清的完整取数路径（前两次都踩空了，务必照此）：
  1. 用**车系配置页** `car.autohome.com.cn/config/series/<seriesid>.html`
     （单配置页 config/spec/<specid>.html **只有 paramtypeitems，没有配置项**）
  2. 页面内嵌三个 JSON：
     · `var config` → result.paramtypeitems   （参数）
     · `var option` → result.configtypeitems  （配置）
     · `var bag`    → result.bagtypeitems     （选装包）
  3. **真正的值不在 value 里，在 sublist 里**：
     · `value` 只有 ●/○ 这类开关项；文本型项目 value 是空串
     · `sublist[] = [{subname, subvalue, price}]`
       - subvalue=1 → 标配
       - subvalue=2 → **选装**（price 是选装价，单位元；0 表示包含在包内）
     · 只读 value 会得到一大片空白，误判成"官方没这配置"
  4. **反爬缺字**：页面把部分汉字换成空 span `<span class='hs_kwN_xxx'></span>`，
     item.name 会残缺（如「厂()」）。用 `var keyLink = [{id, name}]` 按 id 还原完整名称。
  5. ●/○ → 有/无；&nbsp; → 空格

用法:
  python build_factbase.py <车系配置页HTML> <seriesid> <specid> <输出md>
"""
import re
import sys
import json

KW = re.compile(r"hs_kw\d+_\w+")


def extract_var(html, varname):
    i = html.find(f'var {varname} = ')
    if i < 0:
        i = html.find(f'var {varname}=')
    if i < 0:
        return None
    lb, rb = html.find('{', i), html.find('[', i)
    if lb < 0 or (0 <= rb < lb):
        j = rb
    else:
        j = lb
    depth, k, instr, esc = 0, j, False, False
    while k < len(html):
        c = html[k]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c in '{[':
                depth += 1
            elif c in '}]':
                depth -= 1
                if depth == 0:
                    break
        k += 1
    try:
        return json.loads(html[j:k + 1])
    except Exception as e:
        print("JSON FAIL", varname, e, file=sys.stderr)
        return None


def clean(s):
    s = re.sub(r'<[^>]+>', '', str(s))
    s = s.replace('&nbsp;', ' ').replace('●', '有').replace('○', '无')
    return " ".join(s.split()).strip()


def render(vitem):
    """把一个 valueitem 渲染成人话；返回 (文本, 是否选装, 选装价)"""
    parts, optional, price = [], False, 0
    v = clean(vitem.get("value"))
    if v:
        parts.append(v)
    for s in vitem.get("sublist") or []:
        nm = clean(s.get("subname"))
        if not nm:
            continue
        sv, pr = s.get("subvalue"), s.get("price") or 0
        if sv == 2 or pr:
            optional = True
            price = max(price, pr)
            parts.append(f"{nm}【选装" + (f"，{pr}元" if pr else "") + "】")
        else:
            parts.append(nm)
    return " / ".join(parts), optional, price


def main():
    html = open(sys.argv[1], "rb").read().decode("utf-8", "ignore")
    seriesid, specid, out = sys.argv[2], sys.argv[3], sys.argv[4]

    cfg = (extract_var(html, "config") or {}).get("result", {})
    opt = (extract_var(html, "option") or {}).get("result", {})
    bag = (extract_var(html, "bag") or {}).get("result", {})
    idname = {str(k.get("id")): clean(k.get("name")) for k in (extract_var(html, "keyLink") or [])}

    specname = ""
    for s in (cfg.get("speclist") or opt.get("speclist") or []):
        if str(s.get("specid")) == str(specid):
            specname = clean(s.get("specname"))

    L = [f"# 官方配置事实库 —— {specname}",
         f"\n- specid `{specid}` ／ seriesid `{seriesid}`",
         f"- 来源：汽车之家车系配置页 `car.autohome.com.cn/config/series/{seriesid}.html`",
         "\n> **本文件是写口碑的唯一事实依据。写前先读，写完逐项核对。**",
         "> 标注【选装】的项**不能**写成标配；数值一律以本文件为准，不得凭印象或媒体稿改写。",
         "\n## 选装 / 加价项（写作红线，最容易写错）\n"]

    opt_rows, all_rows = [], []
    for src in (cfg, opt, bag):
        for key, tag in (("paramtypeitems", "参数"), ("configtypeitems", "配置"),
                         ("featureitems", "配置"), ("bagtypeitems", "选装包")):
            for grp in src.get(key) or []:
                gname = clean(grp.get("name"))
                for it in (grp.get("paramitems") or grp.get("configitems")
                           or grp.get("bagitems") or []):
                    vt = None
                    for v in it.get("valueitems") or []:
                        if str(v.get("specid")) == str(specid):
                            vt = v
                            break
                    if vt is None:
                        continue
                    nm = idname.get(str(it.get("id"))) or clean(it.get("name"))
                    if not nm:
                        continue
                    txt, isopt, price = render(vt)
                    if not txt:
                        continue
                    all_rows.append((tag, gname, nm, txt, isopt, price))
                    if isopt:
                        opt_rows.append((gname, nm, txt, price))

    for gname, nm, txt, price in opt_rows:
        L.append(f"- **{nm}**：{txt}" + (f"  ← 选装价 {price} 元" if price else ""))
    if not opt_rows:
        L.append("- （无）")

    L.append("\n## 全量配置明细\n")
    cur = None
    for tag, gname, nm, txt, isopt, price in all_rows:
        head = f"{tag} · {gname}"
        if head != cur:
            L.append(f"\n### {head}")
            cur = head
        L.append(f"- {nm}：{txt}")

    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"-> {out}")
    print(f"[统计] 条目 {len(all_rows)} 条，其中选装/加价 {len(opt_rows)} 条")


if __name__ == "__main__":
    main()
