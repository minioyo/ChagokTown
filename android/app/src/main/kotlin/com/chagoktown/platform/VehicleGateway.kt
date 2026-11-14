package com.chagoktown.platform

import com.chagoktown.game.MobilityReading
import kotlinx.coroutines.flow.StateFlow

enum class PlayAccess { Allowed, Restricted, Unknown }

interface VehicleGateway {
    val playAccess: StateFlow<PlayAccess>
    fun refreshAccess()

    /**
     * One cumulative-distance read, tagged with the consent generation captured before the request so a reading that
     * outlives a withdrawal is discarded. Demo returns fake values; vehicle reads the Pleos odometer, or Unavailable when it cannot.
     */
    suspend fun readDistance(consentGeneration: Long): MobilityReading

    /** One location fix, only when the user asks to link the current place. Same generation tagging as [readDistance]. */
    suspend fun readLocation(consentGeneration: Long): LocationReading

    /** Runtime permissions [readLocation] needs; requested when the user turns location on or links a place. */
    val locationPermissions: List<String> get() = emptyList()
}
