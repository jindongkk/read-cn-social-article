# Platform Notes

## GitHub references checked during design

- `JoeanAmier/XHS-Downloader`: Xiaohongshu/RedNote link extraction, note metadata collection, media URL extraction, and media download. Useful design cue: keep cookie/login concerns outside the core reading flow and treat downloaded media as evidence to verify.
- `ReaJason/xhs`: Python request wrapper around Xiaohongshu Web endpoints. Useful design cue: Web-side request signatures and cookie requirements change, so the skill should prefer browser verification over assuming raw API calls remain valid.
- `jackwener/wechat-article-to-markdown`: WeChat Official Account article fetch and Markdown conversion. Useful design cue: WeChat public pages have stable article selectors, so a deterministic converter is worth bundling.
- `joeseesun/qiaomu-anything-to-notebooklm`: Claude Skill for multi-source ingestion including WeChat articles. Useful design cue: separate "reader" work from downstream synthesis formats.
- `runesleo/x-reader`, `nashsu/AutoCLI`, `Panniantong/Agent-Reach`: generalized content readers that include Xiaohongshu or multi-platform extraction. Useful design cue: platform readers are best used as optional adapters, with provenance and visual checks.

## WeChat extraction details

WeChat Official Account pages usually render enough content in HTML to support deterministic extraction:

- Body container: `#js_content`
- Title: `#activity-name`
- Account: `#js_name` or `.profile_nickname`
- Author: `#js_author_name`
- Cover image: JavaScript variable `msg_cdn_url`
- Publish time: JavaScript variable `ct` when present; otherwise visible metadata may need DOM/browser inspection
- Images: `img[data-src]` is usually the original article image; `src` may be a placeholder

Common failure modes:

- Direct HTTP returns a verification or environment warning page.
- Images require a WeChat referer header.
- Some text is embedded in images or styled spans; OCR may be needed for completeness.
- Lazy-loaded images may not appear until scrolling in a rendered browser.

## Xiaohongshu extraction details

Xiaohongshu/RedNote is not reliably readable through raw HTTP alone. Treat these as normal, not exceptional:

- Short links redirect to app/web note URLs.
- Login walls, verification, and anti-automation responses may appear.
- The post body can be split between DOM text, carousel images, hashtags, and comments.
- Important text may be inside images; always inspect carousel images when the user asks to "read" the post.

Image understanding priorities:

- Cover image: analyze first; it often carries the hook, topic promise, and emotional frame.
- Carousel order: keep image order stable because tutorials, story reveals, and before/after examples depend on sequence.
- Image text: record as `visible_text`, not as body text, unless the user asks for a merged reading.
- Visual role: label whether the image is a hook, example, evidence, quote card, product shot, scene-setting image, or CTA.
- Uncertainty: mark blurry screenshots, cropped text, inaccessible carousel pages, and inferred visual details.

Recommended fallback ladder:

1. Browser-rendered page with user-authorized login state.
2. Existing local reader/downloader tools, then verify against browser/screenshot.
3. User-provided screenshots or copied text.
4. State that the content is inaccessible if none of the above is available.

## Reporting confidence

Label source quality clearly:

- `high`: direct DOM/HTML text plus images verified.
- `medium`: browser/screenshot reading with some OCR.
- `low`: partial page, blocked page, incomplete carousel, or missing screenshots.
