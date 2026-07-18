# CozyUI ModernUI 重写 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 CinderUI 的四种 UI 模板（Button、Frame、Slider、Scrollbar）从 Apache Batik GVT 重写为 ModernUI 原生自定义 View，使用 Canvas/Path/Paint API 直接绘制。

**Architecture:** 独立 Gradle 项目 `cozyui-modernui/`，包含纯几何工具类 SquirclePath、渲染层 CozyCanvasRenderer、四个自定义 View（CozyButton/CozyFrame/CozySlider/CozyScrollbar）、颜色方案 ColorScheme、以及 CozyFragment 基类。所有组件继承 ModernUI View，在 onDraw(Canvas) 中调用渲染器。

**Tech Stack:** Java 17, Gradle 8.10+, ModernUI 3.13.0 core + NeoForge, Minecraft 1.21.1 NeoForge

## Global Constraints

- Java 17 源码级别
- 使用 `icyllis.modernui.graphics.Path`（兼容 android.graphics.Path API）
- 使用 `icyllis.modernui.graphics.Canvas`（兼容 android.graphics.Canvas API）
- 颜色格式 `0xAARRGGBB`
- 所有 View 继承 `icyllis.modernui.view.View`
- Fragment 继承 `icyllis.modernui.fragment.Fragment` 实现 `ScreenCallback`
- 不依赖 CinderUI 现有任何模块（:color, :batik）
- 组名 `com.goblincoders.cozyui`
- 模组 ID `cozyui`

## File Structure

```
cozyui-modernui/
├── build.gradle
├── src/main/java/com/goblincoders/cozyui/
│   ├── CozyUI.java
│   ├── color/
│   │   └── ColorScheme.java
│   ├── canvas/
│   │   ├── SquirclePath.java
│   │   └── CozyCanvasRenderer.java
│   ├── widget/
│   │   ├── CozyButton.java
│   │   ├── CozyFrame.java
│   │   ├── CozySlider.java
│   │   └── CozyScrollbar.java
│   └── fragment/
│       └── CozyFragment.java
└── src/main/resources/
    ├── META-INF/
    │   └── neoforge.mods.toml
    └── assets/cozyui/
        └── colors.json
```

---

### Task 1: 项目脚手架 — Gradle 配置 + 模组主类

**Files:**
- Create: `cozyui-modernui/build.gradle`
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/CozyUI.java`
- Create: `cozyui-modernui/src/main/resources/META-INF/neoforge.mods.toml`

**Interfaces:**
- Produces: 可编译的空模组项目，`CozyUI` 类上有 `@Mod("cozyui")` 注解

- [ ] **Step 1: 创建 build.gradle**

创建 `cozyui-modernui/build.gradle`：

```groovy
plugins {
    id 'java-library'
    id 'net.neoforged.moddev' version '2.0.78'
}

java {
    toolchain.languageVersion = JavaLanguageVersion.of(17)
    withSourcesJar()
}

group = 'com.goblincoders'
version = '1.0.0'

repositories {
    mavenCentral()
    maven { url = 'https://maven.neoforged.net/releases' }
}

configurations {
    runtimeClasspath.extendsFrom localRuntime
    all {
        resolutionStrategy {
            force "com.ibm.icu:icu4j:76.1"
            force "it.unimi.dsi:fastutil:8.5.15"
        }
    }
}

dependencies {
    compileOnly "dev.icyllis:modernui-core:3.13.0"
    localRuntime "dev.icyllis:modernui-core:3.13.0"
    implementation "icyllis.modernui:ModernUI-NeoForge:1.21.1-3.13.0.1"
    additionalRuntimeClasspath "dev.icyllis:modernui-core:3.13.0"
}

neoForge {
    version = '21.1.98'
}
```

- [ ] **Step 2: 创建模组主类 CozyUI.java**

创建 `cozyui-modernui/src/main/java/com/goblincoders/cozyui/CozyUI.java`：

```java
package com.goblincoders.cozyui;

import net.neoforged.fml.common.Mod;

@Mod("cozyui")
public class CozyUI {
    public CozyUI() {
    }
}
```

- [ ] **Step 3: 创建 mods.toml**

创建 `cozyui-modernui/src/main/resources/META-INF/neoforge.mods.toml`：

```toml
modLoader = "javafml"
loaderVersion = "[4,)"

[[mods]]
modId = "cozyui"
version = "1.0.0"
displayName = "CozyUI"
description = "CozyUI visual style as ModernUI native widgets"
authors = ["Alma"]

[[dependencies.cozyui]]
    modId = "modernui"
    type = "required"
    versionRange = "[3.13.0.0,)"
    ordering = "AFTER"
    side = "CLIENT"

[[dependencies.cozyui]]
    modId = "neoforge"
    type = "required"
    versionRange = "[21.1,)"
    ordering = "NONE"
    side = "BOTH"
```

- [ ] **Step 4: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL（编译通过，无测试）

- [ ] **Step 5: 提交**

```bash
git add cozyui-modernui/
git commit -m "feat: add project scaffold with Gradle config and mod entry point"
```

---

### Task 2: ColorScheme — 颜色方案类 + JSON 资源

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/color/ColorScheme.java`
- Create: `cozyui-modernui/src/main/resources/assets/cozyui/colors.json`

**Interfaces:**
- Produces: `ColorScheme` 类，7 个 int 字段 (`l0Fill, l1Fill, l1Edge, bgTop, bgBot, fgTop, fgBot`)，9 个预设常量，`toArray()` 方法

- [ ] **Step 1: 创建 ColorScheme.java**

创建 `ColorScheme.java`：

