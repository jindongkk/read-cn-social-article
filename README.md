# read-cn-social-article

一个用于读取、拆解和复用中文社交图文内容的 Codex Skill，支持公众号文章和小红书/RedNote 图文笔记。

它的定位不是“把文章读完”，而是把社交内容转成可学习、可研究、可复用、可沉淀的内容资产。

## 功能

- 读取公开公众号文章：`mp.weixin.qq.com`
- 读取小红书/RedNote 图文：`xiaohongshu.com`、`xhslink.com`，或在受限时使用截图/浏览器内容
- 将不同来源统一成标准内容对象
- 分析小红书封面图、轮播顺序、图片中文字、视觉钩子和 OCR 不确定性
- 将内容保存为 Markdown 知识卡片，默认写入工作区的 `markdown/` 文件夹

## 四个动作

| 动作 | 用途 |
| --- | --- |
| 总结 | 提炼核心观点、关键信息、内容结构、目标人群和可引用点 |
| 爆款拆解 | 拆标题钩子、封面钩子、开头、情绪价值、分享动机和可复用结构 |
| 仿写 | 提取结构模板，为新主题生成原创内容，避免贴近原文洗稿 |
| 加入知识库 | 生成结构化 Markdown 知识卡，保存到 `markdown/` 文件夹 |

## 安装

把 `read-cn-social-article` 文件夹复制到 Codex 的 skills 目录。

### Windows

```powershell
Copy-Item -Recurse .\read-cn-social-article "$HOME\.codex\skills\"
```

### macOS / Linux

```bash
cp -R ./read-cn-social-article ~/.codex/skills/
```

然后重启 Codex，或打开一个新线程，使用：

```text
$read-cn-social-article
```

## 使用示例

### 总结公众号文章

```text
Use $read-cn-social-article to summarize this article:
https://mp.weixin.qq.com/s/...
```

也可以直接中文表达：

```text
用 $read-cn-social-article 总结这篇公众号文章：
https://mp.weixin.qq.com/s/...
```

### 拆解小红书笔记

```text
用 $read-cn-social-article 对这个小红书链接做爆款拆解：
https://www.xiaohongshu.com/discovery/item/...
```

### 加入 Markdown 知识库

```text
用 $read-cn-social-article 读取这个链接，并加入知识库。
```

默认保存位置：

```text
markdown/
```

## 标准内容对象

这个 skill 会先把不同平台的内容统一成一个标准内容对象，然后再执行总结、爆款拆解、仿写或加入知识库。

对象规范在：

```text
read-cn-social-article/references/content-object.md
```

生成一个空模板：

```bash
python read-cn-social-article/scripts/normalize_content_object.py --template
```

把已抽取的文章 Markdown 转成标准对象：

```bash
python read-cn-social-article/scripts/normalize_content_object.py --from-markdown article.md --output content-object.json
```

从标准对象生成知识卡片：

```bash
python read-cn-social-article/scripts/save_knowledge_card.py --kb-dir markdown --content-object content-object.json
```

## 公众号文章抽取

公开公众号文章可以直接转成 Markdown：

```bash
python read-cn-social-article/scripts/wechat_article_to_markdown.py "https://mp.weixin.qq.com/s/..." --output article.md --download-images
```

如果微信阻止直接 HTTP 访问，可以先在浏览器打开文章，保存渲染后的 HTML，再运行：

```bash
python read-cn-social-article/scripts/wechat_article_to_markdown.py saved.html --output article.md --download-images
```

## 小红书图片理解

小红书图文经常把关键信息放在图片里，所以这个 skill 会把图片当成一等内容单元处理。

每张图片会尽量记录：

- `visible_text`：图片里可见的文字
- `visual_summary`：图片展示了什么
- `content_role`：封面钩子、证据、案例、教程步骤、金句卡、产品展示、氛围图或 CTA
- `hook_analysis`：为什么这张图可能让用户停下来
- `confidence` 和 `uncertainty`：OCR 或视觉理解的不确定性

## 知识卡片格式

加入知识库时，会生成类似这样的 Markdown：

```markdown
---
title: "标题"
platform: "xiaohongshu"
source_url: "https://..."
author: "作者"
published: "2026-06-02"
extracted_at: "2026-06-02 12:00:00"
action: "加入知识库"
confidence: "high"
tags:
  - "亲密关系"
  - "爆款拆解"
---

# 标题

## Source Snapshot

## Core Ideas

## Image Understanding

## Reusable Patterns

## Notes
```

## 目录结构

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

## 注意事项

- 脚本只使用 Python 标准库，不需要额外安装第三方包。
- 请尊重平台访问控制，不要绕过付费墙、私密内容、验证码、登录墙或账号限制。
- 小红书内容如果公开 HTML 不完整，可能需要浏览器会话、截图、复制文本或用户提供的导出内容。
- `仿写` 应复用结构和策略，不应贴近原文表达或变相洗稿。
