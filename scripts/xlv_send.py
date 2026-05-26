"""
小绿书内容生成 + 配图 + 发送一体化脚本
用法: python xlv_send.py [--style morning] [--topic 食物对比]

流程：MiMo生成文案 → Pexels匹配图片 → OpenClaw CLI发送到微信
"""

import subprocess
import json
import os
import sys
import time
import argparse

# ============ 配置 ============
MIMO_API_KEY = os.environ.get("XIAOMI_API_KEY", "tp-cyqceah81nao3r9b7o8e5tlc742cjlxoc43cz5w06r16flnm")
MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5"
IMAGE_SCRIPT = r"C:\peiwan-site\scripts\image_fetch.py"
WECHAT_TARGET = "o9cq805lfrS-OgQ59AIP9tamh3Jw@im.wechat"
CHANNEL = "openclaw-weixin"

# 不同时段的风格（文字控制在1-2句话，配图才是重点）
STYLE_PROMPTS = {
    "早间": "随机生成一条能引发讨论的日常生活内容。话题随机（食物对比、价格猜测、生活选择、冷知识等），要有争议性没有标准答案。严格要求：文案不超过2句话，口语化像发朋友圈吐槽，不要长段落。",
    "午间": "随机生成一条轻松搞笑的日常生活内容。话题随机（搞笑日常、反差对比、奇葩选择、神评论风格），要有趣味性能让人笑出来。严格要求：文案不超过2句话，口语化像发朋友圈吐槽，不要长段落。",
    "晚间": "随机生成一条搞笑吐槽或引争议的男性视角日常内容。话题从以下方向随机选：直男迷惑行为（送礼翻车、审美灾难、不会聊天）、打工社畜（加班、工资焦虑、奇葩老板）、生活槽点（租房踩坑、外卖翻车、网购离谱）、争议话题（甜咸之争、该不该AA、彩礼讨论）。严格要求：文案不超过2句话，要么搞笑要么引战，口语化像发朋友圈吐槽，不要情感感悟不要长段落。",
}

# 英文参数映射（避免 Windows 计划任务中文编码问题）
STYLE_ALIAS = {
    "morning": "早间",
    "noon": "午间",
    "evening": "晚间",
}

IMAGE_KEYWORD_MAP = {
    "螃蟹": "crab seafood", "猪肉": "pork meat", "牛肉": "beef steak",
    "火锅": "chinese hot pot", "烧烤": "bbq grill", "外卖": "food delivery",
    "早餐": "breakfast", "宵夜": "late night snack", "水果": "fruits",
    "零食": "snacks", "咖啡": "coffee latte", "奶茶": "bubble tea",
    "蛋糕": "cake dessert", "面条": "noodles ramen", "海鲜": "seafood",
    "汉堡": "hamburger", "冰淇淋": "ice cream",
    "手机": "smartphone", "充电": "phone charging", "电脑": "laptop",
    "床": "bedroom", "沙发": "sofa living room", "厨房": "kitchen",
    "衣服": "fashion outfit", "鞋子": "sneakers", "化妆": "makeup",
    "健身": "gym workout", "旅行": "travel vacation", "宠物": "cute pets",
    "植物": "garden flowers", "钱": "money cash", "快递": "package delivery",
    "城市": "city skyline", "天空": "sky clouds", "海": "ocean beach",
    "山": "mountain nature", "雨": "rain window", "雪": "snow winter",
    "夜晚": "night lights", "日落": "sunset golden hour", "星空": "starry night",
    "情侣": "couple romantic", "朋友": "friends happy", "家人": "family together",
    "孤独": "alone silhouette", "开心": "happy celebration", "难过": "sad rain",
    "工作": "office desk", "学习": "studying books", "运动": "running exercise",
    "凉面": "cold noodles", "办公室": "office workspace", "地铁": "subway commute",
    "猫": "cute cat", "狗": "cute puppy", "花": "flowers bouquet",
    "汽车": "car automobile", "咖啡馆": "coffee shop cafe", "餐厅": "restaurant",
}

