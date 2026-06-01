from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class CallEdge:
    route_func: str
    callee: str


def _collect_import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                aliases[local] = f"{module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                aliases[local] = alias.name
    return aliases


def _call_name(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        base = _call_name(expr.value)
        if base:
            return f"{base}.{expr.attr}"
        return expr.attr
    return None


def trace_calls(source_path: Path) -> list[CallEdge]:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    aliases = _collect_import_aliases(tree)

    edges: list[CallEdge] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        route_name = node.name
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            callee = _call_name(inner.func)
            if not callee:
                continue

            # Prefer resolving imported names to their module paths.
            resolved = aliases.get(callee, callee)
            edges.append(CallEdge(route_func=route_name, callee=resolved))

    return edges


def _workspace_routes_path() -> Path:
    return Path("app/api/routes/workspaces.py")


def main() -> None:
    path = _workspace_routes_path()
    if not path.exists():
        raise SystemExit(f"Not found: {path}")

    edges = trace_calls(path)
    if not edges:
        print("No calls found.")
        return

    # Group by route function name.
    grouped: dict[str, set[str]] = {}
    for edge in edges:
        grouped.setdefault(edge.route_func, set()).add(edge.callee)

    print(f"Source: {path}")
    print()
    for route_func in sorted(grouped.keys()):
        callees = sorted(grouped[route_func])
        print(f"[route] {route_func}")
        for callee in callees:
            print(f"  - {callee}")
        print()


if __name__ == "__main__":
    main()
