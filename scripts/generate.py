#!/usr/bin/env python3
"""
peiwan.co 游戏内容批量生成脚本 (MiMo API 版 - Anthropic 兼容)

用法：
  python generate.py                    # 生成所有未生成的关键词
  python generate.py --category wangzhe # 只生成王者荣耀
  python generate.py --limit 10         # 只生成 10 篇
  python generate.py --dry-run          # 预览不实际生成
  python generate.py --push             # 生成后自动 git push 触发部署

环境变量：
  MIMO_API_KEY      - MiMo API 密钥（必需）
  MIMO_API_BASE     - API 地址（默认 https://token-plan-cn.xiaomimimo.com/anthropic）
  MIMO_MODEL        - 模型名（默认 mimo-v2-flash）

依赖：
  pip install anthropic
"""

import os
import re
import sys
import json
import time
import random
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("请先安装 anthropic: pip install anthropic")
    sys.exit(1)

# ── 配置 ──────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
SITE_DIR = SCRIPT_DIR.parent / "site"
CONTENT_DIR = SITE_DIR / "content"
KEYWORDS_FILE = SCRIPT_DIR / "keywords.txt"
TEMPLATE_FILE = SCRIPT_DIR / "templates" / "article_prompt.txt"
GENERATED_LOG = SCRIPT_DIR / "generated.json"

API_KEY = os.environ.get("MIMO_API_KEY", os.environ.get("ANTHROPIC_AUTH_TOKEN", ""))
API_BASE = os.environ.get("MIMO_API_BASE", os.environ.get("ANTHROPIC_BASE_URL", "https://token-plan-cn.xiaomimimo.com/anthropic"))
MODEL = os.environ.get("MIMO_MODEL", os.environ.get("ANTHROPIC_MODEL", ""))
if not MODEL:
    MODEL = "mimo-v2.5-pro"

GAME_NAMES = {
    "wangzhe": "王者荣耀",
    "yuanshen": "原神",
    "hepingjingying": "和平精英",
    "lolm": "LOL手游",
    "danzaipaidui": "蛋仔派对",
    "xingqiongtiedao": "崩坏：星穹铁道",
    "jinchanchanzhizhan": "金铲铲之战",
}

# 每日每款游戏的发帖权重（总计 2 篇/天，模拟真人更新节奏）
GAME_WEIGHTS = {
    "wangzhe": 1,
    "yuanshen": 0,
    "hepingjingying": 0,
    "lolm": 0,
    "danzaipaidui": 0,
    "xingqiongtiedao": 0,
    "jinchanchanzhizhan": 1,
}

# 轮转权重 — 每周换一批游戏重点发，避免永远只发两款
GAME_ROTATION = [
    {"wangzhe": 1, "yuanshen": 1},                     # 周一
    {"hepingjingying": 1, "lolm": 1},                   # 周二
    {"danzaipaidui": 1, "xingqiongtiedao": 1},          # 周三
    {"wangzhe": 1, "jinchanchanzhizhan": 1},            # 周四
    {"yuanshen": 1, "hepingjingying": 1},               # 周五
    {"lolm": 1, "danzaipaidui": 1},                     # 周六
    {"xingqiongtiedao": 1, "jinchanchanzhizhan": 1},    # 周日
]


# ── AI 味检测与后处理 ──────────────────────────────────

AI_PATTERNS = [
    r"^(首先|其次|最后|总之|综上所述|值得注意的是|需要指出的是)",
    r"^(作为一名|作为一个|在.*中|在当今|在这个)",
    r"(接下来让我们|下面让我们|现在让我们|接下来我们)",
    r"(总而言之|综上所述|总的来说|概括来说)",
    r"(希望这篇|希望以上|以上就是|以上内容)",
    r"(如果你有|如果你还|如有疑问|欢迎在评论)",
    r"(需要注意的是|值得一提的是|不可否认|毋庸置疑)",
    r"(提供了.*保障|奠定了.*基础|发挥了.*作用)",
    r"(评论区问|评论区见|评论区聊|评论区再问|留言区问|评论区留言)",
    r"(好了就这样|冲就完了|绝绝子|属于是|nbcs)",
    r"(玩了三年多|玩了三年的|作为一名.*老玩家)",
]

