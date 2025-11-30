"""
Command-line tool to extract SCPI commands from a PDF manual and save them as JSON.

High-level flow:
1. Convert selected PDF pages to text locally.
2. Chunk the text into manageable pieces.
3. For each chunk, call an LLM to extract SCPI commands.
4. Let the user review and filter the commands in the terminal.
5. Map to a simple JSON schema and write to disk.

You need to:
- Install pdfplumber: pip install pdfplumber
- Implement call_llm_extract_commands() for your LLM of choice.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pdfplumber


# ------------- Utility: page range parsing -------------


def parse_page_ranges(ranges_str: str) -> List[int]:
    """
    "11-35,73-80,90" -> [11,12,...,35,73,...,80,90]
    """
    pages: set[int] = set()
    for part in ranges_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a)
            end = int(b)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


# ------------- PDF helpers -------------


def get_page_count(pdf_path: Path) -> int:
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)


def get_page_preview(pdf_path: Path, page_index: int, max_chars: int = 120) -> str:
    """
    page_index is 0-based.
    """
    with pdfplumber.open(pdf_path) as pdf:
        if page_index < 0 or page_index >= len(pdf.pages):
            return ""
        text = pdf.pages[page_index].extract_text() or ""
    return text.strip().replace("\n", " ")[:max_chars]


def extract_text_for_pages(pdf_path: Path, pages: List[int]) -> Dict[int, str]:
    """
    pages are 1-based page numbers from the user's perspective.
    Returns {page_number: text}
    """
    page_text: Dict[int, str] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for p in pages:
            idx = p - 1  # pdfplumber is 0-based
            if 0 <= idx < len(pdf.pages):
                text = pdf.pages[idx].extract_text() or ""
                page_text[p] = text
    return page_text


# ------------- Chunking -------------


def make_chunks(page_text: Dict[int, str], max_chars: int = 4000) -> List[Dict[str, Any]]:
    """
    Combine selected pages into chunks of at most max_chars characters.

    Returns a list of:
      {
        "chunk_id": int,
        "pages": [int, ...],
        "text": str,
      }
    """
    chunks: List[Dict[str, Any]] = []
    current_text = ""
    current_pages: List[int] = []

    for page in sorted(page_text.keys()):
        text = page_text[page]
        if not text:
            continue

        # Start a new chunk if adding this page would exceed max_chars
        if current_text and len(current_text) + len(text) > max_chars:
            chunks.append(
                {
                    "chunk_id": len(chunks),
                    "pages": current_pages,
                    "text": current_text,
                }
            )
            current_text = ""
            current_pages = []

        # Add page separator markers (optional, helpful for LLM)
        current_text += f"\n\n---- PAGE {page} ----\n\n{text}"
        current_pages.append(page)

    if current_text:
        chunks.append(
            {
                "chunk_id": len(chunks),
                "pages": current_pages,
                "text": current_text,
            }
        )

    return chunks


# ------------- LLM extraction (you fill this in) -------------


def call_llm_extract_commands(chunk_text: str, pages: List[int]) -> List[Dict[str, Any]]:
    """
    Stub for LLM call.

    You should implement this using your LLM of choice (e.g., OpenAI, Codex, etc.).
    Given a chunk of text from the manual, return a list of dicts like:

        [
            {
                "command": ":SENSE:VOLTAGE:DC:RANGE",
                "description": "Sets the DC voltage measurement range.",
                "source_pages": [11, 12],
            },
            ...
        ]

    Suggested prompt logic (pseudocode):

    - Tell the model: "You are given raw text from a SCPI instrument manual."
    - Ask: "Extract all SCPI commands and a short description."
    - Define SCPI examples.
    - Instruct: "Return ONLY JSON with a 'commands' array of objects
      {command: str, description: str}."

    Then parse the JSON and attach source_pages.

    Right now this returns an empty list so the CLI still runs without an API key.
    """
    # TODO: implement with your actual LLM client.
    # For now, return an empty list so that the script runs.
    return []


def extract_commands_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Loop over chunks, call the LLM, and collect candidate commands.
    """
    all_candidates: List[Dict[str, Any]] = []

    for chunk in chunks:
        text = chunk["text"]
        pages = chunk["pages"]

        # Call your LLM here
        commands = call_llm_extract_commands(text, pages)

        for c in commands:
            # make sure required keys exist
            cmd = {
                "command": c.get("command", "").strip(),
                "description": c.get("description", "").strip(),
                "source_pages": c.get("source_pages", pages),
            }
            if cmd["command"]:
                all_candidates.append(cmd)

    return all_candidates


# ------------- Deduplication / normalization -------------


def dedupe_commands(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate by command string (exact match).
    Merge source_pages when duplicates appear.
    """
    seen: Dict[str, Dict[str, Any]] = {}

    for c in candidates:
        key = c["command"].strip()
        if not key:
            continue

        if key not in seen:
            seen[key] = {
                "command": key,
                "description": c.get("description", ""),
                "source_pages": list(sorted(set(c.get("source_pages", [])))),
            }
        else:
            # merge pages; keep existing description
            existing = seen[key]
            existing_pages = set(existing.get("source_pages", []))
            new_pages = set(c.get("source_pages", []))
            existing["source_pages"] = list(sorted(existing_pages | new_pages))

    return list(seen.values())


# ------------- Interactive review (CLI) -------------


def interactive_review(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Let user review and select which commands to keep.

    Simple pagination & toggling by index.
    """
    if not commands:
        print("No commands to review.")
        return []

    selected = [True] * len(commands)
    page_size = 10
    current_page = 0

    def show_page():
        start = current_page * page_size
        end = min(start + page_size, len_
