package com.chagoktown.ui.town

import com.chagoktown.data.TownRoad
import org.junit.Assert.*
import org.junit.Test

class BuildingPresentationTest {
    @Test fun constructionWaitsForTheGroundThenGrowsAndSettlesExactly() {
        assertEquals(.08f, BuildingMotion.scale(0f, false), .00001f)
        assertEquals(.08f, BuildingMotion.scale(.10f, false), .00001f)
        assertTrue(BuildingMotion.scale(.35f, false) > .08f)
        assertTrue(BuildingMotion.scale(.62f, false) > 1f)
        assertEquals(1f, BuildingMotion.scale(BuildingMotion.BUILD_SECONDS, false), .00001f)
        assertEquals(1f, BuildingMotion.scale(10f, false), .00001f)
    }

    @Test fun upgradeShrinksWithoutDisappearingAndReturnsToAuthoredScale() {
        assertEquals(1f, BuildingMotion.scale(0f, true), .00001f)
        assertEquals(.88f, BuildingMotion.scale(BuildingMotion.SWAP_SECONDS, true), .00001f)
        for (frame in 0..100) assertTrue(BuildingMotion.scale(frame / 100f, true) in .8799f..1.0251f)
        assertEquals(1f, BuildingMotion.scale(BuildingMotion.UPGRADE_SECONDS, true), .00001f)
    }

    @Test fun sharedRoadStaysVisibleForEitherOwnerAndIgnoresUnrelatedPlots() {
        val road = TownRoad("shared", setOf("bookshop", "florist"))
        assertFalse(road.isVisible(emptyMap()))
        assertFalse(road.isVisible(mapOf("home" to 3, "florist" to 0)))
        assertTrue(road.isVisible(mapOf("bookshop" to 1)))
        assertTrue(road.isVisible(mapOf("florist" to 3)))
        assertTrue(road.isVisible(mapOf("bookshop" to 0, "florist" to 1)))
    }
}
