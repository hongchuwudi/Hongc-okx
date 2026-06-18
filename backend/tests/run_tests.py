"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: run_tests.py 测试运行器
描述: 运行全部测试并生成报告到 tests/reports/

包含:
- 函数: run_all — 运行全部测试，生成 JUnit XML + HTML 覆盖率 + Markdown 摘要
- 函数: run_quick — 快速运行（仅 calc 测试），不生成覆盖率
- 函数: _summary — 生成 Markdown 格式的测试摘要报告
- 常量: REPORT_DIR — 报告输出目录
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPORT_DIR = Path(__file__).parent / "reports"


# 运行全部 41 个测试，生成完整报告（XML + HTML 覆盖率 + Markdown 摘要）。
def run_all() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = REPORT_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    xml_path = run_dir / "junit.xml"
    cov_dir = run_dir / "coverage"

    print(f"[run_tests] 运行全部测试 → 报告目录: {run_dir}")

    args = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent),
        f"--junit-xml={xml_path}",
        f"--cov=app",
        f"--cov-report=html:{cov_dir}",
        f"--cov-report=term",
        "-v",
    ]

    result = subprocess.run(args, cwd=str(Path(__file__).parent.parent))

    passed = result.returncode == 0
    _summary(run_dir, passed)

    print(f"[run_tests] {'全部通过' if passed else '有失败'} → 报告: {run_dir}")
    return result.returncode


# 仅运行 calc 测试（跳过集成/live/config），不生成覆盖率。
def run_quick() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = REPORT_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    xml_path = run_dir / "junit.xml"

    print(f"[run_tests] 快速测试 → 报告目录: {run_dir}")

    args = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "unit" / "indicators" / "test_calc.py"),
        f"--junit-xml={xml_path}",
        "-v",
    ]

    result = subprocess.run(args, cwd=str(Path(__file__).parent.parent))

    passed = result.returncode == 0
    _summary(run_dir, passed)

    print(f"[run_tests] {'全部通过' if passed else '有失败'} → 报告: {run_dir}")
    return result.returncode


# 生成 Markdown 摘要报告。
def _summary(run_dir: Path, passed: bool) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# 测试报告",
        f"",
        f"**时间**: {ts}",
        f"**结果**: {'全部通过' if passed else '存在失败'}",
        f"",
        f"## 产物",
        f"- JUnit XML: `junit.xml`",
    ]
    cov_dir = run_dir / "coverage"
    if cov_dir.exists():
        lines.append(f"- 覆盖率 HTML: `coverage/index.html`")

    md_path = run_dir / "summary.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if "--quick" in sys.argv:
        sys.exit(run_quick())
    else:
        sys.exit(run_all())
