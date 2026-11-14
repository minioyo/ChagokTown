package com.chagoktown.data

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.chagoktown.data.local.TownDatabase
import com.chagoktown.data.privacy.KeystoreCryptoBox
import com.chagoktown.platform.PlayAccess
import com.chagoktown.session.InteractionGate
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DemoPiecesTest {
    @Test fun rapidConcurrentGrantRequestsOnlyAddSixtyOnce() = runBlocking {
        val context: Context = ApplicationProvider.getApplicationContext()
        val db = Room.inMemoryDatabaseBuilder(context, TownDatabase::class.java).build()
        val gate = InteractionGate().apply { setResumed(true); setPlayAccess(PlayAccess.Allowed) }
        // Demo pieces never touch the sealed baseline, so the key is never created here.
        val repository = TownRepository(db, loadTownLayout(context.assets).catalog, gate, KeystoreCryptoBox("test-demo-pieces"))
        try {
            repository.initialize()
            val token = gate.token()!!
            val results = coroutineScope { List(20) { async(Dispatchers.Default) { repository.claimDemoPieces(token) } }.awaitAll() }
            assertEquals(1, results.count { it == WriteResult.Saved })
            assertEquals(63, repository.snapshot()!!.pieces)
            assertTrue(repository.snapshot()!!.demoPiecesClaimed)
            gate.setPlayAccess(PlayAccess.Restricted)
            assertEquals(WriteResult.SessionExpired, repository.claimDemoPieces(token))
        } finally { db.close() }
    }
}
