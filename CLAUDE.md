# CLAUDE.md - peiwan.co 游戏内容矩阵站

## 项目概述

用 AI 批量生成游戏垂直内容，部署到 peiwan.co，通过搜索引擎流量 + 广告联盟实现被动收入。

## 技术栈

- **静态站点**: Hugo + PaperMod 主题
- **部署**: 服务器 Nginx 托管 + Cloudflare CDN（可选）
- **内容生成**: Python + MiMo API（Anthropic 兼容格式），服务器端全自动
- **广告**: Google AdSense（后续）→ 百青藤（后续）
- **分析**: Google Analytics + 百度统计
- **SEO**: 百度站长平台 + Google Search Console
- **服务器**: 阿里云 4 核 8G Windows（已有）
- **域名**: peiwan.co（已有）

## 项目结构

```
F:\SEOAI\
├── CLAUDE.md
├── .env.example                 # 环境变量模板
├── .gitignore
├── start.ps1                    # 快速启动检查
├── .claude/
│   ├── prds/
│   │   └── peiwan-content-matrix.prd.md
│   └── plans/
│       └── peiwan-content-matrix.plan.md
├── site/                        # Hugo 站点
│   ├── config.toml              # 站点配置（SEO、导航、分类）
│   ├── themes/PaperMod/         # 主题（git clone）
│   ├── content/
│   │   ├── _index.md            # 首页
│   │   ├── about.md             # 关于（AdSense 需要）
│   │   ├── privacy.md           # 隐私政策（AdSense 需要）
│   │   ├── contact.md           # 联系方式（AdSense 需要）
│   │   ├── search.md            # 搜索页
│   │   ├── archives.md          # 归档页
│   │   ├── wangzhe/             # 王者荣耀
│   │   ├── yuanshen/            # 原神
│   │   ├── hepingjingying/      # 和平精英
│   │   ├── lolm/                # LOL手游
│   │   └── danzaipaidui/        # 蛋仔派对
│   ├── layouts/
│   │   ├── partials/
│   │   │   ├── extend_head.html     # GA/AdSense/百度统计/Schema
│   │   │   ├── adsense_article.html # 文章内广告位
│   │   │   └── schema_article.html  # Article 结构化数据
│   │   ├── index.json           # JSON Feed
│   │   └── robots.txt           # robots.txt 模板
│   ├── static/
│   └── archetypes/
├── scripts/
│   ├── generate.py              # 内容生成（MiMo API）
│   ├── keywords.txt             # 100 个关键词（5 品类各 20）
│   ├── templates/
│   │   └── article_prompt.txt   # Prompt 模板（去 AI 味）
│   ├── generated.json           # 已生成记录
│   ├── setup_server.ps1         # 服务器一键部署
│   ├── auto_generate.ps1        # 定时任务脚本
│   ├── install_task.ps1         # 安装 Windows 计划任务
│   └── auto_generate.log        # 运行日志
└── docs/
    └── setup-guide.md           # 完整搭建指南
```

## 核心工作流（全自动）

```
Windows Scheduled Task (daily 3:00 AM)
  -> auto_generate.ps1
    -> generate.py calls MiMo API to generate 10 articles
    -> hugo --minify --destination C:\www\peiwan
    -> git commit + push
    -> Nginx serves C:\www\peiwan
    -> peiwan.co updated
```

Zero manual intervention.

## 关键决策

| 决策 | 决定 | 理由 |
|------|------|------|
| 站点框架 | Hugo + PaperMod | 轻量、快速、SEO 友好、内置搜索 |
| 部署方式 | 服务器 Nginx 托管 | 已有 Nginx，无需额外服务 |
| AI 模型 | MiMo API（Anthropic 兼容） | CC Switch 代理，服务器端调用 |
| 内容去 AI 味 | Prompt 优化 + 后处理 | 口语化 prompt + regex 替换 AI 套路句式 |
| 定时生成 | Windows 计划任务 | 每天 3:00 自动生成 10 篇 |
| CDN | Cloudflare（可选） | 加速国内访问，后续配置 |

## 开发铁律

1. **SEO 优先**: 所有页面有 title/meta/H1/schema/sitemap
2. **去 AI 味**: Prompt 用玩家视角 + 后处理替换套路句式
3. **全自动**: 生成 → 构建 → 部署 全链路自动化
4. **可扩展**: 新增品类只需在 keywords.txt 加关键词

## 服务器部署流程

### 1. 环境准备

```powershell
# 安装 Python 3.10+
winget install Python.Python.3.13

# 安装 Hugo
Invoke-WebRequest -Uri "https://github.com/gohugoio/hugo/releases/download/v0.147.0/hugo_extended_0.147.0_windows-amd64.zip" -OutFile "$env:TEMP\hugo.zip"
Expand-Archive -Path "$env:TEMP\hugo.zip" -DestinationPath "C:\hugo" -Force
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\hugo", "Machine")

# 安装 anthropic
python -m pip install anthropic
```

### 2. 克隆项目

```powershell
cd C:\
git clone https://github.com/zooz7373/peiwan-site.git
cd peiwan-site

# 安装主题
git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git site/themes/PaperMod
```

### 3. 配置环境变量

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "your-token", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://token-plan-cn.xiaomimimo.com/anthropic", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_MODEL", "mimo-v2.5-pro", "User")
```

### 4. 配置 Nginx

```nginx
server {
    listen       80;
    server_name  www.peiwan.co;

    root   C:/www/peiwan;
    index  index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### 5. 创建网站目录并首次构建

```powershell
mkdir C:\www\peiwan -Force
cd C:\peiwan-site\site
hugo --minify --destination C:\www\peiwan
```

### 6. 安装定时任务

```powershell
cd C:\peiwan-site
.\scripts\install_task.ps1
```

### 7. 手动触发测试

```powershell
Start-ScheduledTask -TaskName 'PeiwanAutoGenerate'
```

## 代码修改流程

**所有代码修改在本地进行，提交到 GitHub，服务器拉取更新。**

```bash
# 本地修改代码
git add .
git commit -m "描述"
git push

# 服务器更新
cd C:\peiwan-site
git pull
```

## 当前阶段

**Phase: MVP 运行中**
- ✅ 项目结构和配置
- ✅ generate.py（MiMo API 版）
- ✅ Prompt 模板（去 AI 味）
- ✅ Hugo 站点结构 + PaperMod 主题配置
- ✅ SEO 模板（Schema、robots、GA/AdSense 占位）
- ✅ 服务器部署脚本 + 定时任务
- ✅ Nginx 配置 + 自动构建部署
- ✅ 内容生成流水线验证通过
- ⏳ 首批 100 篇内容生成中
- ⏳ Cloudflare CDN 配置（可选）
- ⏳ Google AdSense 申请（需 VPN）
- ⏳ SEO 提交（百度/Google）
