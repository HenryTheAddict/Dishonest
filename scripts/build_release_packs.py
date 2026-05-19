#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

PACKS = {
    "small": [
        {
            "id": "qwen-0.5b",
            "name": "Qwen 2.5 0.5B",
            "repo": "onnx-community/Qwen2.5-0.5B-Instruct",
        },
    ],
    "good": [
        {
            "id": "gemma-3-1b",
            "name": "Gemma 3 1B IT",
            "repo": "onnx-community/gemma-3-1b-it-ONNX-GQA",
        },
        {
            "id": "qwen-coder-0.5b",
            "name": "Qwen 2.5 Coder 0.5B",
            "repo": "onnx-community/Qwen2.5-Coder-0.5B-Instruct",
        },
    ],
    "all": [
        {
            "id": "qwen-0.5b",
            "name": "Qwen 2.5 0.5B",
            "repo": "onnx-community/Qwen2.5-0.5B-Instruct",
        },
        {
            "id": "qwen-coder-0.5b",
            "name": "Qwen 2.5 Coder 0.5B",
            "repo": "onnx-community/Qwen2.5-Coder-0.5B-Instruct",
        },
        {
            "id": "gemma-3-1b",
            "name": "Gemma 3 1B IT",
            "repo": "onnx-community/gemma-3-1b-it-ONNX-GQA",
        },
    ],
}

ALLOW_PATTERNS = [
    "*.json",
    "*.txt",
    "*.model",
    "*.tiktoken",
    "*.jinja",
    "tokenizer*",
    "onnx/model_q4.onnx",
    "onnx/model_q4.onnx_data",
]

# Keep assets well below GitHub's 2 GiB release-asset ceiling. Individual
# model weight files may be larger than this target, but still must be below
# GitHub's hard limit to upload as a single stored ZIP entry.
MAX_RELEASE_ASSET_BYTES = 700_000_000


def write_app_zip(root: Path, dist: Path) -> None:
    with zipfile.ZipFile(dist / "dishonesty-app.zip", "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ["index.html", "README.md", ".gitattributes"]:
            path = root / name
            if path.exists():
                zf.write(path, name)


def snapshot_model(repo: str, target: Path) -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo,
        local_dir=target,
        local_dir_use_symlinks=False,
        allow_patterns=ALLOW_PATTERNS,
    )


def iter_model_files(model_dir: Path, repo: str) -> list[tuple[Path, str, int]]:
    files = []
    for path in sorted(model_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(model_dir).as_posix()
        archive_name = f"{repo}/resolve/main/{rel}"
        files.append((path, archive_name, path.stat().st_size))
    return files


def write_one_pack(dist: Path, pack_name: str, models: list[dict], files: list[tuple[Path, str, int]], part: int | None = None) -> Path:
    suffix = "" if part is None else f"-part-{part:02d}"
    pack_path = dist / f"dishonesty-model-pack-{pack_name}{suffix}.zip"
    manifest = {
        "pack": pack_name,
        "part": part or "single",
        "format": "transformers-cache-v1",
        "models": models,
        "import": "Open Study Tools, go to Model Hub, click Import Release Pack, then choose this zip.",
    }

    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2), compress_type=zipfile.ZIP_STORED)
        for path, archive_name, _size in files:
            zf.write(path, archive_name, compress_type=zipfile.ZIP_STORED)
    print(f"wrote {pack_path.name}: {pack_path.stat().st_size:,} bytes")
    return pack_path


def collect_pack_files(cache_dir: Path, models: list[dict], download: bool) -> list[tuple[Path, str, int]]:
    all_files = []
    for model in models:
        repo = model["repo"]
        model_dir = cache_dir / repo.replace("/", "__")
        if download:
            snapshot_model(repo, model_dir)
        if model_dir.exists():
            all_files.extend(iter_model_files(model_dir, repo))
    return all_files


def write_pack(root: Path, dist: Path, cache_dir: Path, pack_name: str, models: list[dict], download: bool) -> None:
    all_files = collect_pack_files(cache_dir, models, download)

    parts: list[list[tuple[Path, str, int]]] = []
    current: list[tuple[Path, str, int]] = []
    current_size = 0
    for item in all_files:
        size = item[2]
        if current and current_size + size > MAX_RELEASE_ASSET_BYTES:
            parts.append(current)
            current = []
            current_size = 0
        if size > 2_000_000_000:
            raise RuntimeError(f"{item[1]} is too large for a GitHub release asset by itself: {size:,} bytes")
        current.append(item)
        current_size += size
    if current:
        parts.append(current)

    written = []
    if len(parts) <= 1:
        written.append(write_one_pack(dist, pack_name, models, parts[0] if parts else []))
    else:
        for index, files in enumerate(parts, start=1):
            written.append(write_one_pack(dist, pack_name, models, files, index))

    readme = dist / f"dishonesty-model-pack-{pack_name}.txt"
    readme.write_text(
        f"Dishonesty {pack_name} model pack\n\n"
        "Import each listed ZIP in Model Hub using Import Release Pack.\n"
        "Large packs are split by file size so GitHub can host them under its release asset size limit.\n"
        "The ZIPs are stored, not compressed, so the browser can import them without extra libraries.\n\n"
        + "\n".join(f"- {m['name']} ({m['repo']})" for m in models)
        + "\n\nAssets:\n"
        + "\n".join(f"- {path.name}" for path in written)
        + "\n",
        encoding="utf-8",
    )


def write_megapack(dist: Path, cache_dir: Path, download: bool) -> None:
    models = PACKS["all"]
    files = collect_pack_files(cache_dir, models, download)
    path = dist / "models.zip"
    manifest = {
        "pack": "megapack",
        "format": "transformers-cache-v1",
        "models": models,
        "import": "Put this file next to index.html as models.zip, serve the folder over HTTP, or import it manually from Model Hub.",
    }

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2), compress_type=zipfile.ZIP_STORED)
        for file_path, archive_name, _size in files:
            zf.write(file_path, archive_name, compress_type=zipfile.ZIP_STORED)
    print(f"wrote {path.name}: {path.stat().st_size:,} bytes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--dist", default="dist", type=Path)
    parser.add_argument("--cache", default=".model-cache", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--megapack", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    dist = args.dist.resolve()
    cache_dir = args.cache.resolve()
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    write_app_zip(root, dist)
    for pack_name, models in PACKS.items():
        write_pack(root, dist, cache_dir, pack_name, models, args.download)
    if args.megapack:
        write_megapack(dist, cache_dir, args.download)


if __name__ == "__main__":
    main()
