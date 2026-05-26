# CLAUDE.md

## 服务器

| 名称 | IP | 系统 | SSH |
|------|-----|------|-----|
| Windows-snxr | 101.200.50.157 | Windows Server 2022 | `ssh -i ~/.ssh/id_ed25519_win -o ServerAliveInterval=60 -o ServerAliveCountMax=3 Administrator@101.200.50.157` |

## 项目一：peiwan.co 游戏内容站

- **技术栈**: Hugo + PaperMod + Nginx + MiMo API
- **工作流**: Windows 定时任务 → generate.py → Hugo 构建 → Nginx 托管
- **定时任务**: `PeiwanAutoGenerate`（每天 17:30）, `XlvSendMorning/Noon/Evening`（小绿书）, `AiArticleGenerate`（公众号每天 10:00）
- **关键路径**: 代码 `F:\SEOAI\`，服务器 `C:\peiwan-site\`，站点 `C:\www\peiwan\`
- **API**: MiMo API（Anthropic 兼容），环境变量 `MIMO_API_KEY` / `MIMO_BASE_URL` / `MIMO_MODEL`

## 项目二：AI学徒手记 公众号

- **账号**: AI学徒手记
- **定位**: AI 知识学习 + 职业发展，帮读者从零构建 AI 能力找到 AI 工作
- **内容类目**: 科学科普、教育/职场、科技/互联网
- **内容形式**: 公众号长文教程 + 配图（每篇 3 张 Pexels 图片）
- **工作流**: 定时任务 → MiMo 生成文章 → Pexels 配图 → 保存到网页 → 手动复制到公众号发布
- **管理页面**: `https://peiwan.co/admin/`（手机打开即可查看文章、一键复制标题/正文、下载配图）
- **脚本**: `scripts/ai_article_gen.py`，保存文章到 `C:\www\peiwan\admin\articles\`
- **定时任务**: `AiArticleGenerate`（每天 10:00，RunLevel Highest）
- **选题库**: 24 篇（4 阶段：扫盲→工具→实战→求职）
