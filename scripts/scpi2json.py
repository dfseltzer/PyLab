"""
Command-line tool to extract SCPI commands from a PDF manual and save them as JSON.

High-level flow:
1. Convert selected PDF pages to text locally.
2. Chunk the text into manageable pieces.
3. For each chunk, call an LLM to extract SCPI commands.
4. Let the user review and filter the commands in the terminal.
5. Map to a simple JSON schema and write to disk.

You need to:
- Install PyMuPDF: pip install pymupdf
- Implement call_llm_extract_commands() for your LLM of choice.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

try:
    import fitz #PyMuPDF
except ImportError:
    raise ImportError("Please install PyMuPDF: pip install pymupdf")

# examples...# ./scpi2json.py ./ProgrammingManual_BK8616.pdf -p "26-67" --debug-text

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
    with fitz.open(pdf_path) as pdf:
        return pdf.page_count


def get_page_preview(pdf_path: Path, page_index: int, max_chars: int = 120) -> str:
    """
    page_index is 0-based.
    """
    with fitz.open(pdf_path) as pdf:
        if page_index < 0 or page_index >= pdf.page_count:
            return ""
        text = pdf.load_page(page_index).get_text("text") or ""
    return text.strip().replace("\n", " ")[:max_chars]


def extract_text_for_pages(pdf_path: Path, pages: List[int]) -> Dict[int, str]:
    """
    pages are 1-based page numbers from the user's perspective.
    Returns {page_number: text}
    """
    page_text: Dict[int, str] = {}
    with fitz.open(pdf_path) as pdf:
        for p in pages:
            idx = p - 1  # PyMuPDF is 0-based internally
            if 0 <= idx < pdf.page_count:
                text = pdf.load_page(idx).get_text("text") or ""
                page_text[p] = text
    return page_text


# ------------- Chunking -------------


def make_chunks(page_text: Dict[int, str], max_chars: int = 4000) -> List[Dict[str, Any]]:
    """
    Combine selected pages into chunks of roughly max_chars characters.

    Each chunk overlaps the previous one by up to the last two pages so that
    commands crossing page boundaries remain intact when sent to the LLM.

    Returns a list of:
      {
        "chunk_id": int,
        "pages": [int, ...],
        "text": str,
      }
    """
    chunks: List[Dict[str, Any]] = []
    page_entries: List[Tuple[int, str]] = []
    current_len = 0

    for page in sorted(page_text.keys()):
        text = page_text[page]
        if not text:
            continue

        entry = f"\n\n---- PAGE {page} ----\n\n{text}"
        entry_len = len(entry)

        if page_entries and current_len + entry_len > max_chars:
            chunks.append(
                {
                    "chunk_id": len(chunks),
                    "pages": [p for p, _ in page_entries],
                    "text": "".join(seg for _, seg in page_entries),
                }
            )
            overlap_count = min(2, len(page_entries))
            page_entries = page_entries[-overlap_count:].copy()
            current_len = sum(len(seg) for _, seg in page_entries)

        page_entries.append((page, entry))
        current_len += entry_len

    if page_entries:
        chunks.append(
            {
                "chunk_id": len(chunks),
                "pages": [p for p, _ in page_entries],
                "text": "".join(seg for _, seg in page_entries),
            }
        )

    return chunks


# ------------- LLM extraction (you fill this in) -------------


def call_llm_extract_commands(chunk_text: str, pages: List[int]) -> List[Dict[str, Any]]:
    """
    Takes a chunk of text and returns a list of candidate SCPI commands.

    text input is raw text extracted from the PDF pages. This text may contain
    noise, formatting artifacts, and other non-command content.

    Commands are extracted by prompting an LLM with instructions to identify SCPI commands,
    their descriptions, and the source pages they were found on.

    The returned list should contain dicts like:
    
        [
            {
                "command": "[:SENSe]:VOLTage[:DC]:RANGE",
                "description": "Sets the DC voltage measurement range.",
                "source_pages": [11, 12],
                "text": "full command text"
            },
            ...
        ]


    Note: this function does not parse commands for formatting, arguments, or other infomation.
    It simply extracts blocks of text that appear to be SCPI commands along with their descriptions, 
    while removing any non-command related text.
    """
    # TODO: implement this function per the associated docstring.  Use openAI as the framework.
    # You can use the openai python package or any other method to call your LLM of choice.
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
        end = min(start + page_size, len(commands))
        print("")
        print(f"Showing commands {start + 1}–{end} of {len(commands)}:")
        print("-" * 60)
        for idx in range(start, end):
            c = commands[idx]
            mark = "[x]" if selected[idx] else "[ ]"
            print(
                f"{mark} {idx + 1:3d}) {c['command']}  "
                f"({', '.join(str(p) for p in c.get('source_pages', []))})"
            )
            if c.get("description"):
                print(f"     {c['description']}")
        print("-" * 60)
        print(
            "Commands: n=next page, p=prev page, "
            "e=edit selection, a=accept all, d=deselect all, q=finish"
        )

    while True:
        show_page()
        cmd = input("> ").strip().lower()

        if cmd == "n":
            if (current_page + 1) * page_size < len(commands):
                current_page += 1
            else:
                print("Already at last page.")
        elif cmd == "p":
            if current_page > 0:
                current_page -= 1
            else:
                print("Already at first page.")
        elif cmd == "a":
            selected = [True] * len(commands)
        elif cmd == "d":
            selected = [False] * len(commands)
        elif cmd == "e":
            indices_str = input(
                "Enter indices or ranges to toggle (e.g. '4, 10-12'): "
            ).strip()
            for part in indices_str.split(","):
                part = part.strip()
                if not part:
                    continue
                if "-" in part:
                    a, b = part.split("-", 1)
                    start = int(a)
                    end = int(b)
                    for i in range(start, end + 1):
                        idx = i - 1
                        if 0 <= idx < len(selected):
                            selected[idx] = not selected[idx]
                else:
                    i = int(part)
                    idx = i - 1
                    if 0 <= idx < len(selected):
                        selected[idx] = not selected[idx]
        elif cmd == "q":
            break
        else:
            print("Unknown command. Use n, p, e, a, d, or q.")

    filtered = [c for c, keep in zip(commands, selected) if keep]
    print(f"\nSelected {len(filtered)} out of {len(commands)} commands.")
    return filtered


# ------------- Schema mapping / output -------------


def map_to_schema(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Map simple command dicts to a minimal JSON schema.

    Example output per command:
      {
        "path": ":SENSE:VOLTAGE:DC:RANGE",
        "query": true,
        "set": false,
        "description": "...",
        "source_pages": [11, 12]
      }
    """
    result: List[Dict[str, Any]] = []

    for c in commands:
        raw = c["command"].strip()
        if not raw:
            continue

        is_query = raw.endswith("?")
        path = raw[:-1] if is_query else raw

        item = {
            "path": path,
            "query": is_query,
            "set": not is_query,
            "description": c.get("description", ""),
            "source_pages": c.get("source_pages", []),
        }
        result.append(item)

    return result


