package com.chagoktown.data.privacy

import com.chagoktown.game.MobilityBaseline
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.IOException

/** The distance baseline's only storage form. Bound to `mobility_state` row 1 so the envelope is useless anywhere else. */
internal object SealedBaseline {
    private val Aad = "chagoktown/mobility_state/1/baseline/v1".encodeToByteArray()

    fun seal(box: CryptoBox, baseline: MobilityBaseline): ByteArray {
        val plain = ByteArrayOutputStream().also { bytes ->
            DataOutputStream(bytes).use {
                it.writeDouble(baseline.distance)
                it.writeUTF(baseline.source)
            }
        }.toByteArray()
        return box.seal(plain, Aad)
    }

    fun open(box: CryptoBox, sealed: ByteArray): MobilityBaseline {
        val plain = box.open(sealed, Aad)
        return try {
            DataInputStream(ByteArrayInputStream(plain)).use { input ->
                MobilityBaseline(input.readDouble(), input.readUTF()).also {
                    if (input.available() != 0 || !it.distance.isFinite() || it.distance < 0) throw IOException("Malformed baseline")
                }
            }
        } catch (error: IOException) {
            throw PrivacyStorageException("Stored baseline is malformed", error)
        }
    }
}
