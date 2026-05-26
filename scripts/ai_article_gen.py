"""
AI学徒手记 - 公众号文章生成脚本
用法: python ai_article_gen.py [--count 1] [--topic "自定义选题"]

流程: 从选题库取题 → MiMo生成文章 → Pexels配图 → 保存HTML/JSON → 通过网页查看复制
"""

import subprocess
import json
import os
import sys
import time
import argparse
import random
import urllib.parse

# ============ 配置 ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOPICS_FILE = os.path.join(SCRIPT_DIR, "ai_topics.txt")
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "templates", "ai_article_prompt.txt")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "ai_articles_generated.json")
IMAGE_SCRIPT = os.path.join(SCRIPT_DIR, "image_fetch.py")

# 文章输出目录（Nginx 通过 /admin 访问）
OUTPUT_DIR = r"C:\www\peiwan\admin\articles"
ADMIN_INDEX = r"C:\www\peiwan\admin\index.html"

def _get_env(name: str) -> str:
    """优先进程环境变量，其次 User 级，最后 Machine 级"""
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        r = subprocess.run(
            ["powershell", "-Command", f"[Environment]::GetEnvironmentVariable('{name}','User')"],
            capture_output=True, text=True, timeout=10,
        )
        val = r.stdout.strip()
        if val:
            return val
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["powershell", "-Command", f"[Environment]::GetEnvironmentVariable('{name}','Machine')"],
            capture_output=True, text=True, timeout=10,
        )
        val = r.stdout.strip()
        if val:
            return val
    except Exception:
        pass
    return ""


MIMO_API_KEY = _get_env("MIMO_API_KEY")
MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = _get_env("MIMO_MODEL") or "mimo-v2.5"


# ============ 选题与历史 ============

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"generated": [], "last_phase": 1, "last_index": 0}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_topics():
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
    generated_titles = [t["title"] for t in history["generated"]]
    for topic in topics:
        if topic["title"] not in generated_titles:
            return topic
    return random.choice(topics)

def load_template():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


# ============ MiMo API ============

def call_mimo(prompt: str) -> dict:
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


# ============ 配图 ============

# 选题关键词 → 英文搜图词映射
TOPIC_IMAGE_MAP = {
    "人工智能": "artificial intelligence technology",
    "ChatGPT": "chatgpt ai chatbot",
    "Claude": "ai assistant computer",
    "大模型": "neural network deep learning",
    "Prompt": "typing computer screen",
    "token": "digital currency coins",
    "AI工具": "ai tools workspace",
    "AI就业": "job interview office",
    "AI学习": "student learning online",
    "学习路线": "roadmap planning desk",
    "Python": "python programming code",
    "Midjourney": "digital art creation",
    "Excel": "data analysis spreadsheet",
    "PPT": "presentation slides office",
    "文案": "content writing desk",
    "翻译": "translation languages globe",
    "RAG": "database server technology",
    "本地部署": "server room computer",
    "网站": "website design laptop",
    "数据分析": "data charts analytics",
    "自媒体": "social media phone",
    "机器人": "robot technology",
    "AI岗位": "career job technology",
    "面试": "interview office professional",
    "简历": "resume writing desk",
    "转行": "career change path",
    "产品经理": "product manager team",
    "offer": "celebration success office",
    "AI绘画": "digital art painting",
    "聊天机器人": "chatbot conversation",
    "知识库": "knowledge library books",
    "自动化": "automation technology",
}

def get_image_keywords(topic_title, topic_keywords):
    """从选题中提取英文搜图关键词"""
    # 先在标题中找匹配
    for cn, en in TOPIC_IMAGE_MAP.items():
        if cn in topic_title:
            return en
    # 再从关键词中找
    for kw in topic_keywords.split():
        for cn, en in TOPIC_IMAGE_MAP.items():
            if cn in kw:
                return en
    return "technology learning computer"

def fetch_images(keyword, count=3):
    """调用 image_fetch.py 获取图片URL"""
    try:
        result = subprocess.run(
            ["python", IMAGE_SCRIPT, keyword, "--count", str(count), "--url-only"],
            capture_output=True, timeout=30,
        )
        # image_fetch.py 在 --url-only 时只输出一个URL（第一个）
        # 改为直接调用搜索获取多个URL
        urls = []
        lines = result.stdout.decode("utf-8", errors="replace").strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("http"):
                urls.append(line)
        return urls
    except Exception as e:
        print(f"图片获取错误: {e}", file=sys.stderr)
        return []

def fetch_images_from_pexels(keyword, count=3):
    """直接调用 Pexels API 获取多张图片URL"""
    PEXELS_KEY = "RQ3hvCdTVnWJ5JbZ3FtVBh2Vx5gekJLg2bHG42TVQh0q0A7H6uPUKheq"
    encoded = urllib.parse.quote(keyword)
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page={count}&orientation=landscape"
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: {PEXELS_KEY}", url],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        images = []
        for photo in data.get("photos", []):
            images.append({
                "url": photo["src"]["large"],
                "medium": photo["src"]["medium"],
                "photographer": photo["photographer"],
                "alt": photo.get("alt", ""),
            })
        return images
    except Exception as e:
        print(f"Pexels API error: {e}", file=sys.stderr)
        return []


