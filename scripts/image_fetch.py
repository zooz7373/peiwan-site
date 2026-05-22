"""
Pexels 图片抓取脚本（curl 版，兼容 Windows Server TLS 问题）
支持下载图片到本地，用于微信直接发送图片。

用法:
  python image_fetch.py "关键词" --url-only          # 只返回 URL
  python image_fetch.py "关键词" --download           # 下载到本地，返回本地路径
  python image_fetch.py "关键词" --download --dir C:\temp  # 指定下载目录
"""

import sys
import json
import subprocess
import os
import argparse
import urllib.parse
import tempfile

PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    "RQ3hvCdTVnWJ5JbZ3FtVBh2Vx5gekJLg2bHG42TVQh0q0A7H6uPUKheq"
)

KEYWORD_MAP = {
    "螃蟹": "crab seafood", "猪肉": "pork meat market", "牛肉": "beef steak",
    "火锅": "chinese hot pot", "烧烤": "bbq grill", "外卖": "food delivery",
    "早餐": "breakfast chinese", "宵夜": "late night snack", "水果": "fruits fresh",
    "零食": "snacks candy", "咖啡": "coffee latte", "奶茶": "bubble tea milk tea",
    "蛋糕": "cake dessert", "米饭": "rice bowl asian", "面条": "noodles ramen",
    "海鲜": "seafood platter", "汉堡": "hamburger fast food", "披萨": "pizza slice",
    "冰淇淋": "ice cream cone", "酒": "beer drinks bar", "烧烤": "bbq grill meat",
    "手机": "smartphone mobile phone", "充电": "phone charging cable",
    "电脑": "laptop computer desk", "床": "bed bedroom cozy", "沙发": "sofa living room",
    "厨房": "kitchen cooking", "衣服": "clothes fashion outfit", "鞋子": "sneakers shoes",
    "化妆": "makeup cosmetics", "健身": "gym workout fitness", "旅行": "travel vacation",
    "宠物": "cute pets dogs cats", "植物": "plants garden flowers",
    "钱": "money cash coins", "快递": "package delivery box", "超市": "supermarket grocery",
    "城市": "city skyline night", "天空": "sky clouds sunset", "海": "ocean beach waves",
    "山": "mountain hiking nature", "雨": "rain window drops", "雪": "snow winter cold",
    "夜晚": "night city lights", "日落": "sunset golden hour", "星空": "starry night sky",
    "情侣": "couple holding hands romantic", "朋友": "friends group happy",
    "家人": "family dinner together", "孤独": "alone person silhouette",
    "开心": "happy joyful celebration", "难过": "sad person rain",
    "工作": "office desk work", "学习": "student studying books",
    "运动": "sports running exercise", "派对": "party celebration confetti",
    "自拍": "selfie phone mirror", "装修": "home interior design",
    "生日": "birthday cake candles", "婚礼": "wedding ceremony",
    "驾照": "car driving road", "考试": "exam study stress",
    "减肥": "weight loss healthy food", "失眠": "insomnia night awake",
    "凉面": "cold noodles chinese", "火锅底料": "hot pot broth",
    "办公室": "office workspace", "地铁": "subway metro commute",
    "奶茶店": "milk tea shop", "健身房": "gym fitness equipment",
    "卧室": "bedroom interior", "客厅": "living room modern",
    "冰箱": "refrigerator kitchen", "洗衣机": "washing machine laundry",
    "猫": "cute cat", "狗": "cute dog puppy",
    "花": "flowers bouquet", "树": "trees nature green",
    "汽车": "car automobile", "自行车": "bicycle bike",
    "咖啡馆": "coffee shop cafe", "餐厅": "restaurant dining",
    "电影院": "cinema movie theater", "公园": "park nature bench",
}

FALLBACK_KEYWORDS = ["lifestyle daily", "everyday life", "modern living"]


def translate_keyword(keyword: str) -> str:
    if keyword in KEYWORD_MAP:
        return KEYWORD_MAP[keyword]
    for cn, en in KEYWORD_MAP.items():
        if cn in keyword:
            return en
    return keyword


def search_pexels(query: str, count: int = 1, orientation: str = "square") -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page={count}&orientation={orientation}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: {PEXELS_API_KEY}", url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

    results = []
    for photo in data.get("photos", []):
        results.append({
            "url": photo["src"]["original"],
            "large2x": photo["src"]["large2x"],
            "large": photo["src"]["large"],
            "medium": photo["src"]["medium"],
            "small": photo["src"]["small"],
            "photographer": photo["photographer"],
            "alt": photo.get("alt", ""),
        })
    return results


def download_image(url: str, save_dir: str = None) -> str:
    """下载图片到本地，返回文件路径"""
    if save_dir is None:
        save_dir = os.path.join(tempfile.gettempdir(), "pexels_images")
    os.makedirs(save_dir, exist_ok=True)

    # 从 URL 提取文件名
    filename = url.split("/")[-1].split("?")[0]
    filepath = os.path.join(save_dir, filename)

    try:
        result = subprocess.run(
            ["curl", "-s", "-k", "-L", "-o", filepath, url],
            capture_output=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
    return ""


def fetch_image(keyword: str, count: int = 1, download: bool = False, save_dir: str = None) -> dict:
    en_query = translate_keyword(keyword)
    images = search_pexels(en_query, count)
    if not images:
        for fb in FALLBACK_KEYWORDS:
            images = search_pexels(fb, count)
            if images:
                en_query = fb
                break

    if download and images:
        for img in images:
            img["local_path"] = download_image(img["large2x"], save_dir)

    return {
        "success": len(images) > 0,
        "images": images,
        "query_used": en_query,
        "keyword": keyword,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--url-only", action="store_true", help="只输出图片 URL")
    parser.add_argument("--download", action="store_true", help="下载图片到本地")
    parser.add_argument("--dir", help="下载目录")
    args = parser.parse_args()

    result = fetch_image(args.keyword, args.count, download=args.download, save_dir=args.dir)

    if args.url_only and result["success"]:
        print(result["images"][0]["medium"])
    elif args.download and result["success"]:
        path = result["images"][0].get("local_path", "")
        print(path if path else result["images"][0]["medium"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
