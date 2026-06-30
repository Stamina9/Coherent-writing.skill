# Coherent-writing.skill

> "Let's turn an AI-written paper that's fragmented, redundant, repetitive, and logically chaotic into something coherent!"

## 简介

`coherent` 是一个 Claude Code skill，用于对**中文学术论文（DOCX）**进行逐章逐节的**内容边界规范性审查**。

核心标准：**每个章节只写该章应有之内容，不越界、不混杂、不重复。**

## 六项检查维度

| # | 检查维度 | 核心红线 |
|---|---------|---------|
| 1 | 摘要 | 不写别人问题、不出现引用标记 |
| 2 | 引言 | 不越界到方法实现细节 |
| 3 | 方法章 | 每段开头主语是"我们提出"，不是"已有方法" |
| 4 | 结果章 | 纯粹报告结果，不重复解释方法 |
| 5 | 讨论章 | 讨论意义，不复述结果数据 |
| 6 | 结构一致性 | 无重复章节、无 TODO 残留、编号连续 |

## 安装

克隆到 Claude Code 项目的 `.claude/skills/coherent/` 目录，或直接将 `SKILL.md` 放入该目录即可。

## 使用

- 全面审查：「帮我审查论文的章节规范性」
- 专项审查：「只查方法章有没有写别人问题」

## 作者

Stamina9
