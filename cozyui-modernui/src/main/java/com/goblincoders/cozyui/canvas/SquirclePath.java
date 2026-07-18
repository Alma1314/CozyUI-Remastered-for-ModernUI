package com.goblincoders.cozyui.canvas;

import icyllis.arc3d.sketch.PathBuilder;
import icyllis.arc3d.sketch.Path;

/**
 * 纯几何路径构建 — 将 Batik 的 Path2D.Float 翻译为 ModernUI 的 {@link Path}。
 * Squircle 定义：r=28 时 cubic bezier 控制点 crv=22.12, off=5.88（从 PSD 提取）。
 *
 * <p>内部使用 {@link PathBuilder} 构建路径，然后通过 {@link PathBuilder#build()} 生成 {@link Path}。</p>
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

        PathBuilder pb = new PathBuilder();
        pb.moveTo(x + w - r, y);
        pb.lineTo(x + r, y);
        pb.cubicTo(x + r - crv, y,         x,      y + off,  x,       y + r);
        pb.lineTo(x, y + h - r);
        pb.cubicTo(x, y + h - r + crv,     x + off, y + h,    x + r,   y + h);
        pb.lineTo(x + w - r, y + h);
        pb.cubicTo(x + w - r + crv, y + h, x + w,   y + h - off, x + w, y + h - r);
        pb.lineTo(x + w, y + r);
        pb.cubicTo(x + w, y + r - crv,     x + w - off, y,    x + w - r, y);
        pb.close();
        return pb.build();
    }

    /**
     * 标准圆角矩形（rx=ry=r），使用 cubic bezier 近似。
     */
    public static Path roundRect(float x, float y, float w, float h, float r) {
        // 使用 cubic bezier 近似四分之一圆角
        float c = r * 0.4475f; // kappa 近似

        PathBuilder pb = new PathBuilder();
        pb.moveTo(x + w - r, y);
        // 上边
        pb.lineTo(x + r, y);
        // 左上角
        pb.cubicTo(x + r - c, y, x, y + c, x, y + r);
        // 左边
        pb.lineTo(x, y + h - r);
        // 左下角
        pb.cubicTo(x, y + h - c, x + c, y + h, x + r, y + h);
        // 下边
        pb.lineTo(x + w - r, y + h);
        // 右下角
        pb.cubicTo(x + w - c, y + h, x + w, y + h - c, x + w, y + h - r);
        // 右边
        pb.lineTo(x + w, y + r);
        // 右上角
        pb.cubicTo(x + w, y + c, x + w - c, y, x + w - r, y);
        pb.close();
        return pb.build();
    }

    /**
     * Squircle 环形路径（外 squircle 减去 内 squircle）。
     * 使用 Path.op(DIFFERENCE) 做布尔运算。
     *
     * <p><b>注意：</b>当前 arc3d-sketch 版本（2026.2.0）不支持布尔路径操作。
     * 此方法使用 EVEN_ODD winding 规则叠加内外路径来实现环形效果。</p>
     */
    public static Path squircleRing(float x, float y, float w, float h, float outerR, float ringW) {
        Path outer = squircle(x, y, w, h, outerR);
        float innerR = outerR - ringW;
        Path inner = squircle(x + ringW, y + ringW,
                w - ringW * 2f, h - ringW * 2f, innerR);

        // 使用 EVEN_ODD winding 实现环形效果
        PathBuilder pb = new PathBuilder(Path.WIND_EVEN_ODD);
        pb.addPath(outer, null, PathBuilder.ADD_PATH_APPEND);
        pb.addPath(inner, null, PathBuilder.ADD_PATH_APPEND);
        return pb.build();
    }

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

        PathBuilder pb = new PathBuilder();
        pb.moveTo(left, top);
        pb.lineTo(right, top);
        pb.lineTo(right, curveY);
        // 右下角
        pb.cubicTo(right, curveY + crv, right - off, bottom, right - r, bottom);
        pb.lineTo(left + r, bottom);
        // 左下角
        pb.cubicTo(left + off, bottom, left, curveY + crv, left, curveY);
        pb.close();
        return pb.build();
    }

    /**
     * L1 装饰带通用 Clip（Slider 使用，可缩放 r）。
     * 底部圆角使用 squircle bezier 控制点。
     */
    public static Path l1Clip(float left, float right, float top, float bottom, float r) {
        float scale = r / 28f;
        float crv = 22.12f * scale;
        float off = 5.88f * scale;

        PathBuilder pb = new PathBuilder();
        pb.moveTo(left, top);
        pb.lineTo(right, top);
        pb.lineTo(right, bottom - r);
        // 右下角 squircle
        pb.cubicTo(right, bottom - r + crv, right - off, bottom, right - r, bottom);
        pb.lineTo(left + r, bottom);
        // 左下角 squircle
        pb.cubicTo(left + off, bottom, left, bottom - r + crv, left, bottom - r);
        pb.close();
        return pb.build();
    }

    // ── 滚动条（胶囊形，固定 W=24）──

    /**
     * 滚动条外环 — 半圆端胶囊 24×h r=12。
     * 等价于 Batik 的 path M218,475 c-8.6,0 -12,2.5 -12,12 v104 c0,9.5 3.4,12 12,12 ...。
     * 坐标原点 (0,0)，宽度固定 24。
     */
    public static Path capsuleRing(float h) {
        PathBuilder pb = new PathBuilder();
        pb.moveTo(12f, 0f);
        // 左上圆角
        pb.cubicTo(3.4f, 0f,  0f, 2.5f,  0f, 12f);
        // 左侧直线
        pb.lineTo(0f, h - 12f);
        // 左下圆角
        pb.cubicTo(0f, h - 2.5f,  3.4f, h,  12f, h);
        // 右下圆角
        pb.cubicTo(22.4f, h,  24f, h - 2.5f,  24f, h - 12f);
        // 右侧直线
        pb.lineTo(24f, 12f);
        // 右上圆角
        pb.cubicTo(24f, 2.5f,  22.4f, 0f,  12f, 0f);
        pb.close();
        return pb.build();
    }

    /**
     * 滚动条内填充 — 半圆端胶囊 16×(h-8) r=8。
     * 起点 (4,4)，宽度 16，高度 h-8。
     */
    public static Path capsuleFill(float h) {
        PathBuilder pb = new PathBuilder();
        pb.moveTo(12f, 4f);
        // 左上圆角（bezier 分段）
        pb.cubicTo(15.9f, 4f,        18.25f, 4.39f,  18.98f, 5.17f);
        pb.cubicTo(20f, 6.25f,       20f, 10.43f,     20f, 12f);
        // 右侧直线
        pb.lineTo(20f, h - 12f);
        // 右下圆角
        pb.cubicTo(20f, h - 10.43f,  20f, h - 6.26f,  18.98f, h - 5.17f);
        pb.cubicTo(18.25f, h - 4.39f, 15.9f, h - 4f,   12f, h - 4f);
        // 左下圆角
        pb.cubicTo(8.6f, h - 4f,      6.48f, h - 4.44f, 5.52f, h - 5.35f);
        pb.cubicTo(4.51f, h - 6.3f,   4f, h - 8.54f,    4f, h - 12f);
        // 左侧直线
        pb.lineTo(4f, 12f);
        // 左上圆角（下半）
        pb.cubicTo(4f, 8.54f,         4.51f, 6.3f,      5.52f, 5.35f);
        pb.cubicTo(6.48f, 4.44f,      8.61f, 4f,        12f, 4f);
        pb.close();
        return pb.build();
    }
}
