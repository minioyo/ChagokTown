package com.chagoktown.data.local

import androidx.room.Dao
import androidx.room.ColumnInfo
import androidx.room.Database
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Update
import androidx.room.Upsert
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "town_state")
data class TownEntity(@PrimaryKey val id: Int = 1, val pieces: Int, val revision: Long,
    @ColumnInfo(defaultValue = "0") val demoPiecesClaimed: Boolean = false,
    @ColumnInfo(defaultValue = "0") val rewardCount: Int = 0,
    /** Local epoch day of the last movement reward. */
    val lastRewardDay: Long? = null)

@Entity(tableName = "buildings")
data class BuildingEntity(@PrimaryKey val plotId: String, val level: Int)

/**
 * Distance baseline, kept apart from the town so consent withdrawal can delete it alone.
 * [sealed] is a [com.chagoktown.data.privacy.CryptoBox] envelope; distance and source never reach Room in plain text.
 */
@Entity(tableName = "mobility_state")
class MobilityEntity(@PrimaryKey val id: Int = 1, val sealed: ByteArray)

/**
 * Vehicle-data and location consent. Any change to either starts a new generation, so readings requested before it
 * (distance or location) are discarded.
 */
@Entity(tableName = "privacy_state")
data class PrivacyEntity(
    @PrimaryKey val id: Int = 1,
    val vehicleConsent: Boolean,
    val consentGeneration: Long,
    @ColumnInfo(defaultValue = "0") val locationConsent: Boolean = false,
)

/** MANUAL: an alias the user typed, no location. LOCATION: alias plus the coordinates of a place the user chose to save. */
enum class PlaceKind { MANUAL, LOCATION }

/**
 * At most one place per building (the plot is the key). Alias and coordinates are [com.chagoktown.data.privacy.CryptoBox]
 * envelopes bound to this plot; the kind is the only plain field, so the town screen can say "linked" without decrypting.
 */
@Entity(
    tableName = "place_links",
    foreignKeys = [ForeignKey(entity = BuildingEntity::class, parentColumns = ["plotId"], childColumns = ["plotId"], onDelete = ForeignKey.CASCADE)],
)
class PlaceLinkEntity(@PrimaryKey val plotId: String, val kind: PlaceKind, val sealedAlias: ByteArray, val sealedCoordinates: ByteArray?)

data class PlaceKindRow(val plotId: String, val kind: PlaceKind)

@Entity(tableName = "owned_blueprints")
data class OwnedBlueprintEntity(@PrimaryKey val blueprintId: String)

@Entity(
    tableName = "placements",
    indices = [Index(value = ["slotId"], unique = true), Index("blueprintId")],
    foreignKeys = [ForeignKey(
        entity = OwnedBlueprintEntity::class,
        parentColumns = ["blueprintId"], childColumns = ["blueprintId"],
        onDelete = ForeignKey.RESTRICT,
    )],
)
data class PlacementEntity(@PrimaryKey val id: String, val blueprintId: String, val slotId: String)

@Dao
interface TownDao {
    @Query("SELECT revision FROM town_state WHERE id = 1")
    fun observeRevision(): Flow<Long?>

    @Query("SELECT * FROM town_state WHERE id = 1")
    suspend fun town(): TownEntity?

    @Query("SELECT * FROM owned_blueprints ORDER BY blueprintId")
    suspend fun owned(): List<OwnedBlueprintEntity>

    @Query("SELECT * FROM placements ORDER BY id")
    suspend fun placements(): List<PlacementEntity>

    @Query("SELECT * FROM buildings ORDER BY plotId")
    suspend fun buildings(): List<BuildingEntity>

    @Query("SELECT * FROM mobility_state WHERE id = 1")
    suspend fun mobility(): MobilityEntity?

    @Query("SELECT * FROM privacy_state WHERE id = 1")
    suspend fun privacy(): PrivacyEntity?

    @Query("SELECT * FROM privacy_state WHERE id = 1")
    fun observePrivacy(): Flow<PrivacyEntity?>

    @Query("SELECT * FROM buildings WHERE plotId = :plotId")
    suspend fun building(plotId: String): BuildingEntity?

