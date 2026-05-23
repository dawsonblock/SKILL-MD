import importlib.util
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


if __name__ == "__main__":
    unittest.main()
