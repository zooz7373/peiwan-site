#!/usr/bin/env python3
"""
批量修复存量文章中的评论区引用
只替换文章结尾段的评论区引用，正文叙事中的保留
"""

import re
from pathlib import Path

CONTENT_DIR = Path(__file__).parent.parent / "site" / "content"

REPLACEMENTS = [
    "去试试吧",
    "就这样，冲就完了",
    "好了就这样",
    "去游戏里练练吧",
]

# 结尾段评论区引用的各种模式
ENDING_PATTERNS = [
    r"(有[啥什]?(不懂|明白|问题|具体.*问题).*?)(评论区|留言区)[^。\n]*[。！]?\s*$",
    r"(评论区|留言区)(问|见|聊|再问|再聊|唠唠|甩出来)[^。\n]*[。！]?\s*$",
    r"(不懂的|不明白的|有啥问题|有啥具体.*的).*?(评论区|留言区)[^。\n]*[。！]?\s*$",
    r"(评论区|留言区)(或者.*?群里)?找我[^。\n]*[。！]?\s*$",
    r"(评论区|留言区)(.*?)(看到.*?回)[^。\n]*[。！]?\s*$",
]

# 正文叙事中合理的评论区用法（不替换）
NARRATIVE_PATTERNS = [
    r"评论区(一片|炸锅|全是|刷屏|都)",
    r"(贴吧|论坛).*?评论区",
]


import random


def is_narrative(line: str) -> bool:
    """判断是否是正文叙事中的评论区引用"""
    for pattern in NARRATIVE_PATTERNS:
        if re.search(pattern, line):
            return True
    return False


def fix_article(filepath: Path) -> bool:
    """修复单篇文章，返回是否有修改"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 找正文开始位置（跳过 frontmatter）
    body_start = 0
    in_frontmatter = False
    fm_count = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fm_count += 1
            if fm_count == 1:
                in_frontmatter = True
            elif fm_count == 2:
                body_start = i + 1
                break

    if fm_count < 2:
        return False  # 没有有效的 frontmatter

    # 只处理结尾 15 行
    tail_start = max(body_start, len(lines) - 15)
    modified = False
    new_lines = lines[:tail_start]

    for line in lines[tail_start:]:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue

        # 跳过叙事中的评论区引用
        if is_narrative(stripped):
            new_lines.append(line)
            continue

        original = stripped
        for pattern in ENDING_PATTERNS:
            if re.search(pattern, stripped):
                replacement = random.choice(REPLACEMENTS)
                stripped = re.sub(pattern, replacement, stripped)
                modified = True
                break

        # 兜底：结尾行中包含评论区/留言区的简单引用
        if stripped == original and re.search(r"(评论区|留言区)", stripped):
            stripped = random.choice(REPLACEMENTS)
            modified = True

        new_lines.append(stripped)

    if modified:
        filepath.write_text("\n".join(new_lines), encoding="utf-8")

    return modified


def main():
    md_files = list(CONTENT_DIR.rglob("*.md"))
    # 排除 _index.md 等特殊文件
    md_files = [f for f in md_files if f.name != "_index.md"]

    print(f"扫描 {len(md_files)} 篇文章...")

    fixed = 0
    skipped = 0
    for f in md_files:
        if fix_article(f):
            print(f"  [FIXED] {f.relative_to(CONTENT_DIR)}")
            fixed += 1
        else:
            skipped += 1

    print(f"\n完成！修复: {fixed}, 无需修改: {skipped}")


if __name__ == "__main__":
    main()
