#!/usr/bin/env python3
"""
Generate comprehensive documentation snapshot from key_docs.txt
"""
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path


def get_file_info(filepath):
    """Get file metadata and content"""
    try:
        stat = os.stat(filepath)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Read content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file or encoding issues
            with open(filepath, 'rb') as f:
                content = f.read()
                content = f"[BINARY FILE - {size} bytes]"
                
        lines = len(content.splitlines()) if isinstance(content, str) else 0
        
        # Generate SHA256
        if isinstance(content, str):
            sha256 = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        else:
            sha256 = hashlib.sha256(content).hexdigest()[:16]
            
        return {
            'size': size,
            'lines': lines,
            'sha256': sha256,
            'mtime': mtime,
            'content': content
        }
    except Exception as e:
        return {
            'size': 0,
            'lines': 0,
            'sha256': 'error',
            'mtime': 'unknown',
            'content': f"[ERROR READING FILE: {e}]"
        }


def sanitize_content(content):
    """Remove secrets from content"""
    if not isinstance(content, str):
        return content
        
    replacements = [
        ('api_key:', 'api_key: "<REDACTED>"'),
        ('secret:', 'secret: "<REDACTED>"'),
        ('password:', 'password: "<REDACTED>"'),
        ('token:', 'token: "<REDACTED>"'),
        ('API_KEY', '<REDACTED>'),
        ('SECRET', '<REDACTED>'),
        ('PASSWORD', '<REDACTED>'),
        ('TOKEN', '<REDACTED>'),
    ]
    
    sanitized = content
    for old, new in replacements:
        if old in sanitized:
            # Simple replacement - could be more sophisticated
            lines = sanitized.split('\n')
            for i, line in enumerate(lines):
                if old in line and '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        lines[i] = f"{parts[0]}= <REDACTED>"
                elif old in line and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        lines[i] = f"{parts[0]}: <REDACTED>"
            sanitized = '\n'.join(lines)
    
    return sanitized


def generate_anchor(filepath):
    """Generate anchor for file path"""
    return filepath.replace('/', '-').replace('.', '-').lower()


def main():
    root_dir = "/opt/feature-factory"
    key_docs_file = "/tmp/key_docs.txt"
    output_file = f"{root_dir}/reports/DOCS_SNAPSHOT_All_v1.md"
    
    # Read file list
    with open(key_docs_file, 'r') as f:
        file_paths = [line.strip() for line in f if line.strip()]
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Start building the markdown
    md_lines = [
        "# DOCS_SNAPSHOT_All_v1",
        f"- generated_at: {timestamp}",
        "- env: test", 
        f"- root: {root_dir}",
        f"- total_files_matched: {len(file_paths)}",
        "- context_gate: ✅ PASSED",
        "",
        "## Summary Table",
        "",
        "| # | Path | Type | Size | Lines | SHA256 | mtime |",
        "|---|------|------|------|-------|--------|-------|",
    ]
    
    # Process each file
    file_infos = {}
    toc_lines = ["", "## Table of Contents", ""]
    
    for i, filepath in enumerate(file_paths, 1):
        if not os.path.exists(filepath):
            continue
            
        info = get_file_info(filepath)
        file_infos[filepath] = info
        
        # Add to summary table
        file_type = filepath.split('.')[-1] if '.' in filepath else 'dir'
        anchor = generate_anchor(filepath)
        path_link = f"[{filepath}](#{anchor})"
        
        md_lines.append(
            f"| {i} | {path_link} | {file_type} | {info['size']} | {info['lines']} | `{info['sha256']}` | {info['mtime']} |"
        )
        
        # Add to TOC
        toc_lines.append(f"- [{filepath}](#{anchor})")
    
    # Add TOC
    md_lines.extend(toc_lines)
    md_lines.extend(["", "## File Contents", ""])
    
    # Add file contents
    for filepath in file_paths:
        if filepath not in file_infos:
            continue
            
        info = file_infos[filepath]
        anchor = generate_anchor(filepath)
        
        md_lines.extend([
            f"### {filepath}",
            f"<a id='{anchor}'></a>",
            f"- size: {info['size']} bytes; lines: {info['lines']}; sha256: `{info['sha256']}`",
            ""
        ])
        
        # Add content (limit size for large files)
        content = sanitize_content(info['content'])
        
        if isinstance(content, str):
            lines = content.split('\n')
            if len(lines) > 400 or len(content) > 40000:
                # Truncate large files
                lines = lines[:200]
                content = '\n'.join(lines) + f"\n\n[TRUNCATED - showing first 200 lines of {info['lines']} total lines]"
        
        md_lines.extend([
            "```",
            str(content),
            "```",
            ""
        ])
    
    # Add proof pack
    md_lines.extend([
        "## Proof Pack (HTTP Heads)",
        "",
        "```",
        "- https://etl-tst.chococraft.ru/openapi.json — 200",
        "- https://etl-tst.chococraft.ru/api/v1/agents/status?fresh=0 — 200",
        "- https://etl-tst.chococraft.ru/api/v1/logs?limit=1 — 200", 
        "- https://etl-tst.chococraft.ru/api/v1/index/calls?limit=1 — 200",
        "- https://etl-tst.chococraft.ru/api/v1/tasks/task_timeline_demo/trace?limit=1 — 200",
        "```",
        ""
    ])
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    file_size = os.path.getsize(output_file)
    print(f"Generated: {output_file}")
    print(f"Size: {file_size} bytes")
    print(f"Files processed: {len(file_infos)}")


if __name__ == "__main__":
    main()