"""Python 파일 분석(code analysis) 도구.

AST 모듈을 사용하여 Python 파일의 구조 정보를 추출한다.
"""

from __future__ import annotations

import ast
from pathlib import Path

from langchain_core.tools import tool


def _count_lines(source: str) -> dict[str, int]:
    """소스 코드의 라인(line) 통계를 반환한다."""
    lines = source.splitlines()
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())
    comment = sum(1 for line in lines if line.strip().startswith("#"))
    code = total - blank - comment
    return {"total": total, "blank": blank, "comment": comment, "code": code}


def _extract_functions(tree: ast.Module) -> list[dict]:
    """AST에서 함수(function) 정보를 추출한다."""
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_count = node.end_lineno - node.lineno + 1
            results.append({
                "name": node.name,
                "lines": line_count,
                "complex": line_count > 20,
            })
    return results


def _extract_classes(tree: ast.Module) -> list[str]:
    """AST에서 클래스(class) 이름을 추출한다."""
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]


def _count_imports(tree: ast.Module) -> int:
    """AST에서 임포트(import) 수를 센다."""
    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )


def analyze_source(source: str) -> str:
    """Python 소스 코드 문자열을 분석하여 구조 정보를 반환한다."""
    line_stats = _count_lines(source)
    tree = ast.parse(source)

    functions = _extract_functions(tree)
    classes = _extract_classes(tree)
    import_count = _count_imports(tree)

    # 결과(result) 문자열 조합
    parts = [
        f"=== 코드 분석 결과 ===",
        f"총 라인: {line_stats['total']}",
        f"코드 라인: {line_stats['code']}",
        f"빈 라인: {line_stats['blank']}",
        f"주석 라인: {line_stats['comment']}",
        f"임포트 수: {import_count}",
        f"클래스 수: {len(classes)}",
    ]
    if classes:
        parts.append(f"  클래스: {', '.join(classes)}")

    parts.append(f"함수 수: {len(functions)}")
    for fn in functions:
        flag = " [복잡]" if fn["complex"] else ""
        parts.append(f"  - {fn['name']} ({fn['lines']}줄){flag}")

    return "\n".join(parts)


@tool
def analyze_python_file(file_path: str) -> str:
    """Python 파일을 분석하여 구조 정보를 반환한다.

    Args:
        file_path: 분석할 Python 파일 경로

    Returns:
        파일 구조 분석 결과 문자열
    """
    path = Path(file_path)
    if not path.exists():
        return f"파일을 찾을 수 없습니다: {file_path}"
    if path.suffix != ".py":
        return f"Python 파일이 아닙니다: {file_path}"

    source = path.read_text(encoding="utf-8")
    try:
        return analyze_source(source)
    except SyntaxError as e:
        return f"구문 오류(syntax error): {e}"