```java
package com.goblincoders.cozyui.color;

public class ColorScheme {
    /** L0 外框填充色。alpha=0 不渲染。 */
    public final int l0Fill;
    /** L1 装饰带填充色。alpha=0 不渲染。 */
    public final int l1Fill;
    /** L1 边缘发光色。alpha=0 不渲染。 */
    public final int l1Edge;
    /** L2 内填充渐变上端 */
    public final int bgTop;
    /** L2 内填充渐变下端 */
    public final int bgBot;
    /** L2 描边环渐变上端 */
    public final int fgTop;
    /** L2 描边环渐变下端 */
    public final int fgBot;

    public ColorScheme(int l0Fill, int l1Fill, int l1Edge,
                       int bgTop, int bgBot, int fgTop, int fgBot) {
        this.l0Fill = l0Fill;
        this.l1Fill = l1Fill;
        this.l1Edge = l1Edge;
        this.bgTop = bgTop;
        this.bgBot = bgBot;
        this.fgTop = fgTop;
        this.fgBot = fgBot;
    }

    public ColorScheme(int[] cs) {
        this(cs[0], cs[1], cs[2], cs[3], cs[4], cs[5], cs[6]);
    }

    public int[] toArray() {
        return new int[]{l0Fill, l1Fill, l1Edge, bgTop, bgBot, fgTop, fgBot};
    }

    /** alpha 是否为 0 — 表示该层不渲染 */
    public static boolean isTransparent(int argb) {
        return (argb >>> 24) == 0;
    }

    // ── 按钮预设 ──

    public static final ColorScheme NORMAL = new ColorScheme(
            0xff000000, 0xff5c5958, 0xff4c4948,
            0xff7b7877, 0xff83807f, 0xffc3c0bf, 0xffa3a09f);

    public static final ColorScheme SELECTED = new ColorScheme(
            0xffffffff, 0xff5d53a4, 0xff4b4384,
            0xff786fcf, 0xff7a7cdb, 0xffbac7ff, 0xffa1a9e8);

    public static final ColorScheme DISABLED = new ColorScheme(
            0xff000000, 0xff343130, 0xff2c2928,
            0xff343130, 0xff2c2928, 0xff444140, 0xff646160);

    /** 面板/背景板 */
    public static final ColorScheme PANEL = new ColorScheme(
            0xff000000, 0xff7f8083, 0xff636467,
            0xffbbbcbf, 0xffbbbcbf, 0xfffbfcff, 0xffd7d8db);

    // ── 框类预设（无 L1 层）──

    /** 滑块导轨 */
    public static final ColorScheme SLIDER_TRACK = new ColorScheme(
            0xff000000, 0x00000000, 0x00000000,
            0xff2c2928, 0xff343130, 0xff444140, 0xff646160);

    /** 文本框 */
    public static final ColorScheme TEXT_BOX = new ColorScheme(
            0x00000000, 0x00000000, 0x00000000,
            0xff201d1c, 0xff343130, 0xff83807f, 0xff6f6c6b);

    /** 文本框（选中） */
    public static final ColorScheme TEXT_BOX_SELECTED = new ColorScheme(
            0x00000000, 0x00000000, 0x00000000,
            0xff201d1c, 0xff343130, 0xffc3c0bf, 0xffa3a09f);

    // ── 滚动条预设（无 L1 层，纯色）──

    /** 滚动条导轨 */
    public static final ColorScheme SCROLLBAR_TRACK = new ColorScheme(
            0x00000000, 0x00000000, 0x00000000,
            0xff2c2928, 0xff2c2928, 0xff444140, 0xff444140);

    /** 滚动条手柄 */
    public static final ColorScheme SCROLLBAR_HANDLE = new ColorScheme(
            0x00000000, 0x00000000, 0x00000000,
            0xff83807f, 0xff83807f, 0xffc3c0bf, 0xffc3c0bf);
}
```

- [ ] **Step 2: 创建 colors.json 资源文件**

创建 `cozyui-modernui/src/main/resources/assets/cozyui/colors.json`：

```json
{
  "normal": {
    "l0Fill": "ff000000", "l1Fill": "ff5c5958", "l1Edge": "ff4c4948",
    "bgTop": "ff7b7877", "bgBot": "ff83807f", "fgTop": "ffc3c0bf", "fgBot": "ffa3a09f"
  },
  "selected": {
    "l0Fill": "ffffffff", "l1Fill": "ff5d53a4", "l1Edge": "ff4b4384",
    "bgTop": "ff786fcf", "bgBot": "ff7a7cdb", "fgTop": "ffbac7ff", "fgBot": "ffa1a9e8"
  },
  "disabled": {
    "l0Fill": "ff000000", "l1Fill": "ff343130", "l1Edge": "ff2c2928",
    "bgTop": "ff343130", "bgBot": "ff2c2928", "fgTop": "ff444140", "fgBot": "ff646160"
  },
  "panel": {
    "l0Fill": "ff000000", "l1Fill": "ff7f8083", "l1Edge": "ff636467",
    "bgTop": "ffbbbcbf", "bgBot": "ffbbbcbf", "fgTop": "fffbfcff", "fgBot": "ffd7d8db"
  },
  "slider_track": {
    "l0Fill": "ff000000", "l1Fill": "00000000", "l1Edge": "00000000",
    "bgTop": "ff2c2928", "bgBot": "ff343130", "fgTop": "ff444140", "fgBot": "ff646160"
  },
  "text_box": {
    "l0Fill": "00000000", "l1Fill": "00000000", "l1Edge": "00000000",
    "bgTop": "ff201d1c", "bgBot": "ff343130", "fgTop": "ff83807f", "fgBot": "ff6f6c6b"
  },
  "text_box_selected": {
    "l0Fill": "00000000", "l1Fill": "00000000", "l1Edge": "00000000",
    "bgTop": "ff201d1c", "bgBot": "ff343130", "fgTop": "ffc3c0bf", "fgBot": "ffa3a09f"
  },
  "scrollbar_track": {
    "l0Fill": "00000000", "l1Fill": "00000000", "l1Edge": "00000000",
    "bgTop": "ff2c2928", "bgBot": "ff2c2928", "fgTop": "ff444140", "fgBot": "ff444140"
  },
  "scrollbar_handle": {
    "l0Fill": "00000000", "l1Fill": "00000000", "l1Edge": "00000000",
    "bgTop": "ff83807f", "bgBot": "ff83807f", "fgTop": "ffc3c0bf", "fgBot": "ffc3c0bf"
  }
}
```

- [ ] **Step 3: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 4: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/color/ColorScheme.java
git add cozyui-modernui/src/main/resources/assets/cozyui/colors.json
git commit -m "feat: add ColorScheme with 9 presets and JSON resource"
```

---

### Task 3: SquirclePath — 纯几何路径构建

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/SquirclePath.java`

**Interfaces:**
- Consumes: 无（纯几何，零依赖）
- Produces:
  - `static Path squircle(float x, float y, float w, float h, float r)` — 返回 squircle 封闭路径
  - `static Path squircleRing(float x, float y, float w, float h, float outerR, float ringW)` — 返回 squircle 环路径
  - `static Path l1ExactClip(float left, float right, float top, float bottom)` — 返回 Button 的 L1 精确 clip（r=24）
  - `static Path l1Clip(float left, float right, float top, float bottom, float r)` — 返回 Slider 的 L1 clip（可缩放 r）
  - `static Path capsuleRing(float h)` — 返回 Scrollbar 外环（24×h 胶囊形）
  - `static Path capsuleFill(float h)` — 返回 Scrollbar 内填充（16×(h-8) 胶囊形）

- [ ] **Step 1: 创建 SquirclePath.java — 第一部分（squircle 基础）**

创建文件 `SquirclePath.java`，先写 squircle 基础方法和 roundRect：

```java
package com.goblincoders.cozyui.canvas;

import icyllis.modernui.graphics.Path;

/**
 * 纯几何路径构建 — 将 Batik 的 Path2D.Float 翻译为 ModernUI 的 {@link Path}。
 * Squircle 定义：r=28 时 cubic bezier 控制点 crv=22.12, off=5.88（从 PSD 提取）。
 */
public final class SquirclePath {

    private SquirclePath() {}

    /**
     * Squircle（超椭圆圆角矩形）封闭路径。
     * r=28 时使用精确 bezier 控制点：crv=22.12, off=5.88。
     * 其他 r 值按比例 scale = r/28f 缩放控制点。
     */
    public static Path squircle(float x, float y, float w, float h, float r) {
        float scale = r / 28f;
        float crv = 22.12f * scale;
        float off = 5.88f * scale;

        Path p = new Path();
        p.moveTo(x + w - r, y);
        p.lineTo(x + r, y);
        p.cubicTo(x + r - crv, y,         x,      y + off,  x,       y + r);
        p.lineTo(x, y + h - r);
        p.cubicTo(x, y + h - r + crv,     x + off, y + h,    x + r,   y + h);
        p.lineTo(x + w - r, y + h);
        p.cubicTo(x + w - r + crv, y + h, x + w,   y + h - off, x + w, y + h - r);
        p.lineTo(x + w, y + r);
        p.cubicTo(x + w, y + r - crv,     x + w - off, y,    x + w - r, y);
        p.close();
        return p;
    }

    /**
     * 标准圆角矩形（rx=ry=r）。
     */
    public static Path roundRect(float x, float y, float w, float h, float r) {
        Path p = new Path();
        p.addRoundRect(x, y, x + w, y + h, r, r, Path.Direction.CW);
        return p;
    }

    // scrollbar 胶囊形方法待 Step 2 添加...
}
```

- [ ] **Step 2: 添加 squircleRing 方法**

追加到 `SquirclePath.java` 文件末尾（close brace 之前）：

```java
    /**
     * Squircle 环形路径（外 squircle 减去 内 squircle）。
     * 使用 Path.op(DIFFERENCE) 做布尔运算。
     */
    public static Path squircleRing(float x, float y, float w, float h, float outerR, float ringW) {
        Path outer = squircle(x, y, w, h, outerR);
        float innerR = outerR - ringW;
        Path inner = squircle(x + ringW, y + ringW,
                w - ringW * 2f, h - ringW * 2f, innerR);
        outer.op(inner, Path.Op.DIFFERENCE);
        return outer;
    }
```

- [ ] **Step 3: 添加 L1 clip 方法**

追加到 `SquirclePath.java`：

