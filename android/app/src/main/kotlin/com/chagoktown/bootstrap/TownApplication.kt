package com.chagoktown.bootstrap

import android.app.Application
import android.content.Context
import androidx.room.Room
import com.chagoktown.data.TownRepository
import com.chagoktown.data.loadTownLayout
import com.chagoktown.data.local.TownDatabase
import com.chagoktown.data.local.MIGRATION_1_2
import com.chagoktown.data.local.MIGRATION_2_3
import com.chagoktown.data.local.MIGRATION_3_4
import com.chagoktown.data.local.MIGRATION_4_5
import com.chagoktown.data.privacy.KeystoreCryptoBox
import com.chagoktown.session.InteractionGate

class AppContainer(context: Context) {
    val gate = InteractionGate()
    val gateway = createVehicleGateway(context)
    val today = createLocalDay(gateway)
    val layout = loadTownLayout(context.assets)
    val database = Room.databaseBuilder(context, TownDatabase::class.java, "town.db")
        .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5).build()
    val repository = TownRepository(database, layout.catalog, gate, KeystoreCryptoBox())
}

class TownApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}
