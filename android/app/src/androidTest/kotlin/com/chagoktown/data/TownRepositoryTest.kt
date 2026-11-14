package com.chagoktown.data

import android.content.Context
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.withTransaction
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import com.chagoktown.data.local.MIGRATION_1_2
import com.chagoktown.data.local.MIGRATION_2_3
import com.chagoktown.data.local.MIGRATION_3_4
import com.chagoktown.data.local.MIGRATION_4_5
import com.chagoktown.data.local.PlaceKind
import com.chagoktown.data.local.PlaceLinkEntity
import com.chagoktown.data.local.TownDatabase
import com.chagoktown.platform.LocationReading
import com.chagoktown.data.privacy.KeystoreCryptoBox
import com.chagoktown.data.privacy.SealedBaseline
import com.chagoktown.game.BuildCommand
import com.chagoktown.game.MobilityBaseline
import com.chagoktown.game.MobilityOutcome
import com.chagoktown.game.MobilityReading
import com.chagoktown.platform.PlayAccess
import com.chagoktown.session.InteractionGate
import com.chagoktown.ui.TownViewModel
import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.flow.first
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TownRepositoryTest {
    private val context: Context = ApplicationProvider.getApplicationContext()
    private val databaseName = "test-${UUID.randomUUID()}.db"
    private lateinit var database: TownDatabase
    private lateinit var repository: TownRepository
    private val gate = InteractionGate()
    private val crypto = KeystoreCryptoBox("test-${UUID.randomUUID()}")
    @Volatile private var beforeTownUpdate: (() -> Unit)? = null

    private fun openDatabase() {
        database = Room.databaseBuilder(context, TownDatabase::class.java, databaseName)
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5)
            .setQueryCallback(object : RoomDatabase.QueryCallback {
                override fun onQuery(sqlQuery: String, bindArgs: List<Any?>) {
                    if (sqlQuery.startsWith("UPDATE", ignoreCase = true) && sqlQuery.contains("town_state")) beforeTownUpdate?.invoke()
                }
            }, java.util.concurrent.Executor { it.run() }).build()
        repository = TownRepository(database, loadTownLayout(context.assets).catalog, gate, crypto)
    }

    @Before fun setUp() {
        gate.setPlayAccess(PlayAccess.Allowed)
        gate.setResumed(true)
        openDatabase()
    }

    @After fun tearDown() {
        database.close()
        context.deleteDatabase(databaseName)
        crypto.destroyKey()
    }

    @Test fun repeatedConcurrentInitializationGivesOnlyOneStarterGrant() = runBlocking {
        coroutineScope { List(20) { async(Dispatchers.Default) { repository.initialize() } }.awaitAll() }
        assertEquals(3, repository.snapshot()!!.pieces)
        assertEquals(mapOf("home" to 1), repository.snapshot()!!.buildings)
    }

    @Test fun concurrentConstructionRetriesSpendOnlyOnce() = runBlocking {
        repository.initialize()
        val token = gate.token()!!
        val results = coroutineScope {
            List(20) { async(Dispatchers.Default) { repository.execute(BuildCommand("cafe", 0), token) } }.awaitAll()
        }
        assertEquals(1, results.count { it == WriteResult.Saved })
        val town = repository.snapshot()!!
        assertEquals(0, town.pieces)
        assertEquals(1, town.buildings["cafe"])
        assertEquals(1L, town.revision)
    }

    @Test fun closingAndReopeningRestoresBalanceAndLevelsWithoutAnotherGrant() = runBlocking {
        repository.initialize()
        repository.execute(BuildCommand("cafe", 0), gate.token()!!)
        val saved = repository.snapshot()
        database.close()
        openDatabase()
        repository.initialize()
        assertEquals(saved, repository.snapshot())
    }

    @Test fun storageFailureRollsBackTheBuildingAndBalanceTogether() = runBlocking {
        repository.initialize()
        database.openHelper.writableDatabase.execSQL("CREATE TRIGGER fail_save BEFORE UPDATE ON town_state BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        var failed = false
        try { repository.execute(BuildCommand("cafe", 0), gate.token()!!) }
        catch (_: android.database.sqlite.SQLiteException) { failed = true }
        assertTrue(failed)
        assertEquals(3, repository.snapshot()!!.pieces)
        assertFalse("cafe" in repository.snapshot()!!.buildings)
        database.openHelper.writableDatabase.execSQL("DROP TRIGGER fail_save")
        assertEquals(WriteResult.Saved, repository.execute(BuildCommand("cafe", 0), gate.token()!!))
    }

    @Test fun staleCommandQueuedBeforeRestrictionCannotCommitAfterReturn() = runBlocking {
        withTimeout(10_000) {
            repository.initialize()
            val token = gate.token()!!
            val entered = CompletableDeferred<Unit>()
            val release = CompletableDeferred<Unit>()
            val blocker = async(Dispatchers.Default) { database.withTransaction { entered.complete(Unit); release.await() } }
            entered.await()
            val queued = async(Dispatchers.Default) { repository.execute(BuildCommand("cafe", 0), token) }
            gate.setPlayAccess(PlayAccess.Restricted)
            gate.setPlayAccess(PlayAccess.Allowed)
            release.complete(Unit)
            blocker.await()
            assertEquals(WriteResult.SessionExpired, queued.await())
            assertEquals(3, repository.snapshot()!!.pieces)
        }
    }

    @Test fun restrictionAfterApprovalCommitsTheWholeBuilding() = runBlocking {
        repository.initialize()
        beforeTownUpdate = { gate.setPlayAccess(PlayAccess.Restricted) }
        assertEquals(WriteResult.Saved, repository.execute(BuildCommand("cafe", 0), gate.token()!!))
        assertEquals(PlayAccess.Restricted, gate.state.value.access)
        assertEquals(0, repository.snapshot()!!.pieces)
        assertEquals(1, repository.snapshot()!!.buildings["cafe"])
    }

    @Test fun migrationPreservesLegacyBalanceOwnershipAndEveryPlacement() = runBlocking {
        database.close()
        context.openOrCreateDatabase(databaseName, Context.MODE_PRIVATE, null).use { old ->
            old.execSQL("CREATE TABLE town_state (id INTEGER NOT NULL PRIMARY KEY, pieces INTEGER NOT NULL, revision INTEGER NOT NULL)")
            old.execSQL("CREATE TABLE owned_blueprints (blueprintId TEXT NOT NULL PRIMARY KEY)")
            old.execSQL("CREATE TABLE placements (id TEXT NOT NULL PRIMARY KEY, blueprintId TEXT NOT NULL, slotId TEXT NOT NULL, FOREIGN KEY(blueprintId) REFERENCES owned_blueprints(blueprintId) ON DELETE RESTRICT)")
            old.execSQL("CREATE UNIQUE INDEX index_placements_slotId ON placements(slotId)")
            old.execSQL("CREATE INDEX index_placements_blueprintId ON placements(blueprintId)")
            old.execSQL("INSERT INTO town_state VALUES (1, 2, 7)")
            old.execSQL("INSERT INTO owned_blueprints VALUES ('house.basic'), ('bench.basic')")
            old.execSQL("INSERT INTO placements VALUES ('starter.house','house.basic','building.1'), ('old-bench','bench.basic','decoration.4')")
            old.version = 1
        }
        openDatabase()
        repository.initialize()
        val town = repository.snapshot()!!
        assertEquals(2, town.pieces)
        assertEquals(7L, town.revision)
        assertEquals(setOf("house.basic", "bench.basic"), town.ownedBlueprints)
        assertEquals(2, town.placements.size)
        assertEquals("decoration.4", town.placements.single { it.id == "old-bench" }.slotId)
        assertEquals(mapOf("home" to 1), town.buildings)
        assertFalse(town.demoPiecesClaimed)
        assertEquals(2, repository.snapshot()!!.pieces)
    }

    @Test fun initialReadFailureShowsAnErrorInsteadOfStayingLockedOrLoading() = runBlocking {
        repository.initialize()
        database.close()
        val store = ViewModelStore()
        lateinit var model: TownViewModel
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.runOnMainSync {
            model = ViewModelProvider(store, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    TownViewModel(repository, gate, { _ -> MobilityReading.Unavailable }, { _ -> LocationReading.Unavailable }, LocalDate::now) as T
            })[TownViewModel::class.java]
        }
        try {
            val state = withTimeout(5_000) { model.state.first { it.gate.playable && it.message != null } }
            assertNull(state.town)
        } finally { instrumentation.runOnMainSync { store.clear() } }
    }

    // Movement rewards. Distances are fake test values; the reward size is the temporary demo policy.
    private val day1 = LocalDate.of(2026, 11, 1)
    /** A reading tagged with the consent generation current when it was requested, like the ViewModel does. */
    private suspend fun reading(distance: Double) = MobilityReading.Ready(distance, "test.km", repository.privacySnapshot().generation)
    private suspend fun record(distance: Double, day: LocalDate) = repository.recordMobility(reading(distance), gate.token()!!) { day }
    private fun checked(outcome: MobilityOutcome, pieces: Int = 0) = MobilityWrite.Checked(outcome, pieces)
    private suspend fun startTownWithVehicleData() {
        repository.initialize()
        repository.setVehicleConsent(true)
    }
    private suspend fun storedBaseline() = database.townDao().mobility()

    @Test fun sevenCommuteDaysThroughRoomPayOncePerDayAndSurviveReopen() = runBlocking {
        startTownWithVehicleData()
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(10_000.0, day1.minusDays(1)))
        var odometer = 10_000.0
        repeat(7) { offset ->
            val day = day1.plusDays(offset.toLong())
            odometer += 12.0
            assertEquals(checked(MobilityOutcome.REWARDED, 3), record(odometer, day))
            odometer += 12.0
            assertEquals(checked(MobilityOutcome.CONSUMED), record(odometer, day))
        }
        val town = repository.snapshot()!!
        assertEquals(24, town.pieces)
        assertEquals(7, town.rewardCount)
        assertEquals(day1.plusDays(6), town.lastRewardDay)
        assertEquals(7L, town.revision)

        database.close()
        openDatabase()
        repository.initialize()
        assertEquals(town, repository.snapshot())
        // The baseline survived the reopen, so the movement consumed on the last day is not paid again tomorrow.
        assertEquals(checked(MobilityOutcome.BELOW_THRESHOLD), record(odometer, day1.plusDays(7)))
    }

    @Test fun daysWithoutACheckArePaidTogetherUpToAWeek() = runBlocking {
        startTownWithVehicleData()
        record(10_000.0, day1.minusDays(1))
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(10_012.0, day1))
        assertEquals(checked(MobilityOutcome.REWARDED, 12), record(10_200.0, day1.plusDays(4)))
        assertEquals(checked(MobilityOutcome.REWARDED, 21), record(10_500.0, day1.plusDays(34)))
        val town = repository.snapshot()!!
        assertEquals(3 + 3 + 12 + 21, town.pieces)
        assertEquals(3, town.rewardCount)
        assertEquals(day1.plusDays(34), town.lastRewardDay)
    }

    @Test fun concurrentDuplicateChecksPayOnlyOnce() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        val token = gate.token()!!
        val results = coroutineScope {
            List(20) { async(Dispatchers.Default) { repository.recordMobility(reading(130.0), token) { day1.plusDays(1) } } }.awaitAll()
        }
        assertEquals(1, results.count { it == checked(MobilityOutcome.REWARDED, 3) })
        assertEquals(6, repository.snapshot()!!.pieces)
        assertEquals(1, repository.snapshot()!!.rewardCount)
    }

    @Test fun storageFailureRollsBackTheRewardAndBaselineTogether() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        database.openHelper.writableDatabase.execSQL("CREATE TRIGGER fail_save BEFORE UPDATE ON town_state BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        var failed = false
        try { record(130.0, day1.plusDays(1)) }
        catch (_: android.database.sqlite.SQLiteException) { failed = true }
        assertTrue(failed)
        val town = repository.snapshot()!!
        assertEquals(3, town.pieces)
        assertEquals(0, town.rewardCount)
        assertNull(town.lastRewardDay)
        database.openHelper.writableDatabase.execSQL("DROP TRIGGER fail_save")
        // Had the baseline moved without the reward, this retry would find no new movement.
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(130.0, day1.plusDays(1)))
    }

    @Test fun readingFromBeforeRestrictionIsDiscardedWithoutStoringABaseline() = runBlocking {
        startTownWithVehicleData()
        val token = gate.token()!!
        gate.setPlayAccess(PlayAccess.Restricted)
        gate.setPlayAccess(PlayAccess.Allowed)
        assertEquals(MobilityWrite.SessionExpired, repository.recordMobility(reading(100.0), token) { day1 })
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(500.0, day1))
    }

    @Test fun constructionAndWithdrawalKeepTheRewardHistory() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        record(130.0, day1)
        assertEquals(WriteResult.Saved, repository.execute(BuildCommand("cafe", 0), gate.token()!!))
        repository.snapshot()!!.let {
            assertEquals(3, it.pieces)
            assertEquals(1, it.rewardCount)
            assertEquals(day1, it.lastRewardDay)
        }
        // Withdrawal deletes only the baseline. After re-consent the next reading starts over without paying past distance.
        repository.setVehicleConsent(false)
        repository.setVehicleConsent(true)
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(9_000.0, day1.plusDays(3)))
        repository.snapshot()!!.let {
            assertEquals(3, it.pieces)
            assertEquals(1, it.rewardCount)
            assertEquals(day1, it.lastRewardDay)
        }
    }

    @Test fun migrationFromV2KeepsTheTownAndStartsWithoutRewardHistory() = runBlocking {
        database.close()
        context.openOrCreateDatabase(databaseName, Context.MODE_PRIVATE, null).use { old ->
            old.execSQL("CREATE TABLE town_state (id INTEGER NOT NULL, pieces INTEGER NOT NULL, revision INTEGER NOT NULL, demoPiecesClaimed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(id))")
            old.execSQL("CREATE TABLE owned_blueprints (blueprintId TEXT NOT NULL, PRIMARY KEY(blueprintId))")
            old.execSQL("CREATE TABLE placements (id TEXT NOT NULL, blueprintId TEXT NOT NULL, slotId TEXT NOT NULL, PRIMARY KEY(id), FOREIGN KEY(blueprintId) REFERENCES owned_blueprints(blueprintId) ON UPDATE NO ACTION ON DELETE RESTRICT)")
            old.execSQL("CREATE UNIQUE INDEX index_placements_slotId ON placements(slotId)")
            old.execSQL("CREATE INDEX index_placements_blueprintId ON placements(blueprintId)")
            old.execSQL("CREATE TABLE buildings (plotId TEXT NOT NULL, level INTEGER NOT NULL, PRIMARY KEY(plotId))")
            old.execSQL("INSERT INTO town_state VALUES (1, 17, 11, 1)")
            old.execSQL("INSERT INTO owned_blueprints VALUES ('house.basic'), ('bench.basic')")
            old.execSQL("INSERT INTO placements VALUES ('starter.house','house.basic','building.1'), ('old-bench','bench.basic','decoration.4')")
            old.execSQL("INSERT INTO buildings VALUES ('home', 3), ('cafe', 3), ('cathedral', 3)")
            old.version = 2
        }
        openDatabase()
        repository.initialize()
        val town = repository.snapshot()!!
        assertEquals(17, town.pieces)
        assertEquals(11L, town.revision)
        assertTrue(town.demoPiecesClaimed)
        assertEquals(mapOf("home" to 3, "cafe" to 3, "cathedral" to 3), town.buildings)
        assertEquals(setOf("house.basic", "bench.basic"), town.ownedBlueprints)
        assertEquals(2, town.placements.size)
        assertEquals(0, town.rewardCount)
        assertNull(town.lastRewardDay)
        // Nothing is read until the user turns vehicle data on, and then there is no reward for the distance driven before.
        assertEquals(MobilityWrite.ConsentOff, record(10_000.0, day1))
        repository.setVehicleConsent(true)
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(10_000.0, day1))
        assertEquals(17, repository.snapshot()!!.pieces)
    }

    // Privacy: consent, withdrawal and the sealed baseline.

    @Test fun vehicleDataStartsOffAndNothingIsStoredUntilTurnedOn() = runBlocking {
        repository.initialize()
        assertEquals(PrivacyState(vehicleConsent = false, generation = 0), repository.privacySnapshot())
        assertEquals(MobilityWrite.ConsentOff, record(100.0, day1))
        assertNull(storedBaseline())
    }

    @Test fun withdrawalDeletesOnlyTheBaselineAndRefusesLaterReadings() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(130.0, day1))
        val consented = repository.privacySnapshot()
        val lateReading = reading(170.0)

        repository.setVehicleConsent(false)
        assertNull(storedBaseline())
        assertEquals(PrivacyState(vehicleConsent = false, generation = consented.generation + 1), repository.privacySnapshot())
        repository.snapshot()!!.let {
            assertEquals(6, it.pieces)
            assertEquals(1, it.rewardCount)
            assertEquals(day1, it.lastRewardDay)
        }
        assertEquals(MobilityWrite.ConsentOff, repository.recordMobility(lateReading, gate.token()!!) { day1.plusDays(1) })
        assertNull(storedBaseline())
    }

    @Test fun readingRequestedBeforeWithdrawalCannotComeBackAfterReconsent() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        val stale = reading(160.0)
        repository.setVehicleConsent(false)
        repository.setVehicleConsent(true)
        // The old generation is discarded even though consent is on again: no baseline, no reward.
        assertEquals(checked(MobilityOutcome.IGNORED), repository.recordMobility(stale, gate.token()!!) { day1.plusDays(1) })
        assertNull(storedBaseline())
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(170.0, day1.plusDays(1)))
        assertEquals(3, repository.snapshot()!!.pieces)
    }

    @Test fun reconsentingOnTheSameDayIsNotAnotherReward() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(112.0, day1))
        repository.setVehicleConsent(false)
        repository.setVehicleConsent(true)
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(124.0, day1))
        assertEquals(checked(MobilityOutcome.CONSUMED), record(136.0, day1))
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(148.0, day1.plusDays(1)))
        assertEquals(9, repository.snapshot()!!.pieces)
    }

    @Test fun withdrawalRacingACheckNeverLeavesABaseline() = runBlocking {
        startTownWithVehicleData()
        repeat(20) { round ->
            repository.setVehicleConsent(true)
            val token = gate.token()!!
            val pending = reading(1_000.0 + round)
            coroutineScope {
                val check = async(Dispatchers.Default) { repository.recordMobility(pending, token) { day1 } }
                val withdraw = async(Dispatchers.Default) { repository.setVehicleConsent(false) }
                check.await()
                withdraw.await()
            }
            assertNull("round $round", storedBaseline())
        }
    }

    @Test fun baselineIsStoredOnlyAsAnEnvelopeBoundToItsRow() = runBlocking {
        startTownWithVehicleData()
        record(12_345.678, day1)
        val columns = database.query("SELECT * FROM mobility_state", null).use { it.columnNames.toList() }
        assertEquals(listOf("id", "sealed"), columns)
        val sealed = storedBaseline()!!.sealed
        val distanceBytes = java.nio.ByteBuffer.allocate(8).putDouble(12_345.678).array()
        assertFalse(sealed.contains(distanceBytes))
        assertFalse(sealed.contains("test.km".encodeToByteArray()))
        assertEquals(MobilityBaseline(12_345.678, "test.km"), SealedBaseline.open(crypto, sealed))
        // The same bytes do not open as any other field.
        assertThrowsPrivacy { crypto.open(sealed, "chagoktown/mobility_state/2/baseline/v1".encodeToByteArray()) }
    }

    @Test fun unreadableBaselineLocksChecksUntilTheUserResetsIt() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(112.0, day1))
        val corrupted = storedBaseline()!!.sealed.copyOf().also { it[it.size - 1] = (it.last().toInt() xor 0x01).toByte() }
        database.openHelper.writableDatabase.execSQL("UPDATE mobility_state SET sealed = ?", arrayOf<Any>(corrupted))

        assertEquals(MobilityWrite.PrivacyLocked, record(200.0, day1.plusDays(1)))
        // Nothing replaced the envelope with a guessed or fresh baseline, and the town is untouched.
        assertArrayEquals(corrupted, storedBaseline()!!.sealed)
        repository.snapshot()!!.let {
            assertEquals(6, it.pieces)
            assertEquals(1, it.rewardCount)
        }

        repository.resetMobilityRecord()
        assertNull(storedBaseline())
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(200.0, day1.plusDays(1)))
        assertEquals(checked(MobilityOutcome.REWARDED, 3), record(212.0, day1.plusDays(1)))
        assertEquals(9, repository.snapshot()!!.pieces)
    }

    @Test fun lostKeyIsNotSilentlyReplacedWithANewOne() = runBlocking {
        startTownWithVehicleData()
        record(100.0, day1)
        val envelope = storedBaseline()!!.sealed
        crypto.destroyKey()
        assertEquals(MobilityWrite.PrivacyLocked, record(150.0, day1.plusDays(1)))
        assertArrayEquals(envelope, storedBaseline()!!.sealed)
        assertEquals(3, repository.snapshot()!!.pieces)
        repository.resetMobilityRecord()
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(150.0, day1.plusDays(1)))
    }

    @Test fun migrationFromV3DropsThePlaintextBaselineAndStartsWithVehicleDataOff() = runBlocking {
        database.close()
        context.openOrCreateDatabase(databaseName, Context.MODE_PRIVATE, null).use { old ->
            old.execSQL("CREATE TABLE town_state (id INTEGER NOT NULL, pieces INTEGER NOT NULL, revision INTEGER NOT NULL, demoPiecesClaimed INTEGER NOT NULL DEFAULT 0, rewardCount INTEGER NOT NULL DEFAULT 0, lastRewardDay INTEGER, PRIMARY KEY(id))")
            old.execSQL("CREATE TABLE owned_blueprints (blueprintId TEXT NOT NULL, PRIMARY KEY(blueprintId))")
            old.execSQL("CREATE TABLE placements (id TEXT NOT NULL, blueprintId TEXT NOT NULL, slotId TEXT NOT NULL, PRIMARY KEY(id), FOREIGN KEY(blueprintId) REFERENCES owned_blueprints(blueprintId) ON UPDATE NO ACTION ON DELETE RESTRICT)")
            old.execSQL("CREATE UNIQUE INDEX index_placements_slotId ON placements(slotId)")
            old.execSQL("CREATE INDEX index_placements_blueprintId ON placements(blueprintId)")
            old.execSQL("CREATE TABLE buildings (plotId TEXT NOT NULL, level INTEGER NOT NULL, PRIMARY KEY(plotId))")
            old.execSQL("CREATE TABLE mobility_state (id INTEGER NOT NULL, distance REAL NOT NULL, source TEXT NOT NULL, PRIMARY KEY(id))")
            old.execSQL("INSERT INTO town_state VALUES (1, 5, 20, 1, 3, 20770)")
            old.execSQL("INSERT INTO buildings VALUES ('home', 3), ('cafe', 2)")
            old.execSQL("INSERT INTO mobility_state VALUES (1, 10048.0, 'demo.km')")
            old.version = 3
        }
        openDatabase()
        repository.initialize()
        val town = repository.snapshot()!!
        assertEquals(5, town.pieces)
        assertEquals(20L, town.revision)
        assertEquals(3, town.rewardCount)
        assertEquals(LocalDate.ofEpochDay(20770), town.lastRewardDay)
        assertEquals(mapOf("home" to 3, "cafe" to 2), town.buildings)
        assertNull(storedBaseline())
        assertEquals(listOf("id", "sealed"), database.query("SELECT * FROM mobility_state", null).use { it.columnNames.toList() })
        assertEquals(PrivacyState(vehicleConsent = false, generation = 0), repository.privacySnapshot())
        assertEquals(MobilityWrite.ConsentOff, record(10_060.0, LocalDate.ofEpochDay(20771)))
        repository.setVehicleConsent(true)
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(10_060.0, LocalDate.ofEpochDay(20771)))
        assertEquals(5, repository.snapshot()!!.pieces)
    }

    // Place links. Coordinates are synthetic test values.

    private suspend fun fix(accuracy: Float? = 8f, age: Long = 0) =
        LocationReading.Ready(37.4, 127.1, accuracy, age, repository.privacySnapshot().generation)
    private suspend fun link(plotId: String) = database.townDao().placeLink(plotId)
    private suspend fun buildCafe() = assertEquals(WriteResult.Saved, repository.execute(BuildCommand("cafe", 0), gate.token()!!))
    private fun aad(plotId: String, field: String) = "chagoktown/place_links/$plotId/$field/v1".encodeToByteArray()

    @Test fun aliasIsStoredOnlyAsAnEnvelopeThatOpensForItsOwnBuilding() = runBlocking {
        repository.initialize()
        assertEquals(PlaceWrite.Saved, repository.saveAlias("home", "  단골 카페 앞  ", gate.token()!!))
        val stored = link("home")!!
        assertEquals(PlaceKind.MANUAL, stored.kind)
        assertNull(stored.sealedCoordinates)
        assertFalse(stored.sealedAlias.contains("단골 카페 앞".encodeToByteArray()))
        assertEquals(AliasRead.Ready("단골 카페 앞"), repository.revealAlias("home"))
        assertEquals(mapOf("home" to PlaceKind.MANUAL), repository.places.first())
        // The same envelope moved to another building does not open there.
        buildCafe()
        database.townDao().savePlaceLink(PlaceLinkEntity("cafe", PlaceKind.MANUAL, stored.sealedAlias, null))
        assertEquals(AliasRead.Locked, repository.revealAlias("cafe"))
    }

    @Test fun aliasNeedsABuiltBuildingAValidNameAndACurrentSession() = runBlocking {
        repository.initialize()
        val token = gate.token()!!
        assertEquals(PlaceWrite.Rejected(PlaceRejection.NO_BUILDING), repository.saveAlias("cafe", "카페", token))
        assertEquals(PlaceWrite.Rejected(PlaceRejection.INVALID_ALIAS), repository.saveAlias("home", "   ", token))
        assertEquals(PlaceWrite.Rejected(PlaceRejection.INVALID_ALIAS), repository.saveAlias("home", "가".repeat(MaxAliasLength + 1), token))
        assertEquals(PlaceWrite.Saved, repository.saveAlias("home", "가".repeat(MaxAliasLength), token))
        assertEquals(PlaceWrite.Saved, repository.saveAlias("home", "새 이름", token))
        assertEquals(AliasRead.Ready("새 이름"), repository.revealAlias("home"))
        assertEquals(1, repository.places.first().size)
        gate.setPlayAccess(PlayAccess.Restricted)
        gate.setPlayAccess(PlayAccess.Allowed)
        assertEquals(PlaceWrite.SessionExpired, repository.saveAlias("home", "늦은 이름", token))
        assertEquals(AliasRead.Ready("새 이름"), repository.revealAlias("home"))
    }

    @Test fun locationLinkNeedsConsentAndAFreshPreciseFixFromTheCurrentGeneration() = runBlocking {
        repository.initialize()
        assertEquals(PlaceWrite.ConsentOff, repository.linkCurrentPlace("home", fix(), "집", gate.token()!!))
        repository.setLocationConsent(true)
        val token = gate.token()!!
        assertEquals(PlaceWrite.Rejected(PlaceRejection.LOCATION_STALE), repository.linkCurrentPlace("home", fix(age = 10 * 60_000), "집", token))
        assertEquals(PlaceWrite.Rejected(PlaceRejection.LOCATION_IMPRECISE), repository.linkCurrentPlace("home", fix(accuracy = 500f), "집", token))
        assertEquals(PlaceWrite.Rejected(PlaceRejection.LOCATION_IMPRECISE), repository.linkCurrentPlace("home", fix(accuracy = null), "집", token))
        assertEquals(PlaceWrite.Rejected(PlaceRejection.LOCATION_UNAVAILABLE), repository.linkCurrentPlace("home", LocationReading.Unavailable, "집", token))
        val requestedBefore = fix()
        repository.setLocationConsent(false)
        repository.setLocationConsent(true)
        assertEquals(PlaceWrite.Rejected(PlaceRejection.OLD_GENERATION), repository.linkCurrentPlace("home", requestedBefore, "집", token))
        assertNull(link("home"))

        assertEquals(PlaceWrite.Saved, repository.linkCurrentPlace("home", fix(), "집", token))
        val stored = link("home")!!
        assertEquals(PlaceKind.LOCATION, stored.kind)
        val coordinates = stored.sealedCoordinates!!
        assertFalse(coordinates.contains(java.nio.ByteBuffer.allocate(8).putDouble(37.4).array()))
        assertEquals(16, crypto.open(coordinates, aad("home", "coordinates")).size)
        assertThrowsPrivacy { crypto.open(coordinates, aad("cafe", "coordinates")) }
        assertThrowsPrivacy { crypto.open(coordinates, aad("home", "alias")) }
    }

    @Test fun renamingALocationLinkKeepsItsCoordinates() = runBlocking {
        repository.initialize()
        repository.setLocationConsent(true)
        repository.linkCurrentPlace("home", fix(), "집", gate.token()!!)
        val coordinates = link("home")!!.sealedCoordinates!!
        assertEquals(PlaceWrite.Saved, repository.saveAlias("home", "우리 집", gate.token()!!))
        assertEquals(PlaceKind.LOCATION, link("home")!!.kind)
        assertArrayEquals(coordinates, link("home")!!.sealedCoordinates)
    }

    @Test fun locationWithdrawalDeletesOnlyLocationLinksAndKeepsEveryBuilding() = runBlocking {
        repository.initialize()
        buildCafe()
        repository.setLocationConsent(true)
        assertEquals(PlaceWrite.Saved, repository.linkCurrentPlace("home", fix(), "집", gate.token()!!))
        assertEquals(PlaceWrite.Saved, repository.saveAlias("cafe", "회사 앞", gate.token()!!))
        val town = repository.snapshot()
        val lateFix = fix()

        repository.setLocationConsent(false)
        assertNull(link("home"))
        assertEquals(mapOf("cafe" to PlaceKind.MANUAL), repository.places.first())
        assertEquals(AliasRead.Ready("회사 앞"), repository.revealAlias("cafe"))
        assertEquals(town, repository.snapshot())
        assertEquals(PlaceWrite.ConsentOff, repository.linkCurrentPlace("home", lateFix, "집", gate.token()!!))
        assertNull(link("home"))
    }

    @Test fun unlinkAndDeleteAllRemovePlacesButNotTheTownOrConsent() = runBlocking {
        repository.initialize()
        buildCafe()
        repository.setLocationConsent(true)
        repository.linkCurrentPlace("home", fix(), "집", gate.token()!!)
        repository.saveAlias("cafe", "회사 앞", gate.token()!!)
        val town = repository.snapshot()
        assertEquals(PlaceWrite.Saved, repository.unlinkPlace("home", gate.token()!!))
        assertEquals(mapOf("cafe" to PlaceKind.MANUAL), repository.places.first())
        repository.saveAlias("home", "다시", gate.token()!!)
        repository.deleteAllPlaces()
        assertTrue(repository.places.first().isEmpty())
        assertEquals(town, repository.snapshot())
        assertTrue(repository.privacySnapshot().locationConsent)
    }

    @Test fun unreadableAliasIsReportedAndUnlinkingClearsIt() = runBlocking {
        repository.initialize()
        repository.saveAlias("home", "집", gate.token()!!)
        val corrupted = link("home")!!.sealedAlias.copyOf().also { it[it.size - 1] = (it.last().toInt() xor 0x01).toByte() }
        database.openHelper.writableDatabase.execSQL("UPDATE place_links SET sealedAlias = ?", arrayOf<Any>(corrupted))
        assertEquals(AliasRead.Locked, repository.revealAlias("home"))
        assertEquals(PlaceWrite.Saved, repository.unlinkPlace("home", gate.token()!!))
        assertEquals(AliasRead.Missing, repository.revealAlias("home"))
    }

    @Test fun unlinkFromBeforeARestrictionIsNotSaved() = runBlocking {
        repository.initialize()
        repository.saveAlias("home", "집", gate.token()!!)
        val token = gate.token()!!
        gate.setPlayAccess(PlayAccess.Restricted)
        gate.setPlayAccess(PlayAccess.Allowed)
        assertEquals(PlaceWrite.SessionExpired, repository.unlinkPlace("home", token))
        assertEquals(AliasRead.Ready("집"), repository.revealAlias("home"))
        assertEquals(PlaceWrite.Saved, repository.unlinkPlace("home", gate.token()!!))
        assertEquals(AliasRead.Missing, repository.revealAlias("home"))
    }

    @Test fun resettingAnUnreadableBaselineKeepsPlaceAliasesReadable() = runBlocking {
        startTownWithVehicleData()
        repository.saveAlias("home", "집", gate.token()!!)
        record(100.0, day1)
        val corrupted = storedBaseline()!!.sealed.copyOf().also { it[it.size - 1] = (it.last().toInt() xor 0x01).toByte() }
        database.openHelper.writableDatabase.execSQL("UPDATE mobility_state SET sealed = ?", arrayOf<Any>(corrupted))
        assertEquals(MobilityWrite.PrivacyLocked, record(150.0, day1.plusDays(1)))

        // The key still works, so the reset clears only the baseline.
        repository.resetMobilityRecord()
        assertEquals(AliasRead.Ready("집"), repository.revealAlias("home"))
        assertEquals(checked(MobilityOutcome.BASELINE_SET), record(150.0, day1.plusDays(1)))
    }

    @Test fun linkRacingLocationWithdrawalNeverLeavesALocationLink() = runBlocking {
        repository.initialize()
        repeat(20) { round ->
            repository.setLocationConsent(true)
            val token = gate.token()!!
            val pending = fix()
            coroutineScope {
                val linking = async(Dispatchers.Default) { repository.linkCurrentPlace("home", pending, "집 $round", token) }
                val withdraw = async(Dispatchers.Default) { repository.setLocationConsent(false) }
                linking.await()
                withdraw.await()
            }
            assertNull("round $round", link("home"))
        }
    }

    @Test fun migrationFromV4KeepsVehicleConsentAndStartsWithLocationOff() = runBlocking {
        database.close()
        context.openOrCreateDatabase(databaseName, Context.MODE_PRIVATE, null).use { old ->
            old.execSQL("CREATE TABLE town_state (id INTEGER NOT NULL, pieces INTEGER NOT NULL, revision INTEGER NOT NULL, demoPiecesClaimed INTEGER NOT NULL DEFAULT 0, rewardCount INTEGER NOT NULL DEFAULT 0, lastRewardDay INTEGER, PRIMARY KEY(id))")
            old.execSQL("CREATE TABLE owned_blueprints (blueprintId TEXT NOT NULL, PRIMARY KEY(blueprintId))")
            old.execSQL("CREATE TABLE placements (id TEXT NOT NULL, blueprintId TEXT NOT NULL, slotId TEXT NOT NULL, PRIMARY KEY(id), FOREIGN KEY(blueprintId) REFERENCES owned_blueprints(blueprintId) ON UPDATE NO ACTION ON DELETE RESTRICT)")
            old.execSQL("CREATE UNIQUE INDEX index_placements_slotId ON placements(slotId)")
            old.execSQL("CREATE INDEX index_placements_blueprintId ON placements(blueprintId)")
            old.execSQL("CREATE TABLE buildings (plotId TEXT NOT NULL, level INTEGER NOT NULL, PRIMARY KEY(plotId))")
            old.execSQL("CREATE TABLE mobility_state (id INTEGER NOT NULL, sealed BLOB NOT NULL, PRIMARY KEY(id))")
            old.execSQL("CREATE TABLE privacy_state (id INTEGER NOT NULL, vehicleConsent INTEGER NOT NULL, consentGeneration INTEGER NOT NULL, PRIMARY KEY(id))")
            old.execSQL("INSERT INTO town_state VALUES (1, 3, 20, 1, 3, 20770)")
            old.execSQL("INSERT INTO buildings VALUES ('home', 3), ('cafe', 3)")
            old.execSQL("INSERT INTO privacy_state VALUES (1, 1, 3)")
            old.version = 4
        }
        openDatabase()
        repository.initialize()
        assertEquals(PrivacyState(vehicleConsent = true, generation = 3, locationConsent = false), repository.privacySnapshot())
        assertTrue(repository.places.first().isEmpty())
        assertEquals(mapOf("home" to 3, "cafe" to 3), repository.snapshot()!!.buildings)
        assertEquals(PlaceWrite.ConsentOff, repository.linkCurrentPlace("home", fix(), "집", gate.token()!!))
        assertEquals(PlaceWrite.Saved, repository.saveAlias("home", "집", gate.token()!!))
    }

    private fun ByteArray.contains(part: ByteArray) = (0..size - part.size).any { start -> part.indices.all { this[start + it] == part[it] } }

    private fun assertThrowsPrivacy(block: () -> Unit) {
        assertThrows(com.chagoktown.data.privacy.PrivacyStorageException::class.java) { block() }
    }
}