```java
    /**
     * L1 装饰带精确 Clip（Button 使用）。
     * 使用原始 SVG 的 r=24 固定圆角 bezier 值：crv=19, off=5, r=24。
     * 禁止缩放 — 圆角部分固定使用原始控制点值。
     *
     * @param left   装饰带左边界 x（=4 for 80px button）
     * @param right  装饰带右边界 x（=76 for 80px button）
     * @param top    装饰带顶部 y（=h - 44 for 80×80 button）
     * @param bottom 装饰带底部 y（=h - 4）
     */
    public static Path l1ExactClip(float left, float right, float top, float bottom) {
        float crv = 19f;
        float off = 5f;
        float r = 24f;
        float curveY = bottom - r;

        Path p = new Path();
        p.moveTo(left, top);
        p.lineTo(right, top);
        p.lineTo(right, curveY);
        // 右下角
        p.cubicTo(right, curveY + crv, right - off, bottom, right - r, bottom);
        p.lineTo(left + r, bottom);
        // 左下角
        p.cubicTo(left + off, bottom, left, curveY + crv, left, curveY);
        p.close();
        return p;
    }

    /**
     * L1 装饰带通用 Clip（Slider 使用，可缩放 r）。
     * 底部圆角使用 squircle bezier 控制点。
     */
    public static Path l1Clip(float left, float right, float top, float bottom, float r) {
        float scale = r / 28f;
        float crv = 22.12f * scale;
        float off = 5.88f * scale;

        Path p = new Path();
        p.moveTo(left, top);
        p.lineTo(right, top);
        p.lineTo(right, bottom - r);
        // 右下角 squircle
        p.cubicTo(right, bottom - r + crv, right - off, bottom, right - r, bottom);
        p.lineTo(left + r, bottom);
        // 左下角 squircle
        p.cubicTo(left + off, bottom, left, bottom - r + crv, left, bottom - r);
        p.close();
        return p;
    }
```

- [ ] **Step 4: 添加 Scrollbar 胶囊形方法**

追加到 `SquirclePath.java`（在 close brace 前）：

```java
    // ── 滚动条（胶囊形，固定 W=24）──

    /**
     * 滚动条外环 — 半圆端胶囊 24×h r=12。
     * 等价于 Batik 的 path M218,475 c-8.6,0 -12,2.5 -12,12 v104 c0,9.5 3.4,12 12,12 ...。
     * 坐标原点 (0,0)，宽度固定 24。
     */
    public static Path capsuleRing(float h) {
        Path p = new Path();
        p.moveTo(12f, 0f);
        // 左上圆角
        p.cubicTo(3.4f, 0f,  0f, 2.5f,  0f, 12f);
        // 左侧直线
        p.lineTo(0f, h - 12f);
        // 左下圆角
        p.cubicTo(0f, h - 2.5f,  3.4f, h,  12f, h);
        // 右下圆角
        p.cubicTo(22.4f, h,  24f, h - 2.5f,  24f, h - 12f);
        // 右侧直线
        p.lineTo(24f, 12f);
        // 右上圆角
        p.cubicTo(24f, 2.5f,  22.4f, 0f,  12f, 0f);
        p.close();
        return p;
    }

    /**
     * 滚动条内填充 — 半圆端胶囊 16×(h-8) r=8。
     * 起点 (4,4)，宽度 16，高度 h-8。
     */
    public static Path capsuleFill(float h) {
        Path p = new Path();
        p.moveTo(12f, 4f);
        // 左上圆角（bezier 分段）
        p.cubicTo(15.9f, 4f,        18.25f, 4.39f,  18.98f, 5.17f);
        p.cubicTo(20f, 6.25f,       20f, 10.43f,     20f, 12f);
        // 右侧直线
        p.lineTo(20f, h - 12f);
        // 右下圆角
        p.cubicTo(20f, h - 10.43f,  20f, h - 6.26f,  18.98f, h - 5.17f);
        p.cubicTo(18.25f, h - 4.39f, 15.9f, h - 4f,   12f, h - 4f);
        // 左下圆角
        p.cubicTo(8.6f, h - 4f,      6.48f, h - 4.44f, 5.52f, h - 5.35f);
        p.cubicTo(4.51f, h - 6.3f,   4f, h - 8.54f,    4f, h - 12f);
        // 左侧直线
        p.lineTo(4f, 12f);
        // 左上圆角（下半）
        p.cubicTo(4f, 8.54f,         4.51f, 6.3f,      5.52f, 5.35f);
        p.cubicTo(6.48f, 4.44f,      8.61f, 4f,        12f, 4f);
        p.close();
        return p;
    }
}
```

- [ ] **Step 5: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 6: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/SquirclePath.java
git commit -m "feat: add SquirclePath — squircle, ring, L1 clip, and capsule geometry"
```

---

### Task 4: CozyCanvasRenderer — 渲染层

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/CozyCanvasRenderer.java`

**Interfaces:**
- Consumes: `SquirclePath` (Task 3), `ColorScheme` (Task 2)
- Produces:
  - `static void drawButton(Canvas c, float w, float h, ColorScheme cs)` — 绘制完整 Button（L0+L1+L2）
  - `static void drawFrame(Canvas c, float w, float h, ColorScheme cs)` — 绘制 Frame（L0+L2，无 L1）
  - `static void drawSlider(Canvas c, float w, float h, ColorScheme cs)` — 绘制 Slider（标准圆角矩形 + L1+L2）
  - `static void drawScrollbar(Canvas c, float h, ColorScheme cs)` — 绘制 Scrollbar（胶囊形）

- [ ] **Step 1: 创建 CozyCanvasRenderer.java**

