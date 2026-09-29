# 汽车之家口碑写作

汽车之家「车主口碑」写作流水线——按官方配置数据写、写完逐项核对、满级精华风格、9 个小点全模板。

## 技能清单

| 技能 | 说明 |
|---|---|
| **autohome-koubei-write** · 口碑写作流水线 | **第一原则：汽车之家 ≠ 懂车帝，两套口径不能混。** 9 个小点全写、800-1100 字长文、不轮换模板、必须以官方配置页数据为写作依据并逐项核对。 |

## 安装

把 `skills/` 下的技能目录拷贝到 WorkBuddy 的技能目录：

```bash
cp -r skills/* ~/.workbuddy/skills/
```

Windows PowerShell：

```powershell
Copy-Item .\skills\* "$env:USERPROFILE\.workbuddy\skills\" -Recurse -Force
```

重启 WorkBuddy 后，技能列表即可看到。

## 使用要点

- 内置四套脚本：`build_factbase.py`（构建车型事实库）、`check_against_config.py`（与官方配置核对）、`dedup_check.py`（多篇去重）、`voice_fingerprint.py`（口吻指纹，保证人设互异）。
- 触发词：汽车之家口碑、满级精华、按官方配置写、核对配置、9个小点、不同人设、不同口吻。
- **不适用**于懂车帝——那是 2-3 小点短篇口径，走 `koubei-pipeline-suite`。

## 环境依赖

- Python 3.13

## 目录规范

```
autohome-koubei-write/
└── skills/
    ├── autohome-koubei-write/
```

每个技能遵循统一结构：`SKILL.md`（必需，含 name/description frontmatter）+ `scripts/`（可选）+ `references/`（可选）。

---

## License

MIT — 随意取用、修改、二次分发。
