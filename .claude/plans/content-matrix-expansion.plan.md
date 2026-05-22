# Plan: peiwan.co 内容矩阵扩展与发帖策略

**Source PRD**: `.claude/prds/content-matrix-expansion.prd.md`
**Selected Milestone**: 全部 7 个里程碑（按依赖关系排序）
**Complexity**: Large

## Summary

修复评论区引用问题 → 改造发帖权重 → 新增 2 款游戏目录和关键词 → 补全/生成文章 → 更新站点配置。共涉及 4 个脚本文件、1 个 prompt 模板、2 个 Hugo 新目录、1 个站点配置、50 篇存量文章批量修复。

## Patterns to Mirror

| Category | Source | Pattern |
|---|---|---|
| 目录命名 | `site/content/wangzhe/` | 拼音全称 slug + `_index.md` 首页文件 |
| 关键词格式 | `scripts/keywords.txt:6` | `category\|keyword\|intent` 三列管道分隔 |
| 文章 frontmatter | `site/content/danzaipaidui/20260521182423-蛋仔派对排位赛规则.md:1` | title/description/categories/tags/keywords/draft |
| 后处理替换 | `scripts/generate.py:75-88` | REPLACE_MAP 字典式旧→新替换 |
| AI 味检测 | `scripts/generate.py:64-73` | AI_PATTERNS 正则列表逐行匹配 |
| 发帖调度 | `scripts/auto_generate.ps1:33` | `python generate.py --limit N --push` |
| 游戏名称映射 | `scripts/generate.py:53-59` | GAME_NAMES dict: slug → 中文名 |
| 导航菜单 | `site/config.toml:73-112` | `[[menu.main]]` 块，含 identifier/name/url/weight |

## Files to Change

| File | Action | Why |
|---|---|---|
| `scripts/templates/article_prompt.txt` | UPDATE | 移除第 17 行评论区示例，替换为无评论指向的自然结尾 |
| `scripts/generate.py` | UPDATE | ①REPLACE_MAP 移除评论区条目 ②AI_PATTERNS 增加评论引用检测 ③新增后处理批量替换评论区引用 ④新增权重分配逻辑 ⑤GAME_NAMES 新增 2 款游戏 |
| `scripts/keywords.txt` | UPDATE | 追加星穹铁道和金铲铲各 20 个 AI 生成的 SEO 关键词 |
| `scripts/auto_generate.ps1` | UPDATE | 调用方式从 `--limit 10` 改为使用权重配置 |
| `site/content/xingqiongtiedao/_index.md` | CREATE | 新游戏 Hugo 目录首页 |
| `site/content/jinchanchanzhizhan/_index.md` | CREATE | 新游戏 Hugo 目录首页 |
| `site/config.toml` | UPDATE | 导航菜单 + description + keywords 新增 2 款游戏 |
| `site/content/*/**.md` (约 50 篇存量) | UPDATE | 批量替换结尾段的评论区引用 |

## Tasks

### Task 1: 修复 prompt 模板中的评论区引用
- **Action**: 编辑 `scripts/templates/article_prompt.txt`
  - 第 17 行：`"有不懂的评论区问"这种自然结尾` → 改为 `"好了就这样"、"去试试吧"、"冲就完了"这种自然结尾`
  - 第 17 行是唯一需要改的，移除评论区指向
- **Validate**: grep 模板文件确认无"评论区"字样

### Task 2: 修复 generate.py 后处理中的评论区引用
- **Action**: 编辑 `scripts/generate.py`
  - `REPLACE_MAP` 中 `"如果你还有其他问题，欢迎在评论区留言。"` 条目 → 删除或改为指向非评论的替换
  - `AI_PATTERNS` 增加 `r"(评论区|留言区)"` 模式检测评论引用
  - 新增 `remove_comment_references(text)` 函数：用正则匹配结尾段的评论区引用（含"评论区问/见/聊/再问/留言"），替换为自然结尾如"去试试吧"、"就这样"
  - 在 `parse_article()` 的 `body = reduce_ai_flavor(body)` 之后增加 `body = remove_comment_references(body)` 调用
  - 区分正文叙事中的评论区引用（"评论区一片骂声"）→ 保留
- **Validate**: 生成 1 篇测试文章，grep 输出确认无评论区引用

### Task 3: 批量修复存量 50 篇文章
- **Action**: 编写一次性 Python 脚本或用 PowerShell 批量替换
  - 扫描 `site/content/` 下所有 `.md` 文件
  - 匹配结尾段（文章最后 10 行内）包含"评论区"的行
  - 替换为无评论指向的结尾
  - 正文中间的"评论区"（如"评论区一片骂声"）保留
  - 替换完成后对每个文件 `git add`
- **Validate**: `grep -r "评论区" site/content/` 只返回正文叙事中的合理用法

### Task 4: generate.py 支持按游戏权重分配
- **Action**: 编辑 `scripts/generate.py`
  - 新增 `GAME_WEIGHTS` 配置字典：
    ```python
    GAME_WEIGHTS = {
        "wangzhe": 2,
        "yuanshen": 1,
        "hepingjingying": 1,
        "lolm": 1,
        "danzaipaidui": 1,
        "xingqiongtiedao": 1,
        "jinchanchanzhizhan": 1,
    }
    ```
  - 修改 `main()` 逻辑：
    - 按游戏分组 pending 关键词
    - 对每款游戏取 min(weight, 剩余未生成数量) 个
    - 汇总后打乱顺序生成（避免同一游戏连续生成）
  - `--limit` 参数改为可选，默认按权重总和（8）
- **Validate**: `python generate.py --dry-run` 输出每款游戏各取了几篇

