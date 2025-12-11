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
import os
import pprint
from pathlib import Path
from typing import Dict, List, Any, Tuple

ailib = None
llm_client = None

# Needed to get the json schema for importing data..
from pylab.utilities import load_data_file

try:
    import fitz #PyMuPDF
except ImportError:
    raise ImportError("Please install PyMuPDF: pip install pymupdf")

# examples...
# python ./scpi2json.py ./ProgrammingManual_BK8616.pdf -p "28-67" --debug-text
# python ./scpi2json.py ./ProgrammingManual_BK8616.pdf -p "28-67" --max-chars-per-chunk 2000 --start-line 20 --debug-start
# python ./scpi2json.py ./ProgrammingManual_BK8616.pdf -p "28-67" --debug-text --max-chars-per-chunk 2000

# ------------- Environment variable utilities -------------


def get_openai_api_key() -> Tuple[str | None, str | None]:
    """
    Check for OPENAI_API_KEY environment variable.

    Works on both Windows and Linux environments.

    Returns:
        Tuple of (LLM to use, Key for that LLM)
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is not None:
        return "OpenAI", openai_api_key
    else:
        return None, None


# ------------- Utility: page range parsing -------------


def parse_page_ranges(ranges_str: str) -> List[int]:
    """
    "11-35,73-80,90" -> [11,12,...,35,73,...,80,90]
    """
    print(f">call parse_page_ranges(ranges_str: {ranges_str})")
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

def get_page_count(pdf_path: Path) -> int:
    print(f"> get_page_count(pdf_path: {pdf_path})")
    with fitz.open(pdf_path) as pdf:
        return pdf.page_count

def extract_text_for_pages(pdf_path: Path, pages: List[int]) -> Dict[int, str]:
    """
    pages are 1-based page numbers from the user's perspective.
    Returns {page_number: text}
    """
    print(f">call extract_text_for_pages\n"+
          f"(\n"+
          f">\tpdf_path: {pdf_path}\n"+
          f">\tpage: {pages if len(pages) < 5 else f"[{pages[0]} ... {pages[-1]}]"}\n"+
          f">)")
    page_text: Dict[int, str] = {}
    with fitz.open(pdf_path) as pdf:
        for p in pages:
            idx = p - 1  # PyMuPDF is 0-based internally
            if 0 <= idx < pdf.page_count:
                text = pdf.load_page(idx).get_text("text") or ""
                page_text[p] = text # type: ignore
    return page_text

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
    print(f">call make_chunks\n"+
          ">(\n"+
          ">\tpage_text: Dict[int, str],\n"+
          ">\tmax_chars: {max_chars}\n"+
          ">)")
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

def call_llm_extract_commands_openai(chunk_text: str,
                                     pages: List[int],
                                     schema: dict) -> List[Dict[str, Any]]:
    """
    Takes a chunk of text and returns a list of candidate SCPI commands.

    text input is raw text extracted from the PDF pages. This text may contain
    noise, formatting artifacts, and other non-command content.

    Commands are extracted by prompting an LLM with instructions to identify SCPI commands,
    their descriptions, and the source pages they were found on.

    An API key to use must also be provided.
    """
    response = llm_client.responses.create( #type: ignore
        model="gpt-4.1-mini",      # or gpt-4o, gpt-4o-mini, etc.
        input=[
            {
                "role": "system",
                "content": (
                    "You extract SCPI commands from datasheet text. "
                    "Output ONLY valid JSON following the provided schema. "
                    "If a command is incomplete or truncated, DO NOT include it. "
                    "If no complete commands are present, return: {\"commands\": []}"
                )
            },
            {
                "role": "user",
                "content": chunk_text
            }
        ],
        temperature=0,
        text={
            "format": {
                "type": "json_schema",
                "name": "scpi_extract",
                "schema": schema,
                "strict": True
            }
        }
    )

    # The Responses API returns the JSON as text; load it into Python dict.
    result = json.loads(response.output_text)
    # Schema wraps commands in {"commands": [...]} for OpenAI structured outputs
    return result.get("commands", [])

def extract_commands_from_chunks(chunks: List[Dict[str, Any]],
                                 ai_framework: str) -> List[Dict[str, Any]]:
    """
    Loop over chunks, call the LLM, and collect candidate commands.
    """
    print(f"> extract_commands_from_chunks(chunks: List[Dict[str, Any]])")
    all_candidates: List[Dict[str, Any]] = []

    if ai_framework == "OpenAI":
        call_llm_extract_commands = call_llm_extract_commands_openai
        print(f"Extracting commands using LLM framework: {ai_framework}")
    else:
        raise SystemExit(f"No 'call_llm_extract_commands_?' function found for framework {ai_framework} - needs to be added!")

    scpi_schema = load_data_file("./schemas/SCPI_Command.json")

    for idx, chunk in enumerate(chunks):
        text = chunk["text"]
        pages = chunk["pages"]

        try:
            commands = call_llm_extract_commands(text, pages, scpi_schema)
        except Exception as e:
            raise SystemExit(f"Failed to extract commands on chunk {idx+1}. Failure was:\n\t{str(e)}")

        for k in commands:
            print(f"{k["name"]}: {k["confidence"]} confidence, partial={k["incomplete"]}, notes: {k["extraction_notes"]}")
        pprint.pp(commands)
        raise SystemExit("extracted one")

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
    parser.add_argument(
        "--debug-start",
        action="store_true",
        help="Stop after writing extracting text - use to fine tune pages and start line arguments.",
    )
    parser.add_argument(
        "--start-line",
        type=int,
        default=1,
        help="Line number on the first selected page to start parsing at (1-based). "
        "Lines before this are discarded from the first page only.",
    )

    args = parser.parse_args(argv)

    pdf_path: Path = args.pdf_path
    out_path: Path = args.out
    pages_str: str = args.pages
    no_review: bool = args.no_review
    max_chars: int = args.max_chars_per_chunk
    start_line: int = args.start_line

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    print(f"Extracting from PDF: {pdf_path}")

    # If no pages specified, select on command line.
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

    # Extract text from given range of pages.
    page_text = extract_text_for_pages(pdf_path, page_list)
    if not page_text:
        raise SystemExit("No text extracted from the specified pages.")

    # Apply start-line offset to the first page if specified
    if start_line > 1 and page_list:
        first_page = min(page_text.keys())
        if first_page in page_text:
            lines = page_text[first_page].splitlines(keepends=True)
            print(f"Start page {first_page} has {len(lines)} lines. Starting at line {start_line}")
            if start_line > len(lines):
                print(f"Start line is past end of page... skipping this page.")
                page_text[first_page] = ""
            else:
                # start_line is 1-based, so slice from index (start_line - 1)
                page_text[first_page] = "".join(lines[start_line - 1:])
                print(f"Skipped first {start_line - 1} lines on page {first_page}.")
                print(f"First line is now...")
                print(f">>> {page_text[first_page].splitlines()[0].strip()}")
    if out_path.suffix:
        debug_text_path = out_path.with_suffix(".txt")
    else:
        debug_text_path = out_path.with_name(out_path.name + ".txt")

    if args.debug_start:
        raise SystemExit("Debug start flag was set - exiting after selecting start.")

    # Sort pages by page number
    sorted_pages = sorted(page_text.items())
    debug_chunks = [f"---- PAGE {page} ----\n{text}" for page, text in sorted_pages]
    debug_text_path.write_text("\n\n".join(debug_chunks))
    print(f"Wrote extracted text to {debug_text_path} from {len(page_text)} pages.")

    if args.debug_text:
        raise SystemExit("Debug text flag was set - exiting after writing extracted text.")

    # Create chunks for better LLM submission... 
    chunks = make_chunks(page_text, max_chars=max_chars)
    print(f"Created {len(chunks)} chunk(s) for LLM processing.")

    # Do actual extration
    ai_framework, ai_api_key = get_openai_api_key()
    if ai_framework == "OpenAI":
        global ailib # yucky
        global llm_client
        try:
            from openai import OpenAI as ailib
        except (ImportError) as e:
            raise SystemExit(f"Unable to import openai (API key was for OpenAI) - check this is installed!")
        llm_client = ailib(api_key=os.getenv("OPENAI_API_KEY"))
    else:
        raise SystemExit(f"No LLM API keys - please set one of the following environment variables:\n"
              f"\tOPENAI_API_KEY: When using OpenAI")
    
    # Try and import selected AI framework and set to global so other methods can use...
    

    candidates = extract_commands_from_chunks(chunks, ai_framework) #type: ignore
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