```java
package com.goblincoders.cozyui.canvas;

import com.goblincoders.cozyui.color.ColorScheme;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.graphics.Paint;
import icyllis.modernui.graphics.Path;
import icyllis.modernui.graphics.LinearGradient;
import icyllis.modernui.graphics.Shader;

/**
 * 将 ColorScheme 绘制到 ModernUI Canvas 的渲染器。
 * 所有方法均为静态，接收 Canvas + 设计尺寸 + 颜色方案。
 * 调用方负责在传入前 save/scale Canvas。
 */
public final class CozyCanvasRenderer {

    private CozyCanvasRenderer() {}

    // 复用 Paint 对象减少分配
    private static final Paint PAINT = new Paint(Paint.ANTI_ALIAS_FLAG);

    // ── Button 几何常量 ──
    private static final float R = 28f;
    private static final float RING_R = 24f;
    private static final float RING_W = 4f;
    private static final float L1_BOTTOM_GAP = 4f;
    private static final float L1_H = 40f;
    private static final float L1_EDGE_W = 8f;
    private static final float L1_EDGE_X = 4f;
    private static final float L2_O = 4f;
    private static final float L2_OY_BOTTOM_BUTTON = 12f;

    // ── Frame 几何常量 ──
    private static final float L2_OY_BOTTOM_FRAME = 4f;

    // ── Slider 几何常量 ──
    private static final float SLIDER_R = 14f;
    private static final float SLIDER_RING_R = 10f;

    // ── Scrollbar 常量 ──
    private static final float SCROLLBAR_W = 24f;

    // ═══════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════

    /**
     * 绘制 Button（L0 外框 + L1 装饰带 + L2 外环 + L2 内填充）。
     * @param c  Canvas
     * @param w  设计宽度（min 56）
     * @param h  设计高度（min 68）
     * @param cs 颜色方案
     */
    public static void drawButton(Canvas c, float w, float h, ColorScheme cs) {
        // ── L0 外框（squircle r=28）──
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            Paint paint = acquirePaint();
            paint.setColor(cs.l0Fill);
            Path l0 = SquirclePath.squircle(0, 0, w, h, R);
            c.drawPath(l0, paint);
        }

        // ── L1 装饰带 ──
        if (!ColorScheme.isTransparent(cs.l1Fill)) {
            float l1y = h - L1_BOTTOM_GAP - L1_H;
            float l1Left = L1_EDGE_X;
            float l1Right = w - L1_EDGE_X;
            Path l1Shape = SquirclePath.l1ExactClip(l1Left, l1Right, l1y, h - L1_BOTTOM_GAP);

            // L1 填充
            Paint paint = acquirePaint();
            paint.setColor(cs.l1Fill);
            c.drawPath(l1Shape, paint);

            // L1 左侧边缘发光
            if (!ColorScheme.isTransparent(cs.l1Edge)) {
                c.save();
                Path leftClip = new Path();
                leftClip.addRect(l1Left, l1y, l1Left + L1_EDGE_W, l1y + L1_H, Path.Direction.CW);
                leftClip.op(l1Shape, Path.Op.INTERSECT);
                c.clipPath(leftClip);

                Paint edgePaint = acquirePaint();
                edgePaint.setShader(new LinearGradient(
                        l1Left, 0, l1Left + L1_EDGE_W, 0,
                        new int[]{cs.l1Edge, cs.l1Edge, cs.l1Fill},
                        new float[]{0f, 0.5f, 1f},
                        Shader.TileMode.CLAMP));
                c.drawRect(l1Left, l1y, l1Left + L1_EDGE_W, l1y + L1_H, edgePaint);
                c.restore();
            }

            // L1 右侧边缘发光
            if (!ColorScheme.isTransparent(cs.l1Edge)) {
                c.save();
                Path rightClip = new Path();
                rightClip.addRect(l1Right - L1_EDGE_W, l1y, l1Right, l1y + L1_H, Path.Direction.CW);
                rightClip.op(l1Shape, Path.Op.INTERSECT);
                c.clipPath(rightClip);

                Paint edgePaint = acquirePaint();
                edgePaint.setShader(new LinearGradient(
                        l1Right - L1_EDGE_W, 0, l1Right, 0,
                        new int[]{cs.l1Fill, cs.l1Edge, cs.l1Edge},
                        new float[]{0f, 0.5f, 1f},
                        Shader.TileMode.CLAMP));
                c.drawRect(l1Right - L1_EDGE_W, l1y, l1Right, l1y + L1_H, edgePaint);
                c.restore();
            }
        }

        // ── L2 外环 ──
        float l2w = w - L2_O * 2f;
        float l2h = h - L2_O - L2_OY_BOTTOM_BUTTON;
        drawL2Ring(c, L2_O, l2w, l2h, cs);

        // ── L2 内填充 ──
        float innerR = RING_R - RING_W;
        float ix = L2_O + RING_W;
        float iw = l2w - RING_W * 2f;
        float ih = l2h - RING_W * 2f;
        if (iw > 0 && ih > 0) {
            Paint paint = acquirePaint();
            paint.setShader(new LinearGradient(0, 0, 0, ih,
                    new int[]{cs.bgTop, cs.bgBot},
                    new float[]{0f, 1f},
                    Shader.TileMode.CLAMP));
            Path inner = SquirclePath.squircle(ix, ix, iw, ih, innerR);
            c.drawPath(inner, paint);
        }
    }

    /**
     * 绘制 Frame（L0 外框 + L2 外环 + L2 内填充，无 L1）。
     */
    public static void drawFrame(Canvas c, float w, float h, ColorScheme cs) {
        // ── L0 外框 ──
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            Paint paint = acquirePaint();
            paint.setColor(cs.l0Fill);
            Path l0 = SquirclePath.squircle(0, 0, w, h, R);
            c.drawPath(l0, paint);
        }

        // ── L2 外环（Frame 底部偏移 4px）──
        float l2w = w - L2_O * 2f;
        float l2h = h - L2_O - L2_OY_BOTTOM_FRAME;
        drawL2Ring(c, L2_O, l2w, l2h, cs);

        // ── L2 内填充 ──
        float innerR = RING_R - RING_W;
        float ix = L2_O + RING_W;
        float iw = l2w - RING_W * 2f;
        float ih = l2h - RING_W * 2f;
        if (iw > 0 && ih > 0) {
            Paint paint = acquirePaint();
            paint.setShader(new LinearGradient(0, 0, 0, ih,
                    new int[]{cs.bgTop, cs.bgBot},
                    new float[]{0f, 1f},
                    Shader.TileMode.CLAMP));
            Path inner = SquirclePath.squircle(ix, ix, iw, ih, innerR);
            c.drawPath(inner, paint);
        }
    }

    /**
     * 绘制 Slider（标准圆角矩形 L0 + L1 装饰带 + L2 外环 + L2 内填充）。
     */
    public static void drawSlider(Canvas c, float w, float h, ColorScheme cs) {
        // ── L0 外框（标准圆角矩形 r=14）──
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            Paint paint = acquirePaint();
            paint.setColor(cs.l0Fill);
            Path l0 = SquirclePath.roundRect(0, 0, w, h, SLIDER_R);
            c.drawPath(l0, paint);
        }

        // ── L1 装饰带（与 Button 结构相同，但 clip 底部用 squircle 圆角 r=10）──
        if (!ColorScheme.isTransparent(cs.l1Fill)) {
            float l1y = h - L1_BOTTOM_GAP - L1_H;
            float l1Left = L1_EDGE_X;
            float l1Right = w - L1_EDGE_X;
            float clipBottom = h - L1_BOTTOM_GAP;
            Path l1Shape = SquirclePath.l1Clip(l1Left, l1Right, l1y, clipBottom, SLIDER_RING_R);

            // L1 填充
            Paint paint = acquirePaint();
            paint.setColor(cs.l1Fill);
            c.drawPath(l1Shape, paint);

            // L1 左右边缘发光（与 Button 相同逻辑）
            drawL1Edge(c, l1Shape, l1Left, l1y, L1_EDGE_W, L1_H, cs.l1Edge, cs.l1Fill, true);
            drawL1Edge(c, l1Shape, l1Right - L1_EDGE_W, l1y, L1_EDGE_W, L1_H, cs.l1Edge, cs.l1Fill, false);
        }

        // ── L2 外环（squircle RING_R=10, RING_W=4）──
        float l2w = w - L2_O * 2f;
        float l2h = h - L2_O - L2_OY_BOTTOM_BUTTON;
        {
            Paint paint = acquirePaint();
            paint.setShader(new LinearGradient(0, 0, 0, l2h,
                    new int[]{cs.fgTop, cs.fgBot},
                    new float[]{0f, 1f},
                    Shader.TileMode.CLAMP));
            Path ring = SquirclePath.squircleRing(L2_O, L2_O, l2w, l2h, SLIDER_RING_R, RING_W);
            c.drawPath(ring, paint);
        }

        // ── L2 内填充 ──
        float innerR = SLIDER_RING_R - RING_W;
        float ix = L2_O + RING_W;
        float iw = l2w - RING_W * 2f;
        float ih = l2h - RING_W * 2f;
        if (iw > 0 && ih > 0) {
            Paint paint = acquirePaint();
            paint.setShader(new LinearGradient(0, 0, 0, ih,
                    new int[]{cs.bgTop, cs.bgBot},
                    new float[]{0f, 1f},
                    Shader.TileMode.CLAMP));
            Path inner = SquirclePath.squircle(ix, ix, iw, ih, innerR);
            c.drawPath(inner, paint);
        }
    }

    /**
     * 绘制 Scrollbar（胶囊形外环 + 内填充，固定宽度 24）。
     */
    public static void drawScrollbar(Canvas c, float h, ColorScheme cs) {
        // ── 外环 ──
        Paint paint = acquirePaint();
        paint.setShader(new LinearGradient(0, 0, 0, 1,
                new int[]{cs.fgTop, cs.fgBot},
                new float[]{0f, 1f},
                Shader.TileMode.CLAMP));
        Path ring = SquirclePath.capsuleRing(h);
        c.drawPath(ring, paint);

        // ── 内填充 ──
        paint = acquirePaint();
        paint.setShader(new LinearGradient(0, 0, 0, 1,
                new int[]{cs.bgTop, cs.bgBot},
                new float[]{0f, 1f},
                Shader.TileMode.CLAMP));
        Path fill = SquirclePath.capsuleFill(h);
        c.drawPath(fill, paint);
    }

    // ═══════════════════════════════════════════════════
    // Private helpers
    // ═══════════════════════════════════════════════════

    /** 重用 Paint 对象 — 注意调用方应立即使用，不应持有引用 */
    private static Paint acquirePaint() {
        PAINT.setShader(null);
        PAINT.setColor(0);
        return PAINT;
    }

    /** 绘制 L2 外环（squircle 环 + 垂直渐变）。用于 Button 和 Frame。 */
    private static void drawL2Ring(Canvas c, float x, float w, float h, ColorScheme cs) {
        Paint paint = acquirePaint();
        paint.setShader(new LinearGradient(0, 0, 0, h,
                new int[]{cs.fgTop, cs.fgBot},
                new float[]{0f, 1f},
                Shader.TileMode.CLAMP));
        Path ring = SquirclePath.squircleRing(x, x, w, h, RING_R, RING_W);
        c.drawPath(ring, paint);
    }

    /** 绘制 L1 单侧边缘发光渐变 */
    private static void drawL1Edge(Canvas c, Path l1Shape, float x, float y,
                                   float w, float h, int edgeColor, int fillColor,
                                   boolean leftSide) {
        if (ColorScheme.isTransparent(edgeColor)) return;

        c.save();
        Path clipRect = new Path();
        clipRect.addRect(x, y, x + w, y + h, Path.Direction.CW);
        clipRect.op(l1Shape, Path.Op.INTERSECT);
        c.clipPath(clipRect);

        Paint edgePaint = acquirePaint();
        edgePaint.setShader(new LinearGradient(x, 0, x + w, 0,
                leftSide
                        ? new int[]{edgeColor, edgeColor, fillColor}
                        : new int[]{fillColor, edgeColor, edgeColor},
                new float[]{0f, 0.5f, 1f},
                Shader.TileMode.CLAMP));
        c.drawRect(x, y, x + w, y + h, edgePaint);
        c.restore();
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/CozyCanvasRenderer.java
git commit -m "feat: add CozyCanvasRenderer — draws Button/Frame/Slider/Scrollbar to Canvas"
```