REPLACE_MAP = {
    "首先，": ["直接说", "先说", ""],
    "其次，": ["然后", "接着", ""],
    "最后，": ["最关键的是", "还有", ""],
    "总之，": ["说白了", "简单说", ""],
    "综上所述，": ["总的来说", "一句话总结", ""],
    "值得注意的是：": ["还有个事", "对了", ""],
    "需要指出的是：": ["说个重点", "注意下", ""],
    "希望这篇攻略对你有帮助！": ["就这些，去试试吧", "差不多就这些", "好了开冲"],
    "如果你还有其他问题，欢迎在评论区留言。": ["去试试吧", ""],
    "接下来让我们": ["咱们直接看", "看看"],
    "在当今": ["现在", ""],
    "提供了有力的保障": ["很有用", "帮大忙了"],
    "奠定了坚实的基础": ["打好了底子", "基础就稳了"],
}


def reduce_ai_flavor(text: str) -> str:
    """后处理：降低 AI 味"""
    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.strip()

        for pattern in AI_PATTERNS:
            if re.match(pattern, stripped):
                for old, new_options in REPLACE_MAP.items():
                    if old in stripped:
                        replacement = random.choice(new_options)
                        stripped = stripped.replace(old, replacement, 1)

        for old, new_options in REPLACE_MAP.items():
            if old in stripped:
                replacement = random.choice(new_options)
                stripped = stripped.replace(old, replacement, 1)

        stripped = re.sub(r"了了+", "了", stripped)
        result.append(stripped)

    return "\n".join(result)


COMMENT_ENDING_REPLACEMENTS = [
    "去游戏里试试手感",
    "具体手感还是得自己试",
    "先到训练营练练",
    "",
]

COMMENT_REF_PATTERNS = [
    # 匹配结尾段中引用评论区的各种表述（不含正文叙事中的合理用法）
    r"(有[啥什]?(不懂|明白|问题|具体.*问题).*?)(评论区|留言区)[^。\n]*[。！]?",
    r"(评论区|留言区)(问|见|聊|再问|再聊|唠唠|甩出来)[^。\n]*[。！]?",
    r"(不懂的|不明白的|有啥问题|有啥具体.*的).*?(评论区|留言区)[^。\n]*[。！]?",
    r"(评论区|留言区)(或者.*?群里)?找我[^。\n]*[。！]?",
]


def remove_comment_references(text: str) -> str:
    """后处理：移除指向评论区的表述（网站无评论功能）"""
    lines = text.split("\n")

    # 只处理文章最后 15 行（结尾段），中间的叙事评论区引用保留
    tail_start = max(0, len(lines) - 15)
    result = lines[:tail_start]
    tail_lines = lines[tail_start:]

    for line in tail_lines:
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue

        # 跳过正文叙事中的评论区引用（"评论区一片骂声"、"评论区炸锅"）
        if re.search(r"评论区(一片|炸锅|全是|刷屏|都)", stripped):
            result.append(line)
            continue

        original = stripped
        for pattern in COMMENT_REF_PATTERNS:
            if re.search(pattern, stripped):
                replacement = random.choice(COMMENT_ENDING_REPLACEMENTS)
                # 用替换值替换整行中匹配评论区的部分
                stripped = re.sub(pattern, replacement, stripped)
                break

        # 兜底：简单包含"评论区"或"留言区"的结尾行
        if stripped == original and re.search(r"(评论区|留言区)", stripped):
            stripped = random.choice(COMMENT_ENDING_REPLACEMENTS)

        result.append(stripped)

    return "\n".join(result)


# ── 关键词与记录管理 ──────────────────────────────────


