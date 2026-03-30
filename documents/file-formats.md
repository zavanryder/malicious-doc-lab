# Document Formats

This document describes each file format `maldoc` can generate, why that format matters for adversarial testing, and how attacks are embedded within each.

## Overview

| Format | Extension | Generator library | Primary attack surface |
|--------|-----------|-------------------|----------------------|
| PDF | `.pdf` | fpdf2 | Text extraction, OCR, metadata, off-page content |
| DOCX | `.docx` | python-docx | Metadata, styled text, XML structure |
| HTML | `.html` | string templates | CSS hiding, meta tags, off-screen positioning |
| Markdown | `.md` | string templates | HTML comments, zero-width characters |
| Plain Text | `.txt` | stdlib | Obfuscation, typoglycemia, directive persistence |
| CSV | `.csv` | stdlib csv | Hidden cells, adjacent column injection |
| XLSX | `.xlsx` | openpyxl | Cell-level hiding, workbook metadata |
| PPTX | `.pptx` | python-pptx | Slide text hiding, presentation metadata |
| EML | `.eml` | stdlib email | Header metadata, HTML body payloads |
| Image | `.png/.jpg/.jpeg` | Pillow | OCR bait, visual scaling injection |

---

## Compatibility notes

`maldoc` enforces an attack/format compatibility matrix:

- Unsupported pairs fail with an error.
- Degraded simulations are allowed but explicitly warned in CLI output.

Use these warnings as signal that a format cannot faithfully represent the chosen technique.

---

## PDF

PDF is the most common document format in enterprise AI pipelines. It is also the most complex attack surface because PDF is a container format -- it can hold text, images, metadata, annotations, JavaScript, and embedded files.

**How maldoc uses it:**

- **Normal text**: Visible body content is rendered using DejaVu Sans TTF for full Unicode support.
- **White-on-white**: Payload is appended as white (RGB 255,255,255) text in 1pt font. Invisible in viewers, but extracted by most PDF text parsers.
- **Off-page**: Payload is positioned at negative coordinates (-200, -200), outside the visible page. Most PDF libraries extract all text objects from the content stream without checking page boundaries.
- **OCR bait**: Payload is rendered in very small (4pt), light gray text. When the PDF is processed with OCR (common for scanned-document pipelines), this text is extracted.
- **Metadata**: Payload is injected into the PDF's Author, Subject, and Keywords fields.
- **Zero-width characters**: For hidden_text attacks, zero-width Unicode characters are embedded in the visible text. Some PDF extractors preserve these.

**Why it matters:** Nearly every enterprise document processing pipeline handles PDFs. The complexity of the PDF specification means that parsers vary wildly in what they extract. A parser that simply dumps all text objects (e.g., `page.get_text()` in PyMuPDF) will capture off-page content, white-on-white text, and metadata. This is the default behavior of most popular libraries.

**Testing recommendation:** Test every attack class in PDF format. PDF is where the widest variety of hiding techniques are available.

---

## DOCX

DOCX (Office Open XML) is a ZIP archive containing XML files that define document content, styling, and metadata. It is ubiquitous in corporate environments.

**How maldoc uses it:**

- **Normal text**: Body paragraphs with standard formatting.
- **White-on-white**: A paragraph is added with a run whose font color is set to white (RGB 0xFF, 0xFF, 0xFF) and size 1pt.
- **Metadata**: Payload is injected into core properties: author, subject, keywords. These are stored in `docProps/core.xml` within the ZIP archive.
- **Hidden text runs**: For hidden_text attacks, zero-width characters are embedded in paragraph text.

**Why it matters:** Many RAG pipelines use `python-docx` to extract text from DOCX files. The library extracts paragraphs, tables, and metadata by default. The demo app intentionally extracts metadata and concatenates it with body text -- this is a common pattern in real-world implementations that creates a direct injection vector.

**Testing recommendation:** Prioritize the `metadata` attack with DOCX. Metadata injection is the most reliable vector because DOCX metadata fields are explicitly designed to hold text, and most extraction libraries expose them.

---

## HTML

HTML documents are increasingly common in AI pipelines that process web content, emails, or exported documents.

**How maldoc uses it:**

- **Normal text**: Body content within a `<div>` element.
- **White-on-white**: Payload in a `<span>` with `color: #fff; font-size: 1px`.
- **Off-page**: Payload in a `<div>` with `position: absolute; left: -9999px; top: -9999px`.
- **OCR bait**: Payload in a `<span>` with `color: #e0e0e0; font-size: 4px; background: #f0f0f0`.
- **Metadata**: Payload injected into `<meta>` tags (name, content attributes).
- **Hidden text**: Zero-width characters embedded in visible text content.

**Why it matters:** HTML parsing with BeautifulSoup's `get_text()` extracts all text content regardless of CSS visibility. This includes off-screen elements, zero-size text, and content hidden with `display: none`. The `<meta>` tag content is also commonly extracted. HTML is a primary vector for email-based attacks against AI assistants that process incoming messages.

**Testing recommendation:** Use HTML for testing `off_page` and `metadata` attacks. CSS-based hiding is the simplest and most effective technique against HTML parsers.

