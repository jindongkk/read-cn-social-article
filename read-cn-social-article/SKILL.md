---
name: read-cn-social-article
description: Read, extract, summarize, deconstruct, rewrite, or save Chinese social image-text articles from WeChat Official Account links, mp.weixin.qq.com URLs, Xiaohongshu/RedNote notes, xiaohongshu.com or xhslink.com links, shared screenshots, and saved HTML. Use when Codex needs to recover title, author/account, publish time, body text, images, captions, product lists, links, create summaries, perform viral-content breakdowns, produce original rewrites from structure, or save structured Markdown knowledge cards.
---

# Read CN Social Article

## Overview

Use this skill to turn Chinese social image-text posts into usable content assets. Always read once into the standard content object, then run one of four actions: 总结, 爆款拆解, 仿写, or 加入知识库.

Respect access controls. Do not bypass paywalls, private posts, account restrictions, CAPTCHAs, or login walls. If the user can provide an authenticated browser session, screenshot, exported HTML, or copied text, work from that user-provided access.

## Quick Path

1. Identify the source:
   - `mp.weixin.qq.com`: WeChat Official Account article.
   - `xiaohongshu.com`, `xhslink.com`, `xhs.cn`: Xiaohongshu/RedNote note.
   - image files or screenshots: use visual reading/OCR and ask for missing pages only if necessary.
2. Preserve provenance: record URL, access time, account/author, title, publish time if visible, and whether the result came from HTML, browser DOM, screenshot, visual reading, or OCR.
3. Extract in this order:
   - Structured text and metadata.
   - Images, visible captions, and image text.
   - Links, product names, location tags, hashtags, and engagement counts when relevant.
4. Normalize the result with the standard content object. Use `scripts/normalize_content_object.py` when converting from Markdown or JSON.
5. Run the requested action. If no action is specified, default to 总结 and offer the other actions succinctly.

## Standard Content Object

All actions should consume one normalized object instead of re-reading the source. See `references/content-object.md` for the schema.

Minimum required fields:

- `platform`
- `source_url`
- `title`
- `author.name`
- `published_at`
- `extraction.method`
- `extraction.confidence`
- `content.markdown`
- `media.images`
- `image_understanding`

Create or normalize an object with:

```bash
python <skill-dir>/scripts/normalize_content_object.py --from-markdown article.md --output content-object.json
```

For Xiaohongshu screenshots or browser-read content, assemble a draft JSON manually, then run:

```bash
python <skill-dir>/scripts/normalize_content_object.py draft-content.json --output content-object.json
```

## Actions

Treat UI buttons or natural-language requests as these actions:

- `总结`: explain the core idea, useful facts, structure, audience, and takeaways.
- `爆款拆解`: analyze title, hook, opening, narrative structure, emotional value, credibility devices, share triggers, conversion path, and reusable patterns.
- `仿写`: extract a structure template and write original content for the user's new topic. Do not imitate phrasing closely or preserve distinctive expression from the source.
- `加入知识库`: save a structured Markdown knowledge card in the current workspace's `markdown/` folder by default.

Always preserve the source URL and extraction method across actions. For multiple links, process each source independently, then optionally add a cross-source comparison.

## WeChat Official Account

Use `scripts/wechat_article_to_markdown.py` first for public `mp.weixin.qq.com` article URLs or saved HTML:

```bash
python <skill-dir>/scripts/wechat_article_to_markdown.py "<url>" --output article.md --download-images
```

If the script fails because WeChat blocks direct HTTP access, open the URL in a browser session, wait for the article to render, scroll to lazy-load images, save the full HTML if possible, then run:

```bash
python <skill-dir>/scripts/wechat_article_to_markdown.py saved.html --output article.md --download-images
```

When direct extraction is incomplete, inspect these selectors and variables in the rendered page:

