package com.chagoktown.ui.town

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.layout.layout
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ColorMatrix
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.zIndex
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.chagoktown.data.TownLayout
import com.chagoktown.game.PlotDefinition
import com.chagoktown.platform.PlayAccess
import com.chagoktown.ui.TownUiState
import com.chagoktown.ui.TownViewModel
import com.chagoktown.ui.theme.TownColors
import com.chagoktown.ui.theme.shadowLevel2

private val Edge = 28.dp
private val ActionShape = RoundedCornerShape(16.dp)
private val Description = listOf("작지만 완성된 첫 건물을 지어요.", "공간을 넓혀 더 풍성해져요.", "마지막 단계의 새 모습을 만나요.", "성장을 모두 마쳤어요.")

@Composable
fun TownScreen(
    state: TownUiState,
    model: TownViewModel,
    layout: TownLayout,
    platformPanel: @Composable () -> Unit,
    /** True when location may be read now; otherwise asks the platform for permission and returns false. */
    ensureLocationPermission: () -> Boolean = { true },
) {
    BoxWithConstraints(Modifier.fillMaxSize().background(TownColors.LightSand)) {
        // Remembered above every branch so a folded panel or a restriction never throws the decoded thumbnails away.
        val thumbnails = rememberThumbnails(layout)
        val town = state.town
        if (!state.gate.playable || town == null) {
            Column(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing).padding(Edge)) {
                SceneHeader(platformPanel)
                if (!state.gate.playable) RestrictedNotice(state.gate.access)
                else Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(state.message ?: "마을을 불러오고 있어요.", style = MaterialTheme.typography.bodyLarge, color = TownColors.InkSecondary)
                }
            }
            return@BoxWithConstraints
        }

        // Settings never survive a restriction or a background trip: any gate change closes them.
        var showSettings by remember { mutableStateOf(false) }
        var placePlot by remember { mutableStateOf<String?>(null) }
        LaunchedEffect(state.gate.generation) {
            showSettings = false
            placePlot = null
        }
        LaunchedEffect(state.selection?.plotId) { if (placePlot != state.selection?.plotId) placePlot = null }
        if (showSettings) PrivacySettingsDialog(state.privacy, state.places.size, model::setVehicleConsent,
            onLocationConsent = { enabled ->
                if (enabled) ensureLocationPermission()
                model.setLocationConsent(enabled)
            },
            onDeletePlaces = model::deleteAllPlaces, onReset = model::resetMobilityRecord) { showSettings = false }
        placePlot?.takeIf { it == state.selection?.plotId }?.let { plotId ->
            PlaceDialog(
                plotName = model.catalog.plot(plotId)?.name.orEmpty(),
                kind = state.places[plotId],
                revealedAlias = state.revealedAlias?.alias,
                defaultAlias = "거점 ${state.places.size + 1}",
                locationOn = state.privacy.state.locationConsent,
                busy = state.privacy.busy,
                notice = state.message,
                onSaveAlias = { model.saveAlias(plotId, it) },
                onLinkHere = {
                    if (ensureLocationPermission()) model.linkCurrentPlace(plotId, it)
                    else model.showNotice("위치 권한을 허용하면 지금 주차한 곳과 연결할 수 있어요. 허용한 뒤 다시 눌러 주세요.")
                },
                onReveal = { model.revealAlias(plotId) },
                onHide = model::hideAlias,
                onUnlink = { model.unlinkPlace(plotId) },
            ) {
                model.hideAlias()
                placePlot = null
            }
        }

        // The diorama fills the window; an inspector docked to the right edge takes about a third, like a Pleos split view.
        // It can be folded away to see the whole town. Picking a building opens it again, since actions live there.
        // A narrow window (one half of a Pleos split screen) cannot hold the town and the panel side by side. There the panel
        // starts folded and, when opened, floats over the town instead of squeezing the header into a sliver.
        val fullPanelWidth = (maxWidth * .34f).coerceIn(360.dp, 440.dp).coerceAtMost(maxWidth)
        val compact = maxWidth < fullPanelWidth * 2
        var panelOpen by rememberSaveable(compact) { mutableStateOf(!compact) }
        val panelWidth by animateDpAsState(if (panelOpen) fullPanelWidth else 0.dp, label = "inspectorWidth")
        val lifecycle = LocalLifecycleOwner.current.lifecycle
        var renderError by remember { mutableStateOf<String?>(null) }
        val focusShiftX = with(LocalDensity.current) { if (compact) 0f else -panelWidth.toPx() / 2f }
        val focusShiftY = with(LocalDensity.current) { 24.dp.toPx() }
        AndroidView(
            factory = { context ->
                TownSceneView(context, layout, model.gate, lifecycle, { plotId ->
                    // Picking in the scene, even the building already selected, brings the folded panel back.
                    panelOpen = true
                    model.selectPlot(plotId)
                }) { renderError = it }
            },
            modifier = Modifier.fillMaxSize().testTag("town.scene"),
            onRelease = { it.destroy() },
            update = {
                it.setFocusShift(focusShiftX, focusShiftY)
                it.showTown(town, state.selection?.plotId)
            },
        )
        Box(Modifier.fillMaxWidth().height(160.dp).background(Brush.verticalGradient(listOf(TownColors.LightSand, TownColors.LightSand.copy(alpha = 0f)))))

        // The panel keeps its full width and slides out of a clipping box, so its text never reflows mid-animation.
        // Once fully folded it is not composed at all, so hidden rows cannot be reached by touch or accessibility tools.
        val panel: @Composable (Modifier) -> Unit = { modifier ->
            if (panelWidth > 0.dp) Box(modifier.width(panelWidth).fillMaxHeight().shadowLevel2(RectangleShape).clipToBounds()) {
                val fullPanelPx = with(LocalDensity.current) { fullPanelWidth.roundToPx() }
                Inspector(state, model, thumbnails, Modifier.layout { measurable, constraints ->
                    val placeable = measurable.measure(Constraints.fixed(fullPanelPx, constraints.maxHeight))
                    layout(constraints.maxWidth, constraints.maxHeight) { placeable.place(0, 0) }
                }, openPlace = { plotId ->
                    model.clearNotice()
                    placePlot = plotId
                })
            }
        }
        // The fold tab rides on the panel's left edge and, once folded, stays alone at the screen edge to bring it back.
        // Drawn above the panel so the panel's shadow never falls across it.
        val tab: @Composable (Modifier) -> Unit = { modifier ->
            val edgeInset = if (panelWidth == 0.dp) Modifier.windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.End)) else Modifier
            PanelTab(panelOpen, modifier.zIndex(1f).then(edgeInset)) { panelOpen = !panelOpen }
        }

        Row(Modifier.fillMaxSize()) {
            Column(Modifier.weight(1f).fillMaxHeight().windowInsetsPadding(WindowInsets.safeDrawing).padding(Edge)) {
                SceneHeader(platformPanel, openSettings = { showSettings = true })
                Box(Modifier.weight(1f).fillMaxWidth()) {
                    renderError?.let { Toast(it, Modifier.align(Alignment.TopStart).padding(top = 16.dp)) }
                }
                if (state.message != null) Toast(state.message, Modifier.testTag("town.message"))
                else Text("건물을 눌러 고를 수 있어요", Modifier.testTag("town.message"), style = MaterialTheme.typography.bodyMedium, color = TownColors.Ink)
            }
            if (!compact) {
                tab(Modifier.align(Alignment.CenterVertically))
                panel(Modifier)
            }
        }
        if (compact) Row(Modifier.align(Alignment.CenterEnd).fillMaxHeight(), verticalAlignment = Alignment.CenterVertically) {
            tab(Modifier)
            panel(Modifier)
        }
    }
}