---

## Markdown

Markdown is used extensively in documentation, knowledge bases, wikis, and developer tools.

**How maldoc uses it:**

- **Normal text**: Standard Markdown body content.
- **HTML comments**: Hidden payload content is embedded in HTML comments (`<!-- payload -->`) for techniques that need an out-of-band channel. Many Markdown processors preserve comments, and some AI pipelines extract them.
- **Zero-width characters**: Embedded directly in visible text for hidden_text attacks.

**Why it matters:** Markdown is the default format for many AI knowledge bases (Notion exports, GitHub wikis, Confluence exports). HTML comments in Markdown are often preserved through the processing pipeline because stripping them requires explicit handling.

**Testing recommendation:** Markdown is a good secondary format for confirming that an AI pipeline handles HTML comments correctly. If a pipeline is vulnerable to HTML comment injection in Markdown, it likely has broader issues with content sanitization.

---

## CSV

CSV files are common in data pipelines, analytics tools, and spreadsheet-based workflows.

**How maldoc uses it:**

- **Visible rows**: Document body is split into rows across "Title" and "Content" columns.
- **Hidden payload**: A final row contains the payload in the "Notes" column, with empty Title and Content fields.

**Why it matters:** CSV parsing is straightforward -- every cell is text. The attack surface is that AI pipelines often process all cells without distinguishing between headers, data, and notes columns. A payload in any cell becomes part of the ingested content. CSV is also used in data poisoning scenarios where large datasets are fed to AI systems.

**Testing recommendation:** CSV is most relevant for testing `retrieval_poison` and `summary_steer` attacks against pipelines that ingest tabular data.

---

## XLSX

XLSX is common in enterprise analytics and financial workflows and is frequently ingested by RAG systems.

**How maldoc uses it:**

- **Visible content**: Rows in the main worksheet.
- **Metadata**: Payload injection into workbook properties (creator, subject, keywords, description).
- **Hidden cells**: Payload can be placed in far-away or hidden columns.
- **Obfuscation payloads**: Encoded variants can be inserted into notes-style columns.

**Why it matters:** Spreadsheet ingestion pipelines often flatten all cell values and metadata into text, making “non-primary” columns and workbook metadata useful injection channels.

**Testing recommendation:** Prioritize `metadata`, `retrieval_poison`, `summary_steer`, and `encoding_obfuscation`.

---

## PPTX

PPTX files are widely used in executive reporting and often processed in enterprise copilots.

**How maldoc uses it:**

- **Visible content**: Main slide text box content.
- **Metadata**: Core presentation properties (author/subject/keywords/comments).
- **Off-slide text**: Payload can be placed beyond normal visible bounds.
- **Low-visibility text**: Very small white text in footer regions.

**Why it matters:** Slide parsing commonly extracts all shape text and presentation metadata, not just what is visible in presenter mode.

**Testing recommendation:** Use for `off_page`, `metadata`, and long-form prompt-injection attacks (`tool_routing`, `delayed_trigger`).

---

## EML

Email (`.eml`) is a high-value format for indirect prompt injection because many agentic systems summarize inbound messages and attachments.

**How maldoc uses it:**

- **Visible content**: Plain-text message body.
- **Header metadata**: Payload in custom `X-*` headers.
- **HTML alternative body**: Hidden elements and exfil-style image tags.

**Why it matters:** Email ingestion stacks often combine headers, plain text, and HTML content before chunking, creating multiple channels for attacker content.

**Testing recommendation:** Prioritize `metadata`, `markdown_exfil`, and `tool_routing`.

---

## Plain Text (TXT)

TXT is low-complexity but common in logs, exports, and ingestion fallback paths.

**How maldoc uses it:**

- **Visible content**: Full attack content rendered directly.
- **Obfuscated payloads**: Encoded variants can be embedded for filter-evasion testing.

**Why it matters:** Some pipelines downgrade unknown formats to plain text extraction, so obfuscated prompt injection can survive despite format sanitization.

**Testing recommendation:** Good baseline for `encoding_obfuscation`, `typoglycemia`, and `delayed_trigger`.

---

## Image (PNG/JPG/JPEG)

Image-based attacks target pipelines that include OCR as part of document processing.

**How maldoc uses it:**

- **Visible content**: Title and body text rendered in black on a white background.
- **OCR bait**: Payload rendered at the bottom of the image in a 2px font, white on white. Most OCR engines will attempt to extract this.
- **Near-invisible text**: For ocr_bait attacks, a slightly larger (6px) gray text is used that OCR reads reliably.
- **Visual scaling payloads**: For `visual_scaling_injection`, payload text is placed in low-contrast image regions intended to surface after preprocessing transforms.

**Why it matters:** Many document processing pipelines run OCR on all images, including images embedded within PDFs. Tesseract and similar engines extract text aggressively -- they are designed to find text even in poor conditions. This makes them susceptible to extracting intentionally hidden text that a human would never notice.

**Testing recommendation:** Use image formats (`image`, `png`, `jpg`, `jpeg`) with `ocr_bait` and `visual_scaling_injection`.
