package com.chagoktown.ui.town

import android.content.Context
import android.annotation.SuppressLint
import android.animation.ValueAnimator
import android.provider.Settings
import android.view.MotionEvent
import androidx.lifecycle.Lifecycle
import com.google.android.filament.Camera
import com.google.android.filament.LightManager
import com.google.android.filament.Skybox
import com.chagoktown.data.TownLayout
import com.chagoktown.game.TownState
import com.chagoktown.session.InteractionGate
import dev.romainguy.kotlin.math.Float3
import dev.romainguy.kotlin.math.cross
import dev.romainguy.kotlin.math.normalize
import io.github.sceneview.SceneView
import io.github.sceneview.math.Position
import io.github.sceneview.math.Rotation
import io.github.sceneview.math.Size
import io.github.sceneview.math.Scale
import io.github.sceneview.node.CubeNode
import io.github.sceneview.node.ModelNode
import io.github.sceneview.node.Node
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.math.cos
import kotlin.math.sin

// Counters read by instrumented tests to check scene lifecycle and resource release. Not an FPS meter or a product feature.
internal object SceneDiagnostics {
    val activeViews = AtomicInteger()
    val liveModels = AtomicInteger()
    val liveEnvironments = AtomicInteger()
    val frames = AtomicLong() // drawn frames only; an unchanged scene adds none
    val motionsStarted = AtomicLong()
    val buildFrames = AtomicLong()
    val shrinkFrames = AtomicLong()
    val growFrames = AtomicLong()
}

