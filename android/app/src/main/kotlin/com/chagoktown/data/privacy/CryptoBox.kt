package com.chagoktown.data.privacy

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.GeneralSecurityException
import java.security.KeyStore
import java.security.ProviderException
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** The key or an envelope cannot be used. The message never contains the sealed values. */
class PrivacyStorageException(message: String, cause: Throwable? = null) : Exception(message, cause)

/** Seals personal fields so Room never holds them in plain text. */
interface CryptoBox {
    /** [aad] binds the envelope to its record and field, so a copied envelope does not open elsewhere. */
    fun seal(plain: ByteArray, aad: ByteArray): ByteArray

    /** Throws [PrivacyStorageException] when the key is gone or the envelope fails authentication; never returns a guess. */
    fun open(sealed: ByteArray, aad: ByteArray): ByteArray

    /** Only after every envelope sealed with the key has been deleted, or once the key no longer works at all. */
    fun destroyKey()
}

/**
 * AES-256-GCM with a non-exportable Android Keystore key. Keystore picks a fresh random nonce for every seal.
 * Envelope: version (1 byte) · nonce (12 bytes) · ciphertext with 128-bit tag. Hardware backing is not verified here.
 */
class KeystoreCryptoBox(private val alias: String = DEFAULT_ALIAS) : CryptoBox {
    override fun seal(plain: ByteArray, aad: ByteArray): ByteArray = guard {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key(create = true))
        cipher.updateAAD(aad)
        val body = cipher.doFinal(plain)
        val nonce = cipher.iv
        if (nonce.size != NONCE_BYTES) throw PrivacyStorageException("Unexpected nonce size")
        byteArrayOf(VERSION) + nonce + body
    }

    override fun open(sealed: ByteArray, aad: ByteArray): ByteArray = guard {
        if (sealed.size <= HEADER_BYTES || sealed[0] != VERSION) throw PrivacyStorageException("Unsupported envelope")
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, key(create = false), GCMParameterSpec(TAG_BITS, sealed, 1, NONCE_BYTES))
        cipher.updateAAD(aad)
        cipher.doFinal(sealed, HEADER_BYTES, sealed.size - HEADER_BYTES)
    }

    override fun destroyKey() = guard {
        val store = keyStore()
        if (store.containsAlias(alias)) store.deleteEntry(alias)
    }

    // A missing key is created only when sealing. Opening never replaces a lost key, so old envelopes stay unreadable.
    private fun key(create: Boolean): SecretKey {
        (keyStore().getKey(alias, null) as SecretKey?)?.let { return it }
        if (!create) throw PrivacyStorageException("Privacy key is missing")
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build(),
        )
        return generator.generateKey()
    }

    private fun keyStore() = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }

    private inline fun <T> guard(block: () -> T): T = try {
        block()
    } catch (error: PrivacyStorageException) {
        throw error
    } catch (error: GeneralSecurityException) {
        // Authentication failure, invalidated or unrecoverable key, keystore errors.
        throw PrivacyStorageException("Privacy storage is unavailable", error)
    } catch (error: ProviderException) {
        throw PrivacyStorageException("Privacy storage is unavailable", error)
    }

    private companion object {
        const val DEFAULT_ALIAS = "chagoktown.privacy.v1"
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val VERSION: Byte = 1
        const val NONCE_BYTES = 12
        const val HEADER_BYTES = 1 + NONCE_BYTES
        const val TAG_BITS = 128
    }
}
