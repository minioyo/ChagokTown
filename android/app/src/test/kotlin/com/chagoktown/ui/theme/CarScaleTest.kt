package com.chagoktown.ui.theme

import org.junit.Assert.assertEquals
import org.junit.Test

class CarScaleTest {
    private val roomy = 2_000f // a window tall enough that only the physical size decides

    private fun scale(preset: PleosPanel, windowHeightDp: Float = roomy, xdpi: Float = preset.dpi.toFloat()) =
        carScale(preset.longPx, preset.shortPx, preset.dpi, xdpi, windowHeightDp)

    private fun panel(name: String) = PleosPanels.single { it.name == name }

    @Test fun eachOfficialPanelGetsTheScaleForItsRealPixelDensity() {
        // 0.2 mm per dp divided by the panel's mm per dp. Real panels declare close to their true density, so all land near 1.3.
        assertEquals(1.36f, scale(panel("Connect-S 17\"")), .01f)
        assertEquals(1.27f, scale(panel("Connect-S 14.6\"")), .01f)
        assertEquals(1.34f, scale(panel("Connect-S 12.9\"")), .01f)
        assertEquals(1.26f, scale(panel("Connect-WS 24.6\"")), .01f)
        assertEquals(1.31f, scale(panel("Connect-WE 24.6\"")), .01f)
        assertEquals(1.34f, scale(panel("Connect-WF 18.7\"")), .01f)
    }

    @Test fun samePixelsAtADifferentDeclaredDensityAreADifferentPanel() {
        // 2560x1440 at 160 dpi is the 17" screen, at 200 dpi the 14.6" one.
        assertEquals(1.36f, carScale(2560, 1440, 160, 160f, roomy), .01f)
        assertEquals(1.27f, carScale(2560, 1440, 200, 200f, roomy), .01f)
    }

    @Test fun portraitOrderAndAWrongReportedDpiDoNotChangeAPresetMatch() {
        val s17 = panel("Connect-S 17\"")
        assertEquals(scale(s17), carScale(s17.shortPx, s17.longPx, s17.dpi, 999f, roomy), .001f)
    }

    @Test fun shortWideScreensScaleOnlyAsFarAsTheLayoutStillFits() {
        assertEquals(1.25f, scale(panel("Connect-S 17\""), windowHeightDp = 700f), .001f)
        assertEquals(1f, scale(panel("Connect-WS 24.6\""), windowHeightDp = 500f), .001f)
    }

    @Test fun unknownScreensUseTheReportedPhysicalDpiAndNeverShrink() {
        // A 1600x900 panel reporting 240 physical dpi at 160 declared: 0.106 mm per dp, so 1.89x.
        assertEquals(1.89f, carScale(1600, 900, 160, 240f, roomy), .01f)
        // Nonsense physical dpi falls back to the declared density: 0.159 mm per dp, so 1.26x.
        assertEquals(1.26f, carScale(1600, 900, 160, 0f, roomy), .01f)
        // A coarse panel never scales below 1.
        assertEquals(1f, carScale(1600, 900, 160, 110f, roomy), .001f)
    }
}
