package com.chagoktown.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chagoktown.data.AliasRead
import com.chagoktown.data.MaxAliasLength
import com.chagoktown.data.MobilityWrite
import com.chagoktown.data.PlaceRejection
import com.chagoktown.data.PlaceWrite
import com.chagoktown.data.PrivacyState
import com.chagoktown.data.local.PlaceKind
import com.chagoktown.platform.LocationReading
import com.chagoktown.data.TownRepository
import com.chagoktown.data.WriteResult
import com.chagoktown.game.BuildCommand
import com.chagoktown.game.MobilityOutcome
import com.chagoktown.game.MobilityReading
import com.chagoktown.game.Rejection
import com.chagoktown.game.TownState
import com.chagoktown.session.GateState
import com.chagoktown.session.InteractionGate
import com.chagoktown.session.SessionToken
import java.time.LocalDate
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class PlotSelection(val plotId: String, val token: SessionToken)

data class TownUiState(
    val town: TownState? = null,
    val gate: GateState = GateState(),
    val selection: PlotSelection? = null,
    val busy: Boolean = false,
    val message: String? = null,
    val privacy: PrivacyControls = PrivacyControls(),
    /** Which buildings have a place, by kind only. Aliases stay folded. */
    val places: Map<String, PlaceKind> = emptyMap(),
    /** The one alias the user asked to see. Cleared on any gate change, selection change or withdrawal. */
    val revealedAlias: RevealedAlias? = null,
)

/** What the settings dialog shows. Holds consent flags only, never a distance or the baseline. */
data class PrivacyControls(val state: PrivacyState = PrivacyState(), val busy: Boolean = false, val locked: Boolean = false)

data class RevealedAlias(val plotId: String, val alias: String)

private data class Extras(val message: String?, val privacy: PrivacyControls, val places: Map<String, PlaceKind>, val revealed: RevealedAlias?)

