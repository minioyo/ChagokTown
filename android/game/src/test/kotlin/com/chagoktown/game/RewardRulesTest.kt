package com.chagoktown.game

import java.time.LocalDate
import org.junit.Assert.*
import org.junit.Test

class RewardRulesTest {
    // Test-only values: the real minimum change and reward size wait for the vehicle counter contract.
    private val policy = RewardPolicy(minDelta = 1.0, pieces = 3)
    private val day1 = LocalDate.of(2026, 11, 1)

    private fun observe(state: MobilityState, distance: Double, day: LocalDate, source: String = "odo", generation: Long = 1, consent: Long = 1) =
        RewardRules.observe(state, MobilityReading.Ready(distance, source, generation), consent, day, policy)

    private fun rewardedOn(day: LocalDate, distance: Double) = MobilityState(MobilityBaseline(distance, "odo"), day, rewardCount = 1)

    @Test fun firstReadingOnlySetsTheBaseline() {
        val result = observe(MobilityState(), 12_000.0, day1)
        assertEquals(MobilityOutcome.BASELINE_SET, result.outcome)
        assertEquals(0, result.piecesGranted)
        assertEquals(MobilityState(MobilityBaseline(12_000.0, "odo")), result.state)
    }

    @Test fun unavailableOrInvalidReadingsKeepTheExistingBaseline() {
        val state = rewardedOn(day1, 100.0)
        val unavailable = RewardRules.observe(state, MobilityReading.Unavailable, 1, day1.plusDays(1), policy)
        assertEquals(MobilityResult(MobilityOutcome.IGNORED, state), unavailable)
        listOf(Double.NaN, Double.POSITIVE_INFINITY, -1.0).forEach {
            assertEquals(MobilityResult(MobilityOutcome.IGNORED, state), observe(state, it, day1.plusDays(1)))
        }
    }

    @Test fun callbackFromAnOlderConsentGenerationIsDropped() {
        val state = rewardedOn(day1, 100.0)
        assertEquals(MobilityResult(MobilityOutcome.IGNORED, state), observe(state, 500.0, day1.plusDays(1), generation = 1, consent = 2))
    }

    @Test fun reconsentStartsFromANewBaselineWithoutPayingPastDistance() {
        // Withdrawing consent deletes the baseline; the repository keeps the reward day so it never moves backwards.
        val cleared = rewardedOn(day1, 100.0).copy(baseline = null)
        val result = observe(cleared, 9_000.0, day1.plusDays(3), generation = 2, consent = 2)
        assertEquals(MobilityOutcome.BASELINE_SET, result.outcome)
        assertEquals(0, result.piecesGranted)
        assertEquals(day1, result.state.lastRewardDay)
    }

    @Test fun sameValueAndSmallChangesKeepTheBaselineSoTheyCanAddUp() {
        var state = MobilityState(MobilityBaseline(100.0, "odo"))
        listOf(100.0, 100.4, 100.8).forEach {
            val result = observe(state, it, day1)
            assertEquals(MobilityOutcome.BELOW_THRESHOLD, result.outcome)
            state = result.state
        }
        assertEquals(100.0, state.baseline!!.distance, 0.0)
        assertEquals(MobilityOutcome.REWARDED, observe(state, 101.2, day1).outcome)
    }

    @Test fun counterDecreaseOrSourceChangeResetsWithoutReward() {
        val state = rewardedOn(day1, 100.0)
        val decreased = observe(state, 50.0, day1.plusDays(1))
        assertEquals(MobilityOutcome.BASELINE_RESET, decreased.outcome)
        assertEquals(0, decreased.piecesGranted)
        assertEquals(MobilityBaseline(50.0, "odo"), decreased.state.baseline)

        val otherSource = observe(state, 900.0, day1.plusDays(1), source = "trip")
        assertEquals(MobilityOutcome.BASELINE_RESET, otherSource.outcome)
        assertEquals(MobilityBaseline(900.0, "trip"), otherSource.state.baseline)
        assertEquals(day1, otherSource.state.lastRewardDay)
    }