/**
 * Folds or unfolds the building panel: a slim tab, rounded on the left and open on the right where it meets the panel (or
 * the screen edge), with a chevron toward where the panel goes. The touch area is 64dp wide, the car-game minimum touch
 * target, though only the 36dp tab is drawn.
 */
@Composable
private fun PanelTab(open: Boolean, modifier: Modifier, onToggle: () -> Unit) {
    val label = if (open) "건물 목록 접기" else "건물 목록 펼치기"
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    Box(
        modifier.size(width = 64.dp, height = 112.dp).testTag("panel.toggle")
            .clickable(interaction, indication = null, role = Role.Button, onClick = onToggle)
            .semantics { contentDescription = label },
        contentAlignment = Alignment.CenterEnd,
    ) {
        Canvas(Modifier.size(width = 36.dp, height = 96.dp)) {
            val line = 1.dp.toPx()
            val inset = line / 2
            val radius = 18.dp.toPx()
            val w = size.width
            val h = size.height
            val outline = Path().apply {
                moveTo(w, inset)
                lineTo(radius, inset)
                arcTo(Rect(inset, inset, radius * 2, radius * 2), 270f, -90f, false)
                lineTo(inset, h - radius)
                arcTo(Rect(inset, h - radius * 2, radius * 2, h - inset), 180f, -90f, false)
                lineTo(w, h - inset)
            }
            drawPath(outline, if (pressed) TownColors.BlueTint else TownColors.Panel)
            drawPath(outline, TownColors.Line, style = Stroke(line))
            val cx = w / 2 + 1.dp.toPx()
            val cy = h / 2
            val dx = 4.dp.toPx()
            val dy = 8.dp.toPx()
            val chevron = Path().apply {
                if (open) { moveTo(cx - dx, cy - dy); lineTo(cx + dx, cy); lineTo(cx - dx, cy + dy) }
                else { moveTo(cx + dx, cy - dy); lineTo(cx - dx, cy); lineTo(cx + dx, cy + dy) }
            }
            drawPath(chevron, TownColors.Navy, style = Stroke(width = 3.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round))
        }
    }
}

