package com.chagoktown.data

import androidx.room.withTransaction
import com.chagoktown.data.local.BuildingEntity
import com.chagoktown.data.local.MobilityEntity
import com.chagoktown.data.local.PlaceKind
import com.chagoktown.data.local.PlaceLinkEntity
import com.chagoktown.data.local.PrivacyEntity
import com.chagoktown.data.local.TownDatabase
import com.chagoktown.data.local.TownEntity
import com.chagoktown.data.privacy.CryptoBox
import com.chagoktown.data.privacy.PrivacyStorageException
import com.chagoktown.data.privacy.SealedBaseline
import com.chagoktown.data.privacy.SealedPlace
import com.chagoktown.platform.LocationPolicy
import com.chagoktown.platform.LocationReading
import com.chagoktown.platform.TemporaryLocationPolicy
import com.chagoktown.game.ConstructionCatalog
import com.chagoktown.game.ConstructionRules
import com.chagoktown.game.BuildCommand
import com.chagoktown.game.MobilityOutcome
import com.chagoktown.game.MobilityReading
import com.chagoktown.game.MobilityState
import com.chagoktown.game.Placement
import com.chagoktown.game.RewardPolicy
import com.chagoktown.game.RewardRules
import com.chagoktown.game.RuleResult
import com.chagoktown.game.TownState
import com.chagoktown.session.InteractionGate
import com.chagoktown.session.SessionToken
import java.time.LocalDate
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

sealed interface WriteResult {
    data object Saved : WriteResult
    data object SessionExpired : WriteResult
    data class Rejected(val reason: com.chagoktown.game.Rejection) : WriteResult
}

sealed interface MobilityWrite {
    data class Checked(val outcome: MobilityOutcome, val piecesGranted: Int) : MobilityWrite
    data object SessionExpired : MobilityWrite
    /** Vehicle data is off, or its withdrawal is in progress. Nothing was read from or written to storage. */
    data object ConsentOff : MobilityWrite
    /** The sealed baseline cannot be opened or a new one sealed. Nothing was written; the town is untouched. */
    data object PrivacyLocked : MobilityWrite
}

data class PrivacyState(val vehicleConsent: Boolean = false, val generation: Long = 0, val locationConsent: Boolean = false)

sealed interface PlaceWrite {
    data object Saved : PlaceWrite
    data object SessionExpired : PlaceWrite
    /** Location is off, or its withdrawal is in progress. Nothing was stored. */
    data object ConsentOff : PlaceWrite
    /** The envelope could not be sealed. Nothing was stored. */
    data object PrivacyLocked : PlaceWrite
    data class Rejected(val reason: PlaceRejection) : PlaceWrite
}

enum class PlaceRejection { NO_BUILDING, INVALID_ALIAS, LOCATION_UNAVAILABLE, LOCATION_STALE, LOCATION_IMPRECISE, OLD_GENERATION }

sealed interface AliasRead {
    data class Ready(val alias: String) : AliasRead
    data object Missing : AliasRead
    /** The alias cannot be opened. It is never shown as something else; unlinking deletes it. */
    data object Locked : AliasRead
}

const val MaxAliasLength = 20

/** Temporary values, used by both demo and vehicle until the odometer's update timing and rounding are measured in a real car. */
val TemporaryRewardPolicy = RewardPolicy(minDelta = 1.0, pieces = 3, maxBankedDays = 7)

private val KeyProbe = byteArrayOf(1)
private val KeyProbeAad = "chagoktown/key-probe/v1".encodeToByteArray()

