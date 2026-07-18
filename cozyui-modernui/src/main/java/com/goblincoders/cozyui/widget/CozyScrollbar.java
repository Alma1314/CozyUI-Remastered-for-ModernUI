package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;
import javax.annotation.Nonnull;

/**
 * CozyUI Scrollbar widget.
 *
 * <p>The scrollbar has a fixed design width of 24px and a default height of 128px.
 * The rendered height is taken directly from the view's measured height, so
 * no vertical scaling is applied (only horizontal scaling to 24px design width).</p>
 *
 * <p>By default the widget draws the track. Use {@link #setHandle(boolean)} to
 * switch between track ({@link ColorScheme#SCROLLBAR_TRACK}) and handle
 * ({@link ColorScheme#SCROLLBAR_HANDLE}) appearance.</p>
 */
public class CozyScrollbar extends View {

    private final float mDesignW = 24f;
    private final float mDesignH = 128f;

    private ColorScheme mColorScheme = ColorScheme.SCROLLBAR_TRACK;
    private boolean mIsHandle = false;

    public CozyScrollbar(@Nonnull Context context) {
        super(context);
    }

    @Override
    protected void onDraw(@Nonnull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;

        canvas.save();
        canvas.scale(sx, sy);

        CozyCanvasRenderer.drawScrollbar(canvas, mDesignH, mColorScheme);

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

    // ─── Handle / Track toggle ───────────────────────────────────────────

    public boolean isHandle() {
        return mIsHandle;
    }

    /**
     * Toggle between handle and track appearance. Convenience method that
     * selects the appropriate preset color scheme.
     */
    public void setHandle(boolean handle) {
        if (mIsHandle != handle) {
            mIsHandle = handle;
            mColorScheme = handle ? ColorScheme.SCROLLBAR_HANDLE : ColorScheme.SCROLLBAR_TRACK;
            invalidate();
        }
    }
}