@Composable
private fun SceneHeader(platformPanel: @Composable () -> Unit, openSettings: (() -> Unit)? = null) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("차곡마을", style = MaterialTheme.typography.headlineLarge, color = TownColors.Ink)
                if (openSettings != null) SettingsButton(openSettings)
            }
            Text("작은 집에서 시작하는 우리 동네", style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
        }
        platformPanel()
    }
}

@Composable
private fun Inspector(state: TownUiState, model: TownViewModel, thumbnails: Thumbnails, modifier: Modifier,
    openPlace: (String) -> Unit) {
    val town = state.town ?: return
    val plots = model.catalog.plots
    val selected = state.selection?.let { model.catalog.plot(it.plotId) }
    Surface(modifier, color = TownColors.Panel) {
        Column(Modifier.windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top))) {
            Row(Modifier.padding(start = Edge, end = Edge, top = 24.dp, bottom = 20.dp), verticalAlignment = Alignment.CenterVertically) {
                Stat("마을 조각", Modifier.weight(1f)) {
                    PieceIcon(26.dp)
                    Spacer(Modifier.width(10.dp))
                    Text(buildAnnotatedString {
                        append("${town.pieces}")
                        withStyle(SpanStyle(fontSize = 20.sp)) { append("개") }
                    }, Modifier.testTag("town.balance"), style = MaterialTheme.typography.displaySmall, color = TownColors.Navy)
                }
                Stat("마을 성장", Modifier.weight(1f)) {
                    Text(buildAnnotatedString {
                        append("${plots.sumOf { town.buildings[it.id] ?: 0 }}")
                        withStyle(SpanStyle(fontSize = 20.sp, color = TownColors.InkSecondary)) { append(" / ${plots.size * 3}") }
                    }, style = MaterialTheme.typography.displaySmall, color = TownColors.Navy)
                }
            }
            Hairline()
            Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                plots.forEachIndexed { index, plot ->
                    if (index > 0) Hairline(Modifier.padding(start = Edge + 104.dp))
                    val level = town.buildings[plot.id] ?: 0
                    PlotRow(plot, level, thumbnails[plot.id, maxOf(level, 1)], plot.id == selected?.id, enabled = !state.busy) { model.selectPlot(plot.id) }
                }
                Hairline()
            }
            Column(Modifier.fillMaxWidth().background(TownColors.LightSand).windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom + WindowInsetsSides.End))
                .padding(horizontal = Edge, vertical = 24.dp)) {
                if (selected == null) {
                    Text("건물을 골라 주세요", style = MaterialTheme.typography.titleMedium, color = TownColors.Ink)
                    Text("마을이나 목록에서 고르면 짓거나 키울 수 있어요.", style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
                } else {
                    val level = town.buildings[selected.id] ?: 0
                    NextStep(selected, level, thumbnails[selected.id, minOf(level + 1, 3)])
                    Spacer(Modifier.height(16.dp))
                    if (level < 3) AdvanceButton(level, selected.costs[level], town.pieces, state.busy) { model.advance(selected.id, level) }
                    else MaxLevelBadge()
                    // Linking a place is optional and never changes rewards; only built buildings can carry one.
                    if (level > 0) {
                        Spacer(Modifier.height(12.dp))
                        PlaceChip(state.places[selected.id], enabled = !state.busy) { openPlace(selected.id) }
                    }
                }
            }
        }
    }
}

