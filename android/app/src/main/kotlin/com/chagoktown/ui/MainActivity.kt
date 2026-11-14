package com.chagoktown.ui

import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.chagoktown.bootstrap.PlatformPanel
import com.chagoktown.bootstrap.TownApplication
import com.chagoktown.ui.theme.TownTheme
import com.chagoktown.ui.town.TownScreen
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private val container get() = (application as TownApplication).container
    // The result needs no handling: the next link attempt checks the permission again.
    private val permissionRequest = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { }

    private fun ensureLocationPermission(): Boolean {
        val missing = container.gateway.locationPermissions.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (missing.isNotEmpty()) permissionRequest.launch(missing.toTypedArray())
        return missing.isEmpty()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.RESUMED) {
                container.gateway.refreshAccess()
                container.gateway.playAccess.collect(container.gate::setPlayAccess)
            }
        }
        // Form-factor test hook, honoured only in debuggable builds (see TownTheme).
        val panelOverride = intent.getStringExtra(EXTRA_PANEL).takeIf { applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0 }
        setContent {
            TownTheme(panelOverride) {
                val model: TownViewModel = viewModel(factory = object : ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : ViewModel> create(modelClass: Class<T>): T =
                        TownViewModel(container.repository, container.gate, container.gateway::readDistance, container.gateway::readLocation, container.today) as T
                })
                val state by model.state.collectAsStateWithLifecycle()
                Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    TownScreen(state, model, container.layout, platformPanel = {
                        PlatformPanel(container.gateway, container.repository, container.gate, state, model::showNotice, model::checkMobility)
                    }, ensureLocationPermission = ::ensureLocationPermission)
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        container.gate.setResumed(true)
    }

    override fun onPause() {
        container.gate.setResumed(false)
        super.onPause()
    }

    companion object {
        /** `WIDTHxHEIGHT@DPI` of the panel a form-factor test display stands for. Debuggable builds only. */
        const val EXTRA_PANEL = "chagok.panel"
    }
}
