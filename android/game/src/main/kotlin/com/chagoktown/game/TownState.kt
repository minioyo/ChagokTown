package com.chagoktown.game

import java.time.LocalDate

/** A free-placement record from the first 2D demo (schema v1). Still read so an old town is never dropped silently. */
data class Placement(val id: String, val blueprintId: String, val slotId: String)

data class TownState(
    val pieces: Int,
    // Legacy free-placement records. Nothing writes them any more; the fixed plots live in [buildings].
    val ownedBlueprints: Set<String>,
    val placements: List<Placement>,
    val revision: Long = 0,
    val buildings: Map<String, Int> = emptyMap(),
    val demoPiecesClaimed: Boolean = false,
    // Movement reward history. It outlives the distance baseline, so the reward day never moves backwards.
    val rewardCount: Int = 0,
    val lastRewardDay: LocalDate? = null,
)

enum class Rejection { NOT_ENOUGH_PIECES, UNKNOWN_PLOT, STALE_LEVEL, MAX_LEVEL, ALREADY_CLAIMED }

sealed interface RuleResult {
    data class Accepted(val town: TownState) : RuleResult
    data class Rejected(val reason: Rejection) : RuleResult
}