    @Test fun oneRewardPerDayAndAConsumedMoveIsNotPaidAgainTomorrow() {
        val start = observe(MobilityState(), 100.0, day1).state
        val first = observe(start, 110.0, day1)
        assertEquals(MobilityOutcome.REWARDED, first.outcome)
        assertEquals(3, first.piecesGranted)

        val relaunch = observe(first.state, 110.0, day1)
        assertEquals(MobilityOutcome.BELOW_THRESHOLD, relaunch.outcome)

        val sameDayMove = observe(first.state, 120.0, day1)
        assertEquals(MobilityOutcome.CONSUMED, sameDayMove.outcome)
        assertEquals(0, sameDayMove.piecesGranted)
        assertEquals(120.0, sameDayMove.state.baseline!!.distance, 0.0)

        val nextDaySameValue = observe(sameDayMove.state, 120.0, day1.plusDays(1))
        assertEquals(MobilityOutcome.BELOW_THRESHOLD, nextDaySameValue.outcome)

        val nextDayMove = observe(nextDaySameValue.state, 135.0, day1.plusDays(1))
        assertEquals(MobilityOutcome.REWARDED, nextDayMove.outcome)
        assertEquals(MobilityState(MobilityBaseline(135.0, "odo"), day1.plusDays(1), 2), nextDayMove.state)
    }

    @Test fun movesFromUnobservedDaysPayAtMostOnce() {
        val result = observe(rewardedOn(day1, 100.0), 400.0, day1.plusDays(4))
        assertEquals(MobilityOutcome.REWARDED, result.outcome)
        assertEquals(3, result.piecesGranted)
        assertEquals(2, result.state.rewardCount)
    }

    @Test fun bankedDaysPayEachMissedDayUpToTheLimit() {
        val banked = policy.copy(maxBankedDays = 7)
        fun pay(state: MobilityState, distance: Double, day: LocalDate) =
            RewardRules.observe(state, MobilityReading.Ready(distance, "odo", 1), 1, day, banked)

        val first = pay(MobilityState(MobilityBaseline(100.0, "odo")), 110.0, day1)
        assertEquals(3, first.piecesGranted)
        val nextDay = pay(first.state, 120.0, day1.plusDays(1))
        assertEquals(3, nextDay.piecesGranted)
        val afterFourDays = pay(nextDay.state, 400.0, day1.plusDays(5))
        assertEquals(12, afterFourDays.piecesGranted)
        assertEquals(3, afterFourDays.state.rewardCount)
        val afterAMonth = pay(afterFourDays.state, 500.0, day1.plusDays(35))
        assertEquals(21, afterAMonth.piecesGranted)

        // A clock moved backwards still pays nothing and keeps the reward day, so the next day pays one day only.
        val backwards = pay(afterAMonth.state, 600.0, day1.plusDays(30))
        assertEquals(MobilityOutcome.CONSUMED, backwards.outcome)
        assertEquals(0, backwards.piecesGranted)
        assertEquals(3, pay(backwards.state, 700.0, day1.plusDays(36)).piecesGranted)
    }

    @Test fun clockMovingBackwardsNeverPaysAndNeverRewindsTheRewardDay() {
        val day5 = day1.plusDays(4)
        val backwards = observe(rewardedOn(day5, 100.0), 130.0, day1.plusDays(2))
        assertEquals(MobilityOutcome.CONSUMED, backwards.outcome)
        assertEquals(day5, backwards.state.lastRewardDay)

        val sameDayAgain = observe(backwards.state, 150.0, day5)
        assertEquals(MobilityOutcome.CONSUMED, sameDayAgain.outcome)
        assertEquals(MobilityOutcome.REWARDED, observe(sameDayAgain.state, 170.0, day5.plusDays(1)).outcome)
    }

    @Test fun sevenCommuteDaysGiveSevenRewards() {
        var state = observe(MobilityState(), 10_000.0, day1.minusDays(1)).state
        var pieces = 0
        var odometer = 10_000.0
        repeat(7) { offset ->
            val day = day1.plusDays(offset.toLong())
            listOf(MobilityOutcome.REWARDED, MobilityOutcome.CONSUMED).forEach { expected ->
                odometer += 15.0
                val result = observe(state, odometer, day)
                assertEquals(expected, result.outcome)
                pieces += result.piecesGranted
                state = result.state
            }
        }
        assertEquals(21, pieces)
        assertEquals(7, state.rewardCount)
        assertEquals(day1.plusDays(6), state.lastRewardDay)
    }

    @Test fun policyRejectsUndefinedThresholds() {
        listOf(0.0, -1.0, Double.NaN, Double.POSITIVE_INFINITY).forEach {
            assertThrows(IllegalArgumentException::class.java) { RewardPolicy(it, 3) }
        }
        assertThrows(IllegalArgumentException::class.java) { RewardPolicy(1.0, 3, maxBankedDays = 0) }
    }
}
