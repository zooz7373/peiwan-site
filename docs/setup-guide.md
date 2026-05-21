# peiwan.co 搭建指南

## 架构概览

```
GitHub 仓库 → Cloudflare Pages → peiwan.co
     ↑
服务器定时任务 → Python (MiMo API) → 生成 Markdown → git push
```

全自动流水线：服务器每天凌晨 3 点自动生成 10 篇文章 → 推送 GitHub → Cloudflare 自动部署。

## 环境要求

- Python 3.10+
- Git
- Hugo Extended（setup 脚本会自动安装）
- MiMo API Key

## 快速部署（服务器）

### 1. 克隆仓库

```powershell
git clone https://github.com/你的用户名/peiwan-site.git
cd peiwan-site
```

### 2. 一键部署

```powershell
# 以管理员身份运行
.\scripts\setup_server.ps1 -ApiKey "你的MiMo-API-Key" -RepoUrl "https://github.com/你的用户名/peiwan-site.git"
```

脚本会自动：
- 安装 Python 依赖（openai）
- 安装 Hugo Extended
- 安装 PaperMod 主题
- 配置环境变量
- 初始化 Git 并推送
- 测试 Hugo 构建
- 测试内容生成

### 3. 安装定时任务

```powershell
.\scripts\install_task.ps1
```

安装后每天凌晨 3:00 自动生成 10 篇文章并推送到 GitHub。

## Cloudflare Pages 部署

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 Pages → Create a project → Connect to Git
3. 选择你的 GitHub 仓库
4. 构建设置：
   - **Framework preset**: Hugo
   - **Build command**: `hugo --minify`
   - **Build output directory**: `public`
   - **Environment variables**:
     - `HUGO_VERSION` = `0.147.0`
5. 保存并部署
6. 自定义域名：添加 peiwan.co

### DNS 配置

在域名注册商修改 nameserver 为 Cloudflare 提供的 NS 地址。等待 DNS 生效（通常 1-24 小时）。

## SEO 配置

### Google Search Console

1. 访问 https://search.google.com/search-console
2. 添加资源：https://peiwan.co
3. 验证方式：DNS 验证（推荐，Cloudflare 中添加 TXT 记录）
4. 提交 sitemap: https://peiwan.co/sitemap.xml

### 百度站长平台

1. 访问 https://ziyuan.baidu.com
2. 添加站点：https://peiwan.co
3. 验证站点（文件上传或 DNS）
4. 提交 sitemap

### Google Analytics

1. 创建媒体资源，获取 G-XXXXXXXXXX
2. 编辑 `site/config.toml`，取消注释并填入：
   ```toml
   googleAnalytics = "G-XXXXXXXXXX"
   ```

## Google AdSense

1. 确保网站有 30+ 篇内容
2. 确保有 about、privacy、contact 页面（已有）
3. 访问 https://www.google.com/adsense/ 注册
4. 添加站点，等待审核
5. 审核通过后编辑 `site/config.toml`：
   ```toml
   googleAdSensePubID = "ca-pub-XXXXXXXXXXXXXXXX"
   ```

## 日常操作

### 手动生成文章

```powershell
# 预览
python scripts\generate.py --dry-run

# 生成 10 篇
python scripts\generate.py --limit 10

# 生成并推送
python scripts\generate.py --limit 10 --push

# 只生成某个分类
python scripts\generate.py --category wangzhe --limit 5
```

### 手动触发定时任务

```powershell
Start-ScheduledTask -TaskName 'PeiwanAutoGenerate'
```

### 查看生成日志

```powershell
Get-Content scripts\auto_generate.log -Tail 50
```

## 常见问题

### Q: MiMo API 调用失败？
A: 检查 API Key 是否正确，网络是否通畅。运行 `$env:MIMO_API_KEY='your-key'; python scripts/generate.py --limit 1` 测试。

### Q: Hugo 构建失败？
A: 确认 PaperMod 主题已安装：`ls site/themes/PaperMod`。如果缺失，运行 `git submodule update --init`。

### Q: Cloudflare 部署失败？
A: 检查构建日志。常见问题：Hugo 版本不对（确保环境变量 HUGO_VERSION 设置正确）。

### Q: 百度不收录？
A: 百度对新站有考核期（1-3 个月）。坚持更新内容，使用百度站长的链接提交工具主动推送。

### Q: 文章 AI 味太重？
A: 调整 `scripts/templates/article_prompt.txt` 中的写作要求。后处理已在 `generate.py` 的 `reduce_ai_flavor()` 中内置。
