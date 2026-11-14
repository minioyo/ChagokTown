package com.chagoktown.platform

import com.chagoktown.game.MobilityReading

/**
 * Turns raw platform values into the app's types. Only contracts seen on the Pleos Connect emulator are mapped; anything missing
 * or unexpected becomes Unknown/Unavailable, never a guessed value.
 */
internal object PleosReadMapper {
    /** Identifies the counter a baseline came from. A different source resets the baseline instead of being compared. */
    const val ODOMETER_SOURCE = "pleos.vehicle.odometer.km"

    /** The platform's UX restriction state. No answer yet means no play. Never derived from speed or gear here. */
    fun access(requiresDistractionOptimization: Boolean?): PlayAccess = when (requiresDistractionOptimization) {
        false -> PlayAccess.Allowed
        true -> PlayAccess.Restricted
        null -> PlayAccess.Unknown
    }

    /** `Odometer.getCurrentDistanceDriven` gives km as Float?, with no timestamp. */
    fun distance(readable: Boolean, km: Float?, generation: Long): MobilityReading =
        if (!readable || km == null || !km.isFinite() || km < 0f) MobilityReading.Unavailable
        else MobilityReading.Ready(km.toDouble(), ODOMETER_SOURCE, generation)

    /** Android location: accuracy in metres only when the platform reports one; age from the fix's elapsed-realtime stamp. */
    fun location(latitude: Double, longitude: Double, accuracyMeters: Float?, ageMillis: Long, generation: Long): LocationReading =
        LocationReading.Ready(latitude, longitude, accuracyMeters, ageMillis, generation)
}
