#!/usr/bin/env python3
"""Extract a public WeChat Official Account article to Markdown.

Uses only Python's standard library so the skill remains portable. It accepts a
mp.weixin.qq.com URL, a local HTML file, or "-" for stdin.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1 MicroMessenger/8.0"
)

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


def read_cookie_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return Path(path).read_text(encoding="utf-8").strip()


def fetch_url(url: str, cookie: Optional[str]) -> Tuple[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://mp.weixin.qq.com/",
    }
    if cookie:
        headers["Cookie"] = cookie

    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset()
        if not charset:
            head = raw[:4096].decode("ascii", errors="ignore")
            match = re.search(r"charset=['\"]?([-\w]+)", head, re.I)
            charset = match.group(1) if match else "utf-8"
        final_url = resp.geturl()
    return raw.decode(charset, errors="replace"), final_url


def read_input(source: str, cookie: Optional[str]) -> Tuple[str, str]:
    if source == "-":
        return sys.stdin.read(), "stdin"
    if re.match(r"https?://", source, re.I):
        return fetch_url(source, cookie)
    path = Path(source)
    data = path.read_bytes()
    try:
        return data.decode("utf-8"), str(path)
    except UnicodeDecodeError:
        return data.decode("gb18030", errors="replace"), str(path)


def strip_tags(fragment: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", "", fragment)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    return html.unescape(text).strip()


def first_match(patterns: Iterable[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            value = match.group(1)
            value = value.replace("\\/", "/")
            return strip_tags(value)
    return None


def js_string_match(names: Iterable[str], text: str) -> Optional[str]:
    for name in names:
        pattern = rf"{re.escape(name)}\s*=\s*(['\"])(.*?)\1"
        match = re.search(pattern, text, re.S)
        if match:
            return html.unescape(match.group(2).replace("\\/", "/")).strip()
    return None


def extract_publish_time(text: str) -> Optional[str]:
    match = re.search(r"\bct\s*=\s*['\"]?(\d{9,13})['\"]?", text)
    if match:
        value = int(match.group(1))
        if value > 10_000_000_000:
            value = value // 1000
        try:
            return dt.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, OverflowError, ValueError):
            pass

    return js_string_match(("publish_time", "oriCreateTime"), text)


def extract_metadata(text: str, source: str) -> Dict[str, Optional[str]]:
    title = first_match(
        (
            r"<h1[^>]+id=['\"]activity-name['\"][^>]*>(.*?)</h1>",
            r"<title[^>]*>(.*?)</title>",
            r"var\s+msg_title\s*=\s*['\"](.*?)['\"]",
        ),
        text,
    )
    if title:
        title = re.sub(r"\s*-\s*微信公众平台\s*$", "", title).strip()

    account = first_match(
        (
            r"<a[^>]+id=['\"]js_name['\"][^>]*>(.*?)</a>",
            r"<span[^>]+class=['\"][^'\"]*profile_nickname[^'\"]*['\"][^>]*>(.*?)</span>",
            r"<strong[^>]+class=['\"][^'\"]*profile_nickname[^'\"]*['\"][^>]*>(.*?)</strong>",
        ),
        text,
    )
    author = first_match((r"<em[^>]+id=['\"]js_author_name['\"][^>]*>(.*?)</em>",), text)
    cover = js_string_match(("msg_cdn_url", "cdn_url_1_1"), text)
    description = js_string_match(("msg_desc",), text)

    return {
        "title": title,
        "account": account,
        "author": author,
        "published": extract_publish_time(text),
        "cover": cover,
        "description": description,
        "source": source,
    }


class WeChatContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_content = False
        self.depth = 0
        self.parts: List[str] = []
        self.images: List[str] = []
        self.link_stack: List[Optional[str]] = []

    def handle_starttag(self, tag: str, attrs_list: List[Tuple[str, Optional[str]]]) -> None:
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        tag = tag.lower()

        if not self.in_content:
            if attrs.get("id") == "js_content":
                self.in_content = True
                self.depth = 1
                self._newline()
            return

        if tag not in VOID_TAGS:
            self.depth += 1

        if tag in BLOCK_TAGS:
            self._newline()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self.parts.append("#" * level + " ")
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "blockquote":
            self.parts.append("> ")
        elif tag == "li":
            self.parts.append("- ")
        elif tag == "br":
            self._newline()
        elif tag == "a":
            href = attrs.get("href")
            self.link_stack.append(href)
            self.parts.append("[")
        elif tag == "img":
            url = (
                attrs.get("data-src")
                or attrs.get("data-original")
                or attrs.get("data-backsrc")
                or attrs.get("src")
            )
            if url and not url.startswith("data:"):
                alt = attrs.get("alt") or attrs.get("title") or f"image-{len(self.images) + 1}"
                url = html.unescape(url)
                self.images.append(url)
                self._newline()
                self.parts.append(f"![{clean_inline(alt)}]({url})")
                self._newline()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.in_content:
            return

        if tag == "a":
            href = self.link_stack.pop() if self.link_stack else None
            if href:
                self.parts.append(f"]({html.unescape(href)})")
            else:
                self.parts.append("]")
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag in BLOCK_TAGS:
            self._newline()

        if tag not in VOID_TAGS:
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False

    def handle_data(self, data: str) -> None:
        if not self.in_content:
            return
        text = clean_inline(data)
        if text:
            self.parts.append(text)

    def _newline(self) -> None:
        if not self.parts or not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def markdown(self) -> str:
        return clean_markdown("".join(self.parts))


def clean_inline(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    return value.strip()


def clean_markdown(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    lines = [line.strip() if not line.startswith(("    ", "\t")) else line.rstrip() for line in value.split("\n")]
    return "\n".join(lines).strip() + "\n"


def extract_markdown(html_text: str) -> Tuple[str, List[str]]:
    parser = WeChatContentParser()
    parser.feed(html_text)
    return parser.markdown(), parser.images


def safe_filename(value: str, fallback: str = "wechat-article") -> str:
    value = value or fallback
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    return (value[:80] or fallback).strip()


def guess_extension(url: str, content_type: Optional[str]) -> str:
    if content_type:
        mime = content_type.split(";", 1)[0].strip().lower()
        ext = mimetypes.guess_extension(mime)
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    parsed = urlparse(url)
    suffix = Path(unquote(parsed.path)).suffix
    if suffix and len(suffix) <= 5:
        return suffix
    return ".jpg"


def download_images(markdown: str, output_path: Path, referer: str, cookie: Optional[str]) -> str:
    image_urls = []
    for match in re.finditer(r"!\[[^\]]*\]\((https?://[^)]+)\)", markdown):
        url = match.group(1)
        if url not in image_urls:
            image_urls.append(url)

    if not image_urls:
        return markdown

    image_dir = output_path.parent / f"{output_path.stem}_images"
    image_dir.mkdir(parents=True, exist_ok=True)
    replacements: Dict[str, str] = {}

    for index, url in enumerate(image_urls, start=1):
        headers = {"User-Agent": USER_AGENT, "Referer": referer or "https://mp.weixin.qq.com/"}
        if cookie:
            headers["Cookie"] = cookie
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
                ext = guess_extension(url, resp.headers.get("Content-Type"))
        except Exception as exc:  # Keep Markdown usable even if one image fails.
            print(f"warning: failed to download image {index}: {exc}", file=sys.stderr)
            continue

        filename = f"image-{index:02d}{ext}"
        path = image_dir / filename
        path.write_bytes(data)
        replacements[url] = f"{image_dir.name}/{filename}"

    for original, local in replacements.items():
        markdown = markdown.replace(original, local)
    return markdown


def build_document(metadata: Dict[str, Optional[str]], body: str, method: str) -> str:
    title = metadata.get("title") or "WeChat Article"
    lines = [f"# {title}", ""]
    for label, key in (
        ("Source", "source"),
        ("Account", "account"),
        ("Author", "author"),
        ("Published", "published"),
        ("Cover", "cover"),
    ):
        value = metadata.get(key)
        if value:
            lines.append(f"{label}: {value}")
    lines.append(f"Method: {method}")
    lines.append("")
    if metadata.get("description"):
        lines.extend([f"> {metadata['description']}", ""])
    lines.append(body.strip())
    return clean_markdown("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a WeChat Official Account article to Markdown.")
    parser.add_argument("source", help="mp.weixin.qq.com URL, local HTML file, or '-' for stdin")
    parser.add_argument("--output", "-o", help="Markdown output path. Defaults to stdout unless images are downloaded.")
    parser.add_argument("--download-images", action="store_true", help="Download article images beside the Markdown file")
    parser.add_argument("--cookie-file", help="Optional text file containing a raw Cookie header")
    parser.add_argument("--json", action="store_true", help="Print JSON with metadata and markdown instead of Markdown")
    args = parser.parse_args()

    cookie = read_cookie_file(args.cookie_file)
    html_text, final_source = read_input(args.source, cookie)
    metadata = extract_metadata(html_text, final_source)
    body, images = extract_markdown(html_text)
    method = "HTML"

    if not body.strip():
        print("warning: no #js_content body extracted; the page may be blocked or not fully rendered.", file=sys.stderr)

    document = build_document(metadata, body, method)

    output_path: Optional[Path] = Path(args.output) if args.output else None
    if args.download_images:
        if not output_path:
            output_path = Path(safe_filename(metadata.get("title") or "wechat-article") + ".md")
        document = download_images(document, output_path, final_source, cookie)

    if args.json:
        payload = {
            "metadata": metadata,
            "image_count": len(images),
            "markdown": document,
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = document

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(str(output_path))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