# OpenClaw CLI 路径
OPENCLAW = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"


def call_mimo(prompt: str) -> dict:
    """调用 MiMo API 生成内容"""
    full_prompt = prompt + "\n\n请严格按照以下格式输出，不要多余内容：\n文案：[严格控制在1-2句话以内，不超过50个字，要精炼有趣]\n关键词：[一个能代表文案内容的中文关键词]\n英文搜图词：[对应的英文搜索词，用于在Pexels搜图，2-4个英文单词，要能搜出与文案匹配的图片，例如：sweet tofu pudding, minimalism home, spicy snack]\n标签：[3个标签用空格分隔]"

    body = json.dumps({
        "model": MIMO_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": 1500,
    })

    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{MIMO_BASE_URL}/chat/completions",
             "-H", f"Authorization: Bearer {MIMO_API_KEY}",
             "-H", "Content-Type: application/json",
             "-d", body],
            capture_output=True, timeout=60
        )
        raw = result.stdout.decode("utf-8", errors="replace")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"MiMo API error: {e}", file=sys.stderr)
        return {"text": "", "keyword": ""}

    lines = content.strip().split("\n")
    text_line = keyword_line = search_query = tags_line = ""
    for line in lines:
        if line.startswith("文案："):
            text_line = line[3:].strip()
        elif line.startswith("关键词："):
            keyword_line = line[4:].strip()
        elif line.startswith("英文搜图词："):
            search_query = line[6:].strip()
        elif line.startswith("标签："):
            tags_line = line[3:].strip()

    if not keyword_line:
        for cn in IMAGE_KEYWORD_MAP:
            if cn in content:
                keyword_line = cn
                break
        if not keyword_line:
            keyword_line = "lifestyle daily"

    if not search_query:
        search_query = keyword_line

    return {
        "text": text_line or content,
        "keyword": keyword_line,
        "search_query": search_query,
        "tags": tags_line,
        "raw": content,
    }


def fetch_and_download_image(search_query: str) -> str:
    """调用 image_fetch.py 下载图片，返回本地路径"""
    try:
        result = subprocess.run(
            ["python", IMAGE_SCRIPT, search_query, "--download"],
            capture_output=True, timeout=30
        )
        path = result.stdout.decode("utf-8", errors="replace").strip()
        if path and os.path.exists(path):
            return path
    except Exception as e:
        print(f"Image fetch error: {e}", file=sys.stderr)
    return ""


def restart_gateway():
    """重启 gateway 以重载 contextToken（解决主动推送静默失败问题）"""
    print("重启 gateway...", file=sys.stderr)
    try:
        # 停止 gateway（等它退出）
        subprocess.run([OPENCLAW, "gateway", "stop"], capture_output=True, timeout=30)
        time.sleep(3)

        # 启动 gateway（后台进程，不等待）
        DEVNULL = open(os.devnull, "w")
        subprocess.Popen(
            [OPENCLAW, "gateway", "start"],
            stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        )
        time.sleep(20)
        print("gateway 已重启", file=sys.stderr)
    except Exception as e:
        print(f"gateway 重启失败（静默跳过）: {e}", file=sys.stderr)


def wake_up_connection():
    """发送唤醒心跳，激活微信会话（解决长时间静默后消息丢失问题）"""
    print("发送心跳唤醒微信会话...", file=sys.stderr)
    heartbeat = f"[心跳] {int(time.time())}"
    try:
        subprocess.run(
            [OPENCLAW, "message", "send",
             "--channel", CHANNEL,
             "--target", WECHAT_TARGET,
             "-m", heartbeat],
            capture_output=True, timeout=30
        )
        time.sleep(5)
        print("心跳已发送", file=sys.stderr)
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"心跳发送失败（静默跳过）: {e}", file=sys.stderr)


