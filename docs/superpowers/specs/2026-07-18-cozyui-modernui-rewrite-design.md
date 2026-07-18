# CozyUI ModernUI 重写 — 设计规格

> 状态：已确认  
> 日期：2026-07-18  
> 目标：将 CinderUI 的 Batik GVT 渲染替换为 ModernUI 原生 Canvas/View 渲染

## 1. 范围

将 CinderUI 的四种 UI 模板（Button、Frame、Slider、Scrollbar）完全重构为 ModernUI 原生组件（自定义 View 子类），在 `onDraw(Canvas)` 中直接使用 ModernUI Canvas/Paint API 绘制。

**不包含：**
- `extracted/` SVG 组件的直接加载（留存未来用）
- Batik 渲染器的任何依赖
- 现有 `:color` 模块（颜色方案改为 JSON 资源）
- Minecraft 游戏逻辑集成（仅 UI 渲染层）

## 2. 架构

```
cozyui-modernui/                    ← 根目录新建独立 Gradle 项目
├── build.gradle                    ← ModernUI-NeoForge + core 依赖
├── src/main/java/com/goblincoders/cozyui/
│   ├── CozyUI.java                 ← @Mod 主类
│   ├── color/
│   │   └── ColorScheme.java        ← 运行时颜色方案对象
│   ├── canvas/
│   │   ├── SquirclePath.java       ← squircle Path 构建（纯几何）
│   │   └── CozyCanvasRenderer.java ← Canvas 绘制调用层
│   ├── widget/
│   │   ├── CozyButton.java         ← Button（L0+L1+L2 三层 squircle）
│   │   ├── CozyFrame.java          ← Frame（L0+L2 两层 squircle）
│   │   ├── CozySlider.java         ← Slider（标准圆角矩形 + L1+L2）
│   │   └── CozyScrollbar.java      ← Scrollbar（胶囊形外环+内填充）
│   └── fragment/
│       └── CozyFragment.java       ← Fragment + ScreenCallback 基类
└── src/main/resources/
    └── assets/cozyui/
        └── colors.json             ← 9 种颜色方案 JSON
```

## 3. 组件层级

```
CozyFragment (Fragment + ScreenCallback)
  └── 任意 ViewGroup
       ├── CozyButton extends View
       │    └── onDraw(Canvas) → CozyCanvasRenderer.drawButton(canvas, bounds, colors)
       ├── CozyFrame extends View
       │    └── onDraw(Canvas) → CozyCanvasRenderer.drawFrame(canvas, bounds, colors)
       ├── CozySlider extends View
       │    └── onDraw(Canvas) → CozyCanvasRenderer.drawSlider(canvas, bounds, colors)
       └── CozyScrollbar extends View
            └── onDraw(Canvas) → CozyCanvasRenderer.drawScrollbar(canvas, bounds, colors)
```

## 4. 模块规格

### 4.1 SquirclePath — 几何工具

纯几何计算，零外部依赖。将现有 Batik 的 `Path2D.Float` 翻译为 ModernUI 的 `icyllis.modernui.graphics.Path`。

**方法：**
- `static Path squircle(float x, float y, float w, float h, float r)` — squircle 封闭路径，使用 cubic bezier 控制点 `crv=22.12*s, off=5.88*s`（s = r/28）
- `static Path squircleRing(float x, float y, float w, float h, float outerR, float ringW)` — 通过 `Path.op(DIFFERENCE)` 或手动构建环路径
- `static Path l1ExactClip(float left, float right, float top, float bottom)` — L1 装饰带精确 clip（r=24 固定圆角贝塞尔值）
- `static Path l1Clip(float left, float right, float top, float bottom, float r)` — L1 通用 clip（可缩放圆角）

### 4.2 CozyCanvasRenderer — 渲染层

无状态静态方法，接收 Canvas + bounds + ColorScheme，按层绘制。

**CozyButton 绘制顺序（z-index 从低到高）：**
1. L0 外框 — `squircle(0, 0, w, h, R=28)` + 纯色填充
2. L1 装饰带 — 底部 40px 高，`l1ExactClip` 路径 + 纯色填充
3. L1 左右边缘发光 — `clipRect` 与 L1 path 取交集 + 水平渐变（edge→fill）
4. L2 外环 — `squircleRing(O=4, w-8, h-16, RING_R=24, RING_W=4)` + 垂直渐变
5. L2 内填充 — `squircle(O+RING_W=8, w-16, h-24, innerR=20)` + 垂直渐变

**CozyFrame 绘制顺序：**
1. L0 外框 — 同 Button（颜色可能透明）
2. L2 外环 — 底部偏移 4px（vs Button 的 12px）
3. L2 内填充 — 底部偏移 8px（vs Button 的 16px）
4. 无 L1 层

**CozySlider 绘制顺序：**
1. L0 外框 — 标准圆角矩形 `roundRect(r=14)`
2. L1 装饰带 — 同 Button，但底部圆角匹配 r=14
3. L2 外环 — squircleRing（RING_R=10, RING_W=4）
4. L2 内填充 — squircle（innerR=6）

**CozyScrollbar 绘制顺序：**
1. 外环 — 胶囊形 24×h 半圆端（通过 Path cubicTo 构建）
2. 内填充 — 胶囊形 16×(h-8) 半圆端

