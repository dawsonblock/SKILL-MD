import importlib.util
import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = load_module(ROOT / "scripts" / "validate.py", "validate_module")
sync = load_module(ROOT / "scripts" / "sync_guidelines.py", "sync_module")
check = load_module(ROOT / "scripts" / "check.py", "check_module")
package_release = load_module(
    ROOT / "scripts" / "package_release.py", "package_release_module"
)
clean = load_module(ROOT / "scripts" / "clean.py", "clean_module")


class MarkerExtractionTests(unittest.TestCase):
    def test_sync_extract_canonical_body_requires_end_after_begin(self):
        text = f"{sync.END}\n{sync.BEGIN}\nbody"
        with self.assertRaises(ValueError):
            sync.extract_canonical_body(text)

    def test_validate_extract_marked_body_requires_end_after_begin(self):
        fake_path = ROOT / "docs" / "guidelines.md"
        text = f"{validate.END}\n{validate.BEGIN}\nbody"
        with self.assertRaises(ValueError):
            validate.extract_marked_body(fake_path, text)


class PluginMetadataValidationTests(unittest.TestCase):
    def test_check_plugin_metadata_fails_when_plugin_name_not_listed(self):
        errors = []

        plugin_payload = {
            "name": "expected-plugin",
            "description": "desc",
            "version": "1.2.3",
            "license": "MIT",
            "skills": ["./skills/karpathy-guidelines"],
        }
        marketplace_payload = {
            "metadata": {"version": "1.2.3"},
            "plugins": [
                {
                    "name": "different-plugin",
                    "version": "1.2.3",
                }
            ],
        }

        original_read = validate.read
        original_check_exists = validate.check_exists

        def fake_read(path: Path) -> str:
            if path.name == "plugin.json":
                import json

                return json.dumps(plugin_payload)
            if path.name == "marketplace.json":
                import json

                return json.dumps(marketplace_payload)
            return original_read(path)

        def fake_check_exists(_errors, rel_path: str):
            return ROOT / rel_path

        try:
            validate.read = fake_read
            validate.check_exists = fake_check_exists
            validate.check_plugin_metadata(errors)
        finally:
            validate.read = original_read
            validate.check_exists = original_check_exists

        self.assertTrue(
            any(
                "must include an entry matching plugin.json name" in err
                for err in errors
            )
        )


class ChineseForbiddenPhraseTests(unittest.TestCase):
    def test_check_forbidden_phrases_catches_chinese_promo_in_readme_zh(self):
        errors = []
        original_read = validate.read

        def fake_read(path):
            if path.name == "README.zh.md":
                return "# 受 Karpathy 启发的编码代理指南\n\n查看我的新项目 SomeThing\n"
            return original_read(path)

        try:
            validate.read = fake_read
            validate.check_forbidden_phrases(errors)
        finally:
            validate.read = original_read

        self.assertTrue(
            any("README.zh.md" in err and "查看我的新项目" in err for err in errors),
            f"Expected forbidden phrase error; got: {errors}",
        )

    def test_check_readme_disclaimers_passes_with_correct_chinese_phrase(self):
        errors = []
        original_read = validate.read

        def fake_read(path):
            if path.name == "README.md":
                return "Not affiliated with or endorsed by Andrej Karpathy."
            if path.name == "README.zh.md":
                return "本项目与 Andrej Karpathy 无关，也未得到其认可。"
            return original_read(path)

        try:
            validate.read = fake_read
            validate.check_readme_disclaimers(errors)
        finally:
            validate.read = original_read

        self.assertEqual(errors, [], f"Expected no errors; got: {errors}")

    def test_check_readme_disclaimers_fails_when_chinese_disclaimer_missing(self):
        errors = []
        original_read = validate.read

        def fake_read(path):
            if path.name == "README.md":
                return "Not affiliated with or endorsed by Andrej Karpathy."
            if path.name == "README.zh.md":
                return "# 受 Karpathy 启发的编码代理指南\n"
            return original_read(path)

        try:
            validate.read = fake_read
            validate.check_readme_disclaimers(errors)
        finally:
            validate.read = original_read

        self.assertTrue(
            any("README.zh.md" in err for err in errors),
            f"Expected missing-disclaimer error; got: {errors}",
        )


