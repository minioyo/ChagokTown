package com.chagoktown.bootstrap

import android.content.Context
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.unit.dp
import com.chagoktown.ui.theme.TownColors
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.chagoktown.platform.DemoVehicleGateway
import com.chagoktown.platform.PlayAccess
import com.chagoktown.platform.VehicleGateway
import com.chagoktown.data.TownRepository
import com.chagoktown.data.WriteResult
import com.chagoktown.data.claimDemoPieces
import com.chagoktown.session.InteractionGate
import com.chagoktown.ui.TownUiState
import java.text.NumberFormat
import java.time.LocalDate
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

fun createVehicleGateway(context: Context): VehicleGateway =
    DemoVehicleGateway(context.getSharedPreferences(DemoVehicleGateway.PREFS, Context.MODE_PRIVATE))

fun createLocalDay(gateway: VehicleGateway): () -> LocalDate = (gateway as DemoVehicleGateway)::today

@Composable
fun PlatformPanel(gateway: VehicleGateway, repository: TownRepository, gate: InteractionGate, state: TownUiState,
    showNotice: (String) -> Unit, checkMobility: () -> Unit) {
    val demo = gateway as DemoVehicleGateway
    val access by gateway.playAccess.collectAsStateWithLifecycle()
    val drive by demo.drive.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var granting by remember { mutableStateOf(false) }
    Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            if (state.town != null && !state.town.demoPiecesClaimed && state.gate.playable) {
                DemoChip("시연 재료 +60", enabled = !granting && !state.busy, modifier = Modifier.testTag("demo.pieces"), onClick = {
                    val token = gate.token()
                    if (token != null && !granting) {
                        granting = true
                        scope.launch {
                            try {
                                val result = repository.claimDemoPieces(token)
                                showNotice(if (result == WriteResult.Saved) "시연용 마을 조각 60개를 받았어요. 실제 이동 보상은 아니에요." else "지금은 시연 재료를 받을 수 없어요.")
                            } catch (error: CancellationException) {
                                throw error
                            } catch (_: Exception) {
                                showNotice("시연 재료를 저장하지 못했어요. 다시 시도해 주세요.")
                            } finally { granting = false }
                        }
                    }
                })
            }
            DemoChip(
                if (access == PlayAccess.Restricted) "주차 상태로 복귀" else "주행 제한 시험",
                modifier = Modifier.testTag("demo.restriction"),
                onClick = { demo.setRestricted(access != PlayAccess.Restricted) },
            )
        }
        // A fake drive can happen while restricted; the check itself only runs when the town is playable again.
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            DemoChip("출퇴근 이동 +${CommuteLabel}km", modifier = Modifier.testTag("demo.commute"), onClick = { demo.commute(); checkMobility() })
            DemoChip("다음 날", modifier = Modifier.testTag("demo.next_day"), onClick = { demo.nextDay(); checkMobility() })
        }
        val day = demo.today()
        Text("가상 ${day.monthValue}월 ${day.dayOfMonth}일 · 누적 ${NumberFormat.getIntegerInstance().format(drive.distance)}km · " +
            "${if (drive.atWork) "회사" else "집"} 근처 주차 · 이동 보상 ${state.town?.rewardCount ?: 0}회",
            Modifier.testTag("demo.drive"), style = MaterialTheme.typography.labelMedium, color = TownColors.Ink)
        Text("DEMO · 1시즌 마을 · 임시 건설 비용·이동 보상 · 실제 차량 미연결", style = MaterialTheme.typography.labelMedium, color = TownColors.InkSecondary)
    }
}

private val CommuteLabel = DemoVehicleGateway.CommuteKm.toInt()

@Composable
private fun DemoChip(label: String, modifier: Modifier = Modifier, enabled: Boolean = true, onClick: () -> Unit) {
    Surface(onClick = onClick, modifier = modifier.heightIn(min = 48.dp), enabled = enabled, shape = CircleShape,
        color = TownColors.Panel, border = BorderStroke(1.dp, TownColors.Line)) {
        Text(label, Modifier.padding(horizontal = 20.dp, vertical = 13.dp), style = MaterialTheme.typography.labelMedium,
            color = if (enabled) TownColors.Navy else TownColors.OnDisabled)
    }
}