def openclaw_send_text(text: str) -> bool:
    """通过 OpenClaw CLI 发送文字"""
    result = subprocess.run(
        [OPENCLAW, "message", "send",
         "--channel", CHANNEL,
         "--target", WECHAT_TARGET,
         "-m", text],
        capture_output=True, timeout=90
    )
    out = result.stdout.decode("utf-8", errors="replace")
    if result.returncode == 0:
        print(f"文字发送成功: {out.strip()}", file=sys.stderr)
        return True
    else:
        err = result.stderr.decode("utf-8", errors="replace")
        print(f"文字发送失败: {err.strip()}", file=sys.stderr)
        return False


def openclaw_send_image(image_path: str) -> bool:
    """通过 OpenClaw CLI 发送图片"""
    if not os.path.exists(image_path):
        print(f"图片不存在: {image_path}", file=sys.stderr)
        return False

    result = subprocess.run(
        [OPENCLAW, "message", "send",
         "--channel", CHANNEL,
         "--target", WECHAT_TARGET,
         "--media", image_path],
        capture_output=True, timeout=120
    )
    out = result.stdout.decode("utf-8", errors="replace")
    if result.returncode == 0:
        print(f"图片发送成功: {out.strip()}", file=sys.stderr)
        return True
    else:
        err = result.stderr.decode("utf-8", errors="replace")
        print(f"图片发送失败: {err.strip()}", file=sys.stderr)
        return False


def main():
    all_styles = list(STYLE_PROMPTS.keys()) + list(STYLE_ALIAS.keys())
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", choices=all_styles, default="早间")
    parser.add_argument("--topic", help="指定话题（可选）")
    parser.add_argument("--count", type=int, default=3, help="发送条数（默认 3）")
    args = parser.parse_args()

    # 英文参数转中文
    style = STYLE_ALIAS.get(args.style, args.style)

    # 重启 gateway 恢复 contextToken（一次就够）
    restart_gateway()

    # 发送心跳唤醒微信会话
    wake_up_connection()

    results = []
    for i in range(args.count):
        print(f"\n=== 第 {i+1}/{args.count} 条 ===", file=sys.stderr)

        # Step 1: 生成文案
        prompt = STYLE_PROMPTS[style]
        if args.topic:
            prompt += f"\n话题方向：{args.topic}"
        if i > 0:
            prompt += f"\n（这是第{i+1}条，话题要和前面不同）"

        print("正在生成文案...", file=sys.stderr)
        content = call_mimo(prompt)
        print(f"文案: {content['text']}", file=sys.stderr)
        print(f"关键词: {content['keyword']}", file=sys.stderr)

        # Step 2: 下载图片
        print("正在获取配图...", file=sys.stderr)
        image_path = fetch_and_download_image(content.get("search_query", content["keyword"]))
        print(f"图片: {image_path}", file=sys.stderr)

        # Step 3: 组装消息
        msg_parts = []
        if content["text"]:
            msg_parts.append(content["text"])
        if content["tags"]:
            msg_parts.append(f"\n{content['tags']}")
        full_text = "\n".join(msg_parts) if msg_parts else ""

        # Step 4: 发送
        text_ok = False
        image_ok = False

        if full_text:
            print("发送文字到微信...", file=sys.stderr)
            text_ok = openclaw_send_text(full_text)

        if image_path:
            print("发送图片到微信...", file=sys.stderr)
            image_ok = openclaw_send_image(image_path)

        if text_ok or image_ok:
            print("发送完成！", file=sys.stderr)
        else:
            print("发送失败！", file=sys.stderr)

        # 清理本地图片
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        results.append({
            "index": i + 1,
            "success": text_ok or image_ok,
            "text_sent": text_ok,
            "image_sent": image_ok,
            "text": content["text"],
            "keyword": content["keyword"],
            "tags": content["tags"],
            "image_path": image_path,
        })

        # 文字和图片之间间隔
        if text_ok and image_ok:
            time.sleep(3)

        # 条间间隔，避免微信限流
        if i < args.count - 1:
            time.sleep(30)

    # 输出 JSON 结果
    result_json = json.dumps({
        "total": args.count,
        "sent": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "items": results,
    }, ensure_ascii=False)
    sys.stdout.buffer.write(result_json.encode("utf-8"))


if __name__ == "__main__":
    main()

