#!/usr/bin/env python3
"""Read-only DOCX extraction. No manuscript rewriting, OCR, or semantic verdicts."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile


MAX_BYTES = 128 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_ENTRIES = 10000
OLE_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class ExtractionError(Exception):
    def __init__(self, code, message, exit_code=4):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def load_docx():
    try:
        from docx import Document
        from docx.text.paragraph import Paragraph
        from docx.table import Table
    except ImportError as exc:
        raise ExtractionError(
            "MISSING_DEPENDENCY",
            "Install python-docx in this interpreter: python -m pip install 'python-docx>=1.2,<1.3'.",
            3,
        ) from exc
    return Document, Paragraph, Table


def read_package(path):
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ExtractionError("INPUT_IO", f"Cannot read input: {exc}", 5) from exc
    if len(raw) > MAX_BYTES:
        raise ExtractionError("PACKAGE_LIMIT", "Input exceeds 128 MiB; use a smaller review copy.")
    if raw.startswith(OLE_MAGIC):
        raise ExtractionError(
            "ENCRYPTED_OR_LEGACY",
            "OLE container: possibly encrypted DOCX or legacy DOC. Export an unencrypted DOCX copy; no decryption attempted.",
        )
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as package:
            entries = package.infolist()
            names = [entry.filename for entry in entries]
            if len(entries) > MAX_ENTRIES or sum(e.file_size for e in entries) > MAX_EXPANDED:
                raise ExtractionError("PACKAGE_LIMIT", "Expanded package exceeds extraction limits.")
            if len(names) != len(set(names)):
                raise ExtractionError("INVALID_DOCX", "Duplicate ZIP entries; export a clean DOCX copy.")
            if any(e.flag_bits & 1 for e in entries):
                raise ExtractionError("ENCRYPTED_DOCX", "Encrypted ZIP entries; supply an unencrypted copy.")
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ExtractionError("INVALID_DOCX", "ZIP is not a supported Word DOCX package.")
            if package.testzip() is not None:
                raise ExtractionError("INVALID_DOCX", "DOCX checksum failed; export a clean copy.")
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
        raise ExtractionError("INVALID_DOCX", "Unreadable/corrupt DOCX ZIP; export a clean copy.") from exc
    return raw, names


def heading_level(paragraph):
    """Prefer explicit outline level; support inherited/custom heading styles."""
    props = paragraph._p.find(W + "pPr")
    style = paragraph.style
    seen = set()
    candidates = [props]
    while style is not None and style.style_id not in seen:
        seen.add(style.style_id)
        candidates.append(style.element.find(W + "pPr"))
        style = style.base_style
    for props in candidates:
        if props is not None:
            outline = props.find(W + "outlineLvl")
            if outline is not None:
                value = int(outline.get(W + "val"))
                return value + 1 if 0 <= value <= 8 else None
    name = paragraph.style.name if paragraph.style else ""
    match = re.fullmatch(r"(?:Heading\s*|标题\s*)([1-9])", name, re.IGNORECASE)
    return int(match[1]) if match else None


def extract_docx(source):
    Document, Paragraph, Table = load_docx()
    source = Path(source).resolve()
    raw, names = read_package(source)
    try:
        document = Document(io.BytesIO(raw))
        if not hasattr(document, "iter_inner_content"):
            raise ExtractionError("DEPENDENCY_VERSION", "python-docx 1.2.x is required.", 3)
        blocks = []
        warnings = []

        def warn(code, location, detail):
            warnings.append({"code": code, "location": location, "detail": detail})

        def inspect_xml(element, location):
            groups = {
                "DRAWING_NOT_EXTRACTED": {"drawing", "pict", "object"},
                "TEXTBOX_NOT_EXTRACTED": {"txbxContent"},
                "MATH_NOT_EXTRACTED": {"oMath", "oMathPara"},
                "REVISIONS_NOT_RESOLVED": {"ins", "del", "moveFrom", "moveTo"},
                "CONTENT_CONTROL_NOT_EXTRACTED": {"sdt", "customXml", "altChunk"},
                "FIELD_NOT_EVALUATED": {"fldSimple", "fldChar", "instrText"},
                "NUMBERING_NOT_RENDERED": {"numPr"},
            }
            found = {node.tag.rsplit("}", 1)[-1] for node in element.iter()}
            for code, tags in groups.items():
                if found & tags:
                    warn(code, location, "Verify this object in the original; extracted text may be incomplete.")

        def walk(container, prefix=""):
            p_index = t_index = 0
            # XML inspections expose objects omitted by python-docx's public iterator.
            for child in container._element:
                if child.tag not in {W + "p", W + "tbl", W + "sectPr", W + "tcPr"}:
                    inspect_xml(child, prefix or "body")
                    warn("UNSUPPORTED_BLOCK", prefix or "body", child.tag)
            for item in container.iter_inner_content():
                if isinstance(item, Paragraph):
                    location = f"{prefix}P{p_index}"
                    p_index += 1
                    level = heading_level(item)
                    style = item.style.name if item.style else None
                    blocks.append({
                        "id": location, "kind": "paragraph", "text": item.text,
                        "style": style, "heading_level": level,
                        "caption_candidate": bool(
                            style and "caption" in style.lower()
                            or re.match(r"^\s*(?:图|表|Figure\s|Table\s)\s*\d+", item.text, re.I)
                        ),
                    })
                    inspect_xml(item._p, location)
                elif isinstance(item, Table):
                    location = f"{prefix}T{t_index}"
                    t_index += 1
                    blocks.append({"id": location, "kind": "table", "rows": len(item.rows)})
                    seen_cells = set()
                    for r, row in enumerate(item.rows):
                        for c, cell in enumerate(row.cells):
                            if cell._tc in seen_cells:
                                continue
                            seen_cells.add(cell._tc)
                            walk(cell, f"{location}/R{r}C{c}/")
                    if item._tbl.xpath(".//w:gridSpan | .//w:vMerge | .//w:gridBefore | .//w:gridAfter"):
                        warn("IRREGULAR_TABLE", location, "Merged/omitted cells: IDs are anchors, not a rectangular data matrix.")

        # Document._element is w:document, while inner content lives in w:body.
        from docx.blkcntnr import BlockItemContainer
        walk(BlockItemContainer(document.element.body, document))
        excluded = [n for n in names if re.match(
            r"word/(?:header\d*|footer\d*|footnotes|endnotes|comments)\.xml$", n
        )]
        for part in excluded:
            warn("PART_NOT_EXTRACTED", part, "Headers, footers, notes and comments are outside this extractor's text coverage.")
        paragraphs = [b for b in blocks if b["kind"] == "paragraph"]
        if not any(b["heading_level"] is not None for b in paragraphs):
            warn("NO_HEADINGS", "body", "Infer candidate sections from content/numbering and ask the author if ambiguous.")
        if not any(b["text"].strip() for b in paragraphs):
            raise ExtractionError("EMPTY_TEXT", "No body/table text was extracted; provide a readable text copy.")
        return {
            "schema_version": "1.0", "source": str(source),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "blocks": blocks, "warnings": warnings,
            "coverage": {
                "scope": "main-body paragraphs and recursively nested table-cell paragraphs in XML order",
                "status": "partial" if any(w["code"] != "NO_HEADINGS" for w in warnings) else "text-only",
                "paragraph_count": len(paragraphs),
                "table_count": sum(b["kind"] == "table" for b in blocks),
                "excluded_parts": excluded,
                "limitations": [
                    "Not a rendered view; no page numbers, floating layout or figure OCR.",
                    "Captions are candidates, not verified figure/table associations.",
                    "No field evaluation, reference verification, revision resolution or equation interpretation.",
                    "Heading detection is structural, not semantic; numbering inherited from styles may be absent.",
                ],
            },
        }
    except ExtractionError:
        raise
    except Exception as exc:
        # Third-party XML/package parsers raise several exception types. Do not leak
        # manuscript fragments from their error messages or leave a partial output.
        raise ExtractionError("INVALID_DOCX", f"Cannot parse DOCX ({type(exc).__name__}); export a clean copy.") from exc


def write_result(result, output_dir=None):
    """Exclusively create a unique output; remove it if writing fails."""
    output_path = None
    try:
        if output_dir is not None:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix="coherent-", suffix=".json", dir=output_dir)
        output_path = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        return output_path.resolve()
    except (OSError, TypeError, ValueError) as exc:
        if output_path is not None:
            output_path.unlink(missing_ok=True)
        raise ExtractionError("OUTPUT_IO", "Cannot write extraction output; choose a writable private directory.", 5) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Readable unencrypted DOCX")
    parser.add_argument("--output-dir", type=Path, help="Private work directory; defaults to system temporary directory")
    args = parser.parse_args(argv)
    try:
        result = extract_docx(args.source)
        path = write_result(result, args.output_dir)
    except ExtractionError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
