package com.chagoktown.platform

import android.content.SharedPreferences
import androidx.core.content.edit
import com.chagoktown.game.MobilityReading
import java.time.LocalDate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Fake odometer, calendar and parking spot for the virtual commute demo. Persisted so a restart neither rewinds nor resets them.
 * Each commute moves the car between two synthetic spots ("near home" / "near work"); they are not real places.
 */
data class DemoDrive(val distance: Double, val dayOffset: Long, val atWork: Boolean = false)

class DemoVehicleGateway(private val prefs: SharedPreferences) : VehicleGateway {
    private val access = MutableStateFlow(PlayAccess.Unknown)
    override val playAccess = access.asStateFlow()
    private val mutableDrive = MutableStateFlow(DemoDrive(
        Double.fromBits(prefs.getLong(DISTANCE, StartDistance.toRawBits())),
        prefs.getLong(DAY_OFFSET, 0),
        prefs.getBoolean(AT_WORK, false),
    ))
    val drive = mutableDrive.asStateFlow()

    override fun refreshAccess() {
        if (access.value == PlayAccess.Unknown) access.value = PlayAccess.Allowed
    }

    fun setRestricted(restricted: Boolean) {
        access.value = if (restricted) PlayAccess.Restricted else PlayAccess.Allowed
    }

    override suspend fun readDistance(consentGeneration: Long) = MobilityReading.Ready(mutableDrive.value.distance, SOURCE, consentGeneration)

    override suspend fun readLocation(consentGeneration: Long): LocationReading {
        val (latitude, longitude) = if (mutableDrive.value.atWork) WorkSpot else HomeSpot
        return LocationReading.Ready(latitude, longitude, accuracyMeters = 8f, ageMillis = 0, generation = consentGeneration)
    }

    fun today(): LocalDate = LocalDate.now().plusDays(mutableDrive.value.dayOffset)

    fun commute() = update(mutableDrive.value.let { it.copy(distance = it.distance + CommuteKm, atWork = !it.atWork) })

    fun nextDay() = update(mutableDrive.value.copy(dayOffset = mutableDrive.value.dayOffset + 1))

    private fun update(next: DemoDrive) {
        mutableDrive.value = next
        prefs.edit {
            putLong(DISTANCE, next.distance.toRawBits())
            putLong(DAY_OFFSET, next.dayOffset)
            putBoolean(AT_WORK, next.atWork)
        }
    }

    companion object {
        const val PREFS = "demo_drive"
        const val SOURCE = "demo.km"
        const val CommuteKm = 12.0
        private const val StartDistance = 10_000.0
        private const val DISTANCE = "distance"
        private const val DAY_OFFSET = "day_offset"
        private const val AT_WORK = "at_work"
        // Synthetic round numbers, not anyone's address.
        private val HomeSpot = 37.4000 to 127.1000
        private val WorkSpot = 37.4800 to 127.0300
    }
}
