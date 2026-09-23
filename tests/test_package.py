from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml
from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/coherent-academic-writing"


class PackageTests(unittest.TestCase):
    def test_installable_frontmatter(self):
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        front = yaml.safe_load(content.split("---", 2)[1])
        self.assertEqual(front["name"], SKILL.name)
        self.assertRegex(front["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(front["name"]), 64)
        self.assertTrue(0 < len(front["description"].strip()) <= 1024)
        self.assertLessEqual(set(front), {"name", "description", "license", "compatibility", "metadata", "allowed-tools"})
        self.assertTrue(all(isinstance(k, str) and isinstance(v, str) for k, v in front["metadata"].items()))
        self.assertTrue(0 < len(front["metadata"]["compatibility"]) <= 500)
        self.assertEqual(front["license"], "MIT")

    def test_skill_relative_links_resolve_inside_installable_package(self):
        # Installing only this directory must not break instructions or licensing.
        for path in SKILL.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#")[0]).resolve()
                self.assertTrue(resolved.is_relative_to(SKILL.resolve()), str(resolved))
                self.assertTrue(resolved.exists(), str(resolved))

    def test_license_travels_with_skill(self):
        self.assertEqual((ROOT / "LICENSE").read_bytes(), (SKILL / "LICENSE").read_bytes())
        self.assertTrue((SKILL / "NOTICE.md").is_file())

    def test_ui_keeps_discovery_and_correct_invocation(self):
        data = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertTrue(data.get("policy", {}).get("allow_implicit_invocation", True))
        interface = data["interface"]
        self.assertTrue(25 <= len(interface["short_description"]) <= 64)
        self.assertIn("$" + SKILL.name, interface["default_prompt"])

    def test_installed_folder_runs_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installed = root / "skills" / SKILL.name
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__"))
            source = root / "paper.docx"
            doc = Document()
            doc.add_paragraph("必要限制必须保留。")
            doc.save(source)
            # Same invocation as SKILL.md, now from the installed directory.
            result = subprocess.run([sys.executable, "scripts/extract_docx.py", str(source), "--output-dir", str(root / "output")], cwd=installed, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(Path(result.stdout.decode("utf-8").strip()).read_text(encoding="utf-8"))
            self.assertEqual(report["blocks"][0]["text"], "必要限制必须保留。")
            self.assertEqual((installed / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