# ============ 文章解析 ============

def parse_article(raw_content: str) -> dict:
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
        for line in lines:
            if line.strip():
                title = line.strip().lstrip("#").strip()
                break

    return {"title": title, "body": body.strip(), "cta": cta.strip()}


# ============ 保存文章 ============

def save_article(article, images, topic, history_entry):
    """保存文章为 JSON，供网页读取"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    slug = f"{int(time.time())}"
    article_data = {
        "id": slug,
        "title": article["title"],
        "body": article["body"],
        "cta": article["cta"],
        "images": images,
        "topic": topic["title"],
        "level": topic["level"],
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
    }

    # 保存单篇文章 JSON
    article_file = os.path.join(OUTPUT_DIR, f"{slug}.json")
    with open(article_file, "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)

    # 更新文章列表索引
    index_file = os.path.join(OUTPUT_DIR, "index.json")
    articles_list = []
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            articles_list = json.load(f)

    articles_list.insert(0, {
        "id": slug,
        "title": article["title"],
        "level": topic["level"],
        "created_at": article_data["created_at"],
    })

    # 只保留最近 50 篇
    articles_list = articles_list[:50]
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(articles_list, f, ensure_ascii=False, indent=2)

    print(f"文章已保存: {article_file}", file=sys.stderr)
    return article_file


# ============ 管理页面 ============

def ensure_admin_page():
    """确保管理页面 index.html 存在"""
    admin_dir = r"C:\www\peiwan\admin"
    os.makedirs(admin_dir, exist_ok=True)

    index_path = os.path.join(admin_dir, "index.html")
    if os.path.exists(index_path):
        return

    html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI学徒手记 - 文章管理</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f5f5;color:#333}
.container{max-width:800px;margin:0 auto;padding:16px}
h1{font-size:20px;padding:16px;background:#fff;border-bottom:1px solid #eee;text-align:center}
.article-list{margin-top:12px}
.article-card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.article-card:active{background:#f8f8f8}
.article-card h3{font-size:16px;margin-bottom:8px;line-height:1.4}
.article-card .meta{font-size:12px;color:#999;display:flex;gap:12px}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:#fff}
.badge-入门{background:#52c41a}.badge-进阶{background:#1890ff}.badge-高级{background:#722ed1}.badge-求职{background:#fa8c16}
.article-detail{display:none;background:#fff;border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.article-detail.show{display:block}
.back-btn{background:none;border:none;color:#1890ff;font-size:15px;cursor:pointer;padding:8px 0;margin-bottom:12px}
.article-detail h2{font-size:22px;margin-bottom:16px;line-height:1.3}
.article-body{line-height:1.8;font-size:15px;white-space:pre-wrap;margin-bottom:20px}
.images-section{margin:20px 0}
.images-section h4{margin-bottom:12px;color:#666}
.images-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.images-grid img{width:100%;border-radius:8px;cursor:pointer}
.images-grid .img-wrap{position:relative}
.images-grid .img-wrap .dl-btn{position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,.6);color:#fff;border:none;padding:4px 10px;border-radius:6px;font-size:12px;cursor:pointer}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px;padding-top:16px;border-top:1px solid #eee}
.btn{padding:10px 20px;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:500}
.btn-primary{background:#1890ff;color:#fff}.btn-primary:active{background:#0d7ae5}
.btn-success{background:#52c41a;color:#fff}.btn-success:active{background:#389e0d}
.btn-outline{background:#fff;color:#333;border:1px solid #ddd}.btn-outline:active{background:#f5f5f5}
.toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.75);color:#fff;padding:12px 24px;border-radius:8px;font-size:14px;z-index:999;display:none}
.empty{text-align:center;padding:60px 20px;color:#999}
.cta-text{color:#999;font-style:italic;margin:16px 0;padding:12px;background:#fafafa;border-radius:8px}
</style>
</head>
<body>
<h1>AI学徒手记 - 文章管理</h1>
<div class="container">
  <div id="list-view" class="article-list"></div>
  <div id="detail-view" class="article-detail"></div>
</div>
<div id="toast" class="toast">已复制</div>

<script>
const BASE = '/admin/articles/';
let articles = [];

function showToast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg||'已复制';t.style.display='block';
  setTimeout(()=>t.style.display='none',1500);
}

async function copyText(text){
  try{await navigator.clipboard.writeText(text);showToast('已复制到剪贴板')}
  catch(e){
    const ta=document.createElement('textarea');ta.value=text;
    document.body.appendChild(ta);ta.select();document.execCommand('copy');
    document.body.removeChild(ta);showToast('已复制到剪贴板');
  }
}

async function loadList(){
  try{
    const r=await fetch(BASE+'index.json');
    articles=await r.json();
  }catch(e){articles=[]}
  const el=document.getElementById('list-view');
  if(!articles.length){el.innerHTML='<div class="empty">还没有文章，先去生成一篇吧</div>';return}
  el.innerHTML=articles.map(a=>`
    <div class="article-card" onclick="loadArticle('${a.id}')">
      <h3>${esc(a.title)}</h3>
      <div class="meta">
        <span class="badge badge-${a.level}">${a.level}</span>
        <span>${a.created_at}</span>
      </div>
    </div>
  `).join('');
}

async function loadArticle(id){
  try{
    const r=await fetch(BASE+id+'.json');
    const a=await r.json();
    showDetail(a);
  }catch(e){showToast('加载失败')}
}

function showDetail(a){
  document.getElementById('list-view').style.display='none';
  const el=document.getElementById('detail-view');
  el.classList.add('show');

  const imgsHtml = a.images&&a.images.length ? `
    <div class="images-section">
      <h4>配图（长按或右键保存）</h4>
      <div class="images-grid">
        ${a.images.map((img,i)=>`
          <div class="img-wrap">
            <img src="${img.medium||img.url}" alt="${esc(img.alt||'')}" loading="lazy">
            <button class="dl-btn" onclick="event.stopPropagation();downloadImg('${img.url}','${a.id}_${i}.jpg')">下载</button>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  const ctaHtml = a.cta ? `<div class="cta-text">${esc(a.cta)}</div>` : '';

  el.innerHTML=`
    <button class="back-btn" onclick="goBack()">← 返回列表</button>
    <h2>${esc(a.title)}</h2>
    <div class="article-body">${esc(a.body)}</div>
    ${ctaHtml}
    ${imgsHtml}
    <div class="actions">
      <button class="btn btn-primary" onclick="copyText(decodeURIComponent('${encodeURIComponent(a.title)}'))">复制标题</button>
      <button class="btn btn-success" onclick="copyText(decodeURIComponent('${encodeURIComponent(a.body)}'))">复制正文</button>
      <button class="btn btn-outline" onclick="copyAll('${a.id}')">标题+正文一起复制</button>
    </div>
  `;
}

function goBack(){
  document.getElementById('detail-view').classList.remove('show');
  document.getElementById('detail-view').innerHTML='';
  document.getElementById('list-view').style.display='block';
}

function downloadImg(url,name){
  const a=document.createElement('a');a.href=url;a.download=name||'image.jpg';
  a.target='_blank';document.body.appendChild(a);a.click();document.body.removeChild(a);
}

async function copyAll(id){
  try{
    const r=await fetch(BASE+id+'.json');
    const a=await r.json();
    const full=a.title+'\n\n'+a.body+(a.cta?'\n\n'+a.cta:'');
    await copyText(full);
  }catch(e){showToast('复制失败')}
}

function esc(s){if(!s)return '';return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')}

loadList();
</script>
</body>
</html>'''
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"管理页面已创建: {index_path}", file=sys.stderr)


# ============ 主流程 ============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="生成几篇（默认1）")
    parser.add_argument("--topic", help="自定义选题（覆盖选题库）")
    args = parser.parse_args()

    if not MIMO_API_KEY:
        print("[ERROR] MIMO_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    topics = load_topics()
    history = load_history()
    template = load_template()
    ensure_admin_page()

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

        # 生成文章
        prompt = template.format(
            topic=topic["title"],
            level=topic["level"],
            keywords=topic["keywords"],
        )
        print("正在生成文章...", file=sys.stderr)
        result = call_mimo(prompt)

        if not result["success"]:
            print(f"生成失败: {result.get('error', 'unknown')}", file=sys.stderr)
            results.append({"topic": topic["title"], "success": False})
            continue

        article = parse_article(result["content"])
        print(f"标题: {article['title']}", file=sys.stderr)
        print(f"正文长度: {len(article['body'])} 字", file=sys.stderr)

        # 获取配图
        img_keyword = get_image_keywords(topic["title"], topic["keywords"])
        print(f"正在获取配图 (关键词: {img_keyword})...", file=sys.stderr)
        images = fetch_images_from_pexels(img_keyword, count=3)
        print(f"获取到 {len(images)} 张配图", file=sys.stderr)

        # 保存文章
        article_file = save_article(article, images, topic, None)

        # 记录历史
        history["generated"].append({
            "title": topic["title"],
            "phase": topic["phase"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "article_title": article["title"],
            "saved": True,
        })
        save_history(history)

        results.append({
            "topic": topic["title"],
            "title": article["title"],
            "success": True,
        })

        if i < args.count - 1:
            time.sleep(5)

    # 输出结果
    output = json.dumps({
        "total": args.count,
        "success": sum(1 for r in results if r["success"]),
        "items": results,
        "admin_url": "http://peiwan.co/admin",
    }, ensure_ascii=False)
    sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
