package com.chagoktown.data

import com.chagoktown.game.Rejection
import com.chagoktown.game.RuleResult
import com.chagoktown.session.SessionToken

// Source-set isolation: neither the grant rule nor its button ships in vehicle.
suspend fun TownRepository.claimDemoPieces(token: SessionToken): WriteResult = commit(token) { town ->
    if (town.demoPiecesClaimed) RuleResult.Rejected(Rejection.ALREADY_CLAIMED)
    else RuleResult.Accepted(town.copy(pieces = town.pieces + 60, demoPiecesClaimed = true, revision = town.revision + 1))
}
