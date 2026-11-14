package com.chagoktown.ui.theme

import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/**
 * Official Pleos display presets, as listed by FormFactorConsole in the Pleos Connect emulator v2.1.0 (checked 2026-11-13).
 * Physical pixels, long side first. For the two 200 dpi panels the console's "resolution" (2048x1152, 3072x816) only works
 * out as dp: its own app-window sizes (1700x1185 px, 1570x1000 px) would not fit those pixels, so the panels are taken as
 * 2560x1440 and 3840x1020 px. Every real panel then declares close to its true density (160-212 ppi).
 * The emulator's default AVD (12.8" 2560x1440 at 160 dpi, about 229 ppi) has the same pixels and dpi as the 17" panel and
 * cannot be told apart from it, so it is treated as the 17" car screen.
 */
internal data class PleosPanel(val name: String, val longPx: Int, val shortPx: Int, val dpi: Int, val inches: Float) {
    val ppi: Float get() = (hypot(longPx.toDouble(), shortPx.toDouble()) / inches).toFloat()
}

internal val PleosPanels = listOf(
    PleosPanel("Connect-S 17\"", 2560, 1440, 160, 17f),
    PleosPanel("Connect-S 14.6\"", 2560, 1440, 200, 14.6f),
    PleosPanel("Connect-S 12.9\"", 1920, 1080, 160, 12.9f),
    PleosPanel("Connect-WS 24.6\"", 3840, 850, 160, 24.6f),
    PleosPanel("Connect-WE 24.6\"", 3840, 1440, 160, 24.6f),
    PleosPanel("Connect-WF 18.7\"", 3840, 1020, 200, 18.7f),
)

/**
 * One dp should measure [TargetMmPerDp] on the glass, so an 18sp body is about 3.6 mm (glyphs at least 3 mm) and a 24sp button
 * label about 4.8 mm, after the Pleos UI guide's 3 mm secondary / 5 mm primary text heights.
 */
internal const val TargetMmPerDp = 0.2f

/** Below this much layout height the town header, list and actions stop fitting, so short wide screens scale less. */
internal const val MinCanvasHeightDp = 560f
internal const val MaxCarScale = 2f

/**
 * UI scale for an automotive display. The panel's real pixel density comes from the official preset table when the display
 * matches one, otherwise from the reported physical dpi; it is then capped so at least [MinCanvasHeightDp] of layout fits.
 * Never below 1: a scale only ever enlarges.
 */
internal fun carScale(displayWidthPx: Int, displayHeightPx: Int, densityDpi: Int, reportedXdpi: Float, windowHeightDp: Float): Float {
    val longPx = max(displayWidthPx, displayHeightPx)
    val shortPx = min(displayWidthPx, displayHeightPx)
    val panel = PleosPanels.firstOrNull { it.longPx == longPx && it.shortPx == shortPx && it.dpi == densityDpi }
    val ppi = panel?.ppi ?: reportedXdpi.takeIf { it in 100f..640f } ?: densityDpi.toFloat()
    val mmPerDp = 25.4f / ppi * densityDpi / 160f
    val physical = TargetMmPerDp / mmPerDp
    val fit = windowHeightDp / MinCanvasHeightDp
    return min(physical, fit).coerceIn(1f, MaxCarScale)
}