class TownViewModel(
    private val repository: TownRepository,
    val gate: InteractionGate,
    private val readDistance: suspend (consentGeneration: Long) -> MobilityReading,
    private val readLocation: suspend (consentGeneration: Long) -> LocationReading,
    private val today: () -> LocalDate,
) : ViewModel() {
    val catalog = repository.catalog
    private val selection = MutableStateFlow<PlotSelection?>(null)
    private val busy = MutableStateFlow(false)
    private val message = MutableStateFlow<String?>(null)
    private val privacyBusy = MutableStateFlow(false)
    private val privacyLocked = MutableStateFlow(false)
    private val revealed = MutableStateFlow<RevealedAlias?>(null)
    private val town = repository.town.onStart { emit(null) }.catch {
        message.value = "마을을 읽지 못했어요. 앱을 다시 열어 주세요."
        emit(null)
    }
    private val privacy = combine(repository.privacy.catch { emit(PrivacyState()) }, privacyBusy, privacyLocked, ::PrivacyControls)
    private val extras = combine(message, privacy, repository.places.catch { emit(emptyMap()) }, revealed, ::Extras)

    val state = combine(town, gate.state, selection, busy, extras) { town, access, selected, saving, extra ->
        val shownSelection = selected?.takeIf { access.playable && it.token.generation == access.generation }
        TownUiState(town, access, shownSelection, saving, extra.message, extra.privacy, extra.places,
            extra.revealed?.takeIf { access.playable && it.plotId == shownSelection?.plotId })
    }.stateIn(viewModelScope, SharingStarted.Eagerly, TownUiState())

    private val initialized = viewModelScope.launch {
        try {
            repository.initialize()
        } catch (error: CancellationException) {
            throw error
        } catch (_: Exception) {
            message.value = "마을을 준비하지 못했어요. 기존 데이터는 초기화하지 않았어요."
        }
    }
    private var checkedGeneration: Long? = null

    init {
        viewModelScope.launch {
            gate.state.collect { access ->
                if (selection.value?.token?.generation != access.generation) selection.value = null
                // A shown alias never survives a restriction or a trip to the background.
                revealed.value = null
                // Each time the town opens in a playable state, the distance is read once.
                if (access.playable && checkedGeneration != access.generation) {
                    checkedGeneration = access.generation
                    runMobilityCheck(announceAll = false)
                }
            }
        }
    }

    /** Demo: re-check after a fake drive or day change, as if the car parked and the app opened again. */
    fun checkMobility() = runMobilityCheck(announceAll = true)

    private fun runMobilityCheck(announceAll: Boolean) {
        viewModelScope.launch {
            initialized.join()
            val token = gate.token() ?: return@launch
            try {
                // Nothing is read from the car while vehicle data is off.
                val consent = repository.privacySnapshot()
                val result = if (consent.vehicleConsent) repository.recordMobility(readDistance(consent.generation), token, today)
                else MobilityWrite.ConsentOff
                when (result) {
                    is MobilityWrite.Checked -> {
                        privacyLocked.value = false
                        mobilityNotice(result, announceAll)?.let { message.value = it }
                    }
                    MobilityWrite.ConsentOff -> if (announceAll) message.value = "차량 정보 사용이 꺼져 있어 이동을 확인하지 않았어요. 설정에서 켤 수 있어요."
                    MobilityWrite.PrivacyLocked -> {
                        privacyLocked.value = true
                        message.value = "저장된 이동 기록을 읽을 수 없어 이동 확인을 멈췄어요. 설정에서 이동 기록을 지우고 다시 시작할 수 있어요."
                    }
                    MobilityWrite.SessionExpired -> Unit
                }
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                if (announceAll) message.value = "이동 기록을 저장하지 못했어요. 마지막으로 저장한 마을을 유지했어요."
            }
        }
    }

    /** Settings switch. Turning it off deletes the baseline; "done" is shown only after the deletion is committed. */
    fun setVehicleConsent(enabled: Boolean) = privacyWrite(
        done = if (enabled) "차량 정보 사용을 켰어요." else "차량 정보 사용을 껐어요. 저장된 이동 비교 기준을 지웠어요.",
        failed = if (enabled) "차량 정보 사용을 켜지 못했어요. 다시 시도해 주세요."
        else "이동 기록을 지우지 못했어요. 이동 확인은 멈췄어요. 다시 시도해 주세요.",
        checkAfter = enabled,
    ) { repository.setVehicleConsent(enabled) }

    /** Recovery offered only while the sealed baseline cannot be opened. */
    fun resetMobilityRecord() = privacyWrite(
        done = "이동 기록을 지웠어요. 다음 확인부터 새로 시작해요.",
        failed = "이동 기록을 지우지 못했어요. 다시 시도해 주세요.",
        checkAfter = true,
    ) {
        repository.resetMobilityRecord()
        privacyLocked.value = false
    }

    /** Turning location off deletes every place linked by location; aliases typed without a location stay. */
    fun setLocationConsent(enabled: Boolean) = privacyWrite(
        done = if (enabled) "위치 사용을 켰어요. 장소를 연결할 때만 위치를 한 번 확인해요."
        else "위치 사용을 껐어요. 위치로 연결한 장소를 지웠어요. 건물은 그대로예요.",
        failed = if (enabled) "위치 사용을 켜지 못했어요. 다시 시도해 주세요."
        else "위치로 연결한 장소를 지우지 못했어요. 장소 연결은 멈췄어요. 다시 시도해 주세요.",
        checkAfter = false,
    ) {
        if (!enabled) revealed.value = null
        repository.setLocationConsent(enabled)
    }

    fun deleteAllPlaces() = privacyWrite(
        done = "장소 기록을 모두 지웠어요. 건물은 그대로예요.",
        failed = "장소 기록을 지우지 못했어요. 다시 시도해 주세요.",
        checkAfter = false,
    ) {
        revealed.value = null
        repository.deleteAllPlaces()
    }

    fun saveAlias(plotId: String, alias: String) = placeAction("별명을 저장했어요.") { token -> repository.saveAlias(plotId, alias, token) }

    /** Reads the location once, only now, and only while location is on. */
    fun linkCurrentPlace(plotId: String, alias: String) = placeAction("지금 주차한 곳을 이 건물과 연결했어요.") { token ->
        val consent = repository.privacySnapshot()
        if (!consent.locationConsent) PlaceWrite.ConsentOff
        else repository.linkCurrentPlace(plotId, readLocation(consent.generation), alias, token)
    }

    fun unlinkPlace(plotId: String) = placeAction("장소 연결을 해제했어요. 건물은 그대로예요.") { token ->
        repository.unlinkPlace(plotId, token)
    }

    fun revealAlias(plotId: String) {
        val token = gate.token() ?: return
        viewModelScope.launch {
            try {
                when (val read = repository.revealAlias(plotId)) {
                    // A late answer never shows the alias after a restriction or for a building no longer selected.
                    is AliasRead.Ready -> if (gate.approve(token) && selection.value?.plotId == plotId) revealed.value = RevealedAlias(plotId, read.alias)
                    AliasRead.Locked -> message.value = "별명을 읽을 수 없어요. 연결을 해제하면 지워져요."
                    AliasRead.Missing -> Unit
                }
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                message.value = "별명을 읽지 못했어요. 다시 시도해 주세요."
            }
        }
    }

    fun hideAlias() { revealed.value = null }

    private fun placeAction(done: String, write: suspend (SessionToken) -> PlaceWrite) {
        if (privacyBusy.value) return
        val token = gate.token() ?: return
        privacyBusy.value = true
        revealed.value = null
        viewModelScope.launch {
            try {
                initialized.join()
                message.value = when (val result = write(token)) {
                    PlaceWrite.Saved -> done
                    PlaceWrite.SessionExpired -> "플레이 상태가 바뀌어 저장하지 않았어요."
                    PlaceWrite.ConsentOff -> "위치 사용이 꺼져 있어요. 설정에서 켜면 지금 주차한 곳을 연결할 수 있어요."
                    PlaceWrite.PrivacyLocked -> "장소를 안전하게 저장하지 못해 저장하지 않았어요."
                    is PlaceWrite.Rejected -> when (result.reason) {
                        PlaceRejection.NO_BUILDING -> "먼저 건물을 지어 주세요."
                        PlaceRejection.INVALID_ALIAS -> "별명은 1~${MaxAliasLength}자로 적어 주세요."
                        PlaceRejection.LOCATION_UNAVAILABLE -> "지금 위치를 확인할 수 없어 연결하지 않았어요."
                        PlaceRejection.LOCATION_STALE, PlaceRejection.LOCATION_IMPRECISE ->
                            "위치가 충분히 정확하지 않아 연결하지 않았어요. 잠시 뒤 다시 시도해 주세요."
                        PlaceRejection.OLD_GENERATION -> "위치 설정이 바뀌어 연결하지 않았어요. 다시 시도해 주세요."
                    }
                }
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                message.value = "장소를 저장하지 못했어요. 마지막으로 저장한 마을을 유지했어요."
            } finally {
                privacyBusy.value = false
            }
        }
    }

    private fun privacyWrite(done: String, failed: String, checkAfter: Boolean, write: suspend () -> Unit) {
        if (privacyBusy.value) return
        privacyBusy.value = true
        viewModelScope.launch {
            try {
                initialized.join()
                write()
                message.value = done
                // The first reading after (re)consent or a reset only sets a new baseline.
                if (checkAfter) runMobilityCheck(announceAll = false)
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                message.value = failed
            } finally {
                privacyBusy.value = false
            }
        }
    }

    private fun mobilityNotice(result: MobilityWrite.Checked, announceAll: Boolean) = when (result.outcome) {
        MobilityOutcome.REWARDED -> "이동이 확인돼 마을 조각 ${result.piecesGranted}개를 받았어요."
        MobilityOutcome.BASELINE_SET -> "이동 확인을 시작했어요. 다음 이동부터 마을 조각을 받아요."
        MobilityOutcome.BASELINE_RESET -> "주행 기록이 바뀌어 이동 확인을 새로 시작했어요."
        MobilityOutcome.CONSUMED -> "오늘 이동 보상은 이미 받았어요. 내일 다시 확인해요."
        MobilityOutcome.BELOW_THRESHOLD -> if (announceAll) "새로 확인된 이동이 없어요." else null
        MobilityOutcome.IGNORED -> if (announceAll) "지금은 이동 기록을 확인할 수 없어요." else null
    }

    fun selectPlot(plotId: String) {
        val token = gate.token() ?: return
        if (busy.value || catalog.plot(plotId) == null) return
        selection.value = PlotSelection(plotId, token)
        revealed.value = null
        message.value = null
    }

    fun advance(plotId: String, expectedLevel: Int) {
        val selected = selection.value ?: return
        if (selected.plotId != plotId || busy.value) return
        busy.value = true
        viewModelScope.launch {
            try {
                when (val result = repository.execute(BuildCommand(plotId, expectedLevel), selected.token)) {
                    WriteResult.Saved -> message.value = if (expectedLevel == 0) "새 건물이 마을에 생겼어요." else "건물이 한 단계 자랐어요."
                    WriteResult.SessionExpired -> {
                        selection.value = null
                        message.value = "플레이 상태가 바뀌어 변경을 취소했어요."
                    }
                    is WriteResult.Rejected -> message.value = when (result.reason) {
                        Rejection.NOT_ENOUGH_PIECES -> "마을 조각이 부족해요."
                        Rejection.MAX_LEVEL -> "이미 마지막 단계예요."
                        Rejection.STALE_LEVEL -> "이미 처리한 변경이에요. 현재 단계를 확인해 주세요."
                        else -> "지금은 이 변경을 저장할 수 없어요."
                    }
                }
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                message.value = "저장하지 못했어요. 마지막으로 저장한 마을을 유지했어요. 다시 시도해 주세요."
            } finally {
                busy.value = false
            }
        }
    }

    fun showNotice(notice: String) { message.value = notice }

    fun clearNotice() { message.value = null }
}