@Composable
private fun Stat(label: String, modifier: Modifier, value: @Composable () -> Unit) {
    Column(modifier) {
        Text(label, style = MaterialTheme.typography.labelMedium, color = TownColors.InkSecondary)
        Row(verticalAlignment = Alignment.CenterVertically) { value() }
    }
}

@Composable
private fun PlotRow(plot: PlotDefinition, level: Int, thumbnail: ImageBitmap?, selected: Boolean, enabled: Boolean, onClick: () -> Unit) {
    Row(
        Modifier.testTag("plot.${plot.id}").fillMaxWidth().heightIn(min = 112.dp)
            .background(if (selected) TownColors.BlueTint else Color.Transparent)
            .drawBehind { if (selected) drawRect(TownColors.Navy, size = Size(5.dp.toPx(), size.height)) }
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = Edge, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // An empty lot shows its first building as a faded silhouette.
        Building(thumbnail, 88.dp, ghost = level == 0)
        Spacer(Modifier.width(16.dp))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(plot.name, style = MaterialTheme.typography.titleMedium, color = TownColors.Ink)
            LevelPips(level)
        }
        Text(if (level == 0) "빈 터" else "L$level", style = MaterialTheme.typography.titleMedium,
            color = if (level == 0) TownColors.InkSecondary else TownColors.Navy)
    }
}

@Composable
private fun NextStep(plot: PlotDefinition, level: Int, thumbnail: ImageBitmap?) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Building(thumbnail, 104.dp)
        Spacer(Modifier.width(16.dp))
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(when (level) { 0 -> "빈 터 → L1"; 3 -> "현재 L3"; else -> "L$level → L${level + 1}" }, Modifier.testTag("plot.level"),
                style = MaterialTheme.typography.labelMedium, color = TownColors.InkSecondary)
            Text(plot.name, style = MaterialTheme.typography.headlineSmall, color = TownColors.Ink)
            Text(Description[level], style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
        }
    }
}

@Composable
private fun AdvanceButton(level: Int, cost: Int, pieces: Int, busy: Boolean, advance: () -> Unit) {
    if (pieces < cost) Text("마을 조각이 ${cost - pieces}개 더 필요해요", Modifier.padding(bottom = 8.dp), style = MaterialTheme.typography.bodyMedium, color = TownColors.Warning)
    Button(
        onClick = advance, enabled = !busy && pieces >= cost,
        modifier = Modifier.fillMaxWidth().height(76.dp).testTag("build.advance"),
        shape = ActionShape,
        colors = ButtonDefaults.buttonColors(containerColor = TownColors.Navy, disabledContainerColor = TownColors.Disabled, disabledContentColor = TownColors.OnDisabled),
    ) {
        Text(if (busy) "저장하고 있어요…" else if (level == 0) "건설하기" else "L${level + 1}로 강화하기", Modifier.weight(1f), style = MaterialTheme.typography.labelLarge)
        PieceIcon(24.dp)
        Text(" $cost", style = MaterialTheme.typography.labelLarge)
    }
}

@Composable
private fun MaxLevelBadge() {
    Row(Modifier.fillMaxWidth().height(76.dp).background(TownColors.SuccessTint, ActionShape).padding(horizontal = 24.dp).testTag("build.max"),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        CheckMark(TownColors.Success)
        Text("최대 단계까지 자랐어요", style = MaterialTheme.typography.labelLarge, color = TownColors.Success)
    }
}

