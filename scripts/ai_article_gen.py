"""
AI学徒手记 - 公众号文章生成脚本
用法: python ai_article_gen.py [--count 1] [--topic "自定义选题"]

流程: 从选题库取题 → MiMo生成文章 → OpenClaw发送到微信
"""

import subprocess
import json
import os
import sys
import time
import argparse
import random

# ============ 配置 ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOPICS_FILE = os.path.join(SCRIPT_DIR, "ai_topics.txt")
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "templates", "ai_article_prompt.txt")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "ai_articles_generated.json")

MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
MIMO_BASE_URL = os.environ.get("MIMO_API_BASE", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.5")

WECHAT_TARGET = "o9cq805lfrS-OgQ59AIP9tamh3Jw@im.wechat"
CHANNEL = "openclaw-weixin"
OPENCLAW = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"


def load_history():
    """加载已生成记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"generated": [], "last_phase": 1, "last_index": 0}


def save_history(history):
    """保存已生成记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_topics():
    """加载选题库"""
    topics = []
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                topics.append({
                    "phase": int(parts[0]),
                    "level": parts[1],
                    "title": parts[2],
                    "keywords": parts[3],
                })
    return topics


def pick_topic(topics, history):
    """按阶段顺序选取题，优先跳过已生成的"""
    generated_titles = [t["title"] for t in history["generated"]]

    # 按阶段顺序找第一个未生成的
    for topic in topics:
        if topic["title"] not in generated_titles:
            return topic

    # 全部生成过，随机选一个重做
    return random.choice(topics)


def load_template():
    """加载 prompt 模板"""
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_mimo(prompt: str) -> dict:
    """调用 MiMo API 生成文章"""
    body = json.dumps({
        "model": MIMO_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
    })

    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{MIMO_BASE_URL}/chat/completions",
             "-H", f"Authorization: Bearer {MIMO_API_KEY}",
             "-H", "Content-Type: application/json",
             "-d", body],
            capture_output=True, timeout=120,
        )
        raw = result.stdout.decode("utf-8", errors="replace")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        return {"success": True, "content": content}
    except Exception as e:
        print(f"MiMo API error: {e}", file=sys.stderr)
        return {"success": False, "content": "", "error": str(e)}


def openclaw_send_text(text: str) -> bool:
    """通过 OpenClaw CLI 发送文本"""
    # 分段发送，避免消息太长
    if len(text) > 2000:
        parts = []
        current = ""
        for line in text.split("\n"):
            if len(current) + len(line) > 1800:
                parts.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current.strip():
            parts.append(current)

        success = True
        for i, part in enumerate(parts):
            if i > 0:
                time.sleep(3)
            result = subprocess.run(
                [OPENCLAW, "message", "send",
                 "--channel", CHANNEL,
                 "--target", WECHAT_TARGET,
                 "-m", part.strip()],
                capture_output=True, timeout=90,
            )
            if result.returncode != 0:
                success = False
        return success
    else:
        result = subprocess.run(
            [OPENCLAW, "message", "send",
             "--channel", CHANNEL,
             "--target", WECHAT_TARGET,
             "-m", text],
            capture_output=True, timeout=90,
        )
        return result.returncode == 0


def parse_article(raw_content: str) -> dict:
    """解析 API 返回的文章内容"""
    title = ""
    body = ""
    cta = ""

    lines = raw_content.strip().split("\n")
    section = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("标题："):
            title = stripped[3:].strip()
            section = "title"
        elif stripped.startswith("正文："):
            section = "body"
        elif stripped.startswith("引导关注："):
            cta = stripped[5:].strip()
            section = "cta"
        elif section == "body":
            body += line + "\n"
        elif section == "title" and not title:
            title = stripped
        elif section == "cta" and not cta:
            cta = stripped

    if not title:
        # 尝试从第一行提取
        for line in lines:
            if line.strip():
                title = line.strip().lstrip("#").strip()
                break

    return {
        "title": title,
        "body": body.strip(),
        "cta": cta.strip(),
    }


