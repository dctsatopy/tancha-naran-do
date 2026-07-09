"""実行環境・バージョン整合性テスト（仕様書 §5.1）。

Python は常に最新の安定版を利用し、Dockerfile / CI / README / 仕様書の
4 箇所でバージョンが一致していることを検証する。
また、依存パッケージが requirements にピン留めされ、実行環境と
一致していることを検証する。
"""

import re
import sys
from importlib import metadata
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# 最新安定版の Python マイナーバージョン（§5.1）
EXPECTED_PYTHON = (3, 14)
EXPECTED_PYTHON_STR = ".".join(map(str, EXPECTED_PYTHON))


class TestPythonVersionConsistency:
    """Python バージョンが全設定ファイルで最新安定版に揃っていること。"""

    def test_runtime_python_is_expected_version(self):
        assert sys.version_info[:2] == EXPECTED_PYTHON, (
            f"実行中の Python は {sys.version_info[0]}.{sys.version_info[1]} です。"
            f"仕様書 §5.1 に従い {EXPECTED_PYTHON_STR} を使用してください。"
        )

    def test_dockerfile_base_image(self):
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
        match = re.search(r"^FROM python:(\d+\.\d+)-slim", dockerfile, re.MULTILINE)
        assert match, "Dockerfile に python:<version>-slim のベースイメージ指定がありません"
        assert match.group(1) == EXPECTED_PYTHON_STR

    def test_ci_python_version(self):
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        match = re.search(r'python-version:\s*"(\d+\.\d+)"', ci)
        assert match, "ci.yml に python-version の指定がありません"
        assert match.group(1) == EXPECTED_PYTHON_STR

    def test_readme_python_version(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        match = re.search(r"Python (\d+\.\d+)", readme)
        assert match, "README.md に Python バージョンの記載がありません"
        assert match.group(1) == EXPECTED_PYTHON_STR

    def test_spec_python_version(self):
        spec = (REPO_ROOT / "development_background.md").read_text(encoding="utf-8")
        match = re.search(r"\| バックエンド \| Python (\d+\.\d+)", spec)
        assert match, "仕様書 §5 に Python バージョンの記載がありません"
        assert match.group(1) == EXPECTED_PYTHON_STR


def _parse_requirements(filename: str) -> dict[str, str]:
    """requirements ファイルから {パッケージ名: バージョン} を抽出する。"""
    pins = {}
    for line in (REPO_ROOT / filename).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r ")):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==(.+)", line)
        assert match, f"{filename} の行 '{line}' が == でピン留めされていません（§5.1）"
        pins[match.group(1).lower()] = match.group(2)
    return pins


class TestDependencyPins:
    """依存パッケージのピン留めと実行環境の一致（§5.1）。"""

    @pytest.mark.parametrize("filename", ["requirements.txt", "requirements-dev.txt"])
    def test_all_requirements_are_pinned(self, filename):
        pins = _parse_requirements(filename)
        assert pins, f"{filename} にパッケージ指定がありません"

    @pytest.mark.parametrize("filename", ["requirements.txt", "requirements-dev.txt"])
    def test_installed_versions_match_requirements(self, filename):
        mismatches = []
        for name, pinned in _parse_requirements(filename).items():
            try:
                installed = metadata.version(name)
            except metadata.PackageNotFoundError:
                mismatches.append(f"{name}: 未インストール（ピン: {pinned}）")
                continue
            if installed != pinned:
                mismatches.append(f"{name}: インストール済 {installed} != ピン {pinned}")
        assert not mismatches, "実行環境と requirements が不一致です: " + ", ".join(mismatches)
