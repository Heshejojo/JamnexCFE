package com.example.agente_cfe

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.app.usage.NetworkStatsManager
import android.os.BatteryManager
import android.os.Build
import android.os.Environment
import android.os.StatFs
import android.provider.Settings
import android.telephony.SubscriptionInfo
import android.telephony.SubscriptionManager
import android.telephony.TelephonyManager
import android.util.Log
import androidx.work.Worker
import androidx.work.WorkerParameters
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Calendar

class JamnexSyncWorker(
	context: Context,
	parameters: WorkerParameters,
) : Worker(context, parameters) {
	override fun doWork(): Result {
		val baseUrl = inputData.getString("base_url")?.trimEnd('/')
		if (baseUrl.isNullOrBlank()) return Result.failure()

		return try {
			sync(baseUrl)
			Result.success()
		} catch (error: Exception) {
			Log.e("JamnexSyncWorker", "La sincronización en segundo plano falló", error)
			Result.retry()
		}
	}

	private fun sync(baseUrl: String) {
		val deviceUuid = Settings.Secure.getString(
			applicationContext.contentResolver,
			Settings.Secure.ANDROID_ID,
		)?.takeIf { it.isNotBlank() } ?: error("Android ID no disponible")

		val telephony = applicationContext.getSystemService(TelephonyManager::class.java)
		val memory = ActivityManager.MemoryInfo()
		(applicationContext.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager)
			.getMemoryInfo(memory)
		val storage = StatFs(Environment.getDataDirectory().path)
		val totalStorage = storage.totalBytes
		val availableStorage = storage.availableBytes
		val battery = applicationContext.registerReceiver(
			null,
			IntentFilter(Intent.ACTION_BATTERY_CHANGED),
		)
		val batteryLevel = battery?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
			?.takeIf { it >= 0 }
		val batteryStatus = when (
			battery?.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
		) {
			BatteryManager.BATTERY_STATUS_CHARGING -> "CARGANDO"
			BatteryManager.BATTERY_STATUS_FULL -> "CARGADA"
			BatteryManager.BATTERY_STATUS_DISCHARGING,
			BatteryManager.BATTERY_STATUS_NOT_CHARGING -> "DESCARGANDO"
			else -> "DESCONOCIDO"
		}
		val batteryTemperature = battery
			?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Int.MIN_VALUE)
			?.takeIf { it != Int.MIN_VALUE }
			?.div(10.0)
		val now = System.currentTimeMillis()
		val connection = connectionState()
		val ramTotalMb = bytesToMb(memory.totalMem)
		val ramAvailableMb = bytesToMb(memory.availMem)
		val storageTotalMb = bytesToMb(totalStorage)
		val storageAvailableMb = bytesToMb(availableStorage)
		val devicePayload = json(
			"device_uuid" to deviceUuid,
			"fabricante" to Build.MANUFACTURER,
			"modelo" to Build.MODEL,
			"version_android" to Build.VERSION.RELEASE,
			"android_sdk" to Build.VERSION.SDK_INT,
			"serial" to deviceSerial(),
			"imei_1" to imei(telephony, 0),
			"imei_2" to imei(telephony, 1),
			"ram_total" to ramTotalMb,
			"almacenamiento_total" to storageTotalMb,
		)
		val storedToken = applicationContext
			.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
			.getString("flutter.device_token", null)
			?.takeIf { it.isNotBlank() }
		var token = storedToken ?: registerDevice(baseUrl, devicePayload)

		token = postDevice(
			baseUrl,
			"/device/status/",
			json(
				"device_uuid" to deviceUuid,
				"battery_percent" to batteryLevel,
				"battery_status" to batteryStatus,
				"connected" to connection.first,
				"ram_total" to ramTotalMb,
				"ram_usada" to (ramTotalMb - ramAvailableMb).coerceAtLeast(0),
				"ram_disponible" to ramAvailableMb,
				"almacenamiento_total" to storageTotalMb,
				"almacenamiento_usado" to (storageTotalMb - storageAvailableMb).coerceAtLeast(0),
				"almacenamiento_disponible" to storageAvailableMb,
				"battery_temperature" to batteryTemperature,
				"timestamp" to java.time.Instant.ofEpochMilli(now).toString(),
			),
			token,
			devicePayload,
		)
		token = postDevice(
			baseUrl,
			"/device/network/",
			json("tipo_conexion" to connection.second),
			token,
			devicePayload,
		)

		val dailyUsage = mobileUsageMb(1)
		val weeklyUsage = mobileUsageMb(7)
		if (dailyUsage != null) {
			token = postDevice(
				baseUrl,
				"/device/consumption/",
				json("consumo_datos_movil" to dailyUsage, "periodo" to "diario"),
				token,
				devicePayload,
			)
		}
		if (weeklyUsage != null) {
			token = postDevice(
				baseUrl,
				"/device/consumption/",
				json("consumo_datos_movil" to weeklyUsage, "periodo" to "semanal"),
				token,
				devicePayload,
			)
		}

		activeSubscriptions().forEach { subscription ->
			token = postDevice(
				baseUrl,
				"/device/sim/",
				json(
					"sim_uuid" to subscription.subscriptionId.toString(),
					"iccid" to runCatching { subscription.iccId }.getOrNull(),
					"slot" to subscription.simSlotIndex,
					"operador_nombre" to subscription.carrierName?.toString(),
					"pais" to subscription.countryIso,
					"mcc" to subscriptionMcc(subscription),
					"mnc" to subscriptionMnc(subscription),
					"numero_telefonico" to runCatching { subscription.number }.getOrNull(),
					"carrier_id" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) subscription.carrierId else null,
					"esim" to if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) subscription.isEmbedded else false,
					"tecnologia" to networkTechnology(telephony),
					"roaming" to runCatching { telephony.isNetworkRoaming }.getOrDefault(false),
				),
				token,
				devicePayload,
			)
		}
	}

	private fun postDevice(
		baseUrl: String,
		endpoint: String,
		payload: JSONObject,
		currentToken: String,
		devicePayload: JSONObject,
	): String {
		val response = request(baseUrl, endpoint, payload, currentToken)
		if (response.first in 200..299) return currentToken
		if (response.first != HttpURLConnection.HTTP_UNAUTHORIZED) {
			error("Backend respondió HTTP ${response.first} en $endpoint")
		}
		val refreshedToken = registerDevice(baseUrl, devicePayload)
		val retryResponse = request(baseUrl, endpoint, payload, refreshedToken)
		if (retryResponse.first !in 200..299) {
			error("Backend respondió HTTP ${retryResponse.first} en $endpoint")
		}
		return refreshedToken
	}

	private fun registerDevice(baseUrl: String, payload: JSONObject): String {
		val response = request(baseUrl, "/device/register/", payload, null)
		if (response.first !in 200..299) {
			error("No se pudo registrar el dispositivo: HTTP ${response.first}")
		}
		val token = JSONObject(response.second).optString("token").takeIf { it.isNotBlank() }
			?: error("El backend no devolvió el token del dispositivo")
		applicationContext
			.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
			.edit()
			.putString("flutter.device_token", token)
			.apply()
		return token
	}

	private fun request(
		baseUrl: String,
		endpoint: String,
		payload: JSONObject,
		token: String?,
	): Pair<Int, String> {
		val connection = URL("$baseUrl$endpoint").openConnection() as HttpURLConnection
		try {
			connection.requestMethod = "POST"
			connection.connectTimeout = 20_000
			connection.readTimeout = 20_000
			connection.doOutput = true
			connection.setRequestProperty("Content-Type", "application/json")
			if (token != null) connection.setRequestProperty("Authorization", "Device $token")
			connection.outputStream.use { output ->
				output.write(payload.toString().toByteArray(Charsets.UTF_8))
			}
			val status = connection.responseCode
			val bodyStream = if (status in 200..299) connection.inputStream else connection.errorStream
			val body = bodyStream?.bufferedReader()?.use { it.readText() }.orEmpty()
			return status to body
		} finally {
			connection.disconnect()
		}
	}

	private fun connectionState(): Pair<Boolean, String> {
		val manager = applicationContext.getSystemService(ConnectivityManager::class.java)
		val capabilities = manager.getNetworkCapabilities(manager.activeNetwork)
			?: return false to "SIN_CONEXION"
		return when {
			capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> true to "WIFI"
			capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> true to "DATOS_MOVILES"
			else -> true to "SIN_CONEXION"
		}
	}

	private fun activeSubscriptions(): List<SubscriptionInfo> = try {
		applicationContext.getSystemService(SubscriptionManager::class.java)
			?.activeSubscriptionInfoList.orEmpty()
	} catch (_: SecurityException) {
		emptyList()
	}

	private fun mobileUsageMb(days: Int): Double? {
		return try {
			val telephony = applicationContext.getSystemService(TelephonyManager::class.java)
			val subscriberId = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
				null
			} else {
				telephony.subscriberId ?: return null
			}
			val end = System.currentTimeMillis()
			val start = Calendar.getInstance().apply {
				timeInMillis = end
				set(Calendar.HOUR_OF_DAY, 0)
				set(Calendar.MINUTE, 0)
				set(Calendar.SECOND, 0)
				set(Calendar.MILLISECOND, 0)
				add(Calendar.DAY_OF_YEAR, -(days - 1))
			}
			val manager = applicationContext.getSystemService(NetworkStatsManager::class.java)
			val bucket = manager.querySummaryForDevice(
				ConnectivityManager.TYPE_MOBILE,
				subscriberId,
				start.timeInMillis,
				end,
			)
			(bucket.rxBytes + bucket.txBytes).toDouble() / (1024.0 * 1024.0)
		} catch (_: Exception) {
			null
		}
	}

	private fun deviceSerial(): String? = runCatching {
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) Build.getSerial() else Build.SERIAL
	}.getOrNull() ?: Settings.Secure.getString(
		applicationContext.contentResolver,
		Settings.Secure.ANDROID_ID,
	)

	private fun imei(telephony: TelephonyManager, slot: Int): String? =
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
			runCatching { telephony.getImei(slot) }.getOrNull()
		} else {
			null
		}

	private fun subscriptionMcc(subscription: SubscriptionInfo): String? =
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
			subscription.mccString
		} else {
			subscription.mcc.takeIf { it > 0 }?.toString()?.padStart(3, '0')
		}

	private fun subscriptionMnc(subscription: SubscriptionInfo): String? =
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
			subscription.mncString
		} else {
			subscription.mnc.takeIf { it > 0 }?.toString()
		}

	private fun networkTechnology(telephony: TelephonyManager): String = when (
		telephony.dataNetworkType
	) {
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

	private fun bytesToMb(value: Long): Int =
		(value.toDouble() / (1024.0 * 1024.0)).toInt()

	private fun json(vararg fields: Pair<String, Any?>): JSONObject =
		JSONObject().apply {
			fields.forEach { (key, value) ->
				if (value != null) put(key, value)
			}
		}
}
