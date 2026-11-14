package com.chagoktown.ui.theme

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.view.WindowManager
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.unit.Density
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.draw.dropShadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.shadow.Shadow
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.intl.LocaleList
import androidx.compose.ui.text.style.LineBreak
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Hyundai CI colours (hyundai.com/kr/ko/info/ci/ci-color) with derived tones checked for 4.5:1 text contrast (Pleos UI guide).
object TownColors {
    val Navy = Color(0xFF002C5F)
    val ActiveBlue = Color(0xFF00AAD2) // Marks and outlines only; too light for text.
    val Sand = Color(0xFFE4DCD3)
    val LightSand = Color(0xFFF6F3F2)
    val BlueTint = Color(0xFFE6F3F8)
    val Ink = Color(0xFF17324D)
    val InkSecondary = Color(0xFF526773)
    val Line = Color(0xFFE4DED6)
    val Panel = Color(0xFFFFFFFF)
    val Disabled = Color(0xFFE9ECEF)
    val OnDisabled = Color(0xFF596875)
    val Piece = Color(0xFFE6B54A)
    val PieceLight = Color(0xFFF6D88A)
    val PieceDeep = Color(0xFFB9862A)
    val Success = Color(0xFF286448)
    val SuccessTint = Color(0xFFE5F1E8)
    val Warning = Color(0xFFB4441F)
}

// Pleos shadow level 2 (document.pleos.ai foundations/shadow).
fun Modifier.shadowLevel2(shape: Shape) = dropShadow(shape, Shadow(radius = 32.dp, color = Color(0x29000000), offset = DpOffset(0.dp, 8.dp)))
    .dropShadow(shape, Shadow(radius = 2.dp, color = Color(0x14000000), offset = DpOffset(0.dp, 2.dp)))

// Break Korean at word (eojeol) boundaries instead of mid-word where the platform supports it (API 33+).
// Phrase breaking only applies to text in a Korean locale, so the copy is tagged even on a device set to another language.
private val KoreanBreak = LineBreak(LineBreak.Strategy.Balanced, LineBreak.Strictness.Strict, LineBreak.WordBreak.Phrase)
private val KoreanText = LocaleList("ko-KR")

// Key figures and actions stay at 24sp or above (car app quality guidance for games); meta text never below 16sp.
private val TownTypography = Typography(
    displaySmall = TextStyle(fontSize = 36.sp, lineHeight = 42.sp, fontWeight = FontWeight.Bold, letterSpacing = (-0.5).sp),
    headlineLarge = TextStyle(fontSize = 32.sp, lineHeight = 40.sp, fontWeight = FontWeight.Bold, letterSpacing = (-0.5).sp),
    headlineMedium = TextStyle(fontSize = 28.sp, lineHeight = 36.sp, fontWeight = FontWeight.Bold, letterSpacing = (-0.3).sp),
    headlineSmall = TextStyle(fontSize = 24.sp, lineHeight = 32.sp, fontWeight = FontWeight.Bold),
    titleMedium = TextStyle(fontSize = 20.sp, lineHeight = 28.sp, fontWeight = FontWeight.Bold),
    titleSmall = TextStyle(fontSize = 18.sp, lineHeight = 24.sp, fontWeight = FontWeight.SemiBold),
    bodyLarge = TextStyle(fontSize = 22.sp, lineHeight = 30.sp, lineBreak = KoreanBreak, localeList = KoreanText),
    bodyMedium = TextStyle(fontSize = 18.sp, lineHeight = 26.sp, lineBreak = KoreanBreak, localeList = KoreanText),
    labelLarge = TextStyle(fontSize = 24.sp, lineHeight = 30.sp, fontWeight = FontWeight.Bold),
    labelMedium = TextStyle(fontSize = 16.sp, lineHeight = 22.sp, fontWeight = FontWeight.Medium),
)

/**
 * On an automotive device the whole UI (text, touch targets, spacing) is scaled together per screen so text keeps a similar
 * physical size on every Pleos panel; see [carScale] and its preset table. Phones, tablets and the API 36 dev emulator keep 1.
 */
@Composable
fun TownTheme(panelOverride: String? = null, content: @Composable () -> Unit) {
    val context = LocalContext.current
    val configuration = LocalConfiguration.current
    val automotive = remember(context) { context.packageManager.hasSystemFeature(PackageManager.FEATURE_AUTOMOTIVE) }
    val base = LocalDensity.current
    val windowHeightDp = with(base) { LocalWindowInfo.current.containerSize.height.toDp().value }
    // Re-read on every configuration change: a display resize or density change arrives as one.
    val display = remember(context, configuration, panelOverride) { panelOverride?.let(::parsePanel) ?: displayFacts(context) }
    val scale = if (automotive) carScale(display.widthPx, display.heightPx, display.densityDpi, display.xdpi, windowHeightDp) else 1f
    CompositionLocalProvider(LocalDensity provides Density(base.density * scale, base.fontScale)) {
        TownMaterialTheme(content)
    }
}

private class DisplayFacts(val widthPx: Int, val heightPx: Int, val densityDpi: Int, val xdpi: Float)

/** The whole display (not the app's split window), its declared density and its reported physical dpi. */
private fun displayFacts(context: Context): DisplayFacts {
    val metrics = context.resources.displayMetrics
    val bounds = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) context.getSystemService(WindowManager::class.java)?.maximumWindowMetrics?.bounds else null
    return DisplayFacts(bounds?.width() ?: metrics.widthPixels, bounds?.height() ?: metrics.heightPixels, metrics.densityDpi, metrics.xdpi)
}

/**
 * Form-factor testing on a secondary display: there the "display" is only the app window, so the panel it stands for is
 * given as `WIDTHxHEIGHT@DPI`. MainActivity passes this only in debuggable builds.
 */
private fun parsePanel(value: String): DisplayFacts? =
    Regex("""(\d+)x(\d+)@(\d+)""").matchEntire(value.trim())?.destructured?.let { (width, height, dpi) ->
        DisplayFacts(width.toInt(), height.toInt(), dpi.toInt(), dpi.toFloat())
    }

/** A dialog window gets its own density from the platform, so the car scale is handed in again. */
@Composable
fun TownDialog(onDismissRequest: () -> Unit, properties: DialogProperties = DialogProperties(), content: @Composable () -> Unit) {
    val density = LocalDensity.current
    Dialog(onDismissRequest = onDismissRequest, properties = properties) {
        CompositionLocalProvider(LocalDensity provides density, content = content)
    }
}

@Composable
private fun TownMaterialTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = TownColors.Navy,
            onPrimary = Color.White,
            secondary = TownColors.ActiveBlue,
            background = TownColors.LightSand,
            surface = TownColors.Panel,
            onSurface = TownColors.Ink,
            onSurfaceVariant = TownColors.InkSecondary,
            outline = TownColors.Line,
            error = TownColors.Warning,
        ),
        typography = TownTypography,
        content = content,
    )
}
