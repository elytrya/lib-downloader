"""
преобразование содержимого главы (формат JSON-документа, который
отдаёт апи cdnlibs.org в поле data.content) в хтмл для епаб.

формат похож на ProseMirror/TipTap: узел "doc" содержит список
узлов ("paragraph", "heading", "text" и т.д.), у текстовых узлов
могут быть "marks" (bold, italic, ...).
"""

from html import escape
from typing import Any, Dict


def render_doc(doc: Any) -> str:
    if not doc:
        return ""
    if isinstance(doc, str):
        return doc
    if isinstance(doc, list):
        return "".join(_render_node(c) for c in doc if isinstance(c, dict))
    if not isinstance(doc, dict):
        return ""
    return _render_node(doc)


def _render_children(node):
    children = node.get("content", []) or []
    if isinstance(children, str):
        from html import escape

        return f"<p>{escape(children)}</p>\n"
    return "".join(_render_node(c) for c in children if isinstance(c, dict))


def _render_node(node: Dict[str, Any]) -> str:
    node_type = node.get("type")

    if node_type == "doc":
        return _render_children(node)

    if node_type == "paragraph":
        inner = _render_children(node)
        if not inner.strip():
            inner = "&nbsp;"
        return f"<p>{inner}</p>\n"

    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 3)
        level = max(1, min(6, int(level)))
        inner = _render_children(node)
        return f"<h{level}>{inner}</h{level}>\n"

    if node_type == "text":
        text = escape(node.get("text", ""))
        for mark in node.get("marks", []) or []:
            mark_type = mark.get("type")
            if mark_type == "bold":
                text = f"<strong>{text}</strong>"
            elif mark_type == "italic":
                text = f"<em>{text}</em>"
            elif mark_type == "underline":
                text = f"<u>{text}</u>"
            elif mark_type == "strike":
                text = f"<s>{text}</s>"
            elif mark_type == "link":
                href = escape(mark.get("attrs", {}).get("href", "#"))
                text = f'<a href="{href}">{text}</a>'
        return text

    if node_type == "hardBreak":
        return "<br/>\n"

    if node_type == "horizontalRule":
        return "<hr/>\n"

    if node_type == "blockquote":
        return f"<blockquote>{_render_children(node)}</blockquote>\n"

    if node_type in ("bulletList", "orderedList"):
        tag = "ul" if node_type == "bulletList" else "ol"
        return f"<{tag}>{_render_children(node)}</{tag}>\n"

    if node_type == "listItem":
        return f"<li>{_render_children(node)}</li>\n"

    if node_type == "image":
        src = node.get("attrs", {}).get("src")
        if not src:
            return ""
        return f'<img src="{escape(src)}" alt=""/>\n'

    # неизвестный тип узла - просто рендерим детей, чтобы не потерять текст
    return _render_children(node)
