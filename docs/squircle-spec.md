# CinderUI — 渲染参数规格

> ModernUI/LDLib2 矢量渲染后端的 Squircle 圆角参数规范  
> 数据来源：CozyUI-Plus (005.psd) — 全自动提取，无需人工干预

## 快速入门

```bash
# 只需一条命令
python tools/extract.py

# 输出目录：
extracted/svg/           # 118 个独立 SVG（含颜色/渐变）
extracted/json/          # 结构化元数据
extracted/composites/    # 35 个复合组件（按钮/滑块/进度条等）
extracted/parameters.json # 转角参数 + 复合索引
```

## 复合组件结构

每个 UI 元素是**多层叠加**的复合组件，按 z-index 从低到高：

| 层 | 内容 | 填充方式 | 示例（按钮常态） |
|----|------|---------|----------------|
| z=0 | 背景 | 实色 rgb(0,0,0) | 圆角矩形背景 |
| z=1 | 中层 | 实色 + 内阴影 | 凹陷效果图层 |
| z=2 | 顶层 | 线性渐变 top→bottom | 高光渐变 |

各层有独立的 viewport 尺寸和路径（因内外阴影有扩散效果）。

## Squircle 转角参数

所有 8 节点圆角矩形的节点排列：

```
Knot[0] 左边缘(下) — Knot[1] 左边缘(上)
Knot[2] 上边缘(左) — Knot[3] 上边缘(右)
Knot[4] 右边缘(上) — Knot[5] 右边缘(下)
Knot[6] 下边缘(右) — Knot[7] 下边缘(左)
```

- **t** = `corner_radius / min(w, h)`，范围 (0, 0.5]
- **c** = 转角曲线起始位置比例
- 直线段用 `L`，曲线段用 `C`

## 颜色提取

从 PSD 的 tagged_blocks 自动提取：
- `vscg` → 矢量填充颜色
- `lfx2` → 图层效果(渐变/内阴影/颜色叠加)
- `vstk` → 描边颜色

注意：PSD 存储的颜色值未经颜色管理处理，与 PS 导出 SVG 可能有细微差异。

## 输出结构

```
extracted/
  svg/                              # 独立 SVG（可直接浏览器渲染）
    按钮_18x--按钮常态--按钮常态_0.svg
    按钮_18x--按钮常态--按钮常态_1.svg
    按钮_18x--按钮常态--按钮常态_2.svg
    ...
  json/                             # 结构化元数据
  composites/
    按钮_18x--按钮常态/
      composite.json                # 三层叠加信息
    按钮_18x--按钮选中/
      composite.json
    ...
  parameters.json                   # 统一索引
```

## 验证

转角参数验证脚本：

```bash
python tools/verify_params.py
```
