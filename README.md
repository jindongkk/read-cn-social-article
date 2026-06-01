# read-cn-social-article

A Codex Skill for reading and reusing Chinese social image-text posts from WeChat Official Account articles and Xiaohongshu/RedNote notes.

This skill turns social posts into reusable content assets: summaries, viral-content breakdowns, original rewrite templates, and Markdown knowledge cards.

## Features

- Read public WeChat Official Account articles from `mp.weixin.qq.com`.
- Read Xiaohongshu/RedNote notes from `xiaohongshu.com`, `xhslink.com`, or screenshots when browser access is limited.
- Normalize every source into a standard content object.
- Analyze Xiaohongshu cover images, carousel order, visible image text, visual hooks, and OCR uncertainty.
- Save structured Markdown knowledge cards to a `markdown/` folder.

## Actions

The skill supports four user-facing actions:

| Action | Purpose |
| --- | --- |
| 总结 | Extract core ideas, facts, structure, audience, and takeaways. |
| 爆款拆解 | Analyze title hooks, cover hooks, opening, emotional value, share triggers, and reusable patterns. |
| 仿写 | Extract a structure template and write original content for a new topic. |
| 加入知识库 | Save a structured Markdown card to the workspace `markdown/` folder. |

## Install

Copy the skill folder into your Codex skills directory.

### Windows

```powershell
Copy-Item -Recurse .\read-cn-social-article "$HOME\.codex\skills\"
```

### macOS / Linux

```bash
cp -R ./read-cn-social-article ~/.codex/skills/
```

Restart Codex or open a new thread, then invoke:

```text
$read-cn-social-article
```

## Usage Examples

### Summarize A WeChat Article

```text
Use $read-cn-social-article to summarize this article:
https://mp.weixin.qq.com/s/...
```

### Break Down A Xiaohongshu Note

```text
Use $read-cn-social-article to do 爆款拆解 for this Xiaohongshu link:
https://www.xiaohongshu.com/discovery/item/...
```

### Save To Markdown Knowledge Base

```text
Use $read-cn-social-article to read this post and 加入知识库.
```

By default, knowledge cards are saved to:

```text
markdown/
```

## Standard Content Object

All actions consume one normalized content object. The schema is documented in:

```text
read-cn-social-article/references/content-object.md
```

Create a blank object:

```bash
python read-cn-social-article/scripts/normalize_content_object.py --template
```

Normalize an extracted article Markdown file:

```bash
python read-cn-social-article/scripts/normalize_content_object.py --from-markdown article.md --output content-object.json
```

Save a knowledge card from a content object:

```bash
python read-cn-social-article/scripts/save_knowledge_card.py --kb-dir markdown --content-object content-object.json
```

## WeChat Article Extraction

For public WeChat articles:

```bash
python read-cn-social-article/scripts/wechat_article_to_markdown.py "https://mp.weixin.qq.com/s/..." --output article.md --download-images
```

If direct HTTP extraction is blocked, open the article in a browser, save the rendered HTML, then run:

```bash
python read-cn-social-article/scripts/wechat_article_to_markdown.py saved.html --output article.md --download-images
```

## Xiaohongshu Image Understanding

Xiaohongshu posts often place key information inside images. The skill treats images as first-class content units:

- `visible_text`: text visible inside the image.
- `visual_summary`: what the image shows.
- `content_role`: cover hook, evidence, example, tutorial step, quote card, product display, atmosphere, or CTA.
- `hook_analysis`: why the image may stop scrolling.
- `confidence` and `uncertainty`: OCR and visual-reading caveats.

## Repository Structure

```text
read-cn-social-article/
  SKILL.md
  agents/
    openai.yaml
  references/
    content-object.md
    platform-notes.md
  scripts/
    normalize_content_object.py
    save_knowledge_card.py
    wechat_article_to_markdown.py
```

## Notes

- The scripts use Python standard library only.
- Respect platform access controls. Do not bypass paywalls, private posts, CAPTCHAs, account restrictions, or login walls.
- Xiaohongshu extraction may require a browser session, screenshots, or user-provided exports when public HTML is incomplete.
