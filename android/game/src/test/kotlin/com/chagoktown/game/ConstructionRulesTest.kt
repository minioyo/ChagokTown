package com.chagoktown.game

import org.junit.Assert.*
import org.junit.Test

class ConstructionRulesTest {
    private val catalog = ConstructionCatalog(listOf(
        PlotDefinition("home", "집", listOf(3, 4, 6)),
        PlotDefinition("cafe", "카페", listOf(3, 4, 6)),
        PlotDefinition("cathedral", "성당", listOf(5, 7, 10)),
    ))
    private val initial = ConstructionRules.initialTown()
    private fun advance(town: TownState, id: String, expected: Int) = ConstructionRules.advance(town, BuildCommand(id, expected), catalog)

    @Test fun startsWithOnlyTheFixedHomeAtLevelOne() {
        assertEquals(3, initial.pieces)
        assertEquals(mapOf("home" to 1), initial.buildings)
    }

    @Test fun constructionSpendsTheCatalogCostAndPreservesOriginal() {
        val result = (advance(initial, "cafe", 0) as RuleResult.Accepted).town
        assertEquals(0, result.pieces)
        assertEquals(1, result.buildings["cafe"])
        assertEquals(3, initial.pieces)
        assertFalse("cafe" in initial.buildings)
    }

    @Test fun duplicateIntentDoesNotUpgradeAgain() {
        val first = (advance(initial, "cafe", 0) as RuleResult.Accepted).town
        assertEquals(RuleResult.Rejected(Rejection.STALE_LEVEL), advance(first, "cafe", 0))
    }

    @Test fun cannotOverdrawOrBuildAnUnknownPlot() {
        assertEquals(RuleResult.Rejected(Rejection.NOT_ENOUGH_PIECES), advance(initial, "cathedral", 0))
        assertEquals(RuleResult.Rejected(Rejection.UNKNOWN_PLOT), advance(initial, "unknown", 0))
    }

    @Test fun allThreeBuildingsCanReachLevelThreeAndStopThere() {
        var town = initial.copy(pieces = 63)
        catalog.plots.forEach { plot ->
            while ((town.buildings[plot.id] ?: 0) < 3) {
                town = (advance(town, plot.id, town.buildings[plot.id] ?: 0) as RuleResult.Accepted).town
            }
            assertEquals(RuleResult.Rejected(Rejection.MAX_LEVEL), advance(town, plot.id, 3))
        }
        assertEquals(18, town.pieces)
        assertEquals(mapOf("home" to 3, "cafe" to 3, "cathedral" to 3), town.buildings)
    }

    @Test fun newConstructionKeepsLegacyOwnershipAndPlacements() {
        val legacy = initial.copy(ownedBlueprints = setOf("house.basic", "bench.basic"),
            placements = listOf(Placement("old-bench", "bench.basic", "decoration.1")))
        val after = (advance(legacy, "cafe", 0) as RuleResult.Accepted).town
        assertEquals(legacy.ownedBlueprints, after.ownedBlueprints)
        assertEquals(legacy.placements, after.placements)
    }
}
