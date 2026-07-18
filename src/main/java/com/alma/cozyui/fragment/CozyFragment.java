package com.alma.cozyui.fragment;

import icyllis.modernui.fragment.Fragment;
import icyllis.modernui.mc.ScreenCallback;

/**
 * Base fragment for all CozyUI screens.
 *
 * <p>Implements {@link ScreenCallback} so that subclasses can configure
 * Minecraft-level screen behaviour (pause, background, close handling).</p>
 */
public class CozyFragment extends Fragment implements ScreenCallback {

    public CozyFragment() {
        super();
    }

    // ─── ScreenCallback ──────────────────────────────────────────────────

    /**
     * Called when a key is pressed to check whether it should close the screen.
     * Default: returns {@code false} for all keys (no automatic closing).
     */
    @Override
    public boolean isBackKey(int keyCode, icyllis.modernui.view.KeyEvent event) {
        return false;
    }

    /**
     * Called when the screen should determine if it can be closed.
     * Default: returns {@code true} (screen can close).
     */
    @Override
    public boolean shouldClose() {
        return true;
    }

    /**
     * Whether this screen pauses the game when opened.
     * Default: returns {@code false} (game continues running).
     */
    @Override
    public boolean isPauseScreen() {
        return false;
    }

    /**
     * Whether this screen should have a default dark background overlay.
     * Default: returns {@code true}.
     */
    @Override
    public boolean hasDefaultBackground() {
        return false;
    }

    /**
     * Whether the background should be blurred.
     * Default: returns {@code false}.
     */
    @Override
    public boolean shouldBlurBackground() {
        return false;
    }
}
