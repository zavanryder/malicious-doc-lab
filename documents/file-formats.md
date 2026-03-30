# Document Formats

This document describes each file format `maldoc` can generate, why that format matters for adversarial testing, and how attacks are embedded within each.

## Overview

| Format | Extension | Generator library | Primary attack surface |
|--------|-----------|-------------------|----------------------|
| PDF | `.pdf` | fpdf2 | Text extraction, OCR, metadata, off-page content |
| DOCX | `.docx` | python-docx | Metadata, styled text, XML structure |
| HTML | `.html` | string templates | CSS hiding, meta tags, off-screen positioning |
| Markdown | `.md` | string templates | HTML comments, zero-width characters |
| CSV | `.csv` | stdlib csv | Hidden cells, adjacent column injection |
| Image | `.png` | Pillow | OCR bait, near-invisible text |

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
- **HTML comments**: For white_on_white and metadata attacks, the payload is embedded in an HTML comment (`<!-- payload -->`). Many Markdown processors preserve HTML comments, and some AI pipelines extract them.
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

## Image (PNG)

Image-based attacks target pipelines that include OCR as part of document processing.

**How maldoc uses it:**

- **Visible content**: Title and body text rendered in black on a white background.
- **OCR bait**: Payload rendered at the bottom of the image in a 2px font, white on white. Most OCR engines will attempt to extract this.
- **Near-invisible text**: For ocr_bait attacks, a slightly larger (6px) gray text is used that OCR reads reliably.

**Why it matters:** Many document processing pipelines run OCR on all images, including images embedded within PDFs. Tesseract and similar engines extract text aggressively -- they are designed to find text even in poor conditions. This makes them susceptible to extracting intentionally hidden text that a human would never notice.

**Testing recommendation:** Use the `image` format specifically with the `ocr_bait` attack to test whether a pipeline's OCR component extracts near-invisible text.
