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
    "onnx/*.onnx",
    "onnx/*.onnx_data",
]


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


def add_model_to_zip(zf: zipfile.ZipFile, model_dir: Path, repo: str) -> None:
    for path in sorted(model_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(model_dir).as_posix()
        archive_name = f"{repo}/resolve/main/{rel}"
        zf.write(path, archive_name, compress_type=zipfile.ZIP_STORED)


def write_one_pack(dist: Path, cache_dir: Path, pack_name: str, models: list[dict], download: bool, suffix: str = "") -> Path:
    pack_path = dist / f"dishonesty-model-pack-{pack_name}{suffix}.zip"
    manifest = {
        "pack": pack_name,
        "part": suffix.lstrip("-") or "single",
        "format": "transformers-cache-v1",
        "models": models,
        "import": "Open Study Tools, go to Model Hub, click Import Release Pack, then choose this zip.",
    }

    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2), compress_type=zipfile.ZIP_STORED)
        for model in models:
            repo = model["repo"]
            model_dir = cache_dir / repo.replace("/", "__")
            if download:
                snapshot_model(repo, model_dir)
            if model_dir.exists():
                add_model_to_zip(zf, model_dir, repo)
    return pack_path


def write_pack(root: Path, dist: Path, cache_dir: Path, pack_name: str, models: list[dict], download: bool) -> None:
    written = []
    if len(models) == 1:
        written.append(write_one_pack(dist, cache_dir, pack_name, models, download))
    else:
        for index, model in enumerate(models, start=1):
            safe_id = model["id"].replace("_", "-")
            suffix = f"-part-{index:02d}-{safe_id}"
            written.append(write_one_pack(dist, cache_dir, pack_name, [model], download, suffix))

    readme = dist / f"dishonesty-model-pack-{pack_name}.txt"
    readme.write_text(
        f"Dishonesty {pack_name} model pack\n\n"
        "Import each listed ZIP in Model Hub using Import Release Pack.\n"
        "Multi-model packs are split so GitHub can host them under its release asset size limit.\n"
        "The ZIPs are stored, not compressed, so the browser can import them without extra libraries.\n\n"
        + "\n".join(f"- {m['name']} ({m['repo']})" for m in models)
        + "\n\nAssets:\n"
        + "\n".join(f"- {path.name}" for path in written)
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--dist", default="dist", type=Path)
    parser.add_argument("--cache", default=".model-cache", type=Path)
    parser.add_argument("--download", action="store_true")
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


if __name__ == "__main__":
    main()
