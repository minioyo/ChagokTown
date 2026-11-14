package com.chagoktown.game

import java.time.LocalDate
import java.time.temporal.ChronoUnit
import kotlin.math.min

/** One cumulative-distance read, already normalized by the platform mapper. [source] names the unit/counter contract. */
sealed interface MobilityReading {
    data class Ready(val distance: Double, val source: String, val generation: Long) : MobilityReading
    /** Unsupported, denied, missing or stale. The mapper never turns these into a distance. */
    data object Unavailable : MobilityReading
}

data class MobilityBaseline(val distance: Double, val source: String)

data class MobilityState(
    val baseline: MobilityBaseline? = null,
    val lastRewardDay: LocalDate? = null,
    val rewardCount: Int = 0,
)

/**
 * [minDelta] and [pieces] are undecided until the real counter contract is known, so callers must supply them.
 * [maxBankedDays] lets one check pay [pieces] for each calendar day since the last reward, up to that many days,
 * so someone who drives or opens the town less often is not left behind. The first reward pays one day.
 */
data class RewardPolicy(val minDelta: Double, val pieces: Int, val maxBankedDays: Int = 1) {
    init {
        require(minDelta > 0 && minDelta.isFinite())
        require(pieces >= 0)
        require(maxBankedDays >= 1)
    }
}

enum class MobilityOutcome { IGNORED, BASELINE_SET, BASELINE_RESET, BELOW_THRESHOLD, REWARDED, CONSUMED }

data class MobilityResult(val outcome: MobilityOutcome, val state: MobilityState, val piecesGranted: Int = 0)

object RewardRules {
    /**
     * Compares one reading with the stored baseline. [today] is the local date captured once when the write was approved;
     * [consentGeneration] is the current vehicle-data consent generation, so callbacks from an older one are dropped.
     */
    fun observe(state: MobilityState, reading: MobilityReading, consentGeneration: Long, today: LocalDate, policy: RewardPolicy): MobilityResult {
        if (reading !is MobilityReading.Ready || reading.generation != consentGeneration ||
            !reading.distance.isFinite() || reading.distance < 0) return MobilityResult(MobilityOutcome.IGNORED, state)

        val current = MobilityBaseline(reading.distance, reading.source)
        val baseline = state.baseline ?: return MobilityResult(MobilityOutcome.BASELINE_SET, state.copy(baseline = current))
        val delta = reading.distance - baseline.distance
        if (reading.source != baseline.source || delta < 0) return MobilityResult(MobilityOutcome.BASELINE_RESET, state.copy(baseline = current))
        // Small changes keep the old baseline so they can add up to a valid move later.
        if (delta < policy.minDelta) return MobilityResult(MobilityOutcome.BELOW_THRESHOLD, state)

        val last = state.lastRewardDay
        if (last != null && !today.isAfter(last)) return MobilityResult(MobilityOutcome.CONSUMED, state.copy(baseline = current))
        val days = if (last == null) 1 else min(ChronoUnit.DAYS.between(last, today), policy.maxBankedDays.toLong()).toInt()
        return MobilityResult(
            MobilityOutcome.REWARDED,
            MobilityState(current, today, state.rewardCount + 1),
            policy.pieces * days,
        )
    }
}
