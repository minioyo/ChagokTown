package com.chagoktown.session

import com.chagoktown.platform.PlayAccess
import org.junit.Assert.*
import org.junit.Test

class InteractionGateTest {
    @Test fun bothResumedAndConfirmedAccessAreRequired() {
        val gate = InteractionGate()
        assertNull(gate.token())
        gate.setResumed(true)
        assertNull(gate.token())
        gate.setPlayAccess(PlayAccess.Restricted)
        assertNull(gate.token())
        gate.setPlayAccess(PlayAccess.Allowed)
        assertTrue(gate.approve(gate.token()!!))
    }

    @Test fun restrictionAndReturnNeverRevalidateOldCommands() {
        val gate = InteractionGate()
        gate.setResumed(true)
        gate.setPlayAccess(PlayAccess.Allowed)
        val oldToken = gate.token()!!
        gate.setPlayAccess(PlayAccess.Restricted)
        gate.setPlayAccess(PlayAccess.Allowed)
        assertFalse(gate.approve(oldToken))
        assertTrue(gate.approve(gate.token()!!))
    }

    @Test fun backgroundInvalidatesCommandsEvenAfterResume() {
        val gate = InteractionGate()
        gate.setResumed(true)
        gate.setPlayAccess(PlayAccess.Allowed)
        val oldToken = gate.token()!!
        gate.setResumed(false)
        assertNull(gate.token())
        gate.setResumed(true)
        assertFalse(gate.approve(oldToken))
    }
}
