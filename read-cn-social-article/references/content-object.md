# Standard Content Object

Use this object as the exchange format between reading, summarizing, deconstructing, rewriting, and saving to the Markdown knowledge base.

## Shape

```json
{
  "version": "1.0",
  "platform": "wechat | xiaohongshu | rednote | unknown",
  "source_url": "",
  "canonical_url": "",
  "title": "",
  "author": {
    "name": "",
    "handle": "",
    "profile_url": ""
  },
  "published_at": "",
  "extracted_at": "",
  "extraction": {
    "method": "HTML | browser DOM | screenshot | visual reading | OCR | mixed",
    "confidence": "high | medium | low",
    "notes": []
  },
  "content": {
    "body_text": "",
    "markdown": "",
    "hashtags": [],
    "mentions": [],
    "links": []
  },
  "media": {
    "cover": null,
    "images": [],
    "videos": []
  },
  "image_understanding": [],
  "engagement": {
    "likes": null,
    "collects": null,
    "comments": null,
    "shares": null
  },
  "knowledge": {
    "topics": [],
    "tags": [],
    "entities": [],
    "core_ideas": [],
    "reusable_patterns": []
  },
  "actions": {
    "summary": "",
    "deconstruction": {},
    "rewrite_template": ""
  }
}
```

## Image Object

Use `media.images[]` for image inventory:

```json
{
  "id": "img-001",
  "order": 1,
  "role": "cover | carousel | inline | recommendation | unknown",
  "local_path": "",
  "source_url": "",
  "alt": "",
  "caption": ""
}
```

Use `image_understanding[]` for interpretation:

```json
{
  "image_id": "img-001",
  "order": 1,
  "visible_text": "",
  "visual_summary": "",
  "content_role": "cover hook | evidence | example | tutorial step | quote card | product display | atmosphere | ending CTA | unknown",
  "hook_analysis": "",
  "confidence": "high | medium | low",
  "uncertainty": ""
}
```

## Xiaohongshu Image Rules

- Treat the cover image as a first-class content unit. Analyze its text, composition, emotional hook, curiosity gap, and topic promise.
- Read every carousel image in order when possible. If only partial screenshots are available, mark missing images in `extraction.notes`.
- Keep DOM body text and image text separate. Merge them only in user-facing summaries and label uncertain OCR.
- For `爆款拆解`, prioritize the title, cover image, first two carousel images, opening line, comment bait, and emotional payoff.
- For `加入知识库`, store image-derived insights under `## Image Understanding` or `## Reusable Patterns`.

## Confidence

- `high`: DOM/HTML text plus ordered images are visible and verified.
- `medium`: browser/screenshot reading is complete enough but contains OCR or visual inference.
- `low`: blocked page, partial carousel, missing images, unclear OCR, or unverifiable metadata.
