package com.chagoktown.data.privacy

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.ByteBuffer
import java.nio.charset.CharacterCodingException
import java.nio.charset.CodingErrorAction

/**
 * Place alias and coordinates, each bound to its plot and field. An envelope copied to another building or field does not open.
 * Coordinates are sealed but never opened yet: nothing displays or compares them until place re-recognition is designed.
 */
internal object SealedPlace {
    private fun aad(plotId: String, field: String) = "chagoktown/place_links/$plotId/$field/v1".encodeToByteArray()

    fun sealAlias(box: CryptoBox, plotId: String, alias: String): ByteArray = box.seal(alias.encodeToByteArray(), aad(plotId, "alias"))

    fun openAlias(box: CryptoBox, plotId: String, sealed: ByteArray): String {
        val plain = box.open(sealed, aad(plotId, "alias"))
        return try {
            Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(plain)).toString()
        } catch (error: CharacterCodingException) {
            throw PrivacyStorageException("Stored alias is malformed", error)
        }
    }

    fun sealCoordinates(box: CryptoBox, plotId: String, latitude: Double, longitude: Double): ByteArray {
        val plain = ByteArrayOutputStream().also { bytes ->
            DataOutputStream(bytes).use {
                it.writeDouble(latitude)
                it.writeDouble(longitude)
            }
        }.toByteArray()
        return box.seal(plain, aad(plotId, "coordinates"))
    }
}
