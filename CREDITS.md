# CREDITS — 原作者与许可信息

## 原作者

**零雾〇五 Fogg05**
- B站: https://space.bilibili.com/350715147
- 原项目: [CozyUI+](https://github.com/Fogg05/CozyUI-Plus)
- 许可: GPL-3.0

本仓库（CinderUI）是 CozyUI+ 设计遗产的整理与结构化提取。
原作者于 2025 年不幸离世，我们将其 UI 设计从 PSD 中解构，
以便社区在 ModernUI 等现代渲染后端中重建。

## 字体许可

- **Fluent Emoji**: https://github.com/microsoft/fluentui-emoji
- **Noto Sans CJK**: https://github.com/notofonts/noto-cjk

## 矢量图提取

`005-无样式.svg` 是从 CozyUI+ PSD 导出的合并 SVG 文件，
包含所有 UI 元件的纯净矢量路径（无样式干扰，仅保留几何数据）。

### 提取工具

`tools/extract_components.py` — 基于行范围的 SVG 元件提取器，支持：

- 按行范围精确提取每个 UI 元件
- 自动包围盒（bbox）裁剪
- 边缘发光效果（clipPath + 渐变 overlay）
- 纹理 Pattern href 链解析
- 子元件拆分 + Composite 复合图
- 位图资源自动拷贝

### 已提取的元件（14 个）

| 元件 | 提取模式 | 说明 |
|------|---------|------|
| 按钮（×4 尺寸） | sub_components | 禁用/常态/选中 三态，含边缘发光 |
| 滑块 | sub_components | 滑块本体/导轨 + 三态，含边缘发光 |
| 勾选框 | sub_components | 框底部/框本体/绿色/选中/红色×/绿色√ |
| 文本框 | sub_components | 框本体、框本体（选中） |
| 药水效果 | sub_components | 本体、本体（选中） |
| 小地图 A/B | sub_components | 两种变体 |
| 界面模板 | simple | 通用界面模板，含纹理基 pattern |
| 界面模板 通用背包 | simple | 通用背包外框，含界面边缘发光 |
| 物品栏 | sub_components | 物品栏/副手/选中 |
| 背包 | sub_components | 界面/外框/装备栏/合成台，含界面边缘发光 |

### 技术细节

- **`_1` 层识别**：通过 `data-name` 以" 1"结尾或 `id` 含 `_1-`/`_1_` 模式检测
- **纹理基 Pattern**：`界面模板_2_2物品槽_外框_纹理_基` 硬编码注入 4 个内联渐变
- **边缘发光**：clipPath 约束 + 水平渐变 overlay，左右各 8px
- **层识别策略**：子 `<g>` 中含 `_1` 模式的直接保留为层，否则向下展平

## 维护者

- dalizi2333 — 仓库创建与维护

---

*In memory of Fogg05, whose warmth lives on in pixels.*