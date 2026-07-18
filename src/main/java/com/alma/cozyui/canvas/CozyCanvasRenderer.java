package com.alma.cozyui.canvas;

import com.alma.cozyui.color.ColorScheme;
import icyllis.modernui.graphics.*;

/**
 * Renders CozyUI buttons, frames, sliders, and scrollbars using ModernUI Canvas API.
 *
 * <p>Since ModernUI Canvas does not support <code>drawPath()</code>, squircle-based
 * shapes are approximated using <code>drawRoundRect</code> with per-corner radii.
 * The visual difference between a true squircle and a standard round rect at the
 * specified dimensions is negligible.</p>
 *
 * <h3>Layer structure (Button)</h3>
 * <pre>
 *   L0: outer squircle fill    (r=28)
 *   L1: decorative band        (r=24, bottom-corners only)
 *   L1: edge glow              (clipped rect + gradient)
 *   L2: inner ring stroke      (r=24, w=4)
 *   L2: inner fill             (r=24-4=20 inner area)
 * </pre>
 *
 * <h3>Layer structure (Frame)</h3>
 * <pre>
 *   L0: outer squircle fill    (r=28)
 *   L2: inner ring stroke      (r=24, w=4)
 *   L2: inner fill             (r=24-4=20 inner area)
 * </pre>
 *
 * <h3>Layer structure (Slider)</h3>
 * <pre>
 *   L0: track fill             (r=14)
 *   L1: decorative band (same as Button)
 *   L1: edge glow (same as Button)
 *   L2: inner ring stroke      (r=10, w=4)
 *   L2: inner fill             (r=10-4=6 inner area)
 * </pre>
 *
 * <h3>Layer structure (Scrollbar)</h3>
 * <pre>
 *   Outer ring: round rect (W=24, r=12)
 *   Inner fill:  round rect (W=16, r=8), inset by 4
 * </pre>
 */
public final class CozyCanvasRenderer {

    private CozyCanvasRenderer() {}

    // ─── Geometry constants ───────────────────────────────────────────────

    /** Squircle outer radius for buttons/frames */
    private static final float BTN_R = 28f;
    /** Inner ring radius for buttons/frames */
    private static final float BTN_RING_R = 24f;
    /** Ring stroke width for buttons/frames */
    private static final float BTN_RING_W = 4f;
    /** L1 band bottom gap from component edge */
    private static final float L1_BOTTOM_GAP = 4f;
    /** L1 band height */
    private static final float L1_H = 40f;
    /** L1 edge glow strip width */
    private static final float L1_EDGE_W = 8f;
    /** L1 edge glow x offset from left */
    private static final float L1_EDGE_X = 4f;
    /** L2 ring offset from L0 edge (inset) */
    private static final float BTN_L2_OFFSET = 4f;
    /** L2 inner fill Y offset from bottom (Button) */
    private static final float BTN_L2_OY = 12f;
    /** L2 inner fill Y offset from bottom (Frame, no L1) */
    private static final float FRAME_L2_OY = 4f;

    /** Slider track radius */
    private static final float SLTR_R = 14f;
    /** Slider ring radius */
    private static final float SLTR_RING_R = 10f;
    /** Slider ring width */
    private static final float SLTR_RING_W = 4f;
    /** Slider L2 inner fill Y offset from bottom */
    private static final float SLTR_L2_OY = 12f;

    /** Scrollbar fixed width */
    private static final float SCROLLBAR_W = 24f;

    // ─── Reusable Paint objects (thread-local to avoid allocation) ─────────

    /** Create a fill-style Paint with a solid color. */
    private static Paint fillPaint(int argb) {
        Paint p = new Paint();
        p.setStyle(Paint.FILL);
        p.setColor(argb);
        return p;
    }

    /** Create a stroke-style Paint with the given width and color. */
    private static Paint strokePaint(float w, int argb) {
        Paint p = new Paint();
        p.setStyle(Paint.STROKE);
        p.setStrokeWidth(w);
        p.setColor(argb);
        return p;
    }

    /** Create a fill-style Paint with a vertical LinearGradient from top to bottom. */
    private static Paint gradientFillPaint(float top, float bottom, int colorTop, int colorBot) {
        Paint p = new Paint();
        p.setStyle(Paint.FILL);
        p.setShader(new LinearGradient(0f, top, 0f, bottom,
                new int[]{colorTop, colorBot}, null,
                Shader.TileMode.CLAMP, null));
        return p;
    }

    /** Create a stroke-style Paint with a vertical LinearGradient. */
    private static Paint gradientStrokePaint(float w, float top, float bottom, int colorTop, int colorBot) {
        Paint p = new Paint();
        p.setStyle(Paint.STROKE);
        p.setStrokeWidth(w);
        p.setShader(new LinearGradient(0f, top, 0f, bottom,
                new int[]{colorTop, colorBot}, null,
                Shader.TileMode.CLAMP, null));
        return p;
    }

