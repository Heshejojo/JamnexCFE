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
						updateNetworkState(isUsableNetwork(connectivityManager.getNetworkCapabilities(network)))
					}

					override fun onCapabilitiesChanged(
						network: Network,
						networkCapabilities: NetworkCapabilities,
					) {
						if (connectivityManager.activeNetwork == network) {
							updateNetworkState(isUsableNetwork(networkCapabilities))
						}
					}

					override fun onLost(network: Network) {
						val activeNetwork = connectivityManager.activeNetwork
						updateNetworkState(
							activeNetwork != null &&
								isUsableNetwork(connectivityManager.getNetworkCapabilities(activeNetwork)),
						)
					}
				},
			)
		} catch (error: RuntimeException) {
			Log.e("JamnexApplication", "No se pudo observar la conexión de red", error)
		}
	}

	private fun isUsableNetwork(capabilities: NetworkCapabilities?): Boolean =
		capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true &&
			(Build.VERSION.SDK_INT < Build.VERSION_CODES.M ||
				capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED))

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
				ExistingWorkPolicy.REPLACE,
				request,
			)
		} catch (error: IllegalStateException) {
			Log.e("JamnexApplication", "No se pudo programar la sincronización de red", error)
		}
	}
}