class ValidationFailureModeTests(unittest.TestCase):
    def test_validate_rejects_missing_readme_polished_wording(self):
        path = ROOT / "README.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn(
            "Blocking clarifying questions only when required for correctness",
            original,
        )
        try:
            broken = original.replace(
                "Blocking clarifying questions only when required for correctness",
                "Clarifying questions before implementation",
            )
            path.write_text(broken, encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate.validate_readme_polished_wording()
        finally:
            path.write_text(original, encoding="utf-8")

    def test_validate_rejects_missing_zh_readme_polished_wording(self):
        path = ROOT / "README.zh.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("只有在正确性受阻时才提出必要澄清问题", original)
        try:
            broken = original.replace(
                "只有在正确性受阻时才提出必要澄清问题",
                "如果不确定就先询问",
            )
            path.write_text(broken, encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate.validate_readme_zh_polished_wording()
        finally:
            path.write_text(original, encoding="utf-8")

    def test_validate_rejects_committed_release_zip_in_dist(self):
        dist = ROOT / "dist"
        artifact = dist / "SKILL-MD-main-fixed.zip"
        original_exists = artifact.exists()
        original_bytes = artifact.read_bytes() if original_exists else None
        try:
            dist.mkdir(exist_ok=True)
            artifact.write_bytes(b"fake zip content")
            with self.assertRaises(SystemExit):
                validate.validate_no_committed_release_artifacts()
        finally:
            if original_exists and original_bytes is not None:
                artifact.write_bytes(original_bytes)
            elif artifact.exists():
                artifact.unlink()
            try:
                dist.rmdir()
            except OSError:
                pass

    def test_validate_rejects_old_chinese_confusion_wording(self):
        path = ROOT / "README.zh.md"
        original = path.read_text(encoding="utf-8")
        try:
            broken = original.replace(
                "如果检查可用证据后仍不清楚，应指出阻塞点并询问。",
                "困惑时停下来 — 指出不清楚的地方并要求澄清",
            )
            path.write_text(broken, encoding="utf-8")
            errors = []
            validate.check_forbidden_phrases(errors)
            self.assertTrue(
                any("困惑时停下来" in err for err in errors),
                f"Expected old confusion wording failure; got: {errors}",
            )
        finally:
            path.write_text(original, encoding="utf-8")

    def test_validate_rejects_stale_chinese_assumption_wording(self):
        target = ROOT / "README.zh.md"
        original = target.read_text(encoding="utf-8")
        errors = []
        try:
            target.write_text(
                original + "\n如果不确定，询问而不是猜测\n", encoding="utf-8"
            )
            validate.check_forbidden_phrases(errors)
        finally:
            target.write_text(original, encoding="utf-8")

        self.assertTrue(
            any(
                "README.zh.md" in err and "如果不确定，询问而不是猜测" in err
                for err in errors
            ),
            f"Expected stale assumption phrase failure; got: {errors}",
        )

    def test_validate_rejects_stale_chinese_error_wording(self):
        target = ROOT / "README.zh.md"
        original = target.read_text(encoding="utf-8")
        errors = []
        try:
            target.write_text(
                original + "\n不要为不可能发生的场景做错误处理\n",
                encoding="utf-8",
            )
            validate.check_forbidden_phrases(errors)
        finally:
            target.write_text(original, encoding="utf-8")

        self.assertTrue(
            any(
                "README.zh.md" in err and "不要为不可能发生的场景做错误处理" in err
                for err in errors
            ),
            f"Expected stale error wording failure; got: {errors}",
        )

    def test_validate_rejects_unquoted_frontmatter_description(self):
        path = ROOT / ".cursor" / "rules" / "karpathy-guidelines.mdc"
        original = path.read_text(encoding="utf-8")
        errors = []
        try:
            broken = re.sub(
                r'^description: ".*"$',
                "description: Karpathy-inspired behavioral guidelines for coding agents: clarify assumptions, keep changes simple, edit surgically, and verify before claiming completion.",
                original,
                count=1,
                flags=re.MULTILINE,
            )
            path.write_text(broken, encoding="utf-8")
            validate.check_frontmatter_descriptions_are_quoted(errors)
        finally:
            path.write_text(original, encoding="utf-8")

        self.assertTrue(
            any("description frontmatter must be quoted" in err for err in errors),
            f"Expected unquoted frontmatter failure; got: {errors}",
        )

    def test_validate_rejects_pyc_files(self):
        junk = ROOT / "tests" / "dummy.pyc"
        errors = []
        try:
            junk.write_bytes(b"compiled-cache")
            validate.check_no_junk_files(errors)
        finally:
            if junk.exists():
                junk.unlink()

        self.assertTrue(
            any("dummy.pyc" in err for err in errors),
            f"Expected junk file failure; got: {errors}",
        )

    def test_validate_reports_forbidden_junk_directory_once(self):
        junk_file = ROOT / ".mypy_cache" / "nested" / "artifact.meta.json"
        errors = []
        try:
            junk_file.parent.mkdir(parents=True, exist_ok=True)
            junk_file.write_text("{}", encoding="utf-8")
            validate.check_no_junk_files(errors)
        finally:
            if junk_file.exists():
                junk_file.unlink()
            nested = junk_file.parent
            if nested.exists() and not any(nested.iterdir()):
                nested.rmdir()
            cache_root = ROOT / ".mypy_cache"
            if cache_root.exists() and not any(cache_root.iterdir()):
                cache_root.rmdir()

        hits = [
            err for err in errors if "Forbidden junk path found: .mypy_cache" in err
        ]
        self.assertEqual(
            len(hits),
            1,
            f"Expected one consolidated .mypy_cache error; got: {errors}",
        )

    def test_validate_rejects_macosx_directory(self):
        junk_dir = ROOT / "__MACOSX"
        junk_file = junk_dir / "._README.md"
        errors = []
        try:
            junk_dir.mkdir(exist_ok=True)
            junk_file.write_bytes(b"appledouble")
            validate.check_no_junk_files(errors)
        finally:
            if junk_file.exists():
                junk_file.unlink()
            if junk_dir.exists():
                junk_dir.rmdir()

        self.assertTrue(
            any("__MACOSX" in err for err in errors),
            f"Expected __MACOSX junk failure; got: {errors}",
        )

    def test_validate_rejects_appledouble_file(self):
        junk = ROOT / "._README.md"
        errors = []
        try:
            junk.write_bytes(b"appledouble")
            validate.check_no_junk_files(errors)
        finally:
            if junk.exists():
                junk.unlink()

        self.assertTrue(
            any("._README.md" in err for err in errors),
            f"Expected AppleDouble junk failure; got: {errors}",
        )

    def test_validate_rejects_ruff_cache_directory(self):
        junk_file = ROOT / ".ruff_cache" / "cache.db"
        errors = []
        try:
            junk_file.parent.mkdir(parents=True, exist_ok=True)
            junk_file.write_text("x", encoding="utf-8")
            validate.check_no_junk_files(errors)
        finally:
            if junk_file.exists():
                junk_file.unlink()
            if junk_file.parent.exists():
                junk_file.parent.rmdir()

        self.assertTrue(
            any(".ruff_cache" in err for err in errors),
            f"Expected .ruff_cache junk failure; got: {errors}",
        )

    def test_validate_rejects_pyo_files(self):
        junk = ROOT / "tests" / "dummy.pyo"
        errors = []
        try:
            junk.write_bytes(b"compiled-cache")
            validate.check_no_junk_files(errors)
        finally:
            if junk.exists():
                junk.unlink()

        self.assertTrue(
            any("dummy.pyo" in err for err in errors),
            f"Expected .pyo junk failure; got: {errors}",
        )

    def test_sync_check_rejects_generated_file_drift(self):
        path = ROOT / "CLAUDE.md"
        original = path.read_text(encoding="utf-8")
        errors = []
        try:
            drifted = original.replace(
                "## 1. Think Before Coding",
                "## 1. Think Before Coding (DRIFT)",
                1,
            )
            path.write_text(drifted, encoding="utf-8")
            validate.check_canonical_sync(errors)
        finally:
            path.write_text(original, encoding="utf-8")

        self.assertTrue(
            any("Guideline body drift detected" in err for err in errors),
            f"Expected sync drift failure; got: {errors}",
        )

    def test_validate_rejects_stale_readme_version_badge(self):
        path = ROOT / "README.md"
        original = path.read_text(encoding="utf-8")
        errors = []
        version = validate.get_plugin_version()
        try:
            broken = original.replace(f"version-{version}-", "version-0.0.0-", 1)
            path.write_text(broken, encoding="utf-8")
            validate.check_readme_version_badge(errors)
        finally:
            path.write_text(original, encoding="utf-8")

        self.assertTrue(
            any(
                "README.md version badge does not match plugin version" in err
                for err in errors
            ),
            f"Expected README badge drift failure; got: {errors}",
        )


class SyncResilienceTests(unittest.TestCase):
    def test_sync_main_creates_missing_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            canonical = tmp_root / "docs" / "guidelines.md"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                "# Guidelines\n\n"
                "<!-- BEGIN CANONICAL BODY -->\n"
                "## Section\n"
                "Body\n"
                "<!-- END CANONICAL BODY -->\n",
                encoding="utf-8",
            )

            original_root = sync.ROOT
            original_canonical = sync.CANONICAL_PATH
            original_targets = sync.TARGETS
            original_argv = sync.sys.argv
            try:
                sync.ROOT = tmp_root
                sync.CANONICAL_PATH = canonical
                sync.TARGETS = {
                    "CLAUDE.md": tmp_root / "CLAUDE.md",
                    ".cursor/rules/karpathy-guidelines.mdc": tmp_root
                    / ".cursor"
                    / "rules"
                    / "karpathy-guidelines.mdc",
                    ".github/copilot-instructions.md": tmp_root
                    / ".github"
                    / "copilot-instructions.md",
                    "skills/karpathy-guidelines/SKILL.md": tmp_root
                    / "skills"
                    / "karpathy-guidelines"
                    / "SKILL.md",
                }
                sync.sys.argv = ["sync_guidelines.py"]

                with contextlib.redirect_stdout(io.StringIO()):
                    result = sync.main()
            finally:
                sync.ROOT = original_root
                sync.CANONICAL_PATH = original_canonical
                sync.TARGETS = original_targets
                sync.sys.argv = original_argv

            self.assertEqual(result, 0)
            self.assertTrue((tmp_root / ".cursor" / "rules").exists())
            self.assertTrue((tmp_root / "skills" / "karpathy-guidelines").exists())


class CheckScriptTests(unittest.TestCase):
    def test_check_script_cleans_junk_before_commands(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            (tmp_root / "nested" / "__pycache__").mkdir(parents=True, exist_ok=True)
            (tmp_root / "nested" / "__pycache__" / "x.pyc").write_bytes(b"cache")
            (tmp_root / ".pytest_cache").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".pytest_cache" / "state").write_text("1", encoding="utf-8")
            (tmp_root / ".mypy_cache").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".mypy_cache" / "meta").write_text("{}", encoding="utf-8")
            (tmp_root / ".DS_Store").write_text("junk", encoding="utf-8")

            commands_seen = []

            original_root = check.ROOT
            original_run = check.subprocess.run
            try:
                check.ROOT = tmp_root

                def fake_run(cmd, cwd, env):
                    commands_seen.append((cmd, cwd, env.get("PYTHONDONTWRITEBYTECODE")))

                    class Result:
                        returncode = 0

                    return Result()

                check.subprocess.run = fake_run
                with contextlib.redirect_stdout(io.StringIO()):
                    result = check.main()
            finally:
                check.ROOT = original_root
                check.subprocess.run = original_run

            self.assertEqual(result, 0)
            self.assertEqual(len(commands_seen), 4)
            self.assertFalse(any(tmp_root.rglob("__pycache__")))
            self.assertFalse(any(tmp_root.rglob("*.pyc")))
            self.assertFalse((tmp_root / ".pytest_cache").exists())
            self.assertFalse((tmp_root / ".mypy_cache").exists())
            self.assertFalse((tmp_root / ".DS_Store").exists())