def load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def load_keywords(category: str | None = None) -> list[dict]:
    keywords = []
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 3:
                cat, keyword, intent = parts
                if category is None or cat == category:
                    keywords.append({
                        "category": cat,
                        "keyword": keyword,
                        "intent": intent,
                    })
    return keywords


def load_generated() -> dict:
    if GENERATED_LOG.exists():
        with open(GENERATED_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_generated(generated: dict) -> None:
    with open(GENERATED_LOG, "w", encoding="utf-8") as f:
        json.dump(generated, f, ensure_ascii=False, indent=2)


# ── MiMo API 调用 (Anthropic 兼容) ──────────────────────


def create_client() -> anthropic.Anthropic:
    if not API_KEY:
        print("[ERROR] 请设置环境变量 MIMO_API_KEY")
        print("  PowerShell: $env:MIMO_API_KEY='your-key-here'")
        sys.exit(1)
    return anthropic.Anthropic(api_key=API_KEY, base_url=API_BASE)


def generate_article(
    client: anthropic.Anthropic,
    keyword_data: dict,
    template: str,
    dry_run: bool = False,
) -> str | None:
    """调用 MiMo API 生成一篇文章"""
    game_name = GAME_NAMES.get(keyword_data["category"], keyword_data["category"])

    prompt = template.format(
        game_name=game_name,
        keyword=keyword_data["keyword"],
        search_intent=keyword_data["intent"],
    )

    if dry_run:
        print(f"  [DRY RUN] Would generate: {keyword_data['keyword']}")
        return None

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="你是游戏内容写手，写作风格自然口语化。严禁使用以下表达：好了就这样、绝绝子、属于是、nbcs、作为一名老玩家、玩了三年多、首先其次最后、值得注意的是、综上所述。结尾不要套路化。",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        # Anthropic API 返回 content 是一个列表
        return response.content[0].text
    except Exception as e:
        print(f"  [ERROR] API 调用失败: {e}")
        return None


# ── 文章解析与保存 ──────────────────────────────────────


def parse_article(raw_text: str) -> dict:
    lines = raw_text.strip().split("\n")

    title = ""
    meta = ""
    category = ""
    body_start = 0

    for i, line in enumerate(lines):
        if line.startswith("TITLE:"):
            title = line[6:].strip()
        elif line.startswith("META:"):
            meta = line[5:].strip()
        elif line.startswith("CATEGORY:"):
            category = line[9:].strip()
        elif line.strip() == "---":
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()

    # 后处理：降低 AI 味
    body = reduce_ai_flavor(body)

    # 后处理：移除评论区引用（网站无评论功能）
    body = remove_comment_references(body)

    if not title:
        title = lines[0][:50] if lines else "未命名文章"
    if not meta:
        meta = title[:150]

    return {
        "title": title,
        "meta": meta,
        "category": category,
        "body": body,
    }


def slugify(text: str, max_len: int = 30) -> str:
    slug = re.sub(r"[^\w一-鿿-]", "-", text)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_len]