// Created by AndroidView with scene/session dependencies, never inflated from XML.
@SuppressLint("ViewConstructor")
class TownSceneView(
    context: Context,
    private val layout: TownLayout,
    private val gate: InteractionGate,
    lifecycle: Lifecycle,
    private val selectPlot: (String) -> Unit,
    private val reportError: (String) -> Unit,
) : SceneView(context = context, sharedLifecycle = lifecycle, cameraManipulator = null) {
    private val plotsById = layout.plots.associateBy { it.id }
    private val geometry = mutableListOf<CubeNode>()
    private val pads = mutableMapOf<String, CubeNode>()
    private val models = mutableMapOf<String, Pair<Int, ModelNode>>()
    private val plotNodes = mutableMapOf<Node, String>()
    private data class Motion(val previous: ModelNode?, val durationScale: Float, var started: Long? = null)
    private val motions = mutableMapOf<String, Motion>()
    private val roadNodes = mutableMapOf<String, ModelNode.RenderableNode>()
    private var lastLevels: Map<String, Int>? = null
    private var generation = gate.state.value.generation
    private var selectedId: String? = null
    private var environmentModel: ModelNode? = null
    private var cleaned = false
    // SceneView redraws the whole frame, shadow pass included, on every vsync even when nothing has moved. Draw only after a
    // change: the SurfaceView keeps showing the last frame, and the extra frames cover one that Filament skips to keep pace.
    private var framesToDraw = REDRAW_FRAMES
    private val normalPad = materialLoader.createColorInstance(0xFFDDD2AF.toInt(), roughness = 1f)
    private val selectedPad = materialLoader.createColorInstance(0xFFE9BB72.toInt(), roughness = 1f)
    private val backdrop = Skybox.Builder().color(.42f, .46f, .32f, 1f).build(engine)
    private var focusShiftX = 0f
    private var focusShiftY = 0f
    private val cameraTarget = layout.camera.target.let { Position(it[0], it[1], it[2]) }
    private val cameraOffset = layout.camera.offset.let { Position(it[0], it[1], it[2]) }
    private val cameraForward = normalize(-cameraOffset)
    private val cameraRight = normalize(cross(cameraForward, Float3(0f, 1f, 0f)))
    private val cameraUp = cross(cameraRight, cameraForward)

    init {
        SceneDiagnostics.activeViews.incrementAndGet()
        contentDescription = "차곡마을 3D 장면"
        aimCamera()
        mainLightNode?.let { light ->
            val color = light.color
            // Keep one owned light and the default 1024 map; a small metre bias avoids roof acne.
            LightManager.Builder(LightManager.Type.DIRECTIONAL)
                .color(color.r, color.g, color.b)
                .intensity(45_000f).direction(.45f, -.85f, -.26f).castShadows(true)
                .shadowOptions(LightManager.ShadowOptions().apply { constantBias = .006f; shadowFar = 90f })
                .build(engine, light.entity)
        }
        indirectLight?.intensity = 20_000f
        scene.skybox = backdrop
        view.setShadowingEnabled(true)
        try {
            environmentModel = ModelNode(modelLoader.createModelInstance(layout.environmentModel), autoAnimate = false).apply {
                // Ground and foliage must not intercept building/empty-lot selection.
                isHittable = false
                isTouchable = false
                nodes.forEach { it.isHittable = false; it.isTouchable = false }
                // Terrain/water/paths receive shadows; only the tree groups cast them.
                renderableNodes.forEach { it.isShadowCaster = it.name?.let { name -> name.contains("Leaf") || name.contains("Wood") } == true }
                layout.roads.forEach { road ->
                    roadNodes[road.node] = renderableNodes.single { it.name == road.node }.apply { isVisible = false }
                }
            }
            SceneDiagnostics.liveEnvironments.incrementAndGet()
        } catch (_: Exception) {
            reportError("마을 풍경을 불러오지 못했어요. 앱을 다시 열어 주세요.")
        }
        layout.plots.forEach { plot ->
            val angle = Math.toRadians(plot.rotationY.toDouble()).toFloat()
            val pad = CubeNode(engine, size = Size(plot.width, .04f, plot.depth), materialInstance = normalPad).apply {
                // Rotate the marker offset with the lot; keep the building's authored origin.
                position = Position(plot.x + cos(angle) * plot.padOffsetX + sin(angle) * plot.padOffsetZ,
                    plot.y + .025f, plot.z - sin(angle) * plot.padOffsetX + cos(angle) * plot.padOffsetZ)
                rotation = Rotation(y = plot.rotationY)
                isShadowCaster = false
                isVisible = false
                isHittable = false
            }
            geometry += pad
            pads[plot.id] = pad
            plotNodes[pad] = plot.id
        }
        childNodes = listOfNotNull(environmentModel) + geometry
        onTouchEvent = { event, hit ->
            if (event.actionMasked == MotionEvent.ACTION_UP && gate.state.value.playable) {
                var node = hit?.node
                while (node != null && node !in plotNodes) node = node.parent
                node?.let { plotNodes[it] }?.let(selectPlot)
            }
            true
        }
    }

    /** Moves the town's on-screen centre by the given pixels, e.g. away from panels floating over the scene. */
    fun setFocusShift(xPx: Float, yPx: Float) {
        if (xPx == focusShiftX && yPx == focusShiftY) return
        focusShiftX = xPx
        focusShiftY = yPx
        aimCamera()
    }

    override fun onResized(width: Int, height: Int) {
        super.onResized(width, height)
        // Also called for each new surface, e.g. on return from the background, and a new surface starts empty.
        requestRender()
        aimCamera()
    }

    private fun requestRender() {
        framesToDraw = REDRAW_FRAMES
    }

    // The diorama is drawn with an orthographic projection. Keep picking and panel focus in the same camera.
    private fun aimCamera() {
        if (height <= 0 || width <= 0) return
        val availableWidth = (width - 2f * kotlin.math.abs(focusShiftX)).coerceAtLeast(width * .25f)
        val span = maxOf(layout.camera.verticalSpan, 40f * height / availableWidth)
        val unitsPerPx = span / height
        val halfHeight = span / 2.0
        val halfWidth = halfHeight * width / height
        cameraNode.camera.setProjection(Camera.Projection.ORTHO, -halfWidth, halfWidth, -halfHeight, halfHeight, .1, 200.0)
        val shift = cameraRight * (-focusShiftX * unitsPerPx) + cameraUp * (focusShiftY * unitsPerPx)
        cameraNode.position = cameraTarget + cameraOffset + shift
        cameraNode.lookAt(cameraTarget + shift)
        requestRender()
    }

    private fun releaseBuilding(node: ModelNode) {
        childNodes = childNodes - node
        plotNodes.remove(node)
        modelLoader.destroyModel(node.model)
        SceneDiagnostics.liveModels.decrementAndGet()
    }

    private fun settle(plotId: String) {
        motions.remove(plotId)?.previous?.let(::releaseBuilding)
        models[plotId]?.second?.let { node ->
            val plot = plotsById.getValue(plotId)
            node.scale = Scale(1f)
            node.position = Position(plot.x, plot.y, plot.z)
            node.rotation = Rotation(y = plot.rotationY)
            node.isVisible = true
        }
    }

    private fun removeBuilding(plotId: String) {
        settle(plotId)
        models.remove(plotId)?.second?.let { previous ->
            releaseBuilding(previous)
        }
    }

    internal fun displayedLevels(): Map<String, Int> = models.mapValues { it.value.first }
    internal fun visibleRoads(): Set<String> = roadNodes.filterValues { it.isVisible }.keys
    internal fun visiblePads(): Set<String> = pads.filterValues { it.isVisible }.keys
    internal fun animatingPlots(): Set<String> = motions.keys.toSet()
    internal fun buildingTransform(plotId: String): Pair<Position, Scale>? = models[plotId]?.second?.let { it.position to it.scale }

    private fun updatePads() {
        pads.forEach { (id, pad) ->
            // Empty plots are selected from the inspector. Only a built selection or a brief build pad is shown.
            pad.isVisible = id in models && (id == selectedId || motions[id]?.previous == null && id in motions)
            pad.materialInstance = if (id == selectedId) selectedPad else normalPad
        }
    }

    fun showTown(town: TownState, selected: String?) {
        if (cleaned) return
        val access = gate.state.value
        // AndroidView calls this on every recomposition, i.e. every frame while the panel slides. The same levels in the same
        // gate generation need no model work, and a failed load is retried only when the town or the gate changes.
        if (town.buildings == lastLevels && access.generation == generation) {
            if (selected != selectedId) {
                selectedId = selected
                updatePads()
                requestRender()
            }
            return
        }
        val durationScale = Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
        val animate = lastLevels != null && generation == access.generation && access.playable && ValueAnimator.areAnimatorsEnabled() && durationScale > 0f
        if (!animate) motions.keys.toList().forEach(::settle)
        selectedId = selected
        layout.plots.forEach { plot ->
            val level = town.buildings[plot.id] ?: 0
            val old = models[plot.id]
            if (level > 0 && level != old?.first) {
                try {
                    // Keep metre scale, node transforms and root; never normalize building heights.
                    val next = ModelNode(modelLoader.createModelInstance(plot.modelPath(level)), autoAnimate = false).apply {
                        position = Position(plot.x, plot.y, plot.z)
                        rotation = Rotation(y = plot.rotationY)
                        isEditable = false
                    }
                    // Load before touching the old model. A failed load leaves the complete old building intact.
                    settle(plot.id)
                    val previous = models[plot.id]?.second
                    models[plot.id] = level to next
                    plotNodes[next] = plot.id
                    childNodes = childNodes + next
                    SceneDiagnostics.liveModels.incrementAndGet()
                    if (animate && level > (lastLevels?.get(plot.id) ?: 0)) {
                        motions[plot.id] = Motion(previous, durationScale)
                        next.isVisible = false
                        SceneDiagnostics.motionsStarted.incrementAndGet()
                    } else previous?.let(::releaseBuilding)
                } catch (_: Exception) {
                    reportError("건물 모델을 불러오지 못했어요. 저장된 마을은 유지돼요. 앱을 다시 열어 주세요.")
                }
            }
            if (level == 0) removeBuilding(plot.id)
        }
        layout.roads.forEach { road -> roadNodes[road.node]?.isVisible = road.isVisible(town.buildings) }
        lastLevels = town.buildings.toMap()
        generation = access.generation
        updatePads()
        requestRender()
    }

    override fun onFrame(frameTimeNanos: Long) {
        val access = gate.state.value
        if (!access.playable || cleaned) return
        if (motions.isNotEmpty() && (generation != access.generation || !ValueAnimator.areAnimatorsEnabled())) {
            motions.keys.toList().forEach(::settle)
            updatePads()
            requestRender()
        }
        if (motions.isNotEmpty()) motions.toMap().forEach { (id, motion) ->
            // Every moving frame is drawn, and the extra frames then show where the motion settled.
            requestRender()
            val next = models.getValue(id).second
            // Start on a renderable frame, so loading/layout work cannot consume the animation beforehand.
            if (!uiHelper.isReadyToRender) return@forEach
            val start = motion.started ?: frameTimeNanos.also { motion.started = it }
            val seconds = ((frameTimeNanos - start).coerceAtLeast(0) / 1_000_000_000f) / motion.durationScale
            val upgrade = motion.previous != null
            val duration = if (upgrade) BuildingMotion.UPGRADE_SECONDS else BuildingMotion.BUILD_SECONDS
            if (seconds >= duration) {
                settle(id)
                updatePads()
            } else {
                val shrinking = upgrade && seconds < BuildingMotion.SWAP_SECONDS
                val shown = if (shrinking) checkNotNull(motion.previous) else next
                motion.previous?.isVisible = shrinking
                next.isVisible = !shrinking && (upgrade || seconds >= .10f)
                val factor = BuildingMotion.scale(seconds, upgrade)
                shown.scale = Scale(factor)
                // Keep the authored bottom on its original ground plane, including a slightly negative footing.
                val plot = plotsById.getValue(id)
                val bottom = shown.center.y - shown.halfExtent.y
                shown.position = Position(plot.x, plot.y + bottom * (1f - factor), plot.z)
                if (shown.isVisible && factor in .09f.. .995f) {
                    when {
                        !upgrade -> SceneDiagnostics.buildFrames.incrementAndGet()
                        shrinking -> SceneDiagnostics.shrinkFrames.incrementAndGet()
                        else -> SceneDiagnostics.growFrames.incrementAndGet()
                    }
                }
            }
        }
        if (framesToDraw == 0) return
        super.onFrame(frameTimeNanos)
        if (uiHelper.isReadyToRender) {
            framesToDraw--
            SceneDiagnostics.frames.incrementAndGet()
        }
    }

    override fun destroy() {
        if (!cleaned) {
            motions.keys.toList().forEach(::settle)
            cleaned = true
            childNodes = emptyList()
            plotNodes.clear()
            models.values.forEach { (_, node) -> modelLoader.destroyModel(node.model) }
            SceneDiagnostics.liveModels.addAndGet(-models.size)
            models.clear()
            environmentModel?.let {
                modelLoader.destroyModel(it.model)
                SceneDiagnostics.liveEnvironments.decrementAndGet()
            }
            environmentModel = null
            roadNodes.clear()
            geometry.forEach { it.destroy() }
            geometry.clear()
            scene.skybox = null
            engine.destroySkybox(backdrop)
            SceneDiagnostics.activeViews.decrementAndGet()
        }
        // Stops Choreographer, detaches swapchain and releases owned loaders/engine.
        super.destroy()
    }

    private companion object {
        const val REDRAW_FRAMES = 3
    }
}
