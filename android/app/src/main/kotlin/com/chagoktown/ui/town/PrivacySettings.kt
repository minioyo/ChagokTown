package com.chagoktown.ui.town

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.chagoktown.ui.theme.TownDialog
import androidx.compose.ui.window.DialogProperties
import com.chagoktown.ui.PrivacyControls
import com.chagoktown.ui.theme.TownColors

/** A plain gear beside the town name. Only the glyph is drawn; the 64dp circle around it is the car-game minimum touch target. */
@Composable
internal fun SettingsButton(onClick: () -> Unit) {
    Box(
        Modifier.size(64.dp).clip(CircleShape).clickable(role = Role.Button, onClick = onClick)
            .semantics { contentDescription = "설정" }.testTag("settings.open"),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.size(30.dp)) {
            val w = size.minDimension
            drawCircle(TownColors.InkSecondary, radius = w * .25f, style = Stroke(w * .14f))
            repeat(8) { tooth ->
                rotate(tooth * 45f) {
                    drawLine(TownColors.InkSecondary, Offset(center.x, center.y - w * .30f), Offset(center.x, center.y - w * .42f),
                        strokeWidth = w * .16f, cap = StrokeCap.Round)
                }
            }
        }
    }
}

/** Shown only while the town is playable; the caller closes it on every gate change. Holds consent flags only. */
@Composable
internal fun PrivacySettingsDialog(
    controls: PrivacyControls,
    placeCount: Int,
    onVehicleConsent: (Boolean) -> Unit,
    onLocationConsent: (Boolean) -> Unit,
    onDeletePlaces: () -> Unit,
    onReset: () -> Unit,
    onDismiss: () -> Unit,
) {
    TownDialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.padding(32.dp).widthIn(max = 680.dp).testTag("settings.dialog"), shape = RoundedCornerShape(24.dp), color = TownColors.Panel) {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(36.dp)) {
                Text("설정", style = MaterialTheme.typography.headlineMedium, color = TownColors.Ink)
                Spacer(Modifier.height(24.dp))
                ConsentRow("차량 정보 사용", "켜짐 · 주차 중 마을을 열 때 이동을 확인해요", "꺼짐 · 이동 보상을 받지 않아요",
                    controls.state.vehicleConsent, !controls.busy, "privacy.vehicle", onVehicleConsent)
                Spacer(Modifier.height(12.dp))
                Body("마을을 열 때 차량의 누적 주행거리를 한 번 읽어 지난번 값과 비교해요. 이동이 확인되면 하루 한 번 마을 조각을 받아요.")
                Note("경로·위치·주행 이력은 저장하지 않아요. 비교에 필요한 마지막 값만 암호화해 이 차에만 보관해요. 끄면 그 값을 바로 지우고, 받은 조각과 건물은 그대로예요.")
                if (controls.locked) {
                    Spacer(Modifier.height(20.dp))
                    LockedRecord(controls.busy, onReset)
                }
                Divider()
                ConsentRow("위치 사용", "켜짐 · 장소를 연결할 때만 위치를 한 번 확인해요", "꺼짐 · 별명만 붙일 수 있어요",
                    controls.state.locationConsent, !controls.busy, "privacy.location", onLocationConsent)
                Spacer(Modifier.height(12.dp))
                Body("건물을 고르고 '지금 위치와 연결'을 누를 때만 현재 위치를 한 번 읽어요. 지나간 길이나 다른 곳은 기록하지 않아요.")
                Note("연결한 장소의 좌표와 별명은 암호화해 이 차에만 보관해요. 끄면 위치로 연결한 장소를 바로 지우고, 직접 적은 별명과 건물은 그대로예요.")
                Spacer(Modifier.height(16.dp))
                DeletePlaces(placeCount, controls.busy, onDeletePlaces)
                Divider()
                Note("마을 데이터는 자동 백업과 기기 이전에 포함되지 않아요. 앱을 지우면 마을도 함께 지워져요.")
                Spacer(Modifier.height(24.dp))
                Button(onClick = onDismiss, modifier = Modifier.align(Alignment.End).heightIn(min = 56.dp).width(160.dp).testTag("settings.close"),
                    colors = ButtonDefaults.buttonColors(containerColor = TownColors.Navy)) {
                    Text("닫기", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    }
}

@Composable
private fun Body(text: String) = Text(text, style = MaterialTheme.typography.bodyMedium, color = TownColors.Ink)

@Composable
private fun Note(text: String) {
    Spacer(Modifier.height(6.dp))
    Text(text, style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
}

@Composable
private fun Divider() {
    Spacer(Modifier.height(24.dp))
    Box(Modifier.fillMaxWidth().height(1.dp).background(TownColors.Line))
    Spacer(Modifier.height(20.dp))
}

@Composable
private fun ConsentRow(title: String, onText: String, offText: String, on: Boolean, enabled: Boolean, tag: String, onChange: (Boolean) -> Unit) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 72.dp)
            .toggleable(value = on, enabled = enabled, role = Role.Switch, onValueChange = onChange)
            .testTag(tag),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(24.dp),
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = TownColors.Ink)
            Text(if (on) onText else offText, style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
        }
        // The theme's outline is a faint divider colour; the off state needs its own contrast to read as a control.
        Switch(checked = on, onCheckedChange = null, enabled = enabled,
            colors = SwitchDefaults.colors(
                checkedTrackColor = TownColors.Navy,
                uncheckedThumbColor = TownColors.InkSecondary,
                uncheckedTrackColor = TownColors.Disabled,
                uncheckedBorderColor = TownColors.InkSecondary,
            ))
    }
}