    @Query("SELECT plotId, kind FROM place_links ORDER BY plotId")
    fun observePlaceKinds(): Flow<List<PlaceKindRow>>

    @Query("SELECT * FROM place_links WHERE plotId = :plotId")
    suspend fun placeLink(plotId: String): PlaceLinkEntity?

    @Upsert suspend fun savePlaceLink(link: PlaceLinkEntity)
    @Query("DELETE FROM place_links WHERE plotId = :plotId") suspend fun deletePlaceLink(plotId: String)
    @Query("DELETE FROM place_links WHERE kind = 'LOCATION'") suspend fun deleteLocationLinks()
    @Query("DELETE FROM place_links") suspend fun deleteAllPlaceLinks()

    @Insert suspend fun insertTown(town: TownEntity)
    @Update suspend fun updateTown(town: TownEntity)
    @Upsert suspend fun saveBuildings(buildings: List<BuildingEntity>)
    @Upsert suspend fun saveMobility(mobility: MobilityEntity)
    @Query("DELETE FROM mobility_state") suspend fun deleteMobility()
    @Upsert suspend fun savePrivacy(privacy: PrivacyEntity)
}

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE town_state ADD COLUMN demoPiecesClaimed INTEGER NOT NULL DEFAULT 0")
        db.execSQL("CREATE TABLE IF NOT EXISTS buildings (plotId TEXT NOT NULL, level INTEGER NOT NULL, PRIMARY KEY(plotId))")
        // Every legacy row stays intact. Only the old house maps to the fixed home plot.
        db.execSQL("""INSERT INTO buildings (plotId, level) SELECT 'home', 1
            WHERE EXISTS (SELECT 1 FROM town_state WHERE id = 1)
            AND (EXISTS (SELECT 1 FROM owned_blueprints WHERE blueprintId = 'house.basic')
            OR EXISTS (SELECT 1 FROM placements WHERE blueprintId = 'house.basic'))""")
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // Existing towns start with no reward history and no baseline: the next valid reading only sets a baseline.
        db.execSQL("ALTER TABLE town_state ADD COLUMN rewardCount INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE town_state ADD COLUMN lastRewardDay INTEGER")
        db.execSQL("CREATE TABLE IF NOT EXISTS mobility_state (id INTEGER NOT NULL, distance REAL NOT NULL, source TEXT NOT NULL, PRIMARY KEY(id))")
    }
}

val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // The plaintext baseline only ever held demo distances. It is discarded, never converted, and no consent is assumed:
        // the town and reward history stay, and the first reading after the user turns vehicle data on only sets a baseline.
        db.execSQL("DROP TABLE mobility_state")
        db.execSQL("CREATE TABLE mobility_state (id INTEGER NOT NULL, sealed BLOB NOT NULL, PRIMARY KEY(id))")
        db.execSQL("CREATE TABLE privacy_state (id INTEGER NOT NULL, vehicleConsent INTEGER NOT NULL, consentGeneration INTEGER NOT NULL, PRIMARY KEY(id))")
    }
}

val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(db: SupportSQLiteDatabase) {
        // Vehicle consent and its generation stay as they were; location starts off with no places.
        db.execSQL("ALTER TABLE privacy_state ADD COLUMN locationConsent INTEGER NOT NULL DEFAULT 0")
        db.execSQL("""CREATE TABLE IF NOT EXISTS place_links (plotId TEXT NOT NULL, kind TEXT NOT NULL, sealedAlias BLOB NOT NULL,
            sealedCoordinates BLOB, PRIMARY KEY(plotId),
            FOREIGN KEY(plotId) REFERENCES buildings(plotId) ON UPDATE NO ACTION ON DELETE CASCADE)""")
    }
}

@Database(
    entities = [TownEntity::class, OwnedBlueprintEntity::class, PlacementEntity::class, BuildingEntity::class, MobilityEntity::class,
        PrivacyEntity::class, PlaceLinkEntity::class],
    version = 5,
    exportSchema = true,
)
abstract class TownDatabase : RoomDatabase() {
    abstract fun townDao(): TownDao
}