@Composable
private fun RestrictedNotice(access: PlayAccess) {
    Column(Modifier.fillMaxSize().testTag("play.restricted"), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Box(Modifier.size(88.dp).background(TownColors.Navy, RoundedCornerShape(22.dp)), contentAlignment = Alignment.Center) {
            Text("P", style = MaterialTheme.typography.displaySmall, color = Color.White)
        }
        Spacer(Modifier.height(28.dp))
        Text("잠시 마을을 쉬어 갈게요", style = MaterialTheme.typography.headlineMedium, color = TownColors.Ink)
        Spacer(Modifier.height(8.dp))
        Text(if (access == PlayAccess.Unknown) "차량의 게임 허용 상태를 확인할 수 없어요." else "게임을 이용할 수 있는 주차 상태에서 다시 만나요.",
            style = MaterialTheme.typography.bodyLarge, color = TownColors.Ink)
        Text("마지막으로 저장한 마을은 그대로 남아 있어요.", style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
    }
}

@Composable
private fun Toast(text: String, modifier: Modifier = Modifier) {
    Text(text, modifier.background(TownColors.Navy, RoundedCornerShape(14.dp)).padding(horizontal = 20.dp, vertical = 14.dp),
        style = MaterialTheme.typography.bodyMedium, color = Color.White)
}

@Composable
private fun Hairline(modifier: Modifier = Modifier) {
    Box(modifier.fillMaxWidth().height(1.dp).background(TownColors.Line))
}

@Composable
private fun LevelPips(level: Int) {
    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        repeat(3) { step -> Box(Modifier.size(width = 22.dp, height = 6.dp).background(if (step < level) TownColors.ActiveBlue else TownColors.Sand, CircleShape)) }
    }
}

private val Grayscale = ColorFilter.colorMatrix(ColorMatrix().apply { setToSaturation(0f) })

@Composable
private fun Building(image: ImageBitmap?, side: Dp, ghost: Boolean = false) {
    if (image == null) Box(Modifier.size(side))
    else Image(image, contentDescription = null, Modifier.size(side), alpha = if (ghost) .35f else 1f, colorFilter = if (ghost) Grayscale else null)
}

/**
 * UI thumbnails, rendered from the same runtime GLBs and mirroring their asset paths. Each is decoded the first time a row
 * shows it and then kept; plots that share a model share one bitmap.
 */
private class Thumbnails(private val assets: AssetManager, layout: TownLayout) {
    private val plots = layout.plots.associateBy { it.id }
    private val decoded = mutableMapOf<String, ImageBitmap?>()

    operator fun get(plotId: String, level: Int): ImageBitmap? {
        val plot = plots[plotId] ?: return null
        val path = "thumbnails/" + plot.modelPath(level).removePrefix("models/").removeSuffix(".glb") + ".png"
        return decoded.getOrPut(path) { runCatching { assets.open(path).use { BitmapFactory.decodeStream(it)?.asImageBitmap() } }.getOrNull() }
    }
}

@Composable
private fun rememberThumbnails(layout: TownLayout): Thumbnails {
    val assets = LocalContext.current.assets
    return remember(layout) { Thumbnails(assets, layout) }
}

@Composable
private fun CheckMark(color: Color) {
    Canvas(Modifier.size(28.dp)) {
        drawCircle(color)
        val w = size.width
        drawPath(Path().apply { moveTo(w * .28f, w * .52f); lineTo(w * .44f, w * .67f); lineTo(w * .73f, w * .36f) },
            Color.White, style = Stroke(width = w * .12f, cap = StrokeCap.Round))
    }
}

@Composable
private fun PieceIcon(side: Dp) {
    Canvas(Modifier.size(side)) {
        val w = size.width
        drawPath(Path().apply { moveTo(w / 2, 0f); lineTo(w, w * .28f); lineTo(w / 2, w * .56f); lineTo(0f, w * .28f); close() }, TownColors.PieceLight)
        drawPath(Path().apply { moveTo(0f, w * .28f); lineTo(w / 2, w * .56f); lineTo(w / 2, w); lineTo(0f, w * .72f); close() }, TownColors.Piece)
        drawPath(Path().apply { moveTo(w, w * .28f); lineTo(w / 2, w * .56f); lineTo(w / 2, w); lineTo(w, w * .72f); close() }, TownColors.PieceDeep)
    }
}