---

### Task 5: CozyButton — Button Widget

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyButton.java`

**Interfaces:**
- Consumes: `CozyCanvasRenderer.drawButton()` (Task 4), `ColorScheme` (Task 2)
- Produces: `CozyButton extends View` — 可在 Fragment 布局中添加的按钮组件
  - `setColorScheme(ColorScheme)` — 设置颜色方案
  - `setColorScheme(ColorScheme normal, ColorScheme selected, ColorScheme disabled)` — 设置三种状态颜色
  - `setDesignSize(float w, float h)` — 设置设计尺寸（默认 80×80）

- [ ] **Step 1: 创建 CozyButton.java**

```java
package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;

import icyllis.modernui.annotation.NonNull;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;

/**
 * CozyUI 风格按钮 — squircle 形状，三层叠加（L0+L1+L2）。
 * 支持 NORMAL / SELECTED / DISABLED 三种状态，通过 drawableState 自动切换。
 */
public class CozyButton extends View {

    private float mDesignW = 80f;
    private float mDesignH = 80f;
    private ColorScheme mColorNormal = ColorScheme.NORMAL;
    private ColorScheme mColorSelected = ColorScheme.SELECTED;
    private ColorScheme mColorDisabled = ColorScheme.DISABLED;

    public CozyButton(@NonNull icyllis.modernui.core.Context context) {
        super(context);
    }

