# 文档索引

本文档列出了 `docs/` 目录下的所有文档及其分类。

**最后更新：** 2026-01-10

---

## 文档分类说明

### 前缀含义

| 前缀 | 类型 | 说明 |
|------|------|------|
| `a` | Architecture | 总体架构文档 |
| `f` | Feature | 功能特性文档 |
| `g` | Guide | 指南文档 |
| `l` | Log | 日志/变更文档 |
| `p` | Phase | 阶段报告文档 |
| `t` | Todo | 任务清单 |

---

## 文档列表

### 总体架构（a-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `a1-LIVE2D_REFACTORING_PLAN.md` | Live2D 引入重构规划 | 项目现状分析、架构设计方案、实施计划 | 2026-01-07 |
| `a2-project_structure.md` | 项目文件结构说明 | 完整的项目文件结构和目录说明 | 2026-01-08 |

**阅读顺序：**
1. `a1-LIVE2D_REFACTORING_PLAN.md` - 了解重构规划
2. `a2-project_structure.md` - 了解项目结构

---

### 功能特性（f-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `f1-SCALE_FEATURE.md` | 缩放特性说明 | DPI 适配和缩放功能实现 | 2026-01-08 |
| `f2-DYNAMIC_SIZE_RENDERING.md` | 动态大小渲染功能 | Live2D 和静态图片的动态大小调整 | 2026-01-09 |
| `f3-LIVE2D_CUSTOM_SCALE_OFFSET.md` | Live2D 自定义缩放和偏移 | 自定义缩放比例和位置偏移功能 | 2026-01-10 |

**阅读顺序：**
1. `f1-SCALE_FEATURE.md` - 基础缩放功能
2. `f2-DYNAMIC_SIZE_RENDERING.md` - 动态大小调整
3. `f3-LIVE2D_CUSTOM_SCALE_OFFSET.md` - 自定义参数

---

### 指南文档（g-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `g1-MIGRATION_GUIDE.md` | 迁移指南 | 从旧版本升级到新版本 | 2026-01-08 |
| `g2-LIVE2D_TRACKING_FEATURE.md` | Live2D 跟踪功能 | 鼠标追踪和交互功能说明 | 2026-01-09 |

**阅读顺序：**
1. `g1-MIGRATION_GUIDE.md` - 版本迁移
2. `g2-LIVE2D_TRACKING_FEATURE.md` - 跟踪功能使用

---

### 日志/变更（l-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `l1-CHANGELOG.md` | 变更日志 | 版本历史和功能变更 | 2026-01-08 |
| `l2-UPDATE_SUMMARY.md` | 更新摘要 | 最近更新和重要变更 | 2026-01-08 |
| `l3-LIVE2D_CONFIG_FIX_SUMMARY.md` | Live2D 配置修复总结 | 配置加载问题修复记录 | 2026-01-10 |

**阅读顺序：**
1. `l3-LIVE2D_CONFIG_FIX_SUMMARY.md` - 最新修复
2. `l2-UPDATE_SUMMARY.md` - 近期更新
3. `l1-CHANGELOG.md` - 完整历史

---

### 阶段报告（p-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `p1-REFACTORING_COMPLETION_REPORT.md` | 重构完成报告 | 完成的工作、架构改进、后续计划 | 2026-01-08 |
| `p2-REFACTORING_SUMMARY.md` | 重构摘要 | 重构概览和主要变更 | 2026-01-08 |
| `p3-PET_REFACTORING_STAGE2_COMPLETION.md` | 阶段 2 完成报告 | 核心架构搭建完成 | 2026-01-09 |
| `p5-REFACTORING_TODOLIST.md` | 重构任务清单 | 详细的重构实施计划 | 2026-01-09 |

**阅读顺序：**
1. `p5-REFACTORING_TODOLIST.md` - 了解重构计划
2. `p3-PET_REFACTORING_STAGE2_COMPLETION.md` - 阶段 2 成果
3. `p1-REFACTORING_COMPLETION_REPORT.md` - 总体完成情况
4. `p2-REFACTORING_SUMMARY.md` - 快速摘要

