from datetime import datetime
from pathlib import Path, PureWindowsPath

SHARED_ROOT = Path(r"\\fileserver2\Study Material")


def resolve_shared_path(relative_path=""):
    if not isinstance(relative_path, str):
        return None

    windows_path = PureWindowsPath(relative_path)

    if (
        windows_path.is_absolute()
        or windows_path.drive
        or ".." in windows_path.parts
    ):
        return None

    parts = [
        part
        for part in relative_path.replace("\\", "/").split("/")
        if part not in ("", ".")
    ]

    if any(part == ".." for part in parts):
        return None

    try:
        root = SHARED_ROOT.resolve()
        current = root.joinpath(*parts).resolve()
        current.relative_to(root)
        return current

    except (OSError, ValueError, PermissionError):
        return None


def get_shared_items(relative_path=""):
    current = resolve_shared_path(relative_path)

    if current is None or not current.is_dir():
        return None

    try:
        items = []

        for item in current.iterdir():
            try:
                stat = item.stat()

                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "path": str(item.relative_to(SHARED_ROOT.resolve())),
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                })
            except OSError:
                continue

        return sorted(
            items,
            key=lambda item: (not item["is_dir"], item["name"].lower())
        )

    except OSError:
        return None
