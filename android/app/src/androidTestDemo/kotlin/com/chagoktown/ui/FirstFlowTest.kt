package com.chagoktown.ui

import android.content.Context
import android.graphics.BitmapFactory
import android.os.ParcelFileDescriptor
import android.view.View
import android.view.ViewGroup
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.assertTextContains
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.performTextInput
import com.chagoktown.data.local.PlaceKind
import kotlinx.coroutines.flow.first
import androidx.compose.ui.test.assertIsOn
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTouchInput
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.room.withTransaction
import com.chagoktown.bootstrap.TownApplication
import com.chagoktown.data.local.BuildingEntity
import com.chagoktown.game.BuildCommand
import com.chagoktown.data.WriteResult
import com.chagoktown.platform.DemoVehicleGateway
import com.chagoktown.ui.town.SceneDiagnostics
import com.chagoktown.ui.town.TownSceneView
import io.github.sceneview.collision.Vector3
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.ExternalResource
import org.junit.rules.RuleChain
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class FirstFlowTest {
    private val compose = createAndroidComposeRule<MainActivity>()
    private val cleanDemoDatabase = object : ExternalResource() {
        override fun before() {
            val context = ApplicationProvider.getApplicationContext<Context>()
            context.deleteDatabase("town.db")
            context.getSharedPreferences(DemoVehicleGateway.PREFS, Context.MODE_PRIVATE).edit().clear().commit()
        }
    }
    @get:Rule val rules: RuleChain = RuleChain.outerRule(cleanDemoDatabase).around(compose)

    private fun findScene(view: View): TownSceneView? = when (view) {
        is TownSceneView -> view
        is ViewGroup -> (0 until view.childCount).firstNotNullOfOrNull { findScene(view.getChildAt(it)) }
        else -> null
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        Thread.sleep(700)
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        repeat(100) {
            val bitmap = instrumentation.uiAutomation.takeScreenshot()
            // A submitted frame is not proof that Filament's surface has reached the display yet.
            val rendered = bitmap != null && (bitmap.getPixel(420, 400) and 0x0000ff00) != 0
            bitmap?.recycle()
            if (rendered) {
                ParcelFileDescriptor.AutoCloseInputStream(instrumentation.uiAutomation.executeShellCommand(
                    "screencap -p /data/local/tmp/chagok-$name"
                )).use { it.readBytes() }
                return
            }
            Thread.sleep(100)
        }
        error("The town surface did not render before capture: $name")
    }

    @Test fun constructUpgradePickThreeDimensionalModelAndStopFramesOnRestriction() {
        val container = (compose.activity.application as TownApplication).container
        compose.waitUntil(30_000) { SceneDiagnostics.liveModels.get() == 1 && SceneDiagnostics.frames.get() > 2 }
        assertEquals(1, SceneDiagnostics.liveEnvironments.get())
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            assertTrue(scene.visiblePads().isEmpty())
            assertEquals(container.layout.roads.filter { it.isVisible(mapOf("home" to 1)) }.map { it.node }.toSet(), scene.visibleRoads())
            assertTrue(scene.visibleRoads().size < container.layout.roads.size)
            assertTrue(scene.animatingPlots().isEmpty())
        }
        val startedOnLoad = SceneDiagnostics.motionsStarted.get()
        capture("season1-initial.png")
        // Nothing moves now: the scene keeps its last frame instead of redrawing on every vsync.
        val idleFrames = SceneDiagnostics.frames.get()
        Thread.sleep(500)
        assertEquals("unchanged scene was redrawn", idleFrames, SceneDiagnostics.frames.get())
        compose.onNodeWithTag("town.balance").assertTextContains("3개", substring = true)
        var point = Offset.Zero
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            val home = container.layout.plots.single { it.id == "home" }
            @Suppress("DEPRECATION")
            val projected = scene.cameraNode.worldToScreenPoint(Vector3(home.x, home.y + 1.5f, home.z + 1f))
            point = Offset(projected.x, projected.y)
        }
        // Real ray/collider picking, not a Compose button substituting for the scene.
        compose.onNodeWithTag("town.scene").performTouchInput { click(point) }
        compose.onNodeWithTag("plot.level").assertTextContains("L1", substring = true)
        // The selection pad is a scene change, so it is drawn.
        compose.waitUntil(5_000) { SceneDiagnostics.frames.get() > idleFrames }
        // Home L2 costs exactly the three starting pieces, so the first upgrade is available right away.
        compose.onNodeWithTag("build.advance").assertIsEnabled()
        // Selecting and abandoning an empty plot must not reveal its pad, roads or a model.
        compose.onNodeWithTag("plot.cafe").performClick()
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            assertTrue(scene.visiblePads().isEmpty())
            assertFalse("cafe" in scene.displayedLevels())
        }
        assertEquals(startedOnLoad, SceneDiagnostics.motionsStarted.get())
        // Abort a real Room write through the UI: no animation or road can precede commit.
        container.database.openHelper.writableDatabase.execSQL("CREATE TRIGGER fail_animation_save BEFORE UPDATE ON town_state BEGIN SELECT RAISE(ABORT, 'animation test failure'); END")
        compose.onNodeWithTag("build.advance").performClick()
        waitForText("저장하지 못했어요")
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            assertEquals(mapOf("home" to 1), scene.displayedLevels())
            assertTrue(scene.visiblePads().isEmpty())
            assertEquals(container.layout.roads.filter { it.isVisible(mapOf("home" to 1)) }.map { it.node }.toSet(), scene.visibleRoads())
        }
        assertEquals(startedOnLoad, SceneDiagnostics.motionsStarted.get())
        container.database.openHelper.writableDatabase.execSQL("DROP TRIGGER fail_animation_save")
        compose.onNodeWithTag("demo.pieces").performClick()
        compose.waitUntil(10_000) { runBlocking { container.repository.snapshot()?.pieces == 63 } }

        var recording: ParcelFileDescriptor? = null
        listOf("cafe", "home", "cathedral").forEach { id ->
            compose.onNodeWithTag("plot.$id").performScrollTo().performClick()
            if (id == "cafe") {
                recording = InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommand(
                    "screenrecord --time-limit 12 /data/local/tmp/chagok-construction.mp4")
                Thread.sleep(1000)
            }
            var level = if (id == "home") 1 else 0
            while (level < 3) {
                val startedBefore = SceneDiagnostics.motionsStarted.get()
                val buildBefore = SceneDiagnostics.buildFrames.get()
                val shrinkBefore = SceneDiagnostics.shrinkFrames.get()
                val growBefore = SceneDiagnostics.growFrames.get()
                compose.onNodeWithTag("build.advance").performClick()
                level++
                val expected = level
                compose.waitUntil(15_000) { runBlocking { container.repository.snapshot()?.buildings?.get(id) == expected } }
                compose.onNodeWithTag("plot.level").assertTextContains("L$level", substring = true)
                if (id == "cafe") {
                    var moving = false
                    // Check recorded native frames: Compose synchronization may finish after a short motion.
                    compose.waitUntil(5_000) {
                        SceneDiagnostics.motionsStarted.get() == startedBefore + 1
                    }
                    compose.waitUntil(5_000) {
                        compose.runOnIdle { moving = id in checkNotNull(findScene(compose.activity.window.decorView)).animatingPlots() }
                        !moving
                    }
                    if (level == 1) assertTrue("construction intermediate frames", SceneDiagnostics.buildFrames.get() > buildBefore)
                    else {
                        assertTrue("old model shrink frames", SceneDiagnostics.shrinkFrames.get() > shrinkBefore)
                        assertTrue("new model growth frames", SceneDiagnostics.growFrames.get() > growBefore)
                    }
                    println("cafe L$level native motion frames: build=${SceneDiagnostics.buildFrames.get()-buildBefore}, shrink=${SceneDiagnostics.shrinkFrames.get()-shrinkBefore}, grow=${SceneDiagnostics.growFrames.get()-growBefore}")
                    compose.runOnIdle {
                        val scene = checkNotNull(findScene(compose.activity.window.decorView))
                        val plot = container.layout.plots.single { it.id == id }
                        val (position, scale) = checkNotNull(scene.buildingTransform(id))
                        assertEquals(plot.x, position.x, 0f)
                        assertEquals(plot.y, position.y, 0f)
                        assertEquals(plot.z, position.z, 0f)
                        assertEquals(1f, scale.x, 0f)
                        assertEquals(1f, scale.y, 0f)
                        assertEquals(1f, scale.z, 0f)
                    }
                    capture("construction-cafe-l$level.png")
                }
            }
            compose.onNodeWithTag("build.max").assertExists()
            compose.onNodeWithTag("build.advance").assertDoesNotExist()
        }
        compose.waitUntil(10_000) { SceneDiagnostics.liveModels.get() == 3 }
        recording?.let { ParcelFileDescriptor.AutoCloseInputStream(it).use { stream -> stream.readBytes() } }
        compose.onNodeWithTag("town.balance").assertTextContains("21개", substring = true)
        val saved = runBlocking { container.repository.snapshot() }
        val beforeReturn = SceneDiagnostics.motionsStarted.get()

        repeat(2) {
            compose.onNodeWithTag("demo.restriction").performClick()
            compose.onNodeWithTag("play.restricted").assertExists()
            compose.waitUntil(10_000) { SceneDiagnostics.activeViews.get() == 0 && SceneDiagnostics.liveModels.get() == 0 }
            assertEquals(0, SceneDiagnostics.liveEnvironments.get())
            val stopped = SceneDiagnostics.frames.get()
            Thread.sleep(300)
            assertEquals(stopped, SceneDiagnostics.frames.get())
            compose.onNodeWithTag("demo.restriction").performClick()
            compose.waitUntil(20_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 3 && SceneDiagnostics.frames.get() > stopped }
        }
        compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
        val backgroundFrames = SceneDiagnostics.frames.get()
        Thread.sleep(300)
        assertEquals(backgroundFrames, SceneDiagnostics.frames.get())
        compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
        repeat(2) {
            compose.activityRule.scenario.recreate()
            compose.waitUntil(20_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 3 }
            assertEquals(saved, runBlocking { container.repository.snapshot() })
        }
        compose.onNodeWithTag("town.balance").assertTextContains("21개", substring = true)
        assertEquals(beforeReturn, SceneDiagnostics.motionsStarted.get())
        verifyVirtualCommute()
        verifyPlaceLinks()
        verifyPanelFold()
        verifySeasonMapStagesAndThumbnails()
    }

    // The building panel folds away for a full view of the town; picking a building in the scene brings it back.
    private fun verifyPanelFold() {
        val container = (compose.activity.application as TownApplication).container
        fun panelShown() = compose.onAllNodesWithTag("plot.home").fetchSemanticsNodes().isNotEmpty()
        assertTrue(panelShown())
        compose.onNodeWithTag("panel.toggle").performClick()
        compose.waitUntil(5_000) { !panelShown() }
        compose.onNodeWithTag("town.scene").assertExists()
        capture("panel-folded.png")

        compose.waitForIdle()
        var point = Offset.Zero
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            val home = container.layout.plots.single { it.id == "home" }
            @Suppress("DEPRECATION")
            val projected = scene.cameraNode.worldToScreenPoint(Vector3(home.x, home.y + 1.5f, home.z + 1f))
            point = Offset(projected.x, projected.y)
        }
        compose.onNodeWithTag("town.scene").performTouchInput { click(point) }
        compose.waitUntil(5_000) { panelShown() }
        compose.onNodeWithTag("plot.level").assertExists()

        // The same building tapped again while folded still brings the panel back.
        compose.onNodeWithTag("panel.toggle").performClick()
        compose.waitUntil(5_000) { !panelShown() }
        compose.waitForIdle()
        compose.onNodeWithTag("town.scene").performTouchInput { click(point) }
        compose.waitUntil(5_000) { panelShown() }
    }

    // Place links through the real screen. home and cafe are built by now; places are synthetic demo spots.
    private fun verifyPlaceLinks() {
        val container = (compose.activity.application as TownApplication).container
        fun places() = runBlocking { container.repository.places.first() }
        fun openPlace(plotId: String) {
            compose.onNodeWithTag("plot.$plotId").performScrollTo().performClick()
            compose.onNodeWithTag("place.open").performClick()
            compose.onNodeWithTag("place.dialog").assertExists()
        }
        fun setLocation(on: Boolean) {
            compose.onNodeWithTag("settings.open").performClick()
            compose.onNodeWithTag("privacy.location").performScrollTo().performClick()
            compose.waitUntil(10_000) { runBlocking { container.repository.privacySnapshot().locationConsent == on } }
            compose.onNodeWithTag("settings.close").performScrollTo().performClick()
        }
        assertTrue(places().isEmpty())

        // A typed alias, no location. It is sealed and stays folded until asked for.
        openPlace("home")
        compose.onNodeWithTag("place.link").assertIsNotEnabled()
        compose.onNodeWithTag("place.alias.input").performScrollTo().performTextInput("단골 빵집 앞")
        compose.onNodeWithTag("place.save").performScrollTo().performClick()
        compose.waitUntil(10_000) { places() == mapOf("home" to PlaceKind.MANUAL) }
        compose.onNodeWithTag("place.alias").assertTextContains("접혀 있어요", substring = true)
        val sealed = runBlocking { container.database.townDao().placeLink("home")!!.sealedAlias }
        assertFalse(String(sealed, Charsets.ISO_8859_1).contains("빵집"))
        assertFalse(String(sealed, Charsets.UTF_8).contains("빵집"))
        compose.onNodeWithTag("place.reveal").performScrollTo().performClick()
        compose.waitUntil(10_000) { runCatching { compose.onNodeWithTag("place.alias").assertTextContains("단골 빵집 앞") }.isSuccess }
        capture("place-dialog.png")

        // A restriction closes the dialog and forgets the shown alias.
        val demo = container.gateway as DemoVehicleGateway
        compose.runOnUiThread { demo.setRestricted(true) }
        compose.onNodeWithTag("play.restricted").assertExists()
        compose.onNodeWithTag("place.dialog").assertDoesNotExist()
        compose.runOnUiThread { demo.setRestricted(false) }
        compose.waitUntil(20_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 3 }
        openPlace("home")
        compose.onNodeWithTag("place.alias").assertTextContains("접혀 있어요", substring = true)
        compose.onNodeWithTag("place.close").performScrollTo().performClick()

        // With location on, the parked spot is linked to a second building.
        setLocation(on = true)
        openPlace("cafe")
        compose.onNodeWithTag("place.alias.input").performScrollTo().performTextInput("회사 앞")
        compose.onNodeWithTag("place.link").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(10_000) { places()["cafe"] == PlaceKind.LOCATION }
        waitForText("지금 주차한 곳을 이 건물과 연결했어요")
        compose.onNodeWithTag("place.close").performScrollTo().performClick()
        compose.onNodeWithTag("place.open").assertTextContains("주차한 곳과 연결됨", substring = true)

        // Withdrawing location deletes only the location link; the typed alias and every building stay.
        val town = runBlocking { container.repository.snapshot() }
        setLocation(on = false)
        compose.waitUntil(10_000) { places() == mapOf("home" to PlaceKind.MANUAL) }
        assertEquals(town, runBlocking { container.repository.snapshot() })

        // Deleting every place record asks once more, then keeps the town.
        compose.onNodeWithTag("settings.open").performClick()
        compose.onNodeWithTag("privacy.places.delete").performScrollTo().performClick()
        compose.onNodeWithTag("privacy.places.confirm").performScrollTo().performClick()
        compose.waitUntil(10_000) { places().isEmpty() }
        compose.onNodeWithTag("settings.close").performScrollTo().performClick()
        assertEquals(town, runBlocking { container.repository.snapshot() })
    }

    private fun waitForText(text: String) = compose.waitUntil(10_000) { compose.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty() }

    // Vehicle data starts off, so earlier resumes read nothing and pieces so far come from the demo grant alone.
    private fun verifyVirtualCommute() {
        val container = (compose.activity.application as TownApplication).container
        val motionsBeforeReward = SceneDiagnostics.motionsStarted.get()
        fun town() = runBlocking { checkNotNull(container.repository.snapshot()) }
        fun baselineStored() = runBlocking { container.database.townDao().mobility() != null }
        assertEquals(0, town().rewardCount)

        compose.onNodeWithTag("demo.commute").performClick()
        waitForText("차량 정보 사용이 꺼져 있어")
        assertFalse(baselineStored())
        // Turning vehicle data on only sets a baseline from the current fake odometer.
        setVehicleData(on = true)
        compose.waitUntil(10_000) { baselineStored() }
        capture("privacy-settings.png")
        compose.onNodeWithTag("settings.close").performScrollTo().performClick()
        waitForText("이동 확인을 시작했어요")
        assertEquals(0, town().rewardCount)

        compose.onNodeWithTag("demo.commute").performClick()
        compose.waitUntil(10_000) { town().rewardCount == 1 }
        waitForText("마을 조각 3개를 받았어요")
        compose.onNodeWithTag("town.balance").assertTextContains("24개", substring = true)

        compose.onNodeWithTag("demo.commute").performClick()
        waitForText("이미 받았어요")
        assertEquals(24, town().pieces)

        compose.onNodeWithTag("demo.next_day").performClick()
        waitForText("새로 확인된 이동이 없어요")
        assertEquals(24, town().pieces)

        compose.onNodeWithTag("demo.commute").performClick()
        compose.waitUntil(10_000) { town().rewardCount == 2 }
        compose.onNodeWithTag("town.balance").assertTextContains("27개", substring = true)
        compose.onNodeWithTag("demo.drive").assertTextContains("이동 보상 2회", substring = true)
        capture("reward-demo.png")

        // The drive happens while restricted; the reward arrives with the automatic check on return to parking.
        compose.onNodeWithTag("demo.restriction").performClick()
        compose.onNodeWithTag("play.restricted").assertExists()
        compose.onNodeWithTag("demo.next_day").performClick()
        compose.onNodeWithTag("demo.commute").performClick()
        Thread.sleep(500)
        assertEquals(2, town().rewardCount)
        compose.onNodeWithTag("demo.restriction").performClick()
        compose.waitUntil(10_000) { town().rewardCount == 3 }
        waitForText("마을 조각 3개를 받았어요")
        compose.onNodeWithTag("town.balance").assertTextContains("30개", substring = true)

        // Reopening re-reads the same fake odometer: the automatic check pays nothing more.
        val rewarded = town()
        compose.activityRule.scenario.recreate()
        compose.waitUntil(20_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 3 }
        compose.waitForIdle()
        assertEquals(rewarded, town())
        assertEquals(motionsBeforeReward, SceneDiagnostics.motionsStarted.get())

        // Settings never stay open across a restriction.
        val demo = container.gateway as DemoVehicleGateway
        compose.onNodeWithTag("settings.open").performClick()
        compose.onNodeWithTag("settings.dialog").assertExists()
        compose.runOnUiThread { demo.setRestricted(true) }
        compose.onNodeWithTag("play.restricted").assertExists()
        compose.onNodeWithTag("settings.dialog").assertDoesNotExist()
        compose.runOnUiThread { demo.setRestricted(false) }
        compose.waitUntil(20_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 3 }
        compose.onNodeWithTag("settings.dialog").assertDoesNotExist()

        // Withdrawal deletes the baseline and keeps every reward; a drive while off is never read.
        setVehicleData(on = false)
        compose.waitUntil(10_000) { !baselineStored() && runBlocking { !container.repository.privacySnapshot().vehicleConsent } }
        compose.onNodeWithTag("settings.close").performScrollTo().performClick()
        compose.onNodeWithTag("demo.next_day").performClick()
        compose.onNodeWithTag("demo.commute").performClick()
        waitForText("차량 정보 사용이 꺼져 있어")
        assertFalse(baselineStored())
        assertEquals(rewarded, town())
        // Re-consent starts over from the current odometer: the distance driven while off is not paid.
        setVehicleData(on = true)
        compose.waitUntil(10_000) { baselineStored() }
        compose.onNodeWithTag("settings.close").performScrollTo().performClick()
        waitForText("이동 확인을 시작했어요")
        assertEquals(rewarded, town())

        // Days without a reward, including those with vehicle data off, are paid together on the next one (up to a week).
        compose.onNodeWithTag("demo.next_day").performClick()
        compose.onNodeWithTag("demo.next_day").performClick()
        waitForText("새로 확인된 이동이 없어요")
        compose.onNodeWithTag("demo.commute").performClick()
        compose.waitUntil(10_000) { town().rewardCount == 4 }
        waitForText("마을 조각 9개를 받았어요")
        assertEquals(rewarded.pieces + 9, town().pieces)
        compose.onNodeWithTag("demo.commute").performClick()
        waitForText("이미 받았어요")
        assertEquals(rewarded.pieces + 9, town().pieces)
    }

    private fun setVehicleData(on: Boolean) {
        compose.onNodeWithTag("settings.open").performClick()
        val row = compose.onNodeWithTag("privacy.vehicle")
        if (on) row.assertIsOff() else row.assertIsOn()
        row.performScrollTo().performClick()
        compose.waitUntil(10_000) {
            runCatching { if (on) row.assertIsOn() else row.assertIsOff() }.isSuccess
        }
    }

    private fun awaitMotion(id: String, active: Boolean) {
        var found = false
        compose.waitUntil(10_000) {
            compose.runOnIdle { found = id in checkNotNull(findScene(compose.activity.window.decorView)).animatingPlots() }
            found == active
        }
    }

    private fun verifyInterruptedMotions() {
        val container = (compose.activity.application as TownApplication).container
        fun advance(id: String, before: Int) = runBlocking {
            container.repository.execute(BuildCommand(id, before), checkNotNull(container.gate.token()))
        }
        assertEquals(WriteResult.Saved, advance("bakery", 0))
        awaitMotion("bakery", true)
        assertEquals(WriteResult.Saved, advance("bakery", 1))
        assertTrue(advance("bakery", 1) is WriteResult.Rejected)
        compose.onNodeWithTag("demo.restriction").performClick()
        compose.waitUntil(10_000) { SceneDiagnostics.liveModels.get() == 0 && SceneDiagnostics.liveEnvironments.get() == 0 }
        val startedBeforeReturn = SceneDiagnostics.motionsStarted.get()
        compose.onNodeWithTag("demo.restriction").performClick()
        compose.waitUntil(15_000) { SceneDiagnostics.liveModels.get() == 4 }
        assertEquals(startedBeforeReturn, SceneDiagnostics.motionsStarted.get())
        compose.runOnIdle {
            val scene = checkNotNull(findScene(compose.activity.window.decorView))
            assertEquals(2, scene.displayedLevels()["bakery"])
            assertTrue(scene.animatingPlots().isEmpty())
        }

        assertEquals(WriteResult.Saved, advance("bookshop", 0))
        awaitMotion("bookshop", true)
        compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
        compose.waitUntil(10_000) { SceneDiagnostics.activeViews.get() == 0 }
        val beforeBackgroundReturn = SceneDiagnostics.motionsStarted.get()
        compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
        compose.waitUntil(15_000) { SceneDiagnostics.liveModels.get() == 5 }
        assertEquals(beforeBackgroundReturn, SceneDiagnostics.motionsStarted.get())

        assertEquals(WriteResult.Saved, advance("florist", 0))
        awaitMotion("florist", true)
        val beforeRecreate = SceneDiagnostics.motionsStarted.get()
        compose.activityRule.scenario.recreate()
        compose.waitUntil(15_000) { SceneDiagnostics.liveModels.get() == 6 && SceneDiagnostics.activeViews.get() == 1 }
        assertEquals(beforeRecreate, SceneDiagnostics.motionsStarted.get())

        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        fun shell(command: String) = ParcelFileDescriptor.AutoCloseInputStream(automation.executeShellCommand(command)).use { it.readBytes().toString(Charsets.UTF_8).trim() }
        val setting = shell("settings get global animator_duration_scale")
        try {
            shell("settings put global animator_duration_scale 0")
            val beforeDisabled = SceneDiagnostics.motionsStarted.get()
            assertEquals(WriteResult.Saved, advance("grocer", 0))
            compose.waitUntil(15_000) { SceneDiagnostics.liveModels.get() == 7 }
            assertEquals(beforeDisabled, SceneDiagnostics.motionsStarted.get())
            awaitMotion("grocer", false)
        } finally {
            // Deleting this setting did not restore animations on this API 36 AVD.
            // Restore the effective default explicitly for the following run.
            shell("settings put global animator_duration_scale ${setting.toFloatOrNull() ?: 1f}")
        }

        // A real failed asset load keeps the complete prior model and releases all temporary scene resources.
        compose.runOnIdle {
            val home = container.layout.plots.single { it.id == "home" }
            val invalid = container.layout.copy(plots = listOf(home.copy(models = listOf(home.models[0], "missing-animation-test.glb", home.models[2]))))
            var error: String? = null
            val scene = TownSceneView(compose.activity, invalid, container.gate, compose.activity.lifecycle, {}) { error = it }
            try {
                val saved = runBlocking { checkNotNull(container.repository.snapshot()) }
                scene.showTown(saved.copy(buildings = mapOf("home" to 1)), null)
                val original = scene.buildingTransform("home")
                scene.showTown(saved.copy(buildings = mapOf("home" to 2)), null)
                assertNotNull(error)
                assertEquals(mapOf("home" to 1), scene.displayedLevels())
                assertEquals(original, scene.buildingTransform("home"))
                assertTrue(scene.animatingPlots().isEmpty())
            } finally { scene.destroy() }
        }
        assertEquals(1, SceneDiagnostics.activeViews.get())
        assertEquals(1, SceneDiagnostics.liveEnvironments.get())
        assertEquals(7, SceneDiagnostics.liveModels.get())
    }

    private fun verifySeasonMapStagesAndThumbnails() {
        val container = (compose.activity.application as TownApplication).container
        assertEquals(1, SceneDiagnostics.liveEnvironments.get())
        assertEquals(14, container.layout.plots.size)
        val paths = container.layout.plots.flatMap { it.models }.distinct()
        assertEquals(36, paths.size)
        paths.forEach { path ->
            val thumb = "thumbnails/" + path.removePrefix("models/").removeSuffix(".glb") + ".png"
            compose.activity.assets.open(thumb).use { stream ->
                val bitmap = checkNotNull(BitmapFactory.decodeStream(stream))
                assertEquals(320, bitmap.width)
                assertEquals(320, bitmap.height)
                bitmap.recycle()
            }
        }
        // Extra balance is a test-only fixture, never a new demo reward or vehicle code path.
        runBlocking {
            container.database.withTransaction {
                val before = checkNotNull(container.database.townDao().town())
                // Restart the three previously tested buildings at L1 so every per-level screenshot starts alike.
                container.database.townDao().saveBuildings(listOf("home", "cafe", "cathedral").map { BuildingEntity(it, 1) })
                container.database.townDao().updateTown(before.copy(pieces = 1000, revision = before.revision + 1))
            }
        }
        verifyInterruptedMotions()
        // Return only this test's buildings to L1 so the full-town per-level screenshots start alike.
        runBlocking {
            container.database.withTransaction {
                val before = checkNotNull(container.database.townDao().town())
                val buildings = checkNotNull(container.repository.snapshot()).buildings
                container.database.townDao().saveBuildings(buildings.keys.map { BuildingEntity(it, 1) })
                container.database.townDao().updateTown(before.copy(revision = before.revision + 1))
            }
        }
        for (level in 1..3) {
            container.layout.plots.forEach { plot ->
                runBlocking {
                    val before = checkNotNull(container.repository.snapshot()).buildings[plot.id] ?: 0
                    if (before < level) {
                        assertEquals(WriteResult.Saved, container.repository.execute(BuildCommand(plot.id, before), checkNotNull(container.gate.token())))
                    }
                }
            }
            compose.waitUntil(30_000) { SceneDiagnostics.liveModels.get() == 14 }
            compose.waitForIdle()
            capture("season1-all-l$level.png")
            compose.runOnIdle {
                val scene = checkNotNull(findScene(compose.activity.window.decorView))
                assertEquals(container.layout.plots.associate { it.id to level }, scene.displayedLevels())
                assertEquals(container.layout.roads.map { it.node }.toSet(), scene.visibleRoads())
            }
        }
        // The last, initially offscreen row is selectable in the existing scrolling inspector.
        compose.onNodeWithTag("plot.home_upper_east").performScrollTo().performClick()
        compose.onNodeWithTag("build.max").assertExists()
        val saved = runBlocking { container.repository.snapshot() }
        assertEquals(14, saved!!.buildings.size)
        assertTrue(saved.buildings.values.all { it == 3 })
        compose.activityRule.scenario.recreate()
        compose.waitUntil(30_000) { SceneDiagnostics.activeViews.get() == 1 && SceneDiagnostics.liveModels.get() == 14 && SceneDiagnostics.liveEnvironments.get() == 1 }
        assertEquals(saved, runBlocking { container.repository.snapshot() })
        capture("season1-restored.png")
        compose.onNodeWithTag("demo.restriction").performClick()
        compose.waitUntil(10_000) { SceneDiagnostics.activeViews.get() == 0 && SceneDiagnostics.liveModels.get() == 0 && SceneDiagnostics.liveEnvironments.get() == 0 }
    }
}
