#!/usr/bin/env python3
"""notion_batch_blocks.py — Batch-append blocks to a Notion page from markdown content.

Usage:
    python3 notion_batch_blocks.py <page_id> <markdown_file>

Notion API limits PATCH /v1/blocks/{id}/children to 50 blocks per request.
This script parses markdown into Notion block objects and sends them in batches of 50.

Block types supported:
    - Heading 1/2/3 → heading_1/2/3
    - Paragraph → paragraph
    - Code/Code block → code (language auto-detected)
    - Blockquote → callout (💡 icon) 
    - Bullet list → bulleted_list_item
    - Numbered list → numbered_list_item
    - Thematic break (---, ***) → divider
    - Table rows → paragraph (tables as structured text)
    - Mermaid code blocks → code (language="Mermaid")
    - YAML frontmatter → SKIPPED

Environment: NOTION_API_KEY must be set.
"""

import os, sys, requests, json, re

NOTION_TOKEN=os.env...Y", "").strip()
NOTION_VERSION = "2025-09-03"
BATCH_SIZE = 50

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

def md_to_blocks(text: str) -> list[dict]:
    """Convert markdown text to Notion block objects."""
    blocks = []
    lines = text.split("\n")
    in_code_block = False
    code_buffer = []
    code_lang = ""
    in_frontmatter = False
    
    def flush_code():
        nonlocal code_buffer
        if code_buffer:
            code_text = "\n".join(code_buffer)
            lang = code_lang if code_lang else "plain text"
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code_text}}],
                    "language": lang,
                },
            })
            code_buffer = []
    
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        
        # Handle YAML frontmatter
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            i += 1
            continue
        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            i += 1
            continue
        if in_frontmatter:
            i += 1
            continue
        
        # Handle code blocks
        if line.startswith("```"):
            if in_code_block:
                flush_code()
                in_code_block = False
                code_lang = ""
            else:
                code_lang = line[3:].strip()
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            code_buffer.append(raw)
            i += 1
            continue
        
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
        
        # Detect block type
        if line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:]}]},
                },
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}]},
                },
            })
        elif line.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}]},
                },
            })
        elif line.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}]},
                    "icon": {"emoji": "💡"},
                },
            })
        elif line.startswith("- ") or line.startswith("* "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}]},
                },
            })
        elif re.match(r"^\d+[\.\)] ", line):
            text = re.sub(r"^\d+[\.\)] ", "", line)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text}}],
                },
            })
        elif re.match(r"^---+\s*$", line) or re.match(r"^\*+\s*$", line):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {},
            })
        elif "|" in line and line.count("|") >= 2:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}],
                },
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}]},
                },
            })
        
        i += 1
    
    return blocks


def append_blocks(page_id: str, blocks: list[dict], batch_size: int = BATCH_SIZE):
    """Append blocks to a Notion page in batches."""
    total = len(blocks)
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = blocks[start:end]
        
        resp = requests.patch(url, headers=HEADERS, json={"children": batch})
        if resp.status_code >= 400:
            print(f"  ❌ Batch {start+1}-{end}/{total}: HTTP {resp.status_code}", flush=True)
            print(f"     {resp.text[:500]}", flush=True)
            return False
        
        print(f"  ✅ {start+1}-{end}/{total}", flush=True)
    
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 notion_batch_blocks.py <page_id> <markdown_file>", flush=True)
        sys.exit(1)
    
    page_id = sys.argv[1]
    md_path = sys.argv[2]
    
    if not NOTION_TOKEN:
        print("❌ NOTION_API_KEY not set", flush=True)
        sys.exit(1)
    
    with open(md_path) as f:
        text = f.read()
    
    print(f"📊 Converting markdown to blocks...", flush=True)
    blocks = md_to_blocks(text)
    print(f"📊 {len(blocks)} blocks to add", flush=True)
    
    if not blocks:
        print("⚠️ No blocks to add", flush=True)
        return
    
    success = append_blocks(page_id, blocks)
    if success:
        print(f"\n✅ Done: {len(blocks)} blocks appended to {page_id}", flush=True)
    else:
        print(f"\n❌ Failed to append all blocks", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
