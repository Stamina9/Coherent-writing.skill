# DOCX 抽取契约

需要 Python 3.10+ 和 python-docx 1.2.x。安装：`python -m pip install -r requirements.txt`。
所有路径相对本技能目录解析；不需要 Word、网络或自动解密。支持常规未加密 OOXML DOCX。

`python scripts/extract_docx.py "论文.docx" --output-dir "private-work"`

成功退出 0，stdout 为唯一 UTF-8 JSON 文件绝对路径。输出默认在系统临时目录，
可明确指定私有工作目录；创建新随机文件，不覆盖任何已有文件，失败清理本次不完整输出。
结果包含论文全文，应使用有适当访问权限的目录；使用后删除本次产生的临时 JSON，保留用户需要的报告。
POSIX 临时文件使用限制性权限；Windows 继承目录 ACL，不承诺额外加密。

JSON schema_version=1.0：source、source_sha256、blocks、warnings、coverage。
blocks 中 P0、P1 是正文段落（包括空段落），T0 是表；表内 T0/R0C0/P0 为单元格段落，
嵌套表继续追加路径。顺序按 XML，表记录先于内部文本。单元格合并只输出一次内容并发出警告，
行列 ID 是定位锚点而非完整矩阵坐标。全文不截断，制表符/换行和超链接可见文字保留。
source_sha256 来自实际解析的同一份输入字节；再次抽取相同文件可复现相同 block ID。

Heading 支持 outline level、继承样式及 Heading/标题样式名；不自动把章节名映射到 IMRaD。
缺 Heading 发 NO_HEADINGS，文本仍可审查，按 section-policies 建立候选映射。
普通段落中的图题/表题文本照常输出，caption_candidate 仅是线索，不保证编号或配对正确。

## 可观测限制

- 图片、文本框、公式、内容控件、嵌入对象、修订、域遇到时给定位警告；不解析图片含义，
  不决定接受/拒绝修订，不把域缓存当作已重新计算。
- 页眉页脚、脚注尾注和批注存在的包部件会列在 excluded_parts 中；不读取其文本。
- 不提供页码、浮动图实际位置、视觉阅读顺序或引用真实性；不展开样式继承的所有自动编号。
- coverage.status 为 text-only 或 partial，永远不是“全文全部对象已读”。即使没有警告，
  coverage.limitations 仍适用。依据图、脚注或公式的结论须补充人工核对。

## 错误

| 退出码 | 机器可读前缀 | 处理 |
| --- | --- | --- |
| 2 | argparse usage error | 更正 CLI 参数 |
| 3 | MISSING_DEPENDENCY / DEPENDENCY_VERSION | 在同一 Python 环境安装 requirements.txt |
| 4 | INVALID_DOCX / ENCRYPTED_OR_LEGACY / ENCRYPTED_DOCX | 提供干净、未加密 DOCX；OLE 只能提示可能加密或旧格式，不能确诊 |
| 4 | PACKAGE_LIMIT / EMPTY_TEXT | 减小文件或提供可读文本；不继续空报告 |
| 5 | INPUT_IO / OUTPUT_IO | 检查路径和权限 |

资源上限为压缩输入 128 MiB、声明的解压总量 256 MiB、10000 ZIP entries；超过则停止，
不解包到磁盘、不执行宏、不请求外部关系。损坏 XML 返回清楚错误且不输出原稿内容到错误消息。
