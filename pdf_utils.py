import os

import pdfplumber


def extract_pdf_lines(path):
    lines = []
    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            words = page.extract_words() or []
            if not words:
                continue
            current = []
            current_y = words[0]["top"]
            for word in words:
                if abs(word["top"] - current_y) > 3:
                    if current:
                        lines.append(_words_to_line(current, page_index))
                    current = [word]
                    current_y = word["top"]
                else:
                    current.append(word)
            if current:
                lines.append(_words_to_line(current, page_index))
    return lines


def _words_to_line(words, page):
    text = " ".join(w["text"] for w in words)
    return {
        "text": text,
        "page": page,
        "x0": min(w["x0"] for w in words),
        "y0": min(w["top"] for w in words),
        "x1": max(w["x1"] for w in words),
        "y1": max(w["bottom"] for w in words),
    }


def find_bbox_for_text(path, needle):
    needle_lower = needle.strip().lower()
    if not needle_lower:
        return None
    for line in extract_pdf_lines(path):
        if needle_lower in line["text"].lower():
            return {
                "page": line["page"],
                "x0": line["x0"],
                "y0": line["y0"],
                "x1": line["x1"],
                "y1": line["y1"],
            }
    return None


def extract_full_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages).strip()
