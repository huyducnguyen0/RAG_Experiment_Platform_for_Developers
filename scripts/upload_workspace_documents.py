from __future__ import annotations

import argparse
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bulk upload .md/.txt documents into a workspace.",
    )
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="Target workspace id, for example: ws_123abc456def",
    )
    parser.add_argument(
        "--docs-dir",
        default="sample_data/squad_eval_pack/documents",
        help="Folder containing .md/.txt files.",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Backend API base URL.",
    )
    return parser.parse_args()


def iter_document_files(docs_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.md", "*.txt"):
        files.extend(docs_dir.glob(pattern))
    return sorted(files)


def upload_document(
    client: httpx.Client,
    workspace_id: str,
    file_path: Path,
) -> tuple[bool, str]:
    url = f"/workspaces/{workspace_id}/documents/upload"
    with file_path.open("rb") as file_obj:
        response = client.post(
            url,
            files={"file": (file_path.name, file_obj, "text/plain")},
        )

    if response.is_success:
        payload = response.json()
        return True, f"OK {file_path.name} -> {payload.get('id', '(no id)')}"

    try:
        error_detail = response.json().get("detail", response.text)
    except Exception:
        error_detail = response.text

    return False, f"FAIL {file_path.name} -> {response.status_code} {error_detail}"


def main() -> None:
    args = parse_args()
    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Documents folder not found: {docs_dir}")

    files = iter_document_files(docs_dir)
    if not files:
        raise ValueError(f"No .md or .txt files found in: {docs_dir}")

    print(f"Workspace: {args.workspace_id}")
    print(f"Docs dir: {docs_dir}")
    print(f"API base: {args.api_base}")
    print(f"Files: {len(files)}")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    with httpx.Client(base_url=args.api_base, timeout=60.0) as client:
        for index, file_path in enumerate(files, start=1):
            ok, message = upload_document(client, args.workspace_id, file_path)
            print(f"[{index:03d}/{len(files):03d}] {message}")
            if ok:
                success_count += 1
            else:
                fail_count += 1

    print("-" * 60)
    print(f"Done. success={success_count}, failed={fail_count}")
    if fail_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
