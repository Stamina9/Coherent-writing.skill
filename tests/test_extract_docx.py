import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/coherent-academic-writing/scripts/extract_docx.py"
SPEC = importlib.util.spec_from_file_location("extract_docx", SCRIPT)
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.source = self.directory / "论文.docx"

    def tearDown(self):
        self.temp.cleanup()

    def save(self, doc):
        doc.save(self.source)
        return extractor.extract_docx(self.source)

    def codes(self, result):
        return {w["code"] for w in result["warnings"]}

    def test_full_text_order_tables_and_source_unchanged(self):
        doc = Document()
        doc.add_heading("发现与解释", 1)
        long_text = "仅在本样本中成立，负面结果仍需报告。" * 80
        doc.add_paragraph(long_text)
        table = doc.add_table(rows=2, cols=2)
        for cell, value in zip([c for r in table.rows for c in r.cells], ["组别", "效应", "干预组", "−2.1 (95% CI −3.2 至 −1.0)"]):
            cell.text = value
        doc.add_paragraph("表1 全部结果", style="Caption")
        doc.add_paragraph("")
        doc.add_paragraph("尾段\t含制表符\n以及换行")
        doc.save(self.source)
        before = self.source.read_bytes()
        result = extractor.extract_docx(self.source)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(result["source_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(result["blocks"][1]["text"], long_text)
        self.assertEqual(result["blocks"][2]["id"], "T0")
        self.assertEqual(result["blocks"][6]["text"], "−2.1 (95% CI −3.2 至 −1.0)")
        self.assertEqual(result["blocks"][7]["id"], "P2")
        self.assertTrue(result["blocks"][7]["caption_candidate"])
        self.assertEqual(result["blocks"][-1]["text"], "尾段\t含制表符\n以及换行")
        self.assertEqual(result, extractor.extract_docx(self.source))

    def test_nonstandard_heading_and_inherited_outline(self):
        doc = Document()
        style = doc.styles.add_style("Local section", WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = doc.styles["Heading 2"]
        doc.add_paragraph("命题与证明", style=style)
        normal = doc.add_paragraph("自定义章节")
        outline = OxmlElement("w:outlineLvl")
        outline.set(qn("w:val"), "0")
        normal._p.get_or_add_pPr().append(outline)
        result = self.save(doc)
        self.assertEqual([b["heading_level"] for b in result["blocks"]], [2, 1])
        self.assertNotIn("NO_HEADINGS", self.codes(result))

    def test_no_heading_preserves_candidate_text(self):
        doc = Document()
        doc.add_paragraph("3 发现与解释")
        doc.add_paragraph("仅适用于已测试条件。")
        result = self.save(doc)
        self.assertIn("NO_HEADINGS", self.codes(result))
        self.assertTrue(all(b["heading_level"] is None for b in result["blocks"]))
        self.assertEqual(result["blocks"][0]["text"], "3 发现与解释")

    def test_nested_and_merged_tables_keep_unique_content(self):
        doc = Document()
        table = doc.add_table(rows=1, cols=2)
        merged = table.cell(0, 0).merge(table.cell(0, 1))
        merged.text = "合并证据"
        merged.add_table(rows=1, cols=1).cell(0, 0).text = "嵌套反例"
        result = self.save(doc)
        texts = [b.get("text") for b in result["blocks"]]
        self.assertEqual(texts.count("合并证据"), 1)
        self.assertEqual(texts.count("嵌套反例"), 1)
        self.assertEqual(result["coverage"]["table_count"], 2)
        self.assertIn("IRREGULAR_TABLE", self.codes(result))
        ids = [b["id"] for b in result["blocks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_hyperlink_visible_text(self):
        doc = Document()
        para = doc.add_paragraph("证据见")
        link = OxmlElement("w:hyperlink")
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = "附录 A"
        run.append(text)
        link.append(run)
        para._p.append(link)
        self.assertEqual(self.save(doc)["blocks"][0]["text"], "证据见附录 A")

    def test_incomplete_objects_are_observable(self):
        doc = Document()
        p = doc.add_paragraph("可读取正文")
        p._p.append(OxmlElement("w:ins"))
        p._p.append(OxmlElement("m:oMath"))
        p._p.append(OxmlElement("w:drawing"))
        p._p.append(OxmlElement("w:txbxContent"))
        p._p.append(OxmlElement("w:fldSimple"))
        doc.element.body.append(OxmlElement("w:sdt"))
        doc.sections[0].header.paragraphs[0].text = "页眉证据"
        result = self.save(doc)
        self.assertTrue({"DRAWING_NOT_EXTRACTED", "TEXTBOX_NOT_EXTRACTED", "MATH_NOT_EXTRACTED",
                         "REVISIONS_NOT_RESOLVED", "FIELD_NOT_EVALUATED", "PART_NOT_EXTRACTED",
                         "CONTENT_CONTROL_NOT_EXTRACTED"}.issubset(self.codes(result)))
        self.assertEqual(result["coverage"]["status"], "partial")
        self.assertIn("word/header1.xml", result["coverage"]["excluded_parts"])

    def test_bad_docx_and_encrypted_or_legacy_errors(self):
        for payload, code in [(b"bad zip", "INVALID_DOCX"), (extractor.OLE_MAGIC + b"test", "ENCRYPTED_OR_LEGACY")]:
            with self.subTest(code=code):
                self.source.write_bytes(payload)
                error = io.StringIO()
                with contextlib.redirect_stderr(error):
                    self.assertEqual(extractor.main([str(self.source)]), 4)
                self.assertIn(code, error.getvalue())
                self.assertEqual(self.source.read_bytes(), payload)

    def test_malformed_xml_and_non_docx_zip(self):
        for include_xml in [False, True]:
            with self.subTest(include_xml=include_xml):
                with zipfile.ZipFile(self.source, "w") as package:
                    package.writestr("[Content_Types].xml", "<invalid>")
                    if include_xml:
                        package.writestr("word/document.xml", "<invalid>")
                with self.assertRaises(extractor.ExtractionError) as caught:
                    extractor.extract_docx(self.source)
                self.assertEqual(caught.exception.code, "INVALID_DOCX")

    def test_empty_document_stops(self):
        with self.assertRaises(extractor.ExtractionError) as caught:
            self.save(Document())
        self.assertEqual(caught.exception.code, "EMPTY_TEXT")

    def test_resource_limit(self):
        doc = Document()
        doc.add_paragraph("正文")
        doc.save(self.source)
        with patch.object(extractor, "MAX_EXPANDED", 1):
            with self.assertRaises(extractor.ExtractionError) as caught:
                extractor.extract_docx(self.source)
        self.assertEqual(caught.exception.code, "PACKAGE_LIMIT")

    def test_missing_dependency_in_isolated_interpreter(self):
        # -I -S really removes site-packages; no fake fixed error-string implementation.
        result = subprocess.run([sys.executable, "-I", "-S", str(SCRIPT), str(self.source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn("MISSING_DEPENDENCY", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_unique_outputs_and_failure_cleanup(self):
        doc = Document()
        doc.add_paragraph("事实没有改变。")
        doc.save(self.source)
        paths = []
        for _ in range(2):
            result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), str(self.source), "--output-dir", str(self.directory)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths.append(Path(result.stdout.strip()))
        self.assertNotEqual(*paths)
        self.assertEqual(json.loads(paths[0].read_text(encoding="utf-8")), json.loads(paths[1].read_text(encoding="utf-8")))
        before = set(self.directory.iterdir())
        with patch.object(extractor.json, "dump", side_effect=OSError("disk full")):
            with self.assertRaises(extractor.ExtractionError):
                extractor.write_result({}, self.directory)
        self.assertEqual(set(self.directory.iterdir()), before)

    def test_io_errors_are_actionable(self):
        with self.assertRaises(extractor.ExtractionError) as caught:
            extractor.extract_docx(self.directory / "missing.docx")
        self.assertEqual(caught.exception.exit_code, 5)
        self.source.write_bytes(b"occupied")
        with self.assertRaises(extractor.ExtractionError) as caught:
            extractor.write_result({}, self.source)
        self.assertEqual(caught.exception.code, "OUTPUT_IO")
        self.assertEqual(self.source.read_bytes(), b"occupied")


if __name__ == "__main__":
    unittest.main()
