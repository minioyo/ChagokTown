package com.chagoktown.bootstrap

import android.content.Context
import androidx.compose.runtime.Composable
import com.chagoktown.platform.PleosVehicleGateway
import com.chagoktown.platform.VehicleGateway
import com.chagoktown.data.TownRepository
import com.chagoktown.session.InteractionGate
import com.chagoktown.ui.TownUiState
import java.time.LocalDate

fun createVehicleGateway(context: Context): VehicleGateway = PleosVehicleGateway(context.applicationContext)

fun createLocalDay(gateway: VehicleGateway): () -> LocalDate = { LocalDate.now() }

@Composable
fun PlatformPanel(gateway: VehicleGateway, repository: TownRepository, gate: InteractionGate, state: TownUiState,
    showNotice: (String) -> Unit, checkMobility: () -> Unit) = Unit