class TownRepository(
    private val database: TownDatabase,
    val catalog: ConstructionCatalog,
    private val gate: InteractionGate,
    private val crypto: CryptoBox,
    private val rewardPolicy: RewardPolicy = TemporaryRewardPolicy,
    private val locationPolicy: LocationPolicy = TemporaryLocationPolicy,
) {
    private val dao = database.townDao()
    private val writes = Mutex()
    // Closed in memory the moment withdrawal is requested, before the deletion runs. Reopens only after consent is saved again,
    // so a failed withdrawal still stops checks for the rest of this process.
    private val vehicleChecksOpen = AtomicBoolean(true)
    private val locationLinksOpen = AtomicBoolean(true)

    val town = dao.observeRevision().map { snapshot() }.distinctUntilChanged()
    val privacy = dao.observePrivacy().map { it.toState() }.distinctUntilChanged()
    /** Which buildings have a place and of what kind. Never an alias or coordinates. */
    val places = dao.observePlaceKinds().map { rows -> rows.associate { it.plotId to it.kind } }.distinctUntilChanged()

    suspend fun snapshot(): TownState? = database.withTransaction { readTown() }

    suspend fun privacySnapshot(): PrivacyState = dao.privacy().toState()

    suspend fun initialize() = writes.withLock {
        database.withTransaction {
            if (dao.town() == null) {
                // Absence of the singleton must not silently reset a partially damaged town.
                check(dao.owned().isEmpty() && dao.placements().isEmpty() && dao.buildings().isEmpty())
                val initial = ConstructionRules.initialTown()
                dao.insertTown(TownEntity(pieces = initial.pieces, revision = initial.revision))
                dao.saveBuildings(initial.buildings.map { BuildingEntity(it.key, it.value) })
            }
            // New installs and towns migrated from v3 both start with vehicle data off.
            if (dao.privacy() == null) dao.savePrivacy(PrivacyEntity(vehicleConsent = false, consentGeneration = 0))
        }
    }

    /**
     * Turns vehicle data on or off. Both directions delete the baseline and start a new consent generation, so a reading
     * requested earlier can neither recreate the old baseline nor pay for distance from before re-consent. Pieces, the reward
     * count and the last reward date stay: re-consenting on the same day is not another way to be paid.
     */
    suspend fun setVehicleConsent(enabled: Boolean) {
        if (!enabled) vehicleChecksOpen.set(false)
        writes.withLock {
            database.withTransaction {
                val before = checkNotNull(dao.privacy())
                if (before.vehicleConsent != enabled) {
                    dao.deleteMobility()
                    dao.savePrivacy(before.copy(vehicleConsent = enabled, consentGeneration = before.consentGeneration + 1))
                }
            }
        }
        if (enabled) vehicleChecksOpen.set(true)
    }

    /**
     * Turns location on or off. Withdrawal deletes every LOCATION link with its alias and coordinates, keeps MANUAL aliases
     * and every building, and starts a new generation so a fix requested earlier cannot be linked afterwards.
     */
    suspend fun setLocationConsent(enabled: Boolean) {
        if (!enabled) locationLinksOpen.set(false)
        writes.withLock {
            database.withTransaction {
                val before = checkNotNull(dao.privacy())
                if (before.locationConsent != enabled) {
                    if (!enabled) dao.deleteLocationLinks()
                    dao.savePrivacy(before.copy(locationConsent = enabled, consentGeneration = before.consentGeneration + 1))
                }
            }
        }
        if (enabled) locationLinksOpen.set(true)
    }

    /** Adds or renames the alias of a built building. An existing LOCATION link keeps its coordinates: renaming is not a visit. */
    suspend fun saveAlias(plotId: String, alias: String, token: SessionToken): PlaceWrite = placeWrite {
        if (!gate.approve(token)) return@placeWrite PlaceWrite.SessionExpired
        val clean = cleanAlias(alias) ?: return@placeWrite PlaceWrite.Rejected(PlaceRejection.INVALID_ALIAS)
        if ((dao.building(plotId)?.level ?: 0) < 1) return@placeWrite PlaceWrite.Rejected(PlaceRejection.NO_BUILDING)
        val existing = dao.placeLink(plotId)
        dao.savePlaceLink(PlaceLinkEntity(plotId, existing?.kind ?: PlaceKind.MANUAL, SealedPlace.sealAlias(crypto, plotId, clean), existing?.sealedCoordinates))
        PlaceWrite.Saved
    }

    /**
     * Links the place where the car is parked to a built building. The fix must belong to the current consent generation and be
     * recent and precise enough; otherwise nothing is stored and linking waits. Coordinates are never guessed or reused.
     */
    suspend fun linkCurrentPlace(plotId: String, reading: LocationReading, alias: String, token: SessionToken): PlaceWrite {
        if (!locationLinksOpen.get()) return PlaceWrite.ConsentOff
        return placeWrite {
            if (!gate.approve(token)) return@placeWrite PlaceWrite.SessionExpired
            val privacy = checkNotNull(dao.privacy())
            if (!privacy.locationConsent || !locationLinksOpen.get()) return@placeWrite PlaceWrite.ConsentOff
            val clean = cleanAlias(alias) ?: return@placeWrite PlaceWrite.Rejected(PlaceRejection.INVALID_ALIAS)
            if ((dao.building(plotId)?.level ?: 0) < 1) return@placeWrite PlaceWrite.Rejected(PlaceRejection.NO_BUILDING)
            val fix = reading as? LocationReading.Ready ?: return@placeWrite PlaceWrite.Rejected(PlaceRejection.LOCATION_UNAVAILABLE)
            locationProblem(fix, privacy.consentGeneration)?.let { return@placeWrite PlaceWrite.Rejected(it) }
            dao.savePlaceLink(PlaceLinkEntity(plotId, PlaceKind.LOCATION, SealedPlace.sealAlias(crypto, plotId, clean),
                SealedPlace.sealCoordinates(crypto, plotId, fix.latitude, fix.longitude)))
            PlaceWrite.Saved
        }
    }

    /** Opened only when the user asks to see it. Decrypted off the main thread: Keystore calls can be slow. */
    suspend fun revealAlias(plotId: String): AliasRead = withContext(Dispatchers.IO) {
        val link = dao.placeLink(plotId) ?: return@withContext AliasRead.Missing
        try {
            AliasRead.Ready(SealedPlace.openAlias(crypto, plotId, link.sealedAlias))
        } catch (_: PrivacyStorageException) {
            AliasRead.Locked
        }
    }

    /**
     * The building stays; only its place, alias and coordinates go. A play action from the place dialog, so it follows the
     * same approval boundary as other writes. The settings' deletions and withdrawals deliberately do not need a token.
     */
    suspend fun unlinkPlace(plotId: String, token: SessionToken): PlaceWrite = placeWrite {
        if (!gate.approve(token)) return@placeWrite PlaceWrite.SessionExpired
        dao.deletePlaceLink(plotId)
        PlaceWrite.Saved
    }

    /** Settings' "delete place records": every MANUAL and LOCATION link. Buildings, pieces and consent choices stay. */
    suspend fun deleteAllPlaces() = writes.withLock { dao.deleteAllPlaceLinks() }

    private fun cleanAlias(alias: String): String? = alias.trim().takeIf { clean ->
        clean.isNotEmpty() && clean.codePointCount(0, clean.length) <= MaxAliasLength && clean.none { it.isISOControl() }
    }

    private fun locationProblem(fix: LocationReading.Ready, generation: Long): PlaceRejection? = when {
        fix.generation != generation -> PlaceRejection.OLD_GENERATION
        !fix.latitude.isFinite() || !fix.longitude.isFinite() || fix.latitude !in -90.0..90.0 || fix.longitude !in -180.0..180.0 ->
            PlaceRejection.LOCATION_UNAVAILABLE
        fix.ageMillis < 0 || fix.ageMillis > locationPolicy.maxAgeMillis -> PlaceRejection.LOCATION_STALE
        fix.accuracyMeters == null || !fix.accuracyMeters.isFinite() || fix.accuracyMeters > locationPolicy.maxAccuracyMeters ->
            PlaceRejection.LOCATION_IMPRECISE
        else -> null
    }

    private suspend fun placeWrite(block: suspend () -> PlaceWrite): PlaceWrite = writes.withLock {
        try {
            database.withTransaction { block() }
        } catch (_: PrivacyStorageException) {
            PlaceWrite.PrivacyLocked
        }
    }

    /**
     * Recovery after [MobilityWrite.PrivacyLocked]: deletes the unreadable baseline. The town, pieces, reward history and places
     * stay, and nothing is restored from a guess. Place aliases share the key, so it is destroyed only when it no longer works
     * at all (those aliases are unreadable then anyway); a damaged baseline alone never costs the aliases.
     * The next reading starts a new baseline.
     */
    suspend fun resetMobilityRecord() = writes.withLock {
        database.withTransaction {
            val before = checkNotNull(dao.privacy())
            dao.deleteMobility()
            dao.savePrivacy(before.copy(consentGeneration = before.consentGeneration + 1))
        }
        withContext(Dispatchers.IO) { if (!keyWorks()) crypto.destroyKey() }
    }

    /** Seals and opens a throwaway value. A missing key is created, as the next real seal would do. */
    private fun keyWorks(): Boolean = try {
        crypto.open(crypto.seal(KeyProbe, KeyProbeAad), KeyProbeAad).contentEquals(KeyProbe)
    } catch (_: PrivacyStorageException) {
        false
    }

    suspend fun execute(command: BuildCommand, token: SessionToken): WriteResult =
        commit(token) { ConstructionRules.advance(it, command, catalog) }

    internal suspend fun commit(token: SessionToken, change: (TownState) -> RuleResult): WriteResult = writes.withLock {
        database.withTransaction {
            val before = checkNotNull(readTown())
            // Approval is the boundary: a transaction approved here may finish after restriction.
            if (!gate.approve(token)) return@withTransaction WriteResult.SessionExpired
            when (val result = change(before)) {
                is RuleResult.Rejected -> WriteResult.Rejected(result.reason)
                is RuleResult.Accepted -> {
                    val after = result.town
                    if (before != after) {
                        dao.saveBuildings(after.buildings.filter { before.buildings[it.key] != it.value }
                            .map { BuildingEntity(it.key, it.value) })
                        dao.updateTown(after.toEntity())
                    }
                    WriteResult.Saved
                }
            }
        }
    }

    /**
     * Applies one distance reading. [today] is read once, after approval, so a write never straddles two dates.
     * The reward, its date and the new baseline are stored together or not at all.
     */
    suspend fun recordMobility(reading: MobilityReading, token: SessionToken, today: () -> LocalDate): MobilityWrite {
        if (!vehicleChecksOpen.get()) return MobilityWrite.ConsentOff
        return writes.withLock {
            try {
                database.withTransaction {
                    // Only the town row: a reward never touches buildings or the legacy placement tables.
                    val before = checkNotNull(dao.town())
                    if (!gate.approve(token)) return@withTransaction MobilityWrite.SessionExpired
                    val privacy = checkNotNull(dao.privacy())
                    // Withdrawal deleted the baseline; a reading that arrives afterwards must not recreate it.
                    if (!privacy.vehicleConsent || !vehicleChecksOpen.get()) return@withTransaction MobilityWrite.ConsentOff
                    val baseline = dao.mobility()?.let { SealedBaseline.open(crypto, it.sealed) }
                    val state = MobilityState(baseline, before.lastRewardDay?.let(LocalDate::ofEpochDay), before.rewardCount)
                    val result = RewardRules.observe(state, reading, privacy.consentGeneration, today(), rewardPolicy)
                    result.state.baseline?.let { if (it != baseline) dao.saveMobility(MobilityEntity(sealed = SealedBaseline.seal(crypto, it))) }
                    if (result.outcome == MobilityOutcome.REWARDED) {
                        dao.updateTown(before.copy(
                            pieces = before.pieces + result.piecesGranted,
                            revision = before.revision + 1,
                            rewardCount = result.state.rewardCount,
                            lastRewardDay = result.state.lastRewardDay?.toEpochDay(),
                        ))
                    }
                    MobilityWrite.Checked(result.outcome, result.piecesGranted)
                }
            } catch (_: PrivacyStorageException) {
                // Thrown inside the transaction, so nothing was written. An unreadable baseline is never treated as "no baseline".
                MobilityWrite.PrivacyLocked
            }
        }
    }

    private suspend fun readTown(): TownState? {
        val town = dao.town() ?: return null
        return TownState(
            town.pieces,
            dao.owned().map { it.blueprintId }.toSet(),
            dao.placements().map { Placement(it.id, it.blueprintId, it.slotId) },
            town.revision,
            dao.buildings().associate { it.plotId to it.level },
            town.demoPiecesClaimed,
            town.rewardCount,
            town.lastRewardDay?.let(LocalDate::ofEpochDay),
        )
    }

    private fun PrivacyEntity?.toState() = this?.let { PrivacyState(it.vehicleConsent, it.consentGeneration, it.locationConsent) } ?: PrivacyState()

    private fun TownState.toEntity() = TownEntity(pieces = pieces, revision = revision, demoPiecesClaimed = demoPiecesClaimed,
        rewardCount = rewardCount, lastRewardDay = lastRewardDay?.toEpochDay())
}
