package com.chagoktown.platform

import com.chagoktown.game.MobilityReading
import org.junit.Assert.assertEquals
import org.junit.Test

class PleosReadMapperTest {
    @Test fun onlyAnExplicitNoRestrictionAllowsPlay() {
        assertEquals(PlayAccess.Allowed, PleosReadMapper.access(false))
        assertEquals(PlayAccess.Restricted, PleosReadMapper.access(true))
        assertEquals(PlayAccess.Unknown, PleosReadMapper.access(null))
    }

    @Test fun odometerKilometresBecomeAReadingTaggedWithTheRequestGeneration() {
        assertEquals(MobilityReading.Ready(115_550.0, PleosReadMapper.ODOMETER_SOURCE, 7), PleosReadMapper.distance(true, 115_550f, 7))
    }

    @Test fun missingUnreadableOrImpossibleOdometerValuesAreNeverAReading() {
        assertEquals(MobilityReading.Unavailable, PleosReadMapper.distance(true, null, 1))
        assertEquals(MobilityReading.Unavailable, PleosReadMapper.distance(false, 100f, 1))
        assertEquals(MobilityReading.Unavailable, PleosReadMapper.distance(true, -1f, 1))
        assertEquals(MobilityReading.Unavailable, PleosReadMapper.distance(true, Float.NaN, 1))
        assertEquals(MobilityReading.Unavailable, PleosReadMapper.distance(true, Float.POSITIVE_INFINITY, 1))
    }

    @Test fun locationKeepsAMissingAccuracyAsMissing() {
        assertEquals(LocationReading.Ready(37.5, 127.0, null, 900, 3), PleosReadMapper.location(37.5, 127.0, null, 900, 3))
    }
}