- Title: `#activity-name`
- Account: `#js_name`, `.profile_nickname`
- Author: `#js_author_name`
- Body: `#js_content`
- Cover: JavaScript variable `msg_cdn_url`
- Publish timestamp: JavaScript variable `ct` or visible metadata text
- Images: prefer `data-src`, then `src`; use `https://mp.weixin.qq.com/` as referer when downloading

## Xiaohongshu / RedNote

Prefer a real browser session because Xiaohongshu content is heavily dynamic and often requires login state.

1. Resolve short links (`xhslink.com`, `xhs.cn`) in a browser and keep the final note URL.
2. Let the page fully render; if logged out or challenged, ask the user for a screenshot/export or for permission to use their existing logged-in browser session.
3. Capture the visible note data into the content object:
   - Title or first line, body text, hashtags, mentions, location, product/location cards.
   - Author handle, note date if visible, like/collect/comment counts if requested.
   - All carousel images in order; click/advance the carousel and record captions or text embedded in each image.
4. Perform image understanding for every visible carousel image:
   - `visible_text`: text read from the image.
   - `visual_summary`: what the image shows.
   - `content_role`: cover hook, evidence, example, tutorial step, quote card, product display, atmosphere, or ending CTA.
   - `hook_analysis`: why the cover or image may stop scrolling.
   - `confidence` and `uncertainty`: mark OCR/visual ambiguity explicitly.
5. Distinguish DOM text from image-derived text. Do not merge uncertain OCR into the body without labeling it.
6. If local tools such as `XHS-Downloader`, `xhs`, `AutoCLI`, `Agent-Reach`, or an MCP reader are already installed, use them only as helpers and verify their output against the rendered page or screenshots.

## Outputs

For summaries, include:

- Source and access method.
- Title/account/date when available.
- Key claims or steps, grouped by the user's requested purpose.
- Image-derived text separately if it may be OCR-derived or uncertain.
- For Xiaohongshu, include a short "image understanding" section when images carry meaningful content.

For Markdown conversion, use:

```markdown
# Title

Source: <url>
Account/Author: ...
Published: ...
Extracted: ...
Method: HTML | browser DOM | screenshot/OCR

...
```

Keep images in article order. If images are downloaded locally, use relative paths from the Markdown file.

## Knowledge Base

For `加入知识库`, create or use a folder named `markdown/` in the current workspace unless the user provides another path. Do not store user knowledge cards inside the skill folder.

Use `scripts/save_knowledge_card.py` to write the final card:

```bash
python <skill-dir>/scripts/save_knowledge_card.py --kb-dir markdown --title "<title>" --platform wechat --source-url "<url>" --author "<account>" --published "<date>" --tags "tag1,tag2" --body-file card-body.md
```

If a content object exists, prefer:

```bash
python <skill-dir>/scripts/save_knowledge_card.py --kb-dir markdown --content-object content-object.json
```

Generate each card with:

- YAML front matter: title, platform, source URL, author/account, published date, extracted date, action, tags, and confidence.
- `## Source Snapshot`: visible metadata and access method.
- `## Core Ideas`: distilled points worth remembering.
- `## Reusable Patterns`: structure, hooks, framing, examples, or evidence patterns that can be reused ethically.
- `## Notes`: uncertainties, OCR caveats, and follow-up ideas.

Use one Markdown file per source. Prefer filenames like `2026-06-02-wechat-short-title.md`; let the script sanitize and de-duplicate filenames.

## Fallbacks

- If URL extraction fails, ask for screenshots, copied text, exported HTML, or a browser session rather than repeatedly retrying the same blocked request.
- If only screenshots are available, read each image, preserve page/image order, and label uncertain OCR.
- If content appears private, removed, or region/account restricted, report that state and summarize only what is visible.

## References

Read `references/content-object.md` before creating or consuming normalized content objects. Read `references/platform-notes.md` when choosing between GitHub-inspired approaches, browser extraction, direct HTTP extraction, and OCR fallback.
