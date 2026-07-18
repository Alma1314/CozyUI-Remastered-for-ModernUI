package com.alma.cozyui.widget;

import com.alma.cozyui.canvas.CozyCanvasRenderer;
import com.alma.cozyui.color.ColorScheme;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;
import javax.annotation.Nonnull;

/**
 * CozyUI Slider widget -- a vertical slider track.
 *
 * <p>Draws at 32x80 design size, then scales to fit the view's actual dimensions.
 * Uses {@link ColorScheme#SLIDER_TRACK} by default.</p>
 */
public class CozySlider extends View {

    private final float mDesignW = 32f;
    private final float mDesignH = 80f;

    private ColorScheme mColorScheme = ColorScheme.SLIDER_TRACK;

    public CozySlider(@Nonnull Context context) {
        super(context);
    }

    @Override
    protected void onDraw(@Nonnull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;

        canvas.save();
        canvas.scale(sx, sy);

        CozyCanvasRenderer.drawSlider(canvas, mDesignW, mDesignH, mColorScheme);

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