### Task 5: AI 生成新游戏关键词
- **Action**: 编辑 `scripts/keywords.txt`，追加 40 个关键词
  - 崩坏：星穹铁道 20 个（`xingqiongtiedao|关键词|意图`）
  - 金铲铲之战 20 个（`jinchanchanzhizhan|关键词|意图`）
  - 覆盖：长尾攻略词、版本热点词、百科资讯词、评测推荐词
- **Validate**: `python generate.py --dry-run` 显示新游戏关键词

### Task 6: 创建新游戏 Hugo 目录结构 + 更新站点配置
- **Action**:
  - 创建 `site/content/xingqiongtiedao/_index.md`（参照 `site/content/wangzhe/_index.md` 格式）
  - 创建 `site/content/jinchanchanzhizhan/_index.md`
  - 编辑 `site/config.toml`：
    - `GAME_NAMES`（在 generate.py 中）新增 2 个映射
    - `[[menu.main]]` 新增 2 个导航项，weight 60/70
    - 现有归档/搜索/关于的 weight 顺移（80/90/100）
    - `params.description` 和 `params.keywords` 加入新游戏
    - `params.homeInfoParams.Content` 加入新游戏
- **Validate**: `hugo -s site --minify` 构建成功

### Task 7: 补全现有 5 款游戏剩余关键词文章
- **Action**: 运行 `generate.py` 生成剩余约 50 篇文章
  - 5 款游戏各约 10 篇未生成（100 关键词 - 50 已生成 ≈ 50 待生成）
  - 生成后需检查输出文章是否含评论区引用（Task 2 的后处理应已生效）
  - 每篇生成后自动写入 `generated.json` 去重
- **Validate**: `python generate.py --dry-run` 显示待生成为 0 或接近 0

### Task 8: 生成新游戏首批文章
- **Action**: 为星穹铁道和金铲铲各生成首批 10 篇文章
  - `python generate.py --category xingqiongtiedao --limit 10 --push`
  - `python generate.py --category jinchanchanzhizhan --limit 10 --push`
  - 抽检 2-3 篇内容质量：确认无评论区引用、无编造游戏内容、SEO 关键词自然出现
- **Validate**: 两个新目录下各有 10 个 .md 文件，frontmatter 格式正确

### Task 9: 更新定时任务脚本
- **Action**: 编辑 `scripts/auto_generate.ps1`
  - 第 33 行：`--limit 10` → 改为不传 limit（由 generate.py 内部按权重计算，默认 8）
  - 日志输出增加每款游戏各生成了几篇的统计
- **Validate**: 手动执行 `auto_generate.ps1` 确认按权重发帖

## Implementation Order

```
Task 1 (prompt 模板) ──→ Task 2 (后处理脚本) ──→ Task 3 (存量修复)
                                                        │
Task 4 (权重分配) ←──────────────────────────────────────┘
        │
        ├──→ Task 5 (新游戏关键词)
        ├──→ Task 6 (Hugo 目录 + 站点配置)
        └──→ Task 9 (定时任务脚本)
                │
                ├──→ Task 7 (补全现有 50 篇)
                └──→ Task 8 (新游戏首批 20 篇)
```

Task 1-3 是评论区修复链，必须先完成再生成新文章。Task 4-6 并行。Task 7-8 在关键词和目录就绪后执行。Task 9 最后适配。

## Validation

```bash
# 1. 验证 prompt 模板无评论区引用
grep -i "评论区" "F:\SEOAI\scripts\templates\article_prompt.txt"

# 2. 验证 generate.py 后处理正常
python "F:\SEOAI\scripts\generate.py" --category wangzhe --limit 1 --dry-run

# 3. 验证权重分配
python "F:\SEOAI\scripts\generate.py" --dry-run

# 4. 验证存量文章无评论区引用（仅正文叙事中的合理用法）
grep -rn "评论区" "F:\SEOAI\site\content\" | grep -v "一片骂声\|炸锅"

# 5. 验证 Hugo 构建
hugo -s "F:\SEOAI\site" --minify

# 6. 验证新游戏关键词加载
python "F:\SEOAI\scripts\generate.py" --category xingqiongtiedao --dry-run
python "F:\SEOAI\scripts\generate.py" --category jinchanchanzhizhan --dry-run

# 7. 验证文章总量（目标 120+）
python -c "import json; d=json.load(open(r'F:\SEOAI\scripts\generated.json')); print(f'总文章数: {len(d)}')"
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| 存量替换误伤正文叙事中的合理评论区用语 | Medium | 仅替换文章最后 10 行内的评论区引用，中间的保留 |
| 新游戏关键词 SEO 效果未知 | Medium | 覆盖多种意图类型（攻略/百科/评测/资讯），后续根据搜索数据调整 |
| 权重分配逻辑与 --limit 参数冲突 | Low | 保持 --limit 作为硬上限，权重分配不超过 limit |
| AI 生成星铁/金铲铲内容可能编造不存在的游戏内容 | Medium | prompt 中已禁止编造，但新游戏信息需人工抽检首批文章 |

## Acceptance
- [ ] Task 1-3 完成：prompt 模板、generate.py 后处理、存量 50 篇文章均无评论区引用
- [ ] Task 4 完成：`--dry-run` 显示王者荣耀 2 篇、其余各 1 篇
- [ ] Task 5 完成：keywords.txt 新增 40 个关键词
- [ ] Task 6 完成：Hugo 构建成功，导航显示 7 款游戏
- [ ] Task 7 完成：现有 5 款游戏各 20 篇，共 100 篇
- [ ] Task 8 完成：新游戏各 10 篇，站点总计 120+ 篇
- [ ] Task 9 完成：auto_generate.ps1 使用权重分配

---
*Status: READY — 等待用户确认后开始实施*