**使用的 ModernUI API：**
- `Canvas.drawPath(Path, Paint)` — 路径填充
- `Paint.setShader(LinearGradient)` — 垂直/水平渐变
- `Paint.setColor(int)` — 纯色
- `Canvas.save()/clipPath()/restore()` — L1 边缘发光裁剪

### 4.3 Widget 层 — 自定义 View

每个 Widget 继承 `icyllis.modernui.view.View`。

**公共 API 模式（以 CozyButton 为例）：**
```java
public class CozyButton extends View {
    private ColorScheme colors;
    private float designW, designH;  // 设计尺寸（用于比例计算）

    public void setColorScheme(ColorScheme c) { this.colors = c; invalidate(); }
    public ColorScheme getColorScheme() { return colors; }

    @Override
    protected void onDraw(Canvas canvas) {
        // 缩放 canvas 使设计尺寸适配实际 bounds
        float sx = getWidth() / designW;
        float sy = getHeight() / designH;
        canvas.save();
        canvas.scale(sx, sy);
        CozyCanvasRenderer.drawButton(canvas, 0, 0, designW, designH, colors);
        canvas.restore();
    }
}
```

**状态管理：** 使用 ModernUI 的 `drawableState` 机制。当 `ENABLED/SELECTED/PRESSED` 状态变化时，在 `drawableStateChanged()` 中切换 ColorScheme：
- NORMAL (enabled, not selected)
- SELECTED (enabled, selected)
- DISABLED (not enabled)

### 4.4 ColorScheme — 颜色方案

从现有 `ButtonColorScheme` 翻译为 ModernUI 版本，保留 7 字段结构：

```java
public class ColorScheme {
    public final int l0Fill, l1Fill, l1Edge, bgTop, bgBot, fgTop, fgBot;

    // 9 种预设
    public static final ColorScheme NORMAL = new ColorScheme(...);
    public static final ColorScheme SELECTED = new ColorScheme(...);
    public static final ColorScheme DISABLED = new ColorScheme(...);
    public static final ColorScheme PANEL = new ColorScheme(...);
    public static final ColorScheme SLIDER_TRACK = new ColorScheme(...);
    public static final ColorScheme TEXT_BOX = new ColorScheme(...);
    public static final ColorScheme TEXT_BOX_SELECTED = new ColorScheme(...);
    public static final ColorScheme SCROLLBAR_TRACK = new ColorScheme(...);
    public static final ColorScheme SCROLLBAR_HANDLE = new ColorScheme(...);
}
```

颜色值使用 `0xAARRGGBB` 格式（与现有一致，也兼容 ModernUI 的 `setColor`）。

同时提供 `colors.json` 资源文件，在模组初始化时加载，允许资源包覆盖颜色。

### 4.5 CozyFragment — 基类

```java
public abstract class CozyFragment extends Fragment implements ScreenCallback {
    @Override public boolean hasDefaultBackground() { return false; }
    @Override public boolean shouldClose() { return true; }
    @Override public boolean isPauseScreen() { return false; }
}
```

子类只需实现 `onCreateView()` 构建 View 树。

## 5. 依赖

```groovy
dependencies {
    compileOnly "dev.icyllis:modernui-core:${modernui_core_version}"
    localRuntime "dev.icyllis:modernui-core:${modernui_core_version}"
    implementation "icyllis.modernui:ModernUI-NeoForge:${modernui_mc_version}"
    additionalRuntimeClasspath "dev.icyllis:modernui-core:${modernui_core_version}"
}
```

- Java 17
- Gradle 8.10+
- Minecraft 1.21.1 NeoForge
- ModernUI 3.13.0
- 不依赖 CinderUI 的任何模块

## 6. 文件清单

| 文件 | 职责 | 预计行数 |
|------|------|---------|
| `build.gradle` | Gradle 配置 | ~50 |
| `CozyUI.java` | @Mod 主类 | ~30 |
| `ColorScheme.java` | 颜色方案 + 9 预设 | ~90 |
| `SquirclePath.java` | squircle Path 构建 | ~120 |
| `CozyCanvasRenderer.java` | Canvas 绘制调度 | ~200 |
| `CozyButton.java` | Button Widget | ~80 |
| `CozyFrame.java` | Frame Widget | ~60 |
| `CozySlider.java` | Slider Widget | ~80 |
| `CozyScrollbar.java` | Scrollbar Widget | ~60 |
| `CozyFragment.java` | Fragment 基类 | ~30 |
| `colors.json` | 颜色方案 JSON | ~100 |
| `mods.toml` | NeoForge 模组元数据 | ~20 |

## 7. 技术风险与对策

| 风险 | 对策 |
|------|------|
| ModernUI Path API 无 `Area.subtract`（用于 squircleRing） | 使用 `Path.op(Path, Path, Path.Op.DIFFERENCE)` 或手动构建环的 4 个子路径 |
| Squircle 缩放时 L1 装饰带圆角失真 | L1 使用精确 clip（固定 r=24 bezier），不做几何缩放；仅 L0/L2 整体缩放 |
| Canvas 渐变坐标需要在缩放前计算 | `save/scale` 后渐变坐标在缩放坐标系中定义，保持与设计尺寸一致 |
| Custom View 的触摸事件需手动处理 | `CozyButton` 覆写 `onTouchEvent` 触发 pressed 状态切换；其他组件暂不需要 |
