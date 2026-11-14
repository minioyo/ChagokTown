package com.chagoktown.data.privacy

import androidx.test.ext.junit.runners.AndroidJUnit4
import java.util.UUID
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Test
import org.junit.runner.RunWith

/** Runs against the device's real Android Keystore. Hardware backing is not asserted. */
@RunWith(AndroidJUnit4::class)
class KeystoreCryptoBoxTest {
    private val box = KeystoreCryptoBox("test-${UUID.randomUUID()}")
    private val aad = "record/1/field".encodeToByteArray()
    private val plain = "12345.75 km private".encodeToByteArray()

    @After fun tearDown() = box.destroyKey()

    @Test fun roundTripUsesAFreshNonceAndKeepsNoPlainText() {
        val first = box.seal(plain, aad)
        val second = box.seal(plain, aad)
        assertArrayEquals(plain, box.open(first, aad))
        assertArrayEquals(plain, box.open(second, aad))
        assertFalse(first.copyOfRange(1, 13).contentEquals(second.copyOfRange(1, 13)))
        assertFalse(first.contentEquals(second))
        assertFalse(first.contains(plain))
        assertFalse(first.contains("km private".encodeToByteArray()))
    }

    @Test fun envelopeDoesNotOpenForAnotherRecordOrField() {
        val sealed = box.seal(plain, aad)
        assertLocked { box.open(sealed, "record/2/field".encodeToByteArray()) }
        assertLocked { box.open(sealed, "record/1/other".encodeToByteArray()) }
    }

    @Test fun anyChangedByteFailsInsteadOfReturningAGuess() {
        val sealed = box.seal(plain, aad)
        listOf(0, 1, 12, 13, sealed.size / 2, sealed.size - 1).forEach { index ->
            val changed = sealed.copyOf().also { it[index] = (it[index].toInt() xor 0x01).toByte() }
            assertLocked { box.open(changed, aad) }
        }
        assertLocked { box.open(sealed.copyOf(12), aad) }
    }

    @Test fun destroyedKeyLeavesOldEnvelopesUnreadableEvenAfterANewKey() {
        val old = box.seal(plain, aad)
        box.destroyKey()
        assertLocked { box.open(old, aad) }
        val fresh = box.seal(plain, aad)
        assertArrayEquals(plain, box.open(fresh, aad))
        assertLocked { box.open(old, aad) }
    }

    private fun assertLocked(block: () -> Unit) {
        assertThrows(PrivacyStorageException::class.java) { block() }
    }

    private fun ByteArray.contains(part: ByteArray) = (0..size - part.size).any { start -> part.indices.all { this[start + it] == part[it] } }
}
