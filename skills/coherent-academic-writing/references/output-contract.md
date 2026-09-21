# 输出契约

报告可用 Markdown 或用户要求的格式，但必须包含以下信息。无问题时明确写无已确认问题，
不要为凑数制造建议；检查未覆盖的部分仍需报告。

1. **范围与状态**：mode、来源文件及 SHA-256（文本输入则记录版本/标识）、profile、授权范围；
   抽取覆盖/警告、已查与未查范围，结论状态 complete-within-scope / partial / blocked。
2. **结构图**：原章节名、功能映射、起止 block ID、Heading/推断依据及 confirmed/inferred/unknown。
   非结构审查可仅列涉及段落，未知边界不得伪造。
3. **问题记录**：稳定 ID（如 C001）、维度、定位与足量原文、观察事实、依据或显式假设、
   影响、severity（high/medium/low）、confidence（high/medium/low）、主张及证据定位、
   建议与理由、需作者确认项。缺证据标 unknown；保留证据也可以是一条无须修改的记录。
4. **stance 决策**：每项明确使用 REMOVE / REFRAME / RETAIN / NARROW_CLAIM /
   ESCALATE_TO_AUTHOR 之一；不同片段分项。boundary 问题使用 MOVE / DEDUPLICATE /
   RETAIN / VERIFY，不强塞 stance 分类。建议片段标“提案”，不算已经修改。
5. **行动与审批清单**：按影响列出 ID、最小变更、未决证据、可批准范围；记录批准、拒绝和待定，
   不把作者沉默视为同意。优先处理证据失真，再处理结构，最后处理无害措辞。
6. **改写模式附加项**：批准记录与源版本、输出路径、逐项 before/after 和移动映射、
   evidence-integrity audit 的 pass/fail/blocked 及核验范围，未应用项及原因。

“complete-within-scope”仅指约定范围全部核验，不能替代统计复算、文献真实性审查或同行评审。
单纯词语/样式线索不自动产生 high severity；信心不足时用待核实而非违规指控。
