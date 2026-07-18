package com.goblincoders.cozyui.widget;

import com.goblincoders.cozyui.canvas.CozyCanvasRenderer;
import com.goblincoders.cozyui.color.ColorScheme;
import icyllis.modernui.core.Context;
import icyllis.modernui.graphics.Canvas;
import icyllis.modernui.view.View;
import javax.annotation.Nonnull;

/**
 * CozyUI Button widget with three-state color scheme support.
 *
 * <p>Draws at 80x80 design size, then scales to fit the view's actual dimensions.
 * Supports NORMAL, SELECTED (hover/active), and DISABLED color schemes.</p>
 */
public class CozyButton extends View {

    private final float mDesignW = 80f;
    private final float mDesignH = 80f;

    private ColorScheme mColorNormal = ColorScheme.NORMAL;
    private ColorScheme mColorSelected = ColorScheme.SELECTED;
    private ColorScheme mColorDisabled = ColorScheme.DISABLED;

    private boolean mEnabled = true;
    private boolean mSelected = false;

    public CozyButton(@Nonnull Context context) {
        super(context);
    }

    @Override
    protected void onDraw(@Nonnull Canvas canvas) {
        float sx = getWidth() / mDesignW;
        float sy = getHeight() / mDesignH;

        canvas.save();
        canvas.scale(sx, sy);

        CozyCanvasRenderer.drawButton(canvas, mDesignW, mDesignH, getCurrentColorScheme());

        canvas.restore();
    }

    /**
     * Resolve which color scheme to use based on current state.
     */
    private ColorScheme getCurrentColorScheme() {
        if (!mEnabled) {
            return mColorDisabled;
        }
        if (mSelected) {
            return mColorSelected;
        }
        return mColorNormal;
    }

    // ─── State accessors ─────────────────────────────────────────────────

    public boolean isCozyEnabled() {
        return mEnabled;
    }

    public void setCozyEnabled(boolean enabled) {
        if (mEnabled != enabled) {
            mEnabled = enabled;
            invalidate();
        }
    }

    public boolean isCozySelected() {
        return mSelected;
    }

    public void setCozySelected(boolean selected) {
        if (mSelected != selected) {
            mSelected = selected;
            invalidate();
        }
    }

    // ─── Color scheme overrides ──────────────────────────────────────────

    public ColorScheme getColorNormal() {
        return mColorNormal;
    }

    public void setColorNormal(ColorScheme colorNormal) {
        mColorNormal = colorNormal;
        invalidate();
    }

    public ColorScheme getColorSelected() {
        return mColorSelected;
    }

    public void setColorSelected(ColorScheme colorSelected) {
        mColorSelected = colorSelected;
        invalidate();
    }

    public ColorScheme getColorDisabled() {
        return mColorDisabled;
    }

    public void setColorDisabled(ColorScheme colorDisabled) {
        mColorDisabled = colorDisabled;
        invalidate();
    }
}