class PackageReleaseTests(unittest.TestCase):
    def test_package_release_uses_current_root_name_for_archive_name(self):
        expected_root_name = package_release.normalize_release_root_name(
            package_release.ROOT.name
        )
        self.assertEqual(package_release.RELEASE_ROOT_NAME, expected_root_name)
        self.assertEqual(
            package_release.ARCHIVE_NAME,
            f"{expected_root_name}-fixed.zip",
        )
        self.assertNotIn("-main-main", package_release.ARCHIVE_NAME)

    def test_normalize_release_root_name_adds_main_once(self):
        self.assertEqual(
            package_release.normalize_release_root_name("SKILL-MD"),
            "SKILL-MD-main",
        )
        self.assertEqual(
            package_release.normalize_release_root_name("SKILL-MD-main"),
            "SKILL-MD-main",
        )

    def test_create_archive_excludes_junk_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir) / "repo"
            tmp_root.mkdir(parents=True, exist_ok=True)
            dist_dir = tmp_root / "dist"
            dist_dir.mkdir(parents=True, exist_ok=True)

            (tmp_root / "README.md").write_text("ok", encoding="utf-8")
            (tmp_root / "scripts").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts" / "check.py").write_text(
                "print('ok')", encoding="utf-8"
            )
            (tmp_root / "nested" / "__pycache__").mkdir(parents=True, exist_ok=True)
            (tmp_root / "nested" / "__pycache__" / "x.pyc").write_bytes(b"cache")
            (tmp_root / ".pytest_cache").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".pytest_cache" / "state").write_text("x", encoding="utf-8")
            (tmp_root / "node_modules").mkdir(parents=True, exist_ok=True)
            (tmp_root / "node_modules" / "lib.js").write_text("x", encoding="utf-8")
            (tmp_root / ".DS_Store").write_text("junk", encoding="utf-8")

            archive_path = dist_dir / "out.zip"
            count = package_release.create_archive(tmp_root, archive_path)

            self.assertGreaterEqual(count, 2)
            self.assertTrue(archive_path.exists())

            import zipfile

            with zipfile.ZipFile(archive_path, "r") as archive:
                names = archive.namelist()

            expected_prefix = f"{package_release.RELEASE_ROOT_NAME}/"
            self.assertTrue(
                all(name.startswith(expected_prefix) for name in names),
                f"Expected all archive entries to start with {expected_prefix}; got {names}",
            )

            self.assertTrue(
                any(name.endswith("README.md") for name in names),
                f"Expected README in archive; got {names}",
            )
            self.assertFalse(any("__pycache__/" in name for name in names), names)
            self.assertFalse(any(name.endswith(".pyc") for name in names), names)
            self.assertFalse(any(".pytest_cache/" in name for name in names), names)
            self.assertFalse(any(".mypy_cache/" in name for name in names), names)
            self.assertFalse(any("node_modules/" in name for name in names), names)
            self.assertFalse(any(name.endswith(".DS_Store") for name in names), names)

    def test_package_release_excludes_macosx_path(self):
        self.assertIn("__MACOSX", package_release.FORBIDDEN_PATH_PARTS)
        self.assertFalse(
            package_release.should_include(Path("__MACOSX") / "._README.md")
        )

    def test_package_release_excludes_appledouble_file(self):
        self.assertFalse(package_release.should_include(Path("._README.md")))

    def test_package_release_excludes_trunk_from_release_zip(self):
        self.assertIn(".trunk", package_release.FORBIDDEN_PATH_PARTS)
        self.assertFalse(
            package_release.should_include(Path(".trunk") / "trunk.yaml")
        )

    def test_release_archive_excludes_source_only_and_junk_paths(self):
        forbidden = [
            Path("dist") / "artifact.zip",
            Path(".git") / "config",
            Path("nested") / "__pycache__" / "x.pyc",
            Path("nested") / "__pycache__" / "x.pyo",
            Path(".pytest_cache") / "state",
            Path(".mypy_cache") / "meta.json",
            Path(".ruff_cache") / "cache.db",
            Path("node_modules") / "lib.js",
            Path("__MACOSX") / "._README.md",
            Path("._README.md"),
            Path(".trunk") / "trunk.yaml",
        ]
        for path in forbidden:
            self.assertFalse(
                package_release.should_include(path),
                f"Expected {path} to be excluded from release archive",
            )