def save_article(keyword_data: dict, article: dict) -> Path:
    category = keyword_data["category"]
    keyword = keyword_data["keyword"]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    slug = slugify(keyword)
    filename = f"{timestamp}-{slug}.md"

    article_dir = CONTENT_DIR / category
    article_dir.mkdir(parents=True, exist_ok=True)

    filepath = article_dir / filename

    front_matter = f"""---
title: "{article['title']}"
date: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")}
description: "{article['meta']}"
categories: ["{GAME_NAMES.get(category, category)}"]
tags: ["{keyword_data['intent']}", "{GAME_NAMES.get(category, category)}"]
keywords: ["{keyword}"]
draft: false
---

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + article["body"])

    return filepath


# ── Git 自动推送 ──────────────────────────────────────


def git_push(message: str) -> bool:
    try:
        repo_dir = str(SITE_DIR.parent)

        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir, capture_output=True, text=True, encoding="utf-8",
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        if "nothing to commit" in stdout or "nothing to commit" in stderr:
            print("  [GIT] 没有新变更")
            return True

        subprocess.run(["git", "push"], cwd=repo_dir, check=True, capture_output=True)
        print(f"  [GIT] 已推送到远程仓库")
        return True
    except subprocess.CalledProcessError as e:
        err = e.stderr or "unknown error"
        print(f"  [GIT ERROR] {err}")
        return False


# ── 主流程 ──────────────────────────────────────────────


def select_by_weight(all_pending: list[dict], limit: int | None = None) -> list[dict]:
    """按每日轮转权重从待生成关键词中选取（每天 2 篇）"""
    # 按游戏分组
    by_category: dict[str, list[dict]] = {}
    for kw in all_pending:
        by_category.setdefault(kw["category"], []).append(kw)

    # 根据今天是周几选择权重
    today_weekday = datetime.now().weekday()  # 0=Monday
    weights = GAME_ROTATION[today_weekday % len(GAME_ROTATION)]

    selected = []
    for category, weight in weights.items():
        cat_pending = by_category.get(category, [])
        count = min(weight, len(cat_pending))
        selected.extend(cat_pending[:count])

    # 打乱顺序
    random.shuffle(selected)

    if limit:
        selected = selected[:limit]

    return selected


def main():
    parser = argparse.ArgumentParser(description="peiwan.co 内容批量生成 (MiMo API)")
    parser.add_argument("--category", help="只生成指定分类")
    parser.add_argument("--limit", type=int, help="最多生成几篇")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--push", action="store_true", help="生成后自动 git push")
    args = parser.parse_args()

    print("=" * 50)
    print("peiwan.co 游戏内容批量生成 (MiMo API)")
    print("=" * 50)

    template = load_template()
    keywords = load_keywords(args.category)
    generated = load_generated()

    all_pending = [k for k in keywords if k["keyword"] not in generated]

    # 指定分类时走顺序模式，否则按权重分配
    if args.category:
        pending = all_pending[:args.limit] if args.limit else all_pending
    else:
        pending = select_by_weight(all_pending, args.limit)

    print(f"\nAPI: {API_BASE}")
    print(f"模型: {MODEL}")
    print(f"关键词总数: {len(keywords)}")
    print(f"已生成: {len(generated)}")
    print(f"待生成(全部): {len(all_pending)}")
    print(f"本次选取: {len(pending)}")

    # 显示每款游戏分配情况
    from collections import Counter
    cat_counts = Counter(kw["category"] for kw in pending)
    for cat, count in sorted(cat_counts.items()):
        name = GAME_NAMES.get(cat, cat)
        print(f"  {name}: {count} 篇")

    if args.dry_run:
        print("\n[DRY RUN] 预览待生成文章:")
        for i, kw in enumerate(pending, 1):
            print(f"  {i}. [{kw['category']}] {kw['keyword']} ({kw['intent']})")
        return

    if not pending:
        print("\n所有关键词已生成完毕！")
        return

    client = create_client()

    print(f"\n开始生成 {len(pending)} 篇文章...\n")
    success = 0
    failed = 0

    for i, kw in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] {kw['keyword']}")

        raw = generate_article(client, kw, template)
        if raw:
            article = parse_article(raw)
            filepath = save_article(kw, article)
            print(f"  -> 已保存: {filepath.name}")

            generated[kw["keyword"]] = {
                "file": str(filepath),
                "time": datetime.now().isoformat(),
                "category": kw["category"],
            }
            save_generated(generated)
            success += 1
        else:
            print(f"  -> 生成失败")
            failed += 1

        if i < len(pending):
            time.sleep(random.uniform(1.5, 3.0))

    print(f"\n{'=' * 50}")
    print(f"完成！成功: {success}, 失败: {failed}")
    print(f"文章目录: {CONTENT_DIR}")

    if args.push and success > 0:
        print(f"\n正在推送到 GitHub...")
        git_push(f"feat: 新增 {success} 篇游戏攻略文章")


if __name__ == "__main__":
    main()