def format_for_wechat(article: dict) -> str:
    """格式化为微信可读的消息"""
    parts = []
    parts.append(f"【AI学徒手记】新文章草稿")
    parts.append(f"━━━━━━━━━━")
    parts.append(f"")
    parts.append(f"标题：{article['title']}")
    parts.append(f"")
    parts.append(f"━━━━━━━━━━")
    parts.append(article["body"])
    if article["cta"]:
        parts.append(f"")
        parts.append(f"━━━━━━━━━━")
        parts.append(article["cta"])
    parts.append(f"")
    parts.append(f"━━━━━━━━━━")
    parts.append(f"以上是AI生成的草稿，需要在公众号后台排版后发布。")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="生成几篇（默认1）")
    parser.add_argument("--topic", help="自定义选题（覆盖选题库）")
    parser.add_argument("--dry-run", action="store_true", help="只生成不发送")
    args = parser.parse_args()

    if not MIMO_API_KEY:
        # fallback to env var names used by peiwan
        MIMO_API_KEY_FALLBACK = os.environ.get("MIMO_API_KEY", "")
        if not MIMO_API_KEY_FALLBACK:
            # try reading from system env
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "[Environment]::GetEnvironmentVariable('MIMO_API_KEY','User');"
                     "[Environment]::GetEnvironmentVariable('MIMO_API_KEY','Machine')"],
                    capture_output=True, timeout=10,
                )
                lines = result.stdout.decode("utf-8", errors="replace").strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line and line.startswith("tp-"):
                        globals()["MIMO_API_KEY"] = line
                        break
            except Exception:
                pass

    if not globals().get("MIMO_API_KEY") and not MIMO_API_KEY:
        print("[ERROR] MIMO_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    # Use whichever key we found
    api_key = MIMO_API_KEY or globals().get("MIMO_API_KEY", "")
    if api_key:
        globals()["MIMO_API_KEY"] = api_key

    topics = load_topics()
    history = load_history()
    template = load_template()

    results = []
    for i in range(args.count):
        print(f"\n=== 第 {i + 1}/{args.count} 篇 ===", file=sys.stderr)

        # 选取题
        if args.topic:
            topic = {"phase": 0, "level": "自定义", "title": args.topic, "keywords": ""}
        else:
            topic = pick_topic(topics, history)

        print(f"选题: {topic['title']}", file=sys.stderr)
        print(f"难度: {topic['level']}", file=sys.stderr)

        # 生成 prompt
        prompt = template.format(
            topic=topic["title"],
            level=topic["level"],
            keywords=topic["keywords"],
        )

        # 调用 API
        print("正在生成文章...", file=sys.stderr)
        result = call_mimo(prompt)

        if not result["success"]:
            print(f"生成失败: {result.get('error', 'unknown')}", file=sys.stderr)
            results.append({"topic": topic["title"], "success": False})
            continue

        # 解析文章
        article = parse_article(result["content"])
        print(f"标题: {article['title']}", file=sys.stderr)
        print(f"正文长度: {len(article['body'])} 字", file=sys.stderr)

        # 格式化并发送
        message = format_for_wechat(article)

        if args.dry_run:
            print(message, file=sys.stderr)
            sent = False
        else:
            print("正在发送到微信...", file=sys.stderr)
            # 发送标题提示
            openclaw_send_text(f"正在生成第{i + 1}篇文章：{article['title']}...")
            time.sleep(2)
            # 发送文章内容
            sent = openclaw_send_text(message)
            if sent:
                print("发送成功", file=sys.stderr)
            else:
                print("发送失败", file=sys.stderr)

        # 记录历史
        history["generated"].append({
            "title": topic["title"],
            "phase": topic["phase"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "article_title": article["title"],
            "sent": sent,
        })
        save_history(history)

        results.append({
            "topic": topic["title"],
            "title": article["title"],
            "success": True,
            "sent": sent,
        })

        # 多篇之间间隔
        if i < args.count - 1:
            time.sleep(10)

    # 输出 JSON 结果
    output = json.dumps({
        "total": args.count,
        "success": sum(1 for r in results if r["success"]),
        "items": results,
    }, ensure_ascii=False)
    sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
