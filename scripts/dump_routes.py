from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class RouteInfo:
    method: str
    path: str
    name: str
    endpoint: str


def iter_routes() -> list[RouteInfo]:
    from app.main import app

    routes: list[RouteInfo] = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)
        endpoint = getattr(route, "endpoint", None)
        methods = getattr(route, "methods", None)

        if not path or not endpoint or not methods:
            continue

        endpoint_str = f"{endpoint.__module__}.{getattr(endpoint, '__name__', 'unknown')}"

        for method in sorted(methods):
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.append(
                RouteInfo(
                    method=method,
                    path=path,
                    name=str(name or ""),
                    endpoint=endpoint_str,
                )
            )

    return sorted(routes, key=lambda item: (item.path, item.method))


def main() -> None:
    routes = iter_routes()
    if not routes:
        print("No routes found.")
        return

    print(f"Total routes: {len(routes)}")
    print()

    method_width = max(len(item.method) for item in routes)
    path_width = max(len(item.path) for item in routes)

    for item in routes:
        print(
            f"{item.method:<{method_width}}  {item.path:<{path_width}}  ->  {item.endpoint}"
        )


if __name__ == "__main__":
    main()