/** Deleting every place is permanent, so it asks once more. */
@Composable
private fun DeletePlaces(placeCount: Int, busy: Boolean, onDelete: () -> Unit) {
    var confirming by remember { mutableStateOf(false) }
    if (!confirming) {
        OutlinedButton(onClick = { confirming = true }, enabled = placeCount > 0 && !busy,
            modifier = Modifier.heightIn(min = 56.dp).testTag("privacy.places.delete"), border = BorderStroke(1.dp, TownColors.Line)) {
            Text(if (placeCount > 0) "장소 기록 모두 지우기 (${placeCount}곳)" else "지울 장소 기록이 없어요",
                style = MaterialTheme.typography.titleMedium, color = if (placeCount > 0 && !busy) TownColors.Warning else TownColors.OnDisabled)
        }
        return
    }
    Column(Modifier.fillMaxWidth().background(TownColors.Warning.copy(alpha = .08f), RoundedCornerShape(16.dp)).padding(20.dp)) {
        Text("연결한 장소 ${placeCount}곳의 별명과 위치를 모두 지울까요? 되돌릴 수 없어요. 건물과 마을 조각은 그대로예요.",
            style = MaterialTheme.typography.bodyMedium, color = TownColors.Ink)
        Spacer(Modifier.height(16.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = { confirming = false; onDelete() }, enabled = !busy, modifier = Modifier.heightIn(min = 56.dp).testTag("privacy.places.confirm"),
                colors = ButtonDefaults.buttonColors(containerColor = TownColors.Warning)) {
                Text("모두 지우기", style = MaterialTheme.typography.titleMedium)
            }
            OutlinedButton(onClick = { confirming = false }, modifier = Modifier.heightIn(min = 56.dp)) {
                Text("취소", style = MaterialTheme.typography.titleMedium, color = TownColors.Ink)
            }
        }
    }
}

@Composable
private fun LockedRecord(busy: Boolean, onReset: () -> Unit) {
    Column(Modifier.fillMaxWidth().background(TownColors.Warning.copy(alpha = .08f), RoundedCornerShape(16.dp)).padding(20.dp).testTag("privacy.locked")) {
        Text("저장된 이동 기록을 읽을 수 없어요", style = MaterialTheme.typography.titleMedium, color = TownColors.Warning)
        Spacer(Modifier.height(4.dp))
        Text("마을과 받은 조각은 그대로예요. 이동 기록만 지우면 다음 확인부터 새로 시작해요.",
            style = MaterialTheme.typography.bodyMedium, color = TownColors.Ink)
        Spacer(Modifier.height(16.dp))
        OutlinedButton(onClick = onReset, enabled = !busy, modifier = Modifier.heightIn(min = 56.dp).testTag("privacy.reset"),
            border = BorderStroke(1.dp, TownColors.Warning)) {
            Text("이동 기록 지우고 다시 시작", style = MaterialTheme.typography.titleMedium, color = TownColors.Warning)
        }
    }
}