def write_json(data: Any, out_path: Path) -> None:
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data)} commands to {out_path}")


# ------------- CLI entrypoint -------------


def run_cli(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Extract SCPI commands from a PDF manual and export to JSON."
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the SCPI manual PDF.",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("scpi_commands.json"),
        help="Output JSON file path.",
    )
    parser.add_argument(
        "-p",
        "--pages",
        type=str,
        default="",
        help="Page ranges containing SCPI commands, e.g. '11-35,73-80'. "
        "If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip interactive review and accept all extracted commands.",
    )
    parser.add_argument(
        "--max-chars-per-chunk",
        type=int,
        default=4000,
        help="Maximum characters per chunk sent to the LLM.",
    )
    parser.add_argument(
        "--debug-text",
        action="store_true",
        help="Dump extracted text to '<out>.txt' and stop after writing.",
    )

    args = parser.parse_args(argv)

    pdf_path: Path = args.pdf_path
    out_path: Path = args.out
    pages_str: str = args.pages
    no_review: bool = args.no_review
    max_chars: int = args.max_chars_per_chunk

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    print(f"PDF: {pdf_path}")

    # If no pages specified, help the user choose.
    if not pages_str:
        page_count = get_page_count(pdf_path)
        print(f"PDF has {page_count} pages.")
        pages_str = input(
            "Enter ranges of pages that contain SCPI commands (e.g. 11-35,73-80): "
        ).strip()

    page_list = parse_page_ranges(pages_str)
    if not page_list:
        raise SystemExit("No valid pages specified.")

    print(f"Working from {len(page_list)} pages.")

    # 1) Extract text
    page_text = extract_text_for_pages(pdf_path, page_list)
    if not page_text:
        raise SystemExit("No text extracted from the specified pages.")

    if out_path.suffix:
        debug_text_path = out_path.with_suffix(".txt")
    else:
        debug_text_path = out_path.with_name(out_path.name + ".txt")

    sorted_pages = sorted(page_text.items())
    debug_chunks = [f"---- PAGE {page} ----\n{text}" for page, text in sorted_pages]
    debug_text_path.write_text("\n\n".join(debug_chunks))
    print(f"Wrote extracted text to {debug_text_path}")

    print(f"Extracted text from {len(page_text)} pages.")

    if args.debug_text:
        print("Debug text flag was set - exiting after writing extracted text.")
        return

    # 2) Chunk
    chunks = make_chunks(page_text, max_chars=max_chars)
    print(f"Created {len(chunks)} chunk(s) for LLM processing.")

    # 3) LLM extraction
    candidates = extract_commands_from_chunks(chunks)
    print(f"LLM returned {len(candidates)} candidate command entries.")

    return

    # 4) Dedup
    unique_cmds = dedupe_commands(candidates)
    print(f"After deduplication: {len(unique_cmds)} unique commands.")

    # 5) Interactive review
    if not no_review:
        reviewed = interactive_review(unique_cmds)
    else:
        reviewed = unique_cmds
        print("Skipping interactive review (no-review mode).")

    # 6) Map to schema + write JSON
    schema_cmds = map_to_schema(reviewed)
    write_json(schema_cmds, out_path)


if __name__ == "__main__":
    run_cli()
