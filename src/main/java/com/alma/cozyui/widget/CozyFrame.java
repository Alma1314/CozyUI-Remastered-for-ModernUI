package com.alma.cozyui.widget;

import com.alma.cozyui.canvas.CozyCanvasRenderer;
import com.alma.cozyui.color.ColorScheme;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;
import javax.annotation.Nonnull;

/**
 * CozyUI Frame widget -- a decorative panel/surface.
 *
 * <p>Draws at 80x56 design size, then scales to fit the view's actual dimensions.
 * Frames have no L1 decorative band; the L2 inner fill extends farther downward.</p>
 */
public class CozyFrame extends View {

    private final float mDesignW = 80f;
    private final float mDesignH = 56f;

    private ColorScheme mColorScheme = ColorScheme.PANEL;

    public CozyFrame(@Nonnull Context context) {
        super(context);
    }

    @Override
    protected void onDraw(@Nonnull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;

        canvas.save();
        canvas.scale(sx, sy);

        CozyCanvasRenderer.drawFrame(canvas, mDesignW, mDesignH, mColorScheme);

        canvas.restore();
    }

    // ─── Color scheme ────────────────────────────────────────────────────

    public ColorScheme getColorScheme() {
        return mColorScheme;
    }

    public void setColorScheme(ColorScheme colorScheme) {
        mColorScheme = colorScheme;
        invalidate();
    }
}
