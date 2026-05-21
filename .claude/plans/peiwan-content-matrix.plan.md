# Plan: peiwan.co 游戏内容矩阵站

**Source PRD**: `.claude/prds/peiwan-content-matrix.prd.md`
**Selected Milestone**: #1 站点骨架上线 + #2 AI 内容流水线验证
**Complexity**: Medium

## Summary

项目已有内容生成脚本（`scripts/generate.py`）、100 个关键词（`scripts/keywords.txt`）和 prompt 模板，但 Hugo 站点尚未创建。需要完成 Hugo 站点搭建、主题配置、SEO 基础设置，然后验证 AI 内容生成流水线可用。

## Current State

| 资源 | 状态 |
|------|------|
| `scripts/generate.py` | 已完成，可工作 |
| `scripts/keywords.txt` | 已完成，100 个关键词 |
| `scripts/templates/article_prompt.txt` | 已完成 |
| `docs/setup-guide.md` | 已完成 |
| Hugo | **未安装** |
| `site/` 目录 | **不存在** |
| Python 3.13 + requests | 已就绪 |
| Ollama + Qwen2.5:7b | 需运行时验证 |

## Patterns to Mirror

| Category | Source | Pattern |
|---|---|---|
| Naming | `scripts/keywords.txt:1-5` | 分类用拼音小写（wangzhe, yuanshen），关键词用中文 |
| Config | `docs/setup-guide.md:43-76` | Hugo config.toml 已有参考配置 |
| Prompt | `scripts/templates/article_prompt.txt` | 结构化输出格式 TITLE/META/CATEGORY + 正文 |
| Deploy | `docs/setup-guide.md:108-135` | Cloudflare Pages 自动部署 |

## Files to Change

| File | Action | Why |
|---|---|---|
| `site/` | CREATE | Hugo 站点根目录（`hugo new site`） |
| `site/themes/PaperMod` | CREATE | 安装 PaperMod 主题（git submodule） |
| `site/config.toml` | CREATE | 站点配置（baseURL、主题、SEO、分类） |
| `site/content/_index.md` | CREATE | 首页内容 |
| `site/content/wangzhe/_index.md` | CREATE | 王者荣耀分类页 |
| `site/content/yuanshen/_index.md` | CREATE | 原神分类页 |
| `site/content/hepingjingying/_index.md` | CREATE | 和平精英分类页 |
| `site/content/lolm/_index.md` | CREATE | LOL手游分类页 |
| `site/content/danzaipaidui/_index.md` | CREATE | 蛋仔派对分类页 |
| `site/layouts/robots.txt` | CREATE | robots.txt 模板 |
| `site/layouts/partials/adsense.html` | CREATE | 广告位预留（后续填充） |
| `site/content/about.md` | CREATE | 关于页面（AdSense 审核需要） |
| `site/content/privacy.md` | CREATE | 隐私政策（AdSense 审核需要） |
| `site/content/contact.md` | CREATE | 联系方式（AdSense 审核需要） |

## Tasks

### Task 1: 安装 Hugo
- **Action**: 使用 `winget install Hugo.Hugo.Extended` 或 `scoop install hugo` 安装 Hugo Extended 版
- **Validate**: `hugo version` 输出版本号

### Task 2: 创建 Hugo 站点骨架
- **Action**: 在项目根目录执行 `hugo new site site`，然后安装 PaperMod 主题
- **Validate**: `ls site/themes/PaperMod` 目录存在

### Task 3: 配置站点
- **Action**: 编写 `site/config.toml`，包含：
  - baseURL: `https://peiwan.co/`
  - theme: PaperMod
  - 语言: zh-cn
  - SEO 参数（sitemap、robots、Open Graph）
  - 分类法（categories、tags）
  - Google Analytics 占位
- **Validate**: `hugo server` 能启动无报错

### Task 4: 创建分类页和必要页面
- **Action**: 为 5 个游戏分类创建 `_index.md`，以及 about/privacy/contact 页面
- **Validate**: 分类页在本地预览中可访问

### Task 5: 配置 SEO 模板
- **Action**: 创建 robots.txt 模板、Article schema 结构化数据、广告位 partial
- **Validate**: `hugo --minify` 构建成功，检查 public/ 输出

### Task 6: 生成首批测试文章
- **Action**: 确保 Ollama 运行，执行 `python scripts/generate.py --limit 5` 生成测试文章
- **Validate**: 检查生成的 Markdown 文件 front matter 格式正确

### Task 7: 本地预览验证
- **Action**: `hugo server -D` 启动本地预览，检查首页、分类页、文章页渲染
- **Validate**: 浏览器访问 http://localhost:1313 各页面正常

## Validation

```bash
# 安装验证
hugo version

# 构建验证
cd site && hugo --minify

# 内容生成验证
cd scripts && python generate.py --dry-run
cd scripts && python generate.py --limit 5

# 本地预览
cd site && hugo server -D
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Hugo 安装失败（Windows 权限问题） | Low | 备选方案：直接下载 Hugo 二进制文件 |
| Ollama 未运行或模型未下载 | Medium | 先检查 `ollama list`，必要时 `ollama pull qwen2.5:7b` |
| PaperMod 主题 submodule 克隆超时 | Medium | 使用 `--depth=1` 浅克隆 |
| 生成文章质量不够 | Medium | 先生成 5 篇评估，调整 prompt 模板 |

## Acceptance

- [ ] Hugo 安装成功，`hugo version` 可用
- [ ] `site/` 目录创建，PaperMod 主题安装
- [ ] `config.toml` 配置完整，`hugo server` 无报错
- [ ] 5 个分类页 + 3 个必要页面创建
- [ ] SEO 模板（robots.txt、schema、sitemap）就绪
- [ ] 生成 5 篇测试文章，格式正确
- [ ] 本地预览各页面正常渲染
