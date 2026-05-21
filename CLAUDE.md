# CLAUDE.md - peiwan.co 游戏内容矩阵站

## 项目概述

用 AI 批量生成游戏垂直内容，部署到 peiwan.co，通过搜索引擎流量 + 广告联盟实现被动收入。

## 技术栈

- **静态站点**: Hugo + PaperMod 主题
- **CDN/部署**: Cloudflare Pages（GitHub 推送自动构建部署）
- **内容生成**: Python + MiMo API（OpenAI 兼容格式），服务器端全自动
- **广告**: Google AdSense（MVP）→ 百青藤（后续补充）
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
│   ├── themes/PaperMod/         # 主题（git submodule）
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
Windows 计划任务（每天 3:00）
  → auto_generate.ps1
    → generate.py 调 MiMo API 生成 10 篇文章
    → git commit + push
    → Cloudflare Pages 自动构建部署
    → peiwan.co 更新
```

零人工干预。

## 关键决策

| 决策 | 决定 | 理由 |
|------|------|------|
| 站点框架 | Hugo + PaperMod | 轻量、快速、SEO 友好、内置搜索 |
| 部署方式 | Cloudflare Pages | GitHub 推送自动构建、免费 CDN、SSL |
| AI 模型 | MiMo API（OpenAI 兼容） | 6 亿 token 额度、服务器端调用、无需 GPU |
| 内容去 AI 味 | Prompt 优化 + 后处理 | 口语化 prompt + regex 替换 AI 套路句式 |
| 定时生成 | Windows 计划任务 | 每天 3:00 自动生成 10 篇，无需人工 |
| 广告 | Google AdSense 优先 | .co 不需要 ICP 备案 |

## 开发铁律

1. **SEO 优先**: 所有页面有 title/meta/H1/schema/sitemap
2. **去 AI 味**: Prompt 用玩家视角 + 后处理替换套路句式
3. **全自动**: 生成 → 部署 → 提交 sitemap 全链路自动化
4. **可扩展**: 新增品类只需在 keywords.txt 加关键词

## 当前阶段

**Phase: MVP 开发**
- ✅ 项目结构和配置
- ✅ generate.py（MiMo API 版）
- ✅ Prompt 模板（去 AI 味）
- ✅ Hugo 站点结构 + PaperMod 主题配置
- ✅ SEO 模板（Schema、robots、GA/AdSense 占位）
- ✅ 服务器部署脚本 + 定时任务
- ⏳ 安装 Hugo + PaperMod 主题（需在服务器执行）
- ⏳ 服务器部署（需提供 MiMo API Key）
- ⏳ 首批 100 篇内容生成
- ⏳ Google AdSense 申请
- ⏳ SEO 提交（百度/Google）