class CopilotSupportTests(unittest.TestCase):
    def test_copilot_instructions_generated(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            canonical = tmp_root / "docs" / "guidelines.md"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(
                "# Guidelines\n\n"
                "<!-- BEGIN CANONICAL BODY -->\n"
                "## Section\n"
                "Body\n"
                "<!-- END CANONICAL BODY -->\n",
                encoding="utf-8",
            )

            original_root = sync.ROOT
            original_canonical = sync.CANONICAL_PATH
            original_targets = sync.TARGETS
            original_argv = sync.sys.argv
            try:
                sync.ROOT = tmp_root
                sync.CANONICAL_PATH = canonical
                sync.TARGETS = {
                    "CLAUDE.md": tmp_root / "CLAUDE.md",
                    ".cursor/rules/karpathy-guidelines.mdc": tmp_root
                    / ".cursor"
                    / "rules"
                    / "karpathy-guidelines.mdc",
                    ".github/copilot-instructions.md": tmp_root
                    / ".github"
                    / "copilot-instructions.md",
                    "skills/karpathy-guidelines/SKILL.md": tmp_root
                    / "skills"
                    / "karpathy-guidelines"
                    / "SKILL.md",
                }
                sync.sys.argv = ["sync_guidelines.py"]

                with contextlib.redirect_stdout(io.StringIO()):
                    result = sync.main()
            finally:
                sync.ROOT = original_root
                sync.CANONICAL_PATH = original_canonical
                sync.TARGETS = original_targets
                sync.sys.argv = original_argv

            self.assertEqual(result, 0)
            generated = tmp_root / ".github" / "copilot-instructions.md"
            self.assertTrue(generated.exists())
            content = generated.read_text(encoding="utf-8")
            self.assertIn("# Coding Agent Guidelines", content)
            self.assertIn(sync.BEGIN, content)
            self.assertIn(sync.END, content)

    def test_copilot_instructions_sync_drift_detected(self):
        path = ROOT / ".github" / "copilot-instructions.md"
        original = path.read_text(encoding="utf-8")
        errors = []
        try:
            drifted = original.replace(
                "## 1. Think Before Coding", "## 1. Think Before Coding (DRIFT)", 1
            )
            path.write_text(drifted, encoding="utf-8")
            validate.check_canonical_sync(errors)
        finally:
            path.write_text(original, encoding="utf-8")

        self.assertTrue(
            any(".github/copilot-instructions.md" in err for err in errors),
            f"Expected copilot drift failure; got: {errors}",
        )

    def test_copilot_instructions_scanned_for_forbidden_phrases(self):
        path = ROOT / ".github" / "copilot-instructions.md"
        original = path.read_text(encoding="utf-8")
        errors = []
        try:
            path.write_text(
                original + "\nState your assumptions explicitly. If uncertain, ask.\n",
                encoding="utf-8",
            )
            validate.check_forbidden_phrases(errors)
        finally:
            path.write_text(original, encoding="utf-8")

        self.assertTrue(
            any(
                ".github/copilot-instructions.md" in err
                and "State your assumptions explicitly. If uncertain, ask." in err
                for err in errors
            ),
            f"Expected copilot forbidden-phrase failure; got: {errors}",
        )


class CleanScriptTests(unittest.TestCase):
    def test_clean_removes_dist_and_cache_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            dist = tmp_root / "dist"
            pycache = tmp_root / "tests" / "__pycache__"
            ruff_cache = tmp_root / ".ruff_cache"
            ds = tmp_root / ".DS_Store"
            apple = tmp_root / "._README.md"
            pyo = tmp_root / "tests" / "artifact.pyo"

            dist.mkdir(parents=True, exist_ok=True)
            (dist / "x.zip").write_bytes(b"x")
            pycache.mkdir(parents=True, exist_ok=True)
            (pycache / "x.pyc").write_bytes(b"x")
            ruff_cache.mkdir(parents=True, exist_ok=True)
            (ruff_cache / "cache.db").write_text("x", encoding="utf-8")
            ds.write_text("", encoding="utf-8")
            apple.write_text("", encoding="utf-8")
            pyo.parent.mkdir(parents=True, exist_ok=True)
            pyo.write_bytes(b"x")

            clean.clean(root=tmp_root)

            self.assertFalse(dist.exists())
            self.assertFalse(pycache.exists())
            self.assertFalse(ruff_cache.exists())
            self.assertFalse(ds.exists())
            self.assertFalse(apple.exists())
            self.assertFalse(pyo.exists())


if __name__ == "__main__":
    unittest.main()
