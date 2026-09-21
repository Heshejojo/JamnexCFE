package com.example.agente_cfe

import android.Manifest
import android.app.usage.NetworkStats
import android.app.usage.NetworkStatsManager
import android.app.ActivityManager
import android.net.ConnectivityManager
import android.net.wifi.WifiManager
import android.content.pm.PackageManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.provider.Settings
import android.app.AppOpsManager
import android.os.Build
import android.os.BatteryManager
import android.os.Environment
import android.os.Process
import android.os.StatFs
import android.net.NetworkCapabilities
import android.telephony.TelephonyManager
import android.content.pm.ApplicationInfo
import android.telephony.SubscriptionManager
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.android.FlutterActivity
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
	private val channelName = "agente_cfe/sim"
	private val permissionRequestCode = 901
	private var usageAccessPromptShown = false

	private fun hasUsageAccess(): Boolean {
		if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return true
		val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
		return appOps.checkOpNoThrow(
			AppOpsManager.OPSTR_GET_USAGE_STATS,
			Process.myUid(),
			packageName,
		) == AppOpsManager.MODE_ALLOWED
	}

	private fun requestUsageAccessIfNeeded() {
		if (hasUsageAccess() || usageAccessPromptShown) return
		usageAccessPromptShown = true
		startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
	}

	private fun missingPhonePermissions(): Array<String> {
		val permissions = mutableListOf(
			Manifest.permission.READ_PHONE_STATE,
		)
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
			permissions.add(Manifest.permission.READ_PHONE_NUMBERS)
		}
		return permissions.filter {
			ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
		}.toTypedArray()
	}

	private fun fallbackPhoneNumber(): String? {
		return runCatching { getSystemService(Context.TELEPHONY_SERVICE).let { it as TelephonyManager }.line1Number }
			.getOrNull()
	}

	private fun subscriptionMcc(subscription: android.telephony.SubscriptionInfo): String? {
		return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
			subscription.mccString
		} else {
			subscription.mcc.takeIf { it > 0 }?.toString()?.padStart(3, '0')
		}
	}

	private fun subscriptionMnc(subscription: android.telephony.SubscriptionInfo): String? {
		return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
			subscription.mncString
		} else {
			subscription.mnc.takeIf { it > 0 }?.toString()
		}
	}

	override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
		super.configureFlutterEngine(flutterEngine)
		MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName).setMethodCallHandler { call, result ->
			if (call.method == "getTelemetry") {
				requestUsageAccessIfNeeded()
				Thread {
					try {
						result.success(collectTelemetry())
					} catch (_: Exception) {
						result.success(emptyMap<String, Any?>())
					}
				}.start()
				return@setMethodCallHandler
			}

			if (call.method != "getSimInfo") {
				result.notImplemented()
				return@setMethodCallHandler
			}

			val missingPermissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
				missingPhonePermissions()
			} else {
				emptyArray()
			}
			if (missingPermissions.isNotEmpty()) {
				ActivityCompat.requestPermissions(this, missingPermissions, permissionRequestCode)
				result.success(emptyList<Map<String, Any?>>())
				return@setMethodCallHandler
			}

			try {
				val subscriptions = getSystemService(SubscriptionManager::class.java)?.activeSubscriptionInfoList.orEmpty()
				result.success(subscriptions.map { subscription ->
					mapOf(
						"subscription_id" to subscription.subscriptionId,
						"slot" to subscription.simSlotIndex,
						"operador" to subscription.carrierName?.toString(),
						"pais" to subscription.countryIso,
						"mcc" to subscriptionMcc(subscription),
						"mnc" to subscriptionMnc(subscription),
						"iccid" to runCatching { subscription.iccId }.getOrNull(),
						"numero" to (runCatching { subscription.number }.getOrNull() ?: fallbackPhoneNumber()),
						"carrier_id" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) subscription.carrierId else null,
						"esim" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) subscription.isEmbedded else false,
						"activa" to true,
					)
				})
			} catch (_: SecurityException) {
				result.success(emptyList<Map<String, Any?>>())
			}
		}
	}

	private fun collectTelemetry(): Map<String, Any?> {
		val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
		val telephonyManager = getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
		val wifiInfo = (getSystemService(Context.WIFI_SERVICE) as WifiManager).connectionInfo
		val wifiSignalPercent = wifiInfo?.rssi?.let { rssi ->
			(((rssi + 90).coerceIn(0, 60) * 100) / 60)
		}
		val memory = ActivityManager.MemoryInfo()
		activityManager.getMemoryInfo(memory)
		val storage = StatFs(Environment.getDataDirectory().path)
		val totalStorageBytes = storage.totalBytes.toDouble()
		val availableStorageBytes = storage.availableBytes.toDouble()
		val battery = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
		val batteryPercent = battery?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
			?.takeUnless { it < 0 }
		val temperature = battery?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Int.MIN_VALUE)
			?.takeUnless { it == Int.MIN_VALUE }?.div(10.0)

		return mapOf(
			"ram_total_mb" to bytesToMb(memory.totalMem),
			"ram_used_mb" to bytesToMb((memory.totalMem - memory.availMem)),
			"ram_available_mb" to bytesToMb(memory.availMem),
			"storage_total_mb" to bytesToMb(totalStorageBytes),
			"storage_used_mb" to bytesToMb((totalStorageBytes - availableStorageBytes).toLong()),
			"storage_available_mb" to bytesToMb(availableStorageBytes.toLong()),
			"battery_temperature_c" to temperature,
			"battery_percent" to batteryPercent,
			"serial" to runCatching {
				if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) Build.getSerial() else Build.SERIAL
			}.getOrNull(),
			"imei_1" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) runCatching { telephonyManager.getImei(0) }.getOrNull() else null,
			"imei_2" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) runCatching { telephonyManager.getImei(1) }.getOrNull() else null,
			"mobile_data_day_mb" to queryNetworkUsage(NetworkCapabilities.TRANSPORT_CELLULAR, 1),
			"mobile_data_week_mb" to queryNetworkUsage(NetworkCapabilities.TRANSPORT_CELLULAR, 7),
			"mobile_data_limit_mb" to 2048.0,
			"wifi_data_mb" to queryNetworkUsage(NetworkCapabilities.TRANSPORT_WIFI, 1),
			"wifi_ssid" to wifiInfo?.ssid?.removePrefix("\"")?.removeSuffix("\""),
			"wifi_rssi" to wifiInfo?.rssi?.takeUnless { it == -127 },
			"wifi_signal_percent" to wifiSignalPercent,
			"wifi_frequency_mhz" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) wifiInfo?.frequency else null,
			"wifi_link_speed_mbps" to wifiInfo?.linkSpeed?.takeUnless { it < 0 },
			"applications" to visibleApplications(),
			"network_technology" to networkTechnology(telephonyManager),
			"carrier_name" to telephonyManager.networkOperatorName,
			"carrier_id" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) telephonyManager.simCarrierId else null,
			"roaming" to runCatching { telephonyManager.isNetworkRoaming }.getOrDefault(false),
		)
	}

	private fun bytesToMb(value: Long): Double {
		return value.toDouble() / (1024.0 * 1024.0)
	}

	private fun bytesToMb(value: Double): Double {
		return value / (1024.0 * 1024.0)
	}

	private fun queryNetworkUsage(transport: Int, days: Int): Double? {
		return try {
			if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return null
			val manager = getSystemService(Context.NETWORK_STATS_SERVICE) as NetworkStatsManager
			val end = System.currentTimeMillis()
			val start = end - (days * 24L * 60L * 60L * 1000L)
			val networkType = if (transport == NetworkCapabilities.TRANSPORT_WIFI) {
				ConnectivityManager.TYPE_WIFI
			} else {
				ConnectivityManager.TYPE_MOBILE
			}
			val subscriberId = if (networkType == ConnectivityManager.TYPE_MOBILE) {
				getSystemService(Context.TELEPHONY_SERVICE).let { it as TelephonyManager }.subscriberId
			} else {
				null
			}
			val bucket = manager.querySummaryForDevice(networkType, subscriberId, start, end)
			(bucket.rxBytes + bucket.txBytes).toDouble() / (1024.0 * 1024.0)
		} catch (_: Exception) {
			null
		}
	}

	private fun networkTechnology(telephonyManager: TelephonyManager): String? {
		return runCatching {
			when (telephonyManager.dataNetworkType) {
				TelephonyManager.NETWORK_TYPE_GPRS,
				TelephonyManager.NETWORK_TYPE_EDGE,
				TelephonyManager.NETWORK_TYPE_CDMA,
				TelephonyManager.NETWORK_TYPE_1xRTT,
				TelephonyManager.NETWORK_TYPE_IDEN -> "2G"
				TelephonyManager.NETWORK_TYPE_UMTS,
				TelephonyManager.NETWORK_TYPE_EVDO_0,
				TelephonyManager.NETWORK_TYPE_EVDO_A,
				TelephonyManager.NETWORK_TYPE_EVDO_B,
				TelephonyManager.NETWORK_TYPE_HSDPA,
				TelephonyManager.NETWORK_TYPE_HSUPA,
				TelephonyManager.NETWORK_TYPE_HSPA,
				TelephonyManager.NETWORK_TYPE_HSPAP -> "3G"
				TelephonyManager.NETWORK_TYPE_LTE -> "4G"
				TelephonyManager.NETWORK_TYPE_NR -> "5G"
				else -> "Desconocida"
			}
		}.getOrNull()
	}

	private fun visibleApplications(): List<Map<String, Any?>> {
		return packageManager.getInstalledApplications(PackageManager.GET_META_DATA).map { app ->
			val packageInfo = runCatching { packageManager.getPackageInfo(app.packageName, 0) }.getOrNull()
			mapOf(
				"package_name" to app.packageName,
				"name" to app.loadLabel(packageManager).toString(),
				"version" to packageInfo?.versionName,
				"system" to ((app.flags and ApplicationInfo.FLAG_SYSTEM) != 0),
			)
		}
	}
}
