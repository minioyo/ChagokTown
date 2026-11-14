package com.chagoktown.platform

import ai.pleos.playground.vehicle.Vehicle
import ai.pleos.playground.vehicle.api.model.capability.AccessType
import android.Manifest
import android.car.Car
import android.car.drivingstate.CarUxRestrictionsManager
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.os.CancellationSignal
import android.os.SystemClock
import com.chagoktown.game.MobilityReading
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.coroutines.resume
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull

/**
 * Pleos boundary. Verified on the Pleos Connect emulator only; car behaviour is unverified.
 * - Play access follows CarUxRestrictionsManager. Until it answers, play stays locked (Unknown).
 * - The odometer is read once per check through the public Vehicle SDK. On the emulator the SDK queued requests with no
 *   timeout while its service was gone, so every read has its own timeout and a timed-out SDK instance is replaced.
 * - Location uses Android LocationManager, which reports accuracy in metres. Pleos FusedLocation's `confidence` has no stated
 *   unit, so it is not used as metres.
 * Raw SDK and platform types stay in this file and [PleosReadMapper].
 */
class PleosVehicleGateway(private val context: Context) : VehicleGateway {
    private val access = MutableStateFlow(PlayAccess.Unknown)
    override val playAccess = access.asStateFlow()
    override val locationPermissions = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)

    private var car: Car? = null
    private var restrictions: CarUxRestrictionsManager? = null
    private var vehicle: Vehicle? = null

    @Synchronized
    override fun refreshAccess() {
        try {
            val manager = restrictions ?: connectRestrictions()
            access.value = PleosReadMapper.access(manager?.currentCarUxRestrictions?.isRequiresDistractionOptimization)
        } catch (_: Exception) {
            // Car service gone: lock, and connect afresh on the next resume.
            access.value = PlayAccess.Unknown
            runCatching { car?.disconnect() }
            car = null
            restrictions = null
        }
    }

    private fun connectRestrictions(): CarUxRestrictionsManager? {
        var connected: Car? = null
        try {
            val created = Car.createCar(context) ?: return null
            connected = created
            val manager = created.getCarManager(Car.CAR_UX_RESTRICTION_SERVICE) as? CarUxRestrictionsManager
            if (manager != null) {
                manager.registerListener { access.value = PleosReadMapper.access(it.isRequiresDistractionOptimization) }
                car = created
                restrictions = manager
                return manager
            }
        } catch (_: Throwable) {
            // Includes a missing android.car library on a non-automotive device: stay locked rather than crash.
        }
        // Never keep a half-made connection: this runs on every resume and would pile them up.
        runCatching { connected?.disconnect() }
        return null
    }

    override suspend fun readDistance(consentGeneration: Long): MobilityReading {
        val odometer = sdk().getOdometer()
        val readable = callback<Boolean> { done ->
            odometer.checkCurrentDistanceDrivenCapabilities(
                { done(it.accessType == AccessType.READ || it.accessType == AccessType.READ_WRITE) },
                { done(false) },
            )
        } ?: return timedOut()
        if (!readable) return MobilityReading.Unavailable
        // A refused or failed read (SecurityException and others arrive through onFailed) is simply Unavailable.
        val km = callback<Result<Float?>> { done ->
            odometer.getCurrentDistanceDriven({ done(Result.success(it)) }, { done(Result.failure(it)) })
        } ?: return timedOut()
        return PleosReadMapper.distance(readable = true, km = km.getOrNull(), generation = consentGeneration)
    }

    override suspend fun readLocation(consentGeneration: Long): LocationReading {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return LocationReading.Unavailable
        if (context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return LocationReading.Unavailable
        val manager = context.getSystemService(LocationManager::class.java) ?: return LocationReading.Unavailable
        val providers = buildList {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) add(LocationManager.FUSED_PROVIDER)
            add(LocationManager.GPS_PROVIDER)
        }
        val provider = providers.firstOrNull { runCatching { manager.isProviderEnabled(it) }.getOrDefault(false) } ?: return LocationReading.Unavailable
        val cancel = CancellationSignal()
        val fix = try {
            callback<Location?> { done -> manager.getCurrentLocation(provider, cancel, context.mainExecutor) { done(it) } }
        } catch (_: SecurityException) {
            null
        } finally {
            cancel.cancel()
        }
        fix ?: return LocationReading.Unavailable
        val ageMillis = (SystemClock.elapsedRealtimeNanos() - fix.elapsedRealtimeNanos) / 1_000_000
        return PleosReadMapper.location(fix.latitude, fix.longitude, if (fix.hasAccuracy()) fix.accuracy else null, ageMillis, consentGeneration)
    }

    @Synchronized
    private fun sdk(): Vehicle = vehicle ?: Vehicle(context).also {
        it.initialize()
        vehicle = it
    }

    /** No answer in time: report Unavailable and drop the SDK instance so the next check binds afresh. */
    @Synchronized
    private fun timedOut(): MobilityReading {
        runCatching { vehicle?.release() }
        vehicle = null
        return MobilityReading.Unavailable
    }

    /** One callback answer within [ReadTimeoutMillis], or null. A late or second answer is ignored. */
    private suspend fun <T> callback(start: (done: (T) -> Unit) -> Unit): T? = withTimeoutOrNull(ReadTimeoutMillis) {
        suspendCancellableCoroutine { continuation ->
            val answered = AtomicBoolean(false)
            start { value -> if (answered.compareAndSet(false, true) && continuation.isActive) continuation.resume(value) }
        }
    }

    private companion object {
        const val ReadTimeoutMillis = 5_000L
    }
}
