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

## 项目二：AI学徒手记 公众号（新建）

- **账号**: AI学徒手记
- **定位**: AI 知识学习 + 职业发展，帮读者从零构建 AI 能力找到 AI 工作
- **内容类目**: 科学科普、教育/职场、科技/互联网
- **功能介绍**: 记录AI学习路上的每一步。从入门知识到实战项目，从工具使用到面试准备，陪你从零开始走向AI岗位。
- **内容形式**: 公众号长文教程 + 贴图
- **参考风格**: 图文排版、结构化教程、系列内容（参考 Claude Code 常用命令讲解系列）
- **状态**: 内容体系已搭建，选题库 24 篇（4阶段：扫盲→工具→实战→求职），每天 10:00 自动生成
- **脚本**: `scripts/ai_article_gen.py`，通过 OpenClaw 推送到微信，手动排版发布
- **定时任务**: `AiArticleGenerate`（每天 10:00，RunLevel Highest）
