package com.chagoktown.platform

/** One location fix, read only when the user asks to link the current place. Never logged or kept outside the sealed link. */
sealed interface LocationReading {
    /** [ageMillis] is how old the fix was when read; [accuracyMeters] is null when the platform gives no usable figure. */
    data class Ready(val latitude: Double, val longitude: Double, val accuracyMeters: Float?, val ageMillis: Long, val generation: Long) : LocationReading
    data object Unavailable : LocationReading
}

/** A fix older or vaguer than this is not treated as "here". */
data class LocationPolicy(val maxAgeMillis: Long, val maxAccuracyMeters: Float)

/** Temporary values, used by both demo and vehicle until fix quality is measured in a real car (only emulator GPS has been seen so far). */
val TemporaryLocationPolicy = LocationPolicy(maxAgeMillis = 120_000, maxAccuracyMeters = 100f)
