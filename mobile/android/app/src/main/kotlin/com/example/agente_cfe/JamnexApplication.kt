package com.example.agente_cfe

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.os.Build
import android.util.Log
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf
import io.flutter.app.FlutterApplication

class JamnexApplication : FlutterApplication() {
	private var networkAvailable = false

	override fun onCreate() {
		super.onCreate()
		if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return

		val connectivityManager =
			getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
		try {
			connectivityManager.registerDefaultNetworkCallback(
				object : ConnectivityManager.NetworkCallback() {
					override fun onAvailable(network: Network) {
						val capabilities = connectivityManager.getNetworkCapabilities(network)
							?: return
						updateNetworkState(capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))
					}

					override fun onCapabilitiesChanged(
						network: Network,
						networkCapabilities: NetworkCapabilities,
					) {
						if (connectivityManager.activeNetwork == network) {
							updateNetworkState(
								networkCapabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET),
							)
						}
					}

					override fun onLost(network: Network) {
						if (connectivityManager.activeNetwork != network) {
							updateNetworkState(false)
						}
					}
				},
			)
		} catch (error: RuntimeException) {
			Log.e("JamnexApplication", "No se pudo observar la conexión de red", error)
		}
	}

	@Synchronized
	private fun updateNetworkState(isAvailable: Boolean) {
		val justConnectedToNetwork = isAvailable && !networkAvailable
		networkAvailable = isAvailable
		if (!justConnectedToNetwork) return

		val preferences = getSharedPreferences("JamnexBackgroundSync", Context.MODE_PRIVATE)
		val baseUrl = preferences.getString("base_url", null)?.trimEnd('/')
		if (baseUrl.isNullOrBlank()) return

		val request = OneTimeWorkRequestBuilder<JamnexSyncWorker>()
			.setConstraints(
				Constraints.Builder()
					.setRequiredNetworkType(androidx.work.NetworkType.CONNECTED)
					.build(),
			)
			.setInputData(workDataOf("base_url" to baseUrl))
			.build()
		try {
			WorkManager.getInstance(applicationContext).enqueueUniqueWork(
				"jamnex_network_sync",
				ExistingWorkPolicy.KEEP,
				request,
			)
		} catch (error: IllegalStateException) {
			Log.e("JamnexApplication", "No se pudo programar la sincronización de red", error)
		}
	}
}
