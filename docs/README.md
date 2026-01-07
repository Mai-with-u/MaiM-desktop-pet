# 文档目录说明

本文档说明 `docs/` 目录下文件的命名规范和组织结构。

---

## 命名规范

所有文档文件名遵循以下格式：

```
[类型前缀][序号]-[文档名称].md
```

### 类型前缀说明

| 前缀 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `a` | Architecture | 总体架构文档 | `a1-LIVE2D_REFACTORING_PLAN.md` |
| `p` | Phase | 阶段报告文档 | `p1-REFACTORING_COMPLETION_REPORT.md` |
| `g` | Guide | 指南文档 | `g1-MIGRATION_GUIDE.md` |
| `f` | Feature | 功能特性文档 | `f1-SCALE_FEATURE.md` |
| `l` | Log | 日志/变更文档 | `l1-CHANGELOG.md` |
| `t` | Todo | 任务清单 | `t1-TODOLIST.md` |

### 序号说明

序号表示同一类型文档的阅读顺序或时间顺序，使用数字表示（1, 2, 3...）。

---

## 当前文档列表

### 总体架构（a-）
- **a1-LIVE2D_REFACTORING_PLAN.md** - Live2D 引入重构规划文档
  - 项目现状分析
  - 架构设计方案
  - 实施计划
  - 风险管理

### 阶段报告（p-）
- **p1-REFACTORING_COMPLETION_REPORT.md** - 重构完成报告
  - 完成的工作
  - 架构改进
  - 功能验证
  - 后续计划

- **p2-REFACTORING_SUMMARY.md** - 重构摘要
  - 重构概览
  - 主要变更

### 指南文档（g-）
- **g1-MIGRATION_GUIDE.md** - 迁移指南
  - 从旧版本迁移
  - 常见问题解决
  - 配置说明

### 功能特性（f-）
- **f1-SCALE_FEATURE.md** - 缩放特性说明
  - DPI 适配
  - 缩放功能实现

### 日志/变更（l-）
- **l1-CHANGELOG.md** - 变更日志
  - 版本历史
  - 功能变更
  - Bug 修复

- **l2-UPDATE_SUMMARY.md** - 更新摘要
  - 最近更新
  - 重要变更

### 任务清单（t-）
- **t1-TODOLIST.md** - 任务清单
  - 待办事项
  - 进度跟踪

---

## 文档阅读顺序

### 新手入门
1. `a1-LIVE2D_REFACTORING_PLAN.md` - 了解项目架构和重构规划
2. `g1-MIGRATION_GUIDE.md` - 学习如何使用和迁移
3. `f1-SCALE_FEATURE.md` - 了解核心功能特性

### 开发者参考
1. `a1-LIVE2D_REFACTORING_PLAN.md` - 理解架构设计
2. `p1-REFACTORING_COMPLETION_REPORT.md` - 查看重构成果
3. `t1-TODOLIST.md` - 跟踪开发进度

### 维护者参考
1. `p1-REFACTORING_COMPLETION_REPORT.md` - 了解当前状态
2. `l1-CHANGELOG.md` - 查看历史变更
3. `l2-UPDATE_SUMMARY.md` - 查看最近更新

---

## 添加新文档

### 选择类型前缀

根据文档内容选择合适的前缀：

- **架构设计文档** → 使用 `a-`
- **阶段完成报告** → 使用 `p-`
- **使用指南/教程** → 使用 `g-`
- **功能特性说明** → 使用 `f-`
- **变更日志/更新记录** → 使用 `l-`
- **任务清单/计划** → 使用 `t-`

### 确定序号

1. 查看同类型文档的最大序号
2. 新文档序号 = 最大序号 + 1

例如：
- 已有 `p1-REFACTORING_COMPLETION_REPORT.md` 和 `p2-REFACTORING_SUMMARY.md`
- 新的阶段性报告应命名为 `p3-XXX.md`

### 命名示例

```
✅ 正确命名：
- a2-ARCHITECTURE_OVERVIEW.md
- p3-PHASE4_REPORT.md
- g2-DEVELOPMENT_GUIDE.md
- f2-CUSTOM_THEME.md
- l3-RELEASE_NOTES_v2.0.md

❌ 错误命名：
- ARCHITECTURE_OVERVIEW.md (缺少前缀和序号)
- a-LIVE2D_PLAN.md (缺少序号)
- p-REPORT.md (缺少序号)
- ARCHITECTURE-a1-LIVE2D_PLAN.md (前缀位置错误)
```

---

## 文档维护规范

### 更新现有文档

1. 保持文件名不变（除非需要重新分类）
2. 在文档顶部更新"最后更新"日期
3. 在变更日志（l1-CHANGELOG.md）中记录重要变更

### 废弃文档

1. 将文档移动到 `docs/legacy/` 目录
2. 在 `t1-TODOLIST.md` 中记录废弃信息
3. 更新相关文档的引用

### 文档引用

在文档中引用其他文档时，使用相对路径：

```markdown
详见 [重构规划文档](./a1-LIVE2D_REFACTORING_PLAN.md) 的第三部分
```

---

## 目录结构

```
docs/
├── README.md                          # 本文件
├── a1-LIVE2D_REFACTORING_PLAN.md      # 架构规划
├── p1-REFACTORING_COMPLETION_REPORT.md # 完成报告
├── p2-REFACTORING_SUMMARY.md          # 重构摘要
├── g1-MIGRATION_GUIDE.md              # 迁移指南
├── f1-SCALE_FEATURE.md                # 缩放特性
├── l1-CHANGELOG.md                    # 变更日志
├── l2-UPDATE_SUMMARY.md               # 更新摘要
├── t1-TODOLIST.md                     # 任务清单
└── legacy/                            # 废弃文档目录
    └── ...
```

---

## 注意事项

1. **文件名统一使用大写字母**（LIVE2D, REFACTORING 等）
2. **序号使用数字**，不要用字母（如用 1 而不是 one）
3. **分隔符使用连字符** `-`，不要使用下划线 `_`
4. **文件扩展名统一为 `.md`**
5. **中英文混用时，建议使用英文命名**，在文档内容中使用中文说明

---

## 版本历史

- **2026-01-08** - 初始版本，建立文档命名规范

---

如有疑问或建议，请更新本文档或联系项目负责人。
