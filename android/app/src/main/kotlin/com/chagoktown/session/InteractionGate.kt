package com.chagoktown.session

import com.chagoktown.platform.PlayAccess
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class SessionToken(val generation: Long)

data class GateState(
    val resumed: Boolean = false,
    val access: PlayAccess = PlayAccess.Unknown,
    val generation: Long = 0,
) {
    val playable: Boolean get() = resumed && access == PlayAccess.Allowed
}

class InteractionGate {
    private val mutableState = MutableStateFlow(GateState())
    val state = mutableState.asStateFlow()

    @Synchronized
    fun setResumed(resumed: Boolean) {
        val before = mutableState.value
        if (before.resumed != resumed) mutableState.value = before.copy(resumed = resumed, generation = before.generation + 1)
    }

    @Synchronized
    fun setPlayAccess(access: PlayAccess) {
        val before = mutableState.value
        if (before.access != access) mutableState.value = before.copy(access = access, generation = before.generation + 1)
    }

    @Synchronized
    fun token(): SessionToken? = mutableState.value.let { if (it.playable) SessionToken(it.generation) else null }

    @Synchronized
    fun approve(token: SessionToken): Boolean = mutableState.value.let { it.playable && it.generation == token.generation }
}
