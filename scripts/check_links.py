#!/usr/bin/env python3
"""
Check internal markdown links for broken references.

This script scans markdown files for relative links and verifies that
the target files exist. It reports broken links and can optionally
fix common issues (docs/ -> documentation/, etc.).
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
from urllib.parse import unquote


def find_markdown_files(root: Path) -> List[Path]:
    """Find all markdown files in the repository."""
    markdown_files = []
    for path in root.rglob("*.md"):
        # Skip hidden directories and common exclusions
        if any(part.startswith(".") and part != "." for part in path.parts):
            continue
        if "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        markdown_files.append(path)
    return sorted(markdown_files)


def extract_links(content: str, file_path: Path) -> List[Tuple[str, str, int]]:
    """
    Extract markdown links from content.

    Returns list of (link_text, link_url, line_number) tuples.
    """
    links = []
    # Pattern matches [text](url) and [text](url "title")
    pattern = r'\[([^\]]+)\]\(([^\)]+)(?:\s+"[^"]+")?\)'

    for line_num, line in enumerate(content.split("\n"), start=1):
        for match in re.finditer(pattern, line):
            link_text = match.group(1)
            link_url = match.group(2)
            # Skip external URLs
            if link_url.startswith(("http://", "https://", "mailto:", "#")):
                continue
            links.append((link_text, link_url, line_num))

    return links


def resolve_link(link_url: str, base_path: Path) -> Path:
    """Resolve a relative link URL to an absolute file path."""
    # Remove anchor if present
    if "#" in link_url:
        link_url = link_url.split("#")[0]

    # Decode URL encoding
    link_url = unquote(link_url)

    # Handle relative paths
    if link_url.startswith("/"):
        # Absolute from repo root
        return base_path.parent.parent / link_url.lstrip("/")
    else:
        # Relative to current file
        return (base_path.parent / link_url).resolve()


def check_links(root: Path, fix_common: bool = False) -> Tuple[int, List[str]]:
    """
    Check all markdown links in the repository.

    Returns (error_count, error_messages) tuple.
    """
    errors = []
    markdown_files = find_markdown_files(root)

    # Common fixes mapping
    common_fixes = {
        "../docs/": "../documentation/",
        "../../docs/": "../../documentation/",
        "../../../docs/": "../../../documentation/",
        "../Documentation/": "../documentation/",
        "../../Documentation/": "../../documentation/",
    }

    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            links = extract_links(content, md_file)

            for link_text, link_url, line_num in links:
                try:
                    target = resolve_link(link_url, md_file)

                    # Check if file exists
                    if not target.exists():
                        error_msg = (
                            f"{md_file.relative_to(root)}:{line_num}: "
                            f"Broken link: [{link_text}]({link_url}) -> {target}"
                        )
                        errors.append(error_msg)

                        # Try to fix common issues
                        if fix_common:
                            fixed_url = link_url
                            for old, new in common_fixes.items():
                                if old in fixed_url:
                                    fixed_url = fixed_url.replace(old, new)
                                    break

                            if fixed_url != link_url:
                                # Update the content
                                old_link = f"[{link_text}]({link_url})"
                                new_link = f"[{link_text}]({fixed_url})"
                                content = content.replace(old_link, new_link)
                                print(
                                    f"Fixed: {md_file.relative_to(root)}:{line_num} "
                                    f"{old_link} -> {new_link}"
                                )

                except Exception as e:
                    errors.append(
                        f"{md_file.relative_to(root)}:{line_num}: "
                        f"Error resolving link [{link_text}]({link_url}): {e}"
                    )

            # Write fixed content if we made changes
            if fix_common and content != md_file.read_text(encoding="utf-8"):
                md_file.write_text(content, encoding="utf-8")

        except Exception as e:
            errors.append(f"{md_file.relative_to(root)}: Error reading file: {e}")

    return len(errors), errors


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Check markdown links for broken references")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix common link issues (docs/ -> documentation/)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )

    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"Error: Root directory does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    error_count, errors = check_links(root, fix_common=args.fix)

    if errors:
        print(f"\nFound {error_count} broken link(s):\n", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        sys.exit(1)
    else:
        print("✓ All links are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
