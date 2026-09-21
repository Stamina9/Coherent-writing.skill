# Coherent Academic Writing

面向中文学术论文的章节边界与证据保真审查技能。保留摘要、引言、方法、结果、讨论、
结构一致性六项检查，并增加主张与证据匹配、防御性措辞审查和获批后的最小改写。
它帮助明确论证，不通过删除必要限制或负面结果让结论显得更强。

## 模式与调用

| 模式 | 工作范围 |
| --- | --- |
| `boundary-audit`（默认） | 六项章节边界检查，可限定章节 |
| `stance-audit` | REMOVE / REFRAME / RETAIN / NARROW_CLAIM / ESCALATE_TO_AUTHOR |
| `full-audit` | 结构与措辞两类审查 |
| `rewrite-approved` | 仅实施已批准的具体提案，并执行 evidence-integrity audit |

Codex 示例：

```text
使用 $coherent-academic-writing，以 boundary-audit 审查 /path/to/论文.docx，
重点检查方法章的论证功能。学科为材料科学，文章类型为研究论文。先给报告。
```

Claude Code 示例：

```text
/coherent-academic-writing 用 full-audit 审查 /path/to/论文.docx。
这是定性研究，结果和讨论合并。按作者的结构判断，不套用固定 IMRaD。
```

自然语言也可触发：“检查这篇中文论文的章节边界和防御性表达，保留负面结果及必要限制”。
默认保留自动发现；`agents/openai.yaml` 未关闭 implicit invocation。

## 安装

安装单位是 **整个 `skills/coherent-academic-writing/` 文件夹**，不是仓库根目录或单个 SKILL.md。
Python 仅在抽取 DOCX 时需要；带定位文本可直接审查。

先克隆并安装抽取依赖（建议在你的虚拟环境内）：

```sh
git clone https://github.com/Stamina9/Coherent-writing.skill.git
cd Coherent-writing.skill
python -m pip install -r skills/coherent-academic-writing/requirements.txt
```

把完整技能文件夹复制到下列任一位置，保留目录名 `coherent-academic-writing`：

| 客户端 | 用户级安装 | 当前项目安装 |
| --- | --- | --- |
| Codex | `~/.agents/skills/coherent-academic-writing/` | `.agents/skills/coherent-academic-writing/` |
| Claude Code | `~/.claude/skills/coherent-academic-writing/` | `.claude/skills/coherent-academic-writing/` |

macOS/Linux 用户级 Codex 安装示例（已存在则先检查更新差异，不直接覆盖）：

```sh
mkdir -p ~/.agents/skills
test ! -e ~/.agents/skills/coherent-academic-writing && cp -R skills/coherent-academic-writing ~/.agents/skills/
```

Windows PowerShell 用户级 Codex 安装示例：

```powershell
$skillTarget = Join-Path $HOME '.agents/skills/coherent-academic-writing'
if (Test-Path -LiteralPath $skillTarget) { throw '目标已存在，请先检查现有版本再更新。' }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $skillTarget) | Out-Null
Copy-Item -Recurse -LiteralPath 'skills/coherent-academic-writing' -Destination $skillTarget
```

Claude Code 将以上目标的 `.agents` 换成 `.claude`。项目安装使用表中项目路径。
若客户端未立即发现技能，重启会话后通过技能选择器确认。
路径依据：[Codex 官方技能文档](https://developers.openai.com/zh-Hans/docs/build-skills)、
[Claude Code 官方技能文档](https://code.claude.com/docs/en/skills)（核对于 2026-09-20）。

### 从 coherent 1.x 迁移

旧入口 `coherent` 改为 `coherent-academic-writing`，仓库根目录不再提供可安装 SKILL.md。
检查旧 `.claude/skills/coherent` 或 Codex 技能目录，保留个人修改备份，再将旧技能移出发现目录，
避免两套规则同时生效。不要把旧“疑罪从有”、句数阈值或强制主语规则带入新版本。
仓库不自动删除或修改已有安装。`metadata` 保存 author/version；为兼容旧版 skill-creator
quick_validate，兼容性说明放在 `metadata.compatibility`，而非可选顶层 compatibility。
该包装仍符合 [Agent Skills 规范](https://agentskills.io/specification) 的 metadata 字符串映射。

## 分阶段 prompt

第一阶段：

```text
使用 coherent-academic-writing 的 stance-audit。
先列每个问题的定位、原文、证据、决策、最小修改提案和未决作者问题。
不要写回原稿。若证据不足，明确标 unknown，不补数据或机制。
```

第二阶段（以实际报告 ID 和源版本替换示例）：

```text
对刚才报告的源版本，批准 C001 的删赘语和 C004 的缩小主张，其他项不改。
用 rewrite-approved，最小修改并另存 paper.revised.docx。
给出逐项 before/after 和 evidence-integrity audit，不覆盖 paper.docx。
```

已有明确批准不会被重复询问；泛泛的润色请求不视为批准尚未审阅的具体方案。
审查阶段只交付报告与提案；改写阶段默认另存副本，覆盖原稿需要明确授权和备份。

## 抽取与支持范围

```sh
python skills/coherent-academic-writing/scripts/extract_docx.py "论文.docx" --output-dir "private-work"
```

成功时输出唯一 JSON 路径，包含完整段落、正文顺序、递归表格文本、样式、候选图题、
block ID、原稿 SHA-256 和覆盖警告。原稿不变。临时 JSON 含论文全文，使用后按需要清理。
无 Heading 时保留原文并提示候选映射；非标准章节、合并结果/讨论、理论与综述可使用不同 profile。

范围：常规未加密 DOCX、中文论文和带定位文本；脚本不翻译、不做统计复算、文献真实性验证、
PDF OCR 或格式修复。图像、公式、文本框、修订、域、页眉页脚和注释可能不完整，不能将抽取成功
等同于视觉全文核验。遇到依赖遗漏内容的主张，暂停该项并补充核对；加密/损坏文件给出错误，
不会猜测正文。DOCX 改写依赖宿主可用的编辑能力，抽取器不提供自动写回。
详见 [抽取契约](skills/coherent-academic-writing/references/extraction.md)。

## 开发与验证

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m compileall -q skills tests
git diff --check
# 使用本机 skill-creator 的实际路径：
python /path/to/skill-creator/scripts/quick_validate.py skills/coherent-academic-writing
```

CI 在 Windows/Linux、Python 3.10/3.12 上运行包结构检查和抽取测试，不依赖机器私有的 quick_validate
路径，也不调用付费模型。生成的 DOCX fixtures 仅留在测试临时目录。
[行为评测](evals/README.md)另行检查删改的语义不变量；自动化单元测试通过不代表模型行为必然正确。

```text
skills/coherent-academic-writing/
  SKILL.md                 精简入口与模式路由
  LICENSE, NOTICE.md        可独立分发的许可与来源
  agents/openai.yaml       UI 信息；自动发现保持默认
  requirements.txt         DOCX 抽取依赖
  scripts/extract_docx.py  只读抽取器
  references/              边界、证据、profile、输出、抽取与改写细则
tests/                     可观察抽取与包装不变量
evals/                     合成行为用例与人工评分标准
.github/workflows/         持续集成
```

## 许可与来源

MIT，Copyright (c) 2026 Stamina9。原技能署名 MS-MDA project 保留在 metadata 和来源说明中。
anti-defensive-writing 及其 PR #2 仅提供概念参考，本项目重新编写规则，保留必要限制与负面证据。
详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE.md)。
