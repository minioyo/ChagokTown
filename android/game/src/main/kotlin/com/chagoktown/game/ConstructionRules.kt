package com.chagoktown.game

data class PlotDefinition(val id: String, val name: String, val costs: List<Int>) {
    init {
        require(costs.size == 3 && costs.all { it >= 0 })
    }
}

data class ConstructionCatalog(val plots: List<PlotDefinition>) {
    init {
        require(plots.map { it.id }.distinct().size == plots.size)
        require(plots.any { it.id == "home" })
    }

    fun plot(id: String) = plots.singleOrNull { it.id == id }
}

data class BuildCommand(val plotId: String, val expectedLevel: Int)

object ConstructionRules {
    fun initialTown() = TownState(3, emptySet(), emptyList(), buildings = mapOf("home" to 1))

    fun advance(town: TownState, command: BuildCommand, catalog: ConstructionCatalog): RuleResult {
        val plot = catalog.plot(command.plotId) ?: return RuleResult.Rejected(Rejection.UNKNOWN_PLOT)
        val level = town.buildings[plot.id] ?: 0
        if (command.expectedLevel != level) return RuleResult.Rejected(Rejection.STALE_LEVEL)
        if (level >= 3) return RuleResult.Rejected(Rejection.MAX_LEVEL)
        val cost = plot.costs[level]
        if (town.pieces < cost) return RuleResult.Rejected(Rejection.NOT_ENOUGH_PIECES)
        return RuleResult.Accepted(town.copy(
            pieces = town.pieces - cost,
            buildings = town.buildings + (plot.id to level + 1),
            revision = town.revision + 1,
        ))
    }
}
