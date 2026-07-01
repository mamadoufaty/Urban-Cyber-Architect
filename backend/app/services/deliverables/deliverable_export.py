"""Export livrables — PDF, Markdown, DOCX (texte structuré)."""

from __future__ import annotations

import io
import zipfile
from typing import Any
from xml.sax.saxutils import escape


def _sections_from_content(content: dict[str, Any]) -> list[dict[str, Any]]:
    return list(content.get("sections") or [])


def render_deliverable_markdown(content: dict[str, Any]) -> str:
    lines: list[str] = []
    title = str(content.get("title") or "Livrable")
    lines.append(f"# {title}")
    lines.append("")
    meta = content.get("metadata") or {}
    if meta.get("project_name"):
        lines.append(f"**Projet :** {meta['project_name']}")
    if meta.get("deliverable_type_label"):
        lines.append(f"**Type :** {meta['deliverable_type_label']}")
    if meta.get("generated_at"):
        lines.append(f"**Généré le :** {meta['generated_at']}")
    lines.append("")
    if content.get("user_need"):
        lines.append("## Besoin utilisateur")
        lines.append("")
        lines.append(str(content["user_need"]))
        lines.append("")
    for section in _sections_from_content(content):
        lines.append(f"## {section.get('title', 'Section')}")
        lines.append("")
        body = str(section.get("content") or "").strip()
        if body:
            lines.append(body)
            lines.append("")
        for bullet in section.get("bullets") or []:
            lines.append(f"- {bullet}")
        if section.get("bullets"):
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def export_deliverable_markdown(content: dict[str, Any]) -> bytes:
    return render_deliverable_markdown(content).encode("utf-8")


def export_deliverable_pdf(content: dict[str, Any]) -> bytes:
    from app.services.pdf.document_builder import build_deliverable_pdf

    return build_deliverable_pdf(content)


def export_deliverable_docx(content: dict[str, Any]) -> bytes:
    """DOCX minimal (Open XML) sans dépendance externe."""
    markdown = render_deliverable_markdown(content)
    paragraphs = [line for line in markdown.split("\n") if line.strip()]
    body_xml = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{escape(p)}</w:t></w:r></w:p>'
        for p in paragraphs
    )
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body_xml}<w:sectPr/></w:body>
</w:document>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    return out.getvalue()
