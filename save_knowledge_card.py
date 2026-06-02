#!/usr/bin/env python3
"""Save a structured social-content knowledge card as Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional


def slugify(value: str, fallback: str = "knowledge-card") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_.]+", "-", value)
    value = value.strip("-")
    return value[:80] or fallback


def parse_tags(raw: str) -> List[str]:
    if not raw:
        return []
    parts = re.split(r"[,;，；]\s*", raw)
    return [part.strip() for part in parts if part.strip()]


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


def load_content_object(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def nested_get(data: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def front_matter(args: argparse.Namespace, tags: Iterable[str]) -> str:
    today = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "---",
        f"title: {yaml_quote(args.title)}",
        f"platform: {yaml_quote(args.platform)}",
        f"source_url: {yaml_quote(args.source_url)}",
        f"author: {yaml_quote(args.author)}",
        f"published: {yaml_quote(args.published)}",
        f"extracted_at: {yaml_quote(today)}",
        f"action: {yaml_quote(args.action)}",
        f"confidence: {yaml_quote(args.confidence)}",
        "tags:",
    ]
    tag_list = list(tags)
    if tag_list:
        lines.extend(f"  - {yaml_quote(tag)}" for tag in tag_list)
    else:
        lines.append("  - \"social-content\"")
    lines.append("---")
    return "\n".join(lines)


def unique_path(directory: Path, filename: str) -> Path:
    path = directory / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def read_body(path: str | None) -> str:
    if not path:
        return (
            "## Source Snapshot\n\n"
            "- Fill in visible metadata and access method.\n\n"
            "## Core Ideas\n\n"
            "- Fill in distilled points.\n\n"
            "## Reusable Patterns\n\n"
            "- Fill in reusable structure, hooks, or evidence patterns.\n\n"
            "## Notes\n\n"
            "- Fill in uncertainties or follow-up ideas.\n"
        )
    return Path(path).read_text(encoding="utf-8").strip() + "\n"


def bullet_list(items: Iterable[Any], fallback: str) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return f"- {fallback}\n"
    return "".join(f"- {item}\n" for item in values)


def body_from_content_object(obj: Dict[str, Any]) -> str:
    title = obj.get("title", "")
    platform = obj.get("platform", "")
    source_url = obj.get("source_url", "")
    author = nested_get(obj, "author", "name")
    method = nested_get(obj, "extraction", "method")
    confidence = nested_get(obj, "extraction", "confidence")
    core_ideas = as_list(nested_get(obj, "knowledge", "core_ideas", default=[]))
    reusable_patterns = as_list(nested_get(obj, "knowledge", "reusable_patterns", default=[]))
    notes = as_list(nested_get(obj, "extraction", "notes", default=[]))
    summary = nested_get(obj, "actions", "summary")

    lines = [
        "## Source Snapshot",
        "",
        f"- Platform: {platform or 'unknown'}",
        f"- Source: {source_url or 'unknown'}",
        f"- Author/Account: {author or 'unknown'}",
        f"- Access method: {method or 'unknown'}",
        f"- Confidence: {confidence or 'medium'}",
        "",
        "## Core Ideas",
        "",
    ]
    if core_ideas:
        lines.append(bullet_list(core_ideas, "No core ideas recorded.").rstrip())
    elif summary:
        lines.append(str(summary).strip())
    else:
        body_text = nested_get(obj, "content", "body_text")
        excerpt = str(body_text).strip()[:800]
        lines.append(excerpt or "- No core ideas recorded.")

    image_items = as_list(obj.get("image_understanding"))
    useful_images = [
        item for item in image_items
        if isinstance(item, dict)
        and any(str(item.get(key, "")).strip() for key in ("visible_text", "visual_summary", "hook_analysis", "uncertainty"))
    ]
    if useful_images:
        lines.extend(["", "## Image Understanding", ""])
        for item in useful_images:
            label = item.get("image_id") or f"image-{item.get('order', '')}"
            lines.append(f"### {label}")
            if item.get("content_role"):
                lines.append(f"- Role: {item['content_role']}")
            if item.get("visible_text"):
                lines.append(f"- Visible text: {item['visible_text']}")
            if item.get("visual_summary"):
                lines.append(f"- Visual summary: {item['visual_summary']}")
            if item.get("hook_analysis"):
                lines.append(f"- Hook analysis: {item['hook_analysis']}")
            if item.get("uncertainty"):
                lines.append(f"- Uncertainty: {item['uncertainty']}")
            lines.append("")

    lines.extend(["## Reusable Patterns", "", bullet_list(reusable_patterns, "No reusable patterns recorded.").rstrip()])
    lines.extend(["", "## Notes", "", bullet_list(notes, "No extra notes.").rstrip()])
    if title:
        lines.extend(["", f"Original title: {title}"])
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a Markdown knowledge card.")
    parser.add_argument("--kb-dir", default="markdown", help="Knowledge base directory. Defaults to ./markdown")
    parser.add_argument("--content-object", help="Normalized content-object JSON file")
    parser.add_argument("--title")
    parser.add_argument("--platform", default="unknown", choices=["wechat", "xiaohongshu", "rednote", "unknown"])
    parser.add_argument("--source-url", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--published", default="")
    parser.add_argument("--action", default="加入知识库")
    parser.add_argument("--confidence", default="medium", choices=["high", "medium", "low"])
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--body-file", help="Markdown body file to append after front matter")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Filename date prefix")
    args = parser.parse_args()

    obj = load_content_object(args.content_object)
    if obj:
        args.title = args.title or obj.get("title", "")
        if args.platform == "unknown":
            args.platform = obj.get("platform", "unknown")
        args.source_url = args.source_url or obj.get("source_url", "")
        args.author = args.author or nested_get(obj, "author", "name")
        args.published = args.published or obj.get("published_at", "")
        if args.confidence == "medium":
            args.confidence = nested_get(obj, "extraction", "confidence", default="medium")
        if not args.tags:
            args.tags = ",".join(as_list(nested_get(obj, "knowledge", "tags", default=[])))

    if not args.title:
        parser.error("--title is required unless --content-object provides title")

    kb_dir = Path(args.kb_dir)
    kb_dir.mkdir(parents=True, exist_ok=True)

    tags = parse_tags(args.tags)
    body = read_body(args.body_file) if args.body_file else (body_from_content_object(obj) if obj else read_body(None))
    platform = slugify(args.platform, "source")
    title_slug = slugify(args.title)
    filename = f"{args.date}-{platform}-{title_slug}.md"
    path = unique_path(kb_dir, filename)

    content = f"{front_matter(args, tags)}\n\n# {args.title}\n\n{body}"
    path.write_text(content, encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