    /** 设置所有状态统一颜色方案 */
    public void setColorScheme(ColorScheme cs) {
        setColorScheme(cs, cs, cs);
    }

    /** 分状态设置颜色方案 */
    public void setColorScheme(ColorScheme normal, ColorScheme selected, ColorScheme disabled) {
        mColorNormal = normal;
        mColorSelected = selected;
        mColorDisabled = disabled;
        invalidate();
    }

    /** 获取当前状态对应的颜色方案 */
    public ColorScheme getCurrentColorScheme() {
        if (!isEnabled()) return mColorDisabled;
        if (isSelected() || isPressed()) return mColorSelected;
        return mColorNormal;
    }

    /** 设置设计尺寸（用于等比缩放） */
    public void setDesignSize(float w, float h) {
        mDesignW = w;
        mDesignH = h;
        invalidate();
    }

    public float getDesignW() { return mDesignW; }
    public float getDesignH() { return mDesignH; }

    @Override
    protected void onDraw(@NonNull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;
        canvas.save();
        canvas.scale(sx, sy);
        CozyCanvasRenderer.drawButton(canvas, mDesignW, mDesignH, getCurrentColorScheme());
        canvas.restore();
    }

    @Override
    protected void drawableStateChanged() {
        super.drawableStateChanged();
        invalidate();
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyButton.java
git commit -m "feat: add CozyButton widget with drawableState-based color switching"
```

---

### Task 6: CozyFrame — Frame Widget

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyFrame.java`

**Interfaces:**
- Consumes: `CozyCanvasRenderer.drawFrame()` (Task 4), `ColorScheme` (Task 2)
- Produces: `CozyFrame extends View` — 无 L1 装饰带的框架组件（用作面板/文本框背景）

- [ ] **Step 1: 创建 CozyFrame.java**

```java
package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;

import icyllis.modernui.annotation.NonNull;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;

/**
 * CozyUI 风格框架 — squircle L0 外框 + L2 环 + L2 内填充，无 L1 装饰带。
 * 适用于滑块导轨、文本框、面板等纯框元件。
 */
public class CozyFrame extends View {

    private float mDesignW = 80f;
    private float mDesignH = 56f;
    private ColorScheme mColors = ColorScheme.TEXT_BOX;

    public CozyFrame(@NonNull Context context) {
        super(context);
    }

    public void setColorScheme(ColorScheme cs) {
        mColors = cs;
        invalidate();
    }

    public ColorScheme getColorScheme() { return mColors; }

    public void setDesignSize(float w, float h) {
        mDesignW = w;
        mDesignH = h;
        invalidate();
    }

    public float getDesignW() { return mDesignW; }
    public float getDesignH() { return mDesignH; }

    @Override
    protected void onDraw(@NonNull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;
        canvas.save();
        canvas.scale(sx, sy);
        CozyCanvasRenderer.drawFrame(canvas, mDesignW, mDesignH, mColors);
        canvas.restore();
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyFrame.java
git commit -m "feat: add CozyFrame widget for panel/text-box backgrounds"
```

---

### Task 7: CozySlider — Slider Widget

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozySlider.java`

**Interfaces:**
- Consumes: `CozyCanvasRenderer.drawSlider()` (Task 4), `ColorScheme` (Task 2)
- Produces: `CozySlider extends View` — 滑块手柄组件（标准圆角矩形 + L1+L2）

- [ ] **Step 1: 创建 CozySlider.java**

```java
package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;

import icyllis.modernui.annotation.NonNull;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;

/**
 * CozyUI 风格滑块手柄 — 标准圆角矩形 r=14，三层叠加（L0+L1+L2）。
 * 默认设计尺寸 32×80。
 */
public class CozySlider extends View {

    private float mDesignW = 32f;
    private float mDesignH = 80f;
    private ColorScheme mColorNormal = ColorScheme.NORMAL;
    private ColorScheme mColorSelected = ColorScheme.SELECTED;
    private ColorScheme mColorDisabled = ColorScheme.DISABLED;

    public CozySlider(@NonNull Context context) {
        super(context);
    }

    public void setColorScheme(ColorScheme cs) {
        setColorScheme(cs, cs, cs);
    }

    public void setColorScheme(ColorScheme normal, ColorScheme selected, ColorScheme disabled) {
        mColorNormal = normal;
        mColorSelected = selected;
        mColorDisabled = disabled;
        invalidate();
    }

    public ColorScheme getCurrentColorScheme() {
        if (!isEnabled()) return mColorDisabled;
        if (isSelected() || isPressed()) return mColorSelected;
        return mColorNormal;
    }

    public void setDesignSize(float w, float h) {
        mDesignW = w;
        mDesignH = h;
        invalidate();
    }

    public float getDesignW() { return mDesignW; }
    public float getDesignH() { return mDesignH; }

    @Override
    protected void onDraw(@NonNull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;
        canvas.save();
        canvas.scale(sx, sy);
        CozyCanvasRenderer.drawSlider(canvas, mDesignW, mDesignH, getCurrentColorScheme());
        canvas.restore();
    }

    @Override
    protected void drawableStateChanged() {
        super.drawableStateChanged();
        invalidate();
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozySlider.java
git commit -m "feat: add CozySlider widget — standard round-rect handle with L1+L2"
```

---

### Task 8: CozyScrollbar — Scrollbar Widget

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyScrollbar.java`

**Interfaces:**
- Consumes: `CozyCanvasRenderer.drawScrollbar()` (Task 4), `ColorScheme` (Task 2)
- Produces: `CozyScrollbar extends View` — 胶囊形滚动条组件（固定宽度 24）

- [ ] **Step 1: 创建 CozyScrollbar.java**

```java
package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;

import icyllis.modernui.annotation.NonNull;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;

/**
 * CozyUI 风格滚动条 — 胶囊形（半圆端），固定宽度 24px。
 * 外环 + 内填充两层，无 L0/L1。
 */
public class CozyScrollbar extends View {

    private static final float DESIGN_W = 24f;
    private float mDesignH = 128f;
    private ColorScheme mColors = ColorScheme.SCROLLBAR_TRACK;

    public CozyScrollbar(@NonNull Context context) {
        super(context);
    }

    public void setColorScheme(ColorScheme cs) {
        mColors = cs;
        invalidate();
    }

    public ColorScheme getColorScheme() { return mColors; }

    /**
     * 设置设计高度（宽度固定 24）。
     * 实际渲染时 Canvas 缩放使设计尺寸填满 View bounds。
     */
    public void setDesignHeight(float h) {
        mDesignH = Math.max(h, 24f);
        invalidate();
    }

    public float getDesignH() { return mDesignH; }

    @Override
    protected void onDraw(@NonNull Canvas canvas) {
        float sy = getHeight() / mDesignH;
        canvas.save();
        canvas.translate((getWidth() - DESIGN_W * (getWidth() / DESIGN_W)) / 2f, 0);
        canvas.scale(getWidth() / DESIGN_W, sy);
        CozyCanvasRenderer.drawScrollbar(canvas, mDesignH, mColors);
        canvas.restore();
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyScrollbar.java
git commit -m "feat: add CozyScrollbar widget — capsule shape, fixed 24px width"
```

---

### Task 9: CozyFragment — Fragment 基类

**Files:**
- Create: `cozyui-modernui/src/main/java/com/goblincoders/cozyui/fragment/CozyFragment.java`

**Interfaces:**
- Consumes: 无
- Produces: `CozyFragment extends Fragment implements ScreenCallback` — 提供合理的默认 ScreenCallback 实现

- [ ] **Step 1: 创建 CozyFragment.java**

```java
package com.goblincoders.cozyui.fragment;

import icyllis.modernui.fragment.Fragment;
import icyllis.modernui.mc.ScreenCallback;

/**
 * CozyUI Fragment 基类 — 提供合理的 ScreenCallback 默认实现。
 * 子类只需实现 {@link #onCreateView} 构建 UI。
 */
public abstract class CozyFragment extends Fragment implements ScreenCallback {

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public boolean shouldClose() {
        return true;
    }

    @Override
    public boolean hasDefaultBackground() {
        return false;
    }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd cozyui-modernui && ./gradlew build
```

Expected: BUILD SUCCESSFUL

- [ ] **Step 3: 提交**

```bash
git add cozyui-modernui/src/main/java/com/goblincoders/cozyui/fragment/CozyFragment.java
git commit -m "feat: add CozyFragment base class with ScreenCallback defaults"
```

---

### Task 10: 最终集成验证

**Files:**
- 无新文件，验证所有组件可编译且可导入

- [ ] **Step 1: 完整构建**

```bash
cd cozyui-modernui && ./gradlew clean build
```

Expected: BUILD SUCCESSFUL（所有子任务源码编译通过）

- [ ] **Step 2: 验证源码结构**

```bash
find cozyui-modernui/src -name "*.java" | sort
```

Expected:
```
cozyui-modernui/src/main/java/com/goblincoders/cozyui/CozyUI.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/CozyCanvasRenderer.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/canvas/SquirclePath.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/color/ColorScheme.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/fragment/CozyFragment.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyButton.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyFrame.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozyScrollbar.java
cozyui-modernui/src/main/java/com/goblincoders/cozyui/widget/CozySlider.java
```

- [ ] **Step 3: 提交**

```bash
git add . && git commit -m "chore: final verification — all components build successfully"
```
