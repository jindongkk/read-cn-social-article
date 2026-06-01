#!/usr/bin/env python3
"""Normalize Chinese social article data into the skill content object."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple


VERSION = "1.0"


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def empty_object() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "platform": "unknown",
        "source_url": "",
        "canonical_url": "",
        "title": "",
        "author": {"name": "", "handle": "", "profile_url": ""},
        "published_at": "",
        "extracted_at": now(),
        "extraction": {"method": "mixed", "confidence": "medium", "notes": []},
        "content": {"body_text": "", "markdown": "", "hashtags": [], "mentions": [], "links": []},
        "media": {"cover": None, "images": [], "videos": []},
        "image_understanding": [],
        "engagement": {"likes": None, "collects": None, "comments": None, "shares": None},
        "knowledge": {"topics": [], "tags": [], "entities": [], "core_ideas": [], "reusable_patterns": []},
        "actions": {"summary": "", "deconstruction": {}, "rewrite_template": ""},
    }


def deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        elif value is not None:
            base[key] = value
    return base


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [value] if value else []
    return [value]


def infer_platform(url: str, fallback: str = "unknown") -> str:
    lower = (url or "").lower()
    if "mp.weixin.qq.com" in lower:
        return "wechat"
    if "xiaohongshu.com" in lower or "xhslink.com" in lower or "xhs.cn" in lower:
        return "xiaohongshu"
    return fallback


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def strip_markdown_images(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)
    value = re.sub(r"\[[^\]]*\]\(([^)]+)\)", "", value)
    value = re.sub(r"[*_`>#-]+", " ", value)
    value = re.sub(r"[ \t]+", " ", value)
    return clean_text(value)


def parse_markdown_image(line: str, order: int) -> Optional[Dict[str, Any]]:
    match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", line)
    if not match:
        return None
    return {
        "id": f"img-{order:03d}",
        "order": order,
        "role": "cover" if order == 1 else "inline",
        "local_path": match.group(2) if not re.match(r"https?://", match.group(2), re.I) else "",
        "source_url": match.group(2) if re.match(r"https?://", match.group(2), re.I) else "",
        "alt": match.group(1),
        "caption": "",
    }


def parse_metadata_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    match = re.match(r"^([A-Za-z][A-Za-z /_-]*):\s*(.*?)\s*$", line)
    if not match:
        return None, None
    return match.group(1).strip().lower(), match.group(2).strip()


def object_from_markdown(path: Path, platform_arg: str = "unknown") -> Dict[str, Any]:
    markdown = path.read_text(encoding="utf-8")
    lines = markdown.splitlines()
    obj = empty_object()
    obj["content"]["markdown"] = clean_text(markdown)
    obj["extraction"]["method"] = "HTML"
    obj["extraction"]["confidence"] = "high"

    body_start = 0
    for index, line in enumerate(lines):
        if line.startswith("# ") and not obj["title"]:
            obj["title"] = line[2:].strip()
            body_start = index + 1
            continue
        key, value = parse_metadata_line(line)
        if not key:
            if obj["title"] and line.strip() and not line.startswith(">"):
                body_start = index
                break
            continue
        body_start = index + 1
        if key == "source":
            obj["source_url"] = value
            obj["canonical_url"] = value
        elif key == "account":
            obj["author"]["name"] = value
        elif key == "author" and not obj["author"]["name"]:
            obj["author"]["name"] = value
        elif key == "published":
            obj["published_at"] = value
        elif key == "method":
            obj["extraction"]["method"] = value
        elif key == "cover" and value:
            obj["media"]["cover"] = {"id": "cover", "order": 0, "role": "cover", "source_url": value, "local_path": "", "alt": "cover", "caption": ""}

    image_order = 1
    images: List[Dict[str, Any]] = []
    for line in lines:
        image = parse_markdown_image(line, image_order)
        if image:
            images.append(image)
            image_order += 1
    obj["media"]["images"] = images
    obj["image_understanding"] = [
        {
            "image_id": image["id"],
            "order": image["order"],
            "visible_text": "",
            "visual_summary": "",
            "content_role": "cover hook" if image["role"] == "cover" else "unknown",
            "hook_analysis": "",
            "confidence": "low",
            "uncertainty": "Image is inventoried but has not been visually inspected yet.",
        }
        for image in images
    ]

    body = "\n".join(lines[body_start:])
    obj["content"]["body_text"] = strip_markdown_images(body)
    obj["content"]["hashtags"] = sorted(set(re.findall(r"#[\w\u4e00-\u9fff-]+", markdown)))
    obj["content"]["mentions"] = sorted(set(re.findall(r"@[\w\u4e00-\u9fff.-]+", markdown)))
    obj["content"]["links"] = sorted(set(re.findall(r"(?<!\()https?://[^\s)]+", markdown)))
    obj["platform"] = infer_platform(obj["source_url"], platform_arg)
    return obj


def normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
    merged = deep_merge(empty_object(), obj)
    merged["version"] = str(merged.get("version") or VERSION)
    merged["platform"] = infer_platform(merged.get("source_url", ""), merged.get("platform", "unknown"))
    merged["extracted_at"] = merged.get("extracted_at") or now()

    author = merged.get("author")
    if isinstance(author, str):
        merged["author"] = {"name": author, "handle": "", "profile_url": ""}
    else:
        merged["author"] = deep_merge({"name": "", "handle": "", "profile_url": ""}, author or {})

    extraction = merged.get("extraction") or {}
    merged["extraction"] = deep_merge({"method": "mixed", "confidence": "medium", "notes": []}, extraction)
    merged["extraction"]["notes"] = as_list(merged["extraction"].get("notes"))

    content = merged.get("content") or {}
    merged["content"] = deep_merge({"body_text": "", "markdown": "", "hashtags": [], "mentions": [], "links": []}, content)
    for key in ("hashtags", "mentions", "links"):
        merged["content"][key] = as_list(merged["content"].get(key))

    media = merged.get("media") or {}
    merged["media"] = deep_merge({"cover": None, "images": [], "videos": []}, media)
    merged["media"]["images"] = as_list(merged["media"].get("images"))
    merged["media"]["videos"] = as_list(merged["media"].get("videos"))

    normalized_images = []
    for index, image in enumerate(merged["media"]["images"], start=1):
        if isinstance(image, str):
            image = {"source_url": image if re.match(r"https?://", image, re.I) else "", "local_path": image if not re.match(r"https?://", image, re.I) else ""}
        image_obj = deep_merge(
            {"id": f"img-{index:03d}", "order": index, "role": "unknown", "local_path": "", "source_url": "", "alt": "", "caption": ""},
            image or {},
        )
        image_obj["id"] = image_obj.get("id") or f"img-{index:03d}"
        image_obj["order"] = image_obj.get("order") or index
        normalized_images.append(image_obj)
    merged["media"]["images"] = normalized_images

    existing_understanding = {item.get("image_id"): item for item in as_list(merged.get("image_understanding")) if isinstance(item, dict)}
    understanding = []
    for image in normalized_images:
        image_id = image["id"]
        item = existing_understanding.get(image_id, {})
        understanding.append(
            deep_merge(
                {
                    "image_id": image_id,
                    "order": image["order"],
                    "visible_text": "",
                    "visual_summary": "",
                    "content_role": "cover hook" if image.get("role") == "cover" else "unknown",
                    "hook_analysis": "",
                    "confidence": "low",
                    "uncertainty": "Image has not been visually inspected yet.",
                },
                item,
            )
        )
    merged["image_understanding"] = understanding

    knowledge = merged.get("knowledge") or {}
    merged["knowledge"] = deep_merge({"topics": [], "tags": [], "entities": [], "core_ideas": [], "reusable_patterns": []}, knowledge)
    for key in ("topics", "tags", "entities", "core_ideas", "reusable_patterns"):
        merged["knowledge"][key] = as_list(merged["knowledge"].get(key))

    actions = merged.get("actions") or {}
    merged["actions"] = deep_merge({"summary": "", "deconstruction": {}, "rewrite_template": ""}, actions)
    return merged


def apply_overrides(obj: Dict[str, Any], args: argparse.Namespace) -> None:
    for attr, key in (
        ("platform", "platform"),
        ("source_url", "source_url"),
        ("title", "title"),
        ("published", "published_at"),
        ("method", None),
        ("confidence", None),
    ):
        value = getattr(args, attr, None)
        if not value:
            continue
        if key:
            obj[key] = value
    if args.author:
        obj["author"]["name"] = args.author
    if args.method:
        obj["extraction"]["method"] = args.method
    if args.confidence:
        obj["extraction"]["confidence"] = args.confidence
    if args.tags:
        tags = [tag.strip() for tag in re.split(r"[,;，；]\s*", args.tags) if tag.strip()]
        obj["knowledge"]["tags"] = sorted(set(as_list(obj["knowledge"].get("tags")) + tags))


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Chinese social content into a standard content object.")
    parser.add_argument("input", nargs="?", help="Draft content-object JSON file")
    parser.add_argument("--from-markdown", help="Create object from article Markdown")
    parser.add_argument("--template", action="store_true", help="Print an empty content-object template")
    parser.add_argument("--output", "-o", help="Output JSON path. Defaults to stdout")
    parser.add_argument("--platform", choices=["wechat", "xiaohongshu", "rednote", "unknown"], help="Override platform")
    parser.add_argument("--source-url", help="Override source URL")
    parser.add_argument("--title", help="Override title")
    parser.add_argument("--author", help="Override author/account name")
    parser.add_argument("--published", help="Override publish time")
    parser.add_argument("--method", help="Override extraction method")
    parser.add_argument("--confidence", choices=["high", "medium", "low"], help="Override extraction confidence")
    parser.add_argument("--tags", help="Comma-separated knowledge tags")
    args = parser.parse_args()

    if args.template:
        obj = empty_object()
    elif args.from_markdown:
        obj = object_from_markdown(Path(args.from_markdown), args.platform or "unknown")
    elif args.input:
        obj = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        parser.error("provide an input JSON, --from-markdown, or --template")

    obj = normalize(obj)
    apply_overrides(obj, args)
    obj = normalize(obj)
    text = json.dumps(obj, ensure_ascii=False, indent=2)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(str(output))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
