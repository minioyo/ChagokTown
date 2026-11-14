package com.chagoktown.ui.town

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.chagoktown.ui.theme.TownDialog
import androidx.compose.ui.window.DialogProperties
import com.chagoktown.data.MaxAliasLength
import com.chagoktown.data.local.PlaceKind
import com.chagoktown.ui.theme.TownColors

/** Says only whether and how a building is linked. The alias itself stays folded on the shared screen. */
@Composable
internal fun PlaceChip(kind: PlaceKind?, enabled: Boolean, onClick: () -> Unit) {
    OutlinedButton(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("place.open"),
        shape = RoundedCornerShape(16.dp), border = BorderStroke(1.dp, TownColors.Line)) {
        Text(when (kind) {
            null -> "이 건물에 장소 연결하기"
            PlaceKind.MANUAL -> "장소 · 직접 적은 별명"
            PlaceKind.LOCATION -> "장소 · 주차한 곳과 연결됨"
        }, style = MaterialTheme.typography.titleMedium, color = TownColors.Navy)
    }
}

/**
 * Link, rename, reveal or unlink one building's place. Shown only while playable for the selected building; the caller
 * closes it on any gate or selection change, and the revealed alias is cleared by the ViewModel at the same moments.
 */
@Composable
internal fun PlaceDialog(
    plotName: String,
    kind: PlaceKind?,
    revealedAlias: String?,
    defaultAlias: String,
    locationOn: Boolean,
    busy: Boolean,
    notice: String?,
    onSaveAlias: (String) -> Unit,
    onLinkHere: (String) -> Unit,
    onReveal: () -> Unit,
    onHide: () -> Unit,
    onUnlink: () -> Unit,
    onDismiss: () -> Unit,
) {
    var text by remember { mutableStateOf("") }
    var confirmUnlink by remember { mutableStateOf(false) }
    val focus = LocalFocusManager.current
    val linked = kind != null
    // A new place may fall back to the neutral default name; renaming an existing one needs a typed alias.
    val alias = text.trim().ifEmpty { if (linked) "" else defaultAlias }
    TownDialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.padding(32.dp).widthIn(max = 680.dp).testTag("place.dialog"), shape = RoundedCornerShape(24.dp), color = TownColors.Panel) {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(36.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("$plotName · 장소", style = MaterialTheme.typography.headlineMedium, color = TownColors.Ink)
                Text(when (kind) {
                    null -> "아직 연결한 장소가 없어요. 별명만 붙이거나, 지금 주차한 곳과 연결할 수 있어요. 연결해도 마을 조각이 늘지는 않아요."
                    PlaceKind.MANUAL -> "직접 적은 별명이 있어요. 위치는 저장하지 않았어요."
                    PlaceKind.LOCATION -> "주차했던 곳과 연결돼 있어요. 위치는 화면에 보여주지 않아요."
                }, style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
                if (linked) {
                    Row(Modifier.fillMaxWidth().background(TownColors.LightSand, RoundedCornerShape(16.dp)).padding(horizontal = 20.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Text(revealedAlias ?: "별명은 접혀 있어요", Modifier.weight(1f).testTag("place.alias"),
                            style = MaterialTheme.typography.titleMedium, color = if (revealedAlias != null) TownColors.Ink else TownColors.InkSecondary)
                        OutlinedButton(onClick = if (revealedAlias == null) onReveal else onHide, modifier = Modifier.heightIn(min = 56.dp).testTag("place.reveal")) {
                            Text(if (revealedAlias == null) "보기" else "숨기기", style = MaterialTheme.typography.titleMedium, color = TownColors.Navy)
                        }
                    }
                }
                OutlinedTextField(
                    value = text,
                    onValueChange = { input -> text = input.filterNot { it.isISOControl() }.let { it.take(it.offsetByCodePoints(0, minOf(MaxAliasLength, it.codePointCount(0, it.length)))) } },
                    modifier = Modifier.fillMaxWidth().testTag("place.alias.input"),
                    label = { Text(if (linked) "새 별명 (최대 ${MaxAliasLength}자)" else "별명 (최대 ${MaxAliasLength}자)") },
                    placeholder = { Text(if (linked) "바꿀 때만 적어 주세요" else defaultAlias) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    textStyle = MaterialTheme.typography.titleMedium,
                )
                val canLink = !busy && locationOn && alias.isNotEmpty()
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = { focus.clearFocus(); onSaveAlias(alias); text = "" }, enabled = !busy && alias.isNotEmpty(),
                        modifier = Modifier.heightIn(min = 56.dp).testTag("place.save"), colors = ButtonDefaults.buttonColors(containerColor = TownColors.Navy)) {
                        Text(if (linked) "별명 바꾸기" else "별명만 저장", style = MaterialTheme.typography.titleMedium)
                    }
                    OutlinedButton(onClick = { focus.clearFocus(); onLinkHere(alias); text = "" }, enabled = canLink,
                        modifier = Modifier.heightIn(min = 56.dp).testTag("place.link"),
                        border = BorderStroke(1.dp, if (canLink) TownColors.Navy else TownColors.Line)) {
                        Text("지금 위치와 연결", style = MaterialTheme.typography.titleMedium, color = if (canLink) TownColors.Navy else TownColors.OnDisabled)
                    }
                }
                if (!locationOn) Text("위치 사용을 켜면 지금 주차한 곳과 연결할 수 있어요. 설정에서 바꿀 수 있어요.",
                    style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
                else if (linked && text.isBlank()) Text("위치와 연결하려면 새 별명을 적어 주세요.",
                    style = MaterialTheme.typography.bodyMedium, color = TownColors.InkSecondary)
                if (linked) {
                    if (!confirmUnlink) {
                        OutlinedButton(onClick = { confirmUnlink = true }, enabled = !busy, modifier = Modifier.heightIn(min = 56.dp).testTag("place.unlink"),
                            border = BorderStroke(1.dp, TownColors.Line)) {
                            Text("연결 해제", style = MaterialTheme.typography.titleMedium, color = TownColors.Warning)
                        }
                    } else {
                        Row(Modifier.fillMaxWidth().background(TownColors.Warning.copy(alpha = .08f), RoundedCornerShape(16.dp)).padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Text("별명과 저장한 위치를 지울까요? 건물은 그대로예요.", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium, color = TownColors.Ink)
                            Button(onClick = { confirmUnlink = false; onUnlink() }, enabled = !busy, modifier = Modifier.heightIn(min = 56.dp).testTag("place.unlink.confirm"),
                                colors = ButtonDefaults.buttonColors(containerColor = TownColors.Warning)) {
                                Text("해제", style = MaterialTheme.typography.titleMedium)
                            }
                            OutlinedButton(onClick = { confirmUnlink = false }, modifier = Modifier.heightIn(min = 56.dp)) {
                                Text("취소", style = MaterialTheme.typography.titleMedium, color = TownColors.Ink)
                            }
                        }
                    }
                }
                notice?.let { Text(it, Modifier.testTag("place.message"), style = MaterialTheme.typography.bodyMedium, color = TownColors.Navy) }
                Spacer(Modifier.height(4.dp))
                Button(onClick = onDismiss, modifier = Modifier.align(Alignment.End).heightIn(min = 56.dp).width(160.dp).testTag("place.close"),
                    colors = ButtonDefaults.buttonColors(containerColor = TownColors.Navy)) {
                    Text("닫기", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    }
}