---

### 任务清单（t-）

| 文件名 | 标题 | 描述 | 创建日期 |
|--------|------|------|----------|
| `t1-TODOLIST.md` | 总体任务清单 | 项目开发的所有待办事项 | 2026-01-08 |
| `t2-PET_REFACTORING_TODOLIST.md` | pet.py 解构重构任务清单 | 重构实施详细计划 | 2026-01-09 |

**阅读顺序：**
1. `t1-TODOLIST.md` - 总体任务
2. `t2-PET_REFACTORING_TODOLIST.md` - 重构任务

---

## 文档统计

| 分类 | 数量 |
|------|------|
| 总体架构（a-） | 2 |
| 功能特性（f-） | 3 |
| 指南文档（g-） | 2 |
| 日志/变更（l-） | 3 |
| 阶段报告（p-） | 4 |
| 任务清单（t-） | 2 |
| **总计** | **16** |

---

## 推荐阅读路径

### 新手入门
1. `a1-LIVE2D_REFACTORING_PLAN.md` - 了解项目架构
2. `a2-project_structure.md` - 了解项目结构
3. `g1-MIGRATION_GUIDE.md` - 学习迁移方法
4. `f1-SCALE_FEATURE.md` - 了解基础功能

### 开发者
1. `a1-LIVE2D_REFACTORING_PLAN.md` - 理解架构设计
2. `p5-REFACTORING_TODOLIST.md` - 查看重构计划
3. `t2-PET_REFACTORING_TODOLIST.md` - 跟踪开发进度
4. `a2-project_structure.md` - 查看代码结构

### 维护者
1. `p3-PET_REFACTORING_STAGE2_COMPLETION.md` - 了解最新进展
2. `l3-LIVE2D_CONFIG_FIX_SUMMARY.md` - 查看最近修复
3. `l1-CHANGELOG.md` - 查看完整历史
4. `p1-REFACTORING_COMPLETION_REPORT.md` - 查看总体情况

### 功能用户
1. `g1-MIGRATION_GUIDE.md` - 版本迁移
2. `f1-SCALE_FEATURE.md` - 缩放功能
3. `f2-DYNAMIC_SIZE_RENDERING.md` - 动态大小
4. `f3-LIVE2D_CUSTOM_SCALE_OFFSET.md` - 自定义参数
5. `g2-LIVE2D_TRACKING_FEATURE.md` - 跟踪功能

---

## 文档维护规范

### 添加新文档

1. 选择合适的类型前缀（a/f/g/l/p/t）
2. 查看同类型文档的最大序号
3. 新文档序号 = 最大序号 + 1
4. 文件名格式：`[前缀][序号]-[文档名称].md`

### 更新现有文档

1. 保持文件名不变（除非需要重新分类）
2. 在文档顶部更新"最后更新"日期
3. 在 `l1-CHANGELOG.md` 中记录重要变更

### 废弃文档

1. 将文档移动到 `docs/legacy/` 目录
2. 在 `t1-TODOLIST.md` 中记录废弃信息
3. 更新相关文档的引用

---

## 附录

### A. 命名规范

所有文档文件名遵循以下格式：

```
[类型前缀][序号]-[文档名称].md
```

**示例：**
- ✅ `a1-LIVE2D_REFACTORING_PLAN.md`
- ✅ `f2-DYNAMIC_SIZE_RENDERING.md`
- ✅ `g1-MIGRATION_GUIDE.md`
- ❌ `LIVE2D_CONFIG_FIX.md` (缺少前缀和序号)
- ❌ `config-fix-summary.md` (缺少前缀和序号)

### B. 联系方式

如有问题或建议，请联系：
- 项目地址：https://github.com/MaiM-with-u/MaiM-desktop-pet
- 问题反馈：https://github.com/MaiM-with-u/MaiM-desktop-pet/issues

---

**文档结束**