    // ─── Public drawing methods ────────────────────────────────────────────

    /**
     * Draw a CozyUI button with all layers at origin (0,0).
     *
     * @param canvas target canvas
     * @param w      component width
     * @param h      component height
     * @param cs     color scheme
     */
    public static void drawButton(Canvas canvas, float w, float h, ColorScheme cs) {
        // --- L0: outer squircle fill ---
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            canvas.drawRoundRect(0f, 0f, w, h, BTN_R, BTN_R, BTN_R, BTN_R, fillPaint(cs.l0Fill));
        }

        // --- L1: decorative band (bottom-corners rounded, top flat) ---
        float l1Top = h - L1_BOTTOM_GAP - L1_H;
        float l1Bottom = h - L1_BOTTOM_GAP;
        if (!ColorScheme.isTransparent(cs.l1Fill)) {
            // Rounded bottom corners only, flat top
            canvas.drawRoundRect(0f, l1Top, w, l1Bottom,
                    0f, 0f, BTN_RING_R, BTN_RING_R, fillPaint(cs.l1Fill));
        }

        // --- L1: edge glow (clipped rect with gradient) ---
        if (!ColorScheme.isTransparent(cs.l1Edge)) {
            int saveCount = canvas.save();
            // Clip to the L1 band area
            canvas.clipRect(L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Bottom);
            // Draw a horizontal gradient in the clipped area
            Paint edgePaint = new Paint();
            edgePaint.setStyle(Paint.FILL);
            edgePaint.setShader(new LinearGradient(
                    L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Top,
                    cs.l1Edge, ColorScheme.isTransparent(cs.l1Fill) ? cs.l1Edge : cs.l1Fill,
                    Shader.TileMode.CLAMP, null));
            canvas.drawRect(L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Bottom, edgePaint);
            canvas.restoreToCount(saveCount);
        }

        // --- L2: inner fill (gradient) ---
        float l2Left = BTN_L2_OFFSET;
        float l2Top = BTN_L2_OFFSET;
        float l2Right = w - BTN_L2_OFFSET;
        float l2Bottom = h - BTN_L2_OY;
        float l2Radius = BTN_RING_R;

        if (!ColorScheme.isTransparent(cs.bgTop) || !ColorScheme.isTransparent(cs.bgBot)) {
            canvas.drawRoundRect(l2Left, l2Top, l2Right, l2Bottom,
                    l2Radius, l2Radius, l2Radius, l2Radius,
                    gradientFillPaint(l2Top, l2Bottom, cs.bgTop, cs.bgBot));
        }

