package com.alma.cozyui.color;

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
