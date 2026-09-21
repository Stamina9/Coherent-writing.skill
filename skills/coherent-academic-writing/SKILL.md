---
name: coherent-academic-writing
description: >-
  审查中文学术论文 DOCX 或带定位的论文文本的章节边界、重复内容及主张与证据是否匹配，
  识别不必要的防御性表达，并在审查方案获批后进行最小改写。用于投稿前结构自查、
  章节越界检查和证据保真的措辞审查；不用于通用文案润色、代写研究结果、文献真实性核验或排版修复。
license: MIT
metadata:
  author: "Stamina9 (original skill attribution: MS-MDA project)"
  version: "2.0.0"
  compatibility: "Codex / Claude Code / Agent Skills clients; DOCX extraction requires Python 3.10+ and python-docx 1.2.x; local files only, no network required."
---

# 证据保真的学术连贯性审查

让章节服务于论证，让措辞强度与证据一致。保留六项边界审查，但将关键词、句长、
数字密度、主语和相似度视为定位线索，不能据此自动判违规。尊重学科、文章类型和投稿要求。

## 选择模式

| 模式 | 适用请求 | 按需读取 |
| --- | --- | --- |
| `boundary-audit` | 章节规范性、重复、结构；未指定模式时默认 | [section-boundaries](references/section-boundaries.md) |
| `stance-audit` | 防御性措辞、过强主张、必要限制 | [evidence-faithful-confidence](references/evidence-faithful-confidence.md) |
| `full-audit` | 明确要求结构与措辞全面审查 | 上述两份 |
| `rewrite-approved` | 已批准具体审查方案的改写 | 上述相关维度及 [rewrite](references/rewrite.md) |

所有模式读取 [section-policies](references/section-policies.md) 确定适用 profile，
按 [output-contract](references/output-contract.md) 输出。不要把一次局部审查扩成全文重写。

## 不可跨越的证据边界

- 为涉及修改的主张关联可定位的原文、表格或作者提供的证据；区分观测、解释、假设及未知。
- 不得创造或擅改数字、单位、分母、数据集、引用、显著性、置信区间、机制或实验。
  未提供的材料标为未核验；不能将“未检出差异”改成“等效”，不能把相关性写成因果。
- 必要限制、统计不确定性、适用范围、必要比较及影响核心结论的负面结果必须保留。
  若主张与之冲突，缩小主张；不通过换指标、藏入附录或删掉对照制造优势。
- 允许删去无信息的道歉或自我贬低；“仅”“可能”“未能”等不是禁词。
  任何改写都先判断删词是否改变事实、范围、强度或读者对结论的理解。
- 缺证据时提出作者问题，不补造“合理原因”；未知不等于违规。

## 输入与抽取

接收 DOCX 路径，或带稳定段落定位的论文文本。记录模式、审查范围、venue、article type、
discipline、用户已确认的章节映射及修改授权。缺少 profile 时采用临时假设并标明，
可先做不依赖 profile 的检查，不反复索取不必要信息。

DOCX 使用本技能目录下的脚本（相对路径需从技能目录解析）：

```sh
python scripts/extract_docx.py /path/to/paper.docx --output-dir /path/to/private-work
```

依赖见 [requirements.txt](requirements.txt)。脚本只读原稿，在指定目录创建唯一 JSON，
stdout 仅返回结果路径；失败时 stderr 提供错误码与处理建议。不要上传论文或覆盖原稿。
读取完整 `blocks`、`warnings` 和 `coverage`，不可截断段落后宣称全文审查。
详细定位、退出码与覆盖限制见 [extraction](references/extraction.md)。

## 两阶段工作流

1. **审查**：先确认抽取覆盖范围及章节映射，再执行所选模式。为问题提供原文定位、
   证据和 profile 依据、影响、置信度及最小建议。审查阶段只输出报告和建议片段；
   不写回原稿，也不生成声称已获批准的修订稿。
2. **获批后改写**：把已批准的问题 ID、范围和来源版本与现有授权对应；已有明确授权不再重复询问。
   模糊的“润色一下”或新材料不是对具体方案的批准。未批准项保留在报告中。
   默认最小修改并另存副本；覆盖原稿还须用户明确要求该路径且先保留可恢复备份。
   按 rewrite 参考执行修改后 evidence-integrity audit，失败则撤销对应修改并报告阻塞。

抽取失败、证据缺失或章节映射不确定时，限制结论到已核验内容，按 profile 的停止条件处理。
不得将部分抽取、尚未执行的实验或尚未核验的引用写成已完成检查。