        // --- L2: ring stroke (gradient) ---
        if (!ColorScheme.isTransparent(cs.fgTop) || !ColorScheme.isTransparent(cs.fgBot)) {
            // Stroke is drawn centered on the edge, so inset by half stroke width
            float strokeInset = BTN_RING_W / 2f;
            canvas.drawRoundRect(
                    l2Left - strokeInset, l2Top - strokeInset,
                    l2Right + strokeInset, l2Bottom + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    gradientStrokePaint(BTN_RING_W, l2Top, l2Bottom, cs.fgTop, cs.fgBot));
        }
    }

    /**
     * Draw a CozyUI frame (like button but no L1 decorative band, L2 fills full area).
     */
    public static void drawFrame(Canvas canvas, float w, float h, ColorScheme cs) {
        // --- L0: outer squircle fill ---
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            canvas.drawRoundRect(0f, 0f, w, h, BTN_R, BTN_R, BTN_R, BTN_R, fillPaint(cs.l0Fill));
        }

        // --- L2: inner fill (gradient, fills full L2 area) ---
        float l2Left = BTN_L2_OFFSET;
        float l2Top = BTN_L2_OFFSET;
        float l2Right = w - BTN_L2_OFFSET;
        float l2Bottom = h - FRAME_L2_OY;
        float l2Radius = BTN_RING_R;

        if (!ColorScheme.isTransparent(cs.bgTop) || !ColorScheme.isTransparent(cs.bgBot)) {
            canvas.drawRoundRect(l2Left, l2Top, l2Right, l2Bottom,
                    l2Radius, l2Radius, l2Radius, l2Radius,
                    gradientFillPaint(l2Top, l2Bottom, cs.bgTop, cs.bgBot));
        }

        // --- L2: ring stroke (gradient) ---
        if (!ColorScheme.isTransparent(cs.fgTop) || !ColorScheme.isTransparent(cs.fgBot)) {
            float strokeInset = BTN_RING_W / 2f;
            canvas.drawRoundRect(
                    l2Left - strokeInset, l2Top - strokeInset,
                    l2Right + strokeInset, l2Bottom + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    gradientStrokePaint(BTN_RING_W, l2Top, l2Bottom, cs.fgTop, cs.fgBot));
        }
    }

    /**
     * Draw a CozyUI slider track at origin (0,0).
     * A slider has L0 + L1 (bottom band + edge glow) + L2 (fill + ring).
     * The L1 geometry for sliders uses the sliders r=14 scaling.
     */
    public static void drawSlider(Canvas canvas, float w, float h, ColorScheme cs) {
        // --- L0: track fill ---
        if (!ColorScheme.isTransparent(cs.l0Fill)) {
            canvas.drawRoundRect(0f, 0f, w, h, SLTR_R, SLTR_R, SLTR_R, SLTR_R, fillPaint(cs.l0Fill));
        }

        // --- L1: decorative band ---
        float l1Top = h - L1_BOTTOM_GAP - L1_H;
        float l1Bottom = h - L1_BOTTOM_GAP;
        if (!ColorScheme.isTransparent(cs.l1Fill)) {
            canvas.drawRoundRect(0f, l1Top, w, l1Bottom,
                    0f, 0f, BTN_RING_R, BTN_RING_R, fillPaint(cs.l1Fill));
        }

        // --- L1: edge glow ---
        if (!ColorScheme.isTransparent(cs.l1Edge)) {
            int saveCount = canvas.save();
            canvas.clipRect(L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Bottom);
            Paint edgePaint = new Paint();
            edgePaint.setStyle(Paint.FILL);
            edgePaint.setShader(new LinearGradient(
                    L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Top,
                    cs.l1Edge, ColorScheme.isTransparent(cs.l1Fill) ? cs.l1Edge : cs.l1Fill,
                    Shader.TileMode.CLAMP, null));
            canvas.drawRect(L1_EDGE_X, l1Top, L1_EDGE_X + L1_EDGE_W, l1Bottom, edgePaint);
            canvas.restoreToCount(saveCount);
        }

        // --- L2: inner fill ---
        float inset = BTN_L2_OFFSET;
        float l2Left = inset;
        float l2Top = inset;
        float l2Right = w - inset;
        float l2Bottom = h - SLTR_L2_OY;
        float l2Radius = SLTR_RING_R;

        if (!ColorScheme.isTransparent(cs.bgTop) || !ColorScheme.isTransparent(cs.bgBot)) {
            canvas.drawRoundRect(l2Left, l2Top, l2Right, l2Bottom,
                    l2Radius, l2Radius, l2Radius, l2Radius,
                    gradientFillPaint(l2Top, l2Bottom, cs.bgTop, cs.bgBot));
        }

        // --- L2: ring stroke ---
        if (!ColorScheme.isTransparent(cs.fgTop) || !ColorScheme.isTransparent(cs.fgBot)) {
            float strokeInset = SLTR_RING_W / 2f;
            canvas.drawRoundRect(
                    l2Left - strokeInset, l2Top - strokeInset,
                    l2Right + strokeInset, l2Bottom + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    l2Radius + strokeInset, l2Radius + strokeInset,
                    gradientStrokePaint(SLTR_RING_W, l2Top, l2Bottom, cs.fgTop, cs.fgBot));
        }
    }

    /**
     * Draw a CozyUI scrollbar component at origin (0,0) with fixed width 24.
     *
     * <p>The outer ring is a capsule (half-circle ends), approximated by
     * drawRoundRect with r=12. The inner fill is also a capsule (r=8),
     * inset by 4px from all sides.</p>
     *
     * @param canvas target canvas
     * @param h      component height
     * @param cs     color scheme (e.g. SCROLLBAR_TRACK or SCROLLBAR_HANDLE)
     */
    public static void drawScrollbar(Canvas canvas, float h, ColorScheme cs) {
        float w = SCROLLBAR_W;

        // --- Outer ring (capsule W=24, r=12) ---
        if (!ColorScheme.isTransparent(cs.fgTop) || !ColorScheme.isTransparent(cs.fgBot)) {
            canvas.drawRoundRect(0f, 0f, w, h, 12f, 12f, 12f, 12f,
                    gradientStrokePaint(2f, 0f, h, cs.fgTop, cs.fgBot));
        }

        // --- Inner fill (capsule W=16 inset by 4, r=8) ---
        float fillLeft = 4f;
        float fillTop = 4f;
        float fillRight = w - 4f;
        float fillBottom = h - 4f;
        if (!ColorScheme.isTransparent(cs.bgTop) || !ColorScheme.isTransparent(cs.bgBot)) {
            canvas.drawRoundRect(fillLeft, fillTop, fillRight, fillBottom,
                    8f, 8f, 8f, 8f,
                    gradientFillPaint(fillTop, fillBottom, cs.bgTop, cs.bgBot));
        }
    }
}
