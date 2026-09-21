class DeviceSnapshot {
  final String? deviceId;
  final String? fabricante;
  final String? modelo;
  final String? versionAndroid;
  final String? imei1;
  final String? imei2;
  final String? serial;
  final int? androidSdk;
  final int? ramTotalMb;
  final int? ramUsedMb;
  final int? ramAvailableMb;
  final int? almacenamientoTotalMb;
  final int? almacenamientoUsadoMb;
  final int? almacenamientoDisponibleMb;
  final int? batteryPercent;
  final String? batteryStatus;
  final String? connectionType;
  final double? batteryTemperature;
  final double? mobileDataMb;
  final double? mobileDataDayMb;
  final double? mobileDataWeekMb;
  final double? mobileDataLimitMb;
  final double? wifiDataMb;
  final String? wifiSsid;
  final int? wifiRssi;
  final int? wifiSignalPercent;
  final int? wifiFrequency;
  final int? wifiLinkSpeed;
  final String? networkTechnology;
  final String? carrierName;
  final int? carrierId;
  final bool roaming;
  final List<Map<String, dynamic>> applications;
  final List<Map<String, dynamic>> sims;
  final bool connected;
  final DateTime timestamp;

  const DeviceSnapshot({
    this.deviceId,
    this.fabricante,
    this.modelo,
    this.versionAndroid,
    this.imei1,
    this.imei2,
    this.serial,
    this.androidSdk,
    this.ramTotalMb,
    this.ramUsedMb,
    this.ramAvailableMb,
    this.almacenamientoTotalMb,
    this.almacenamientoUsadoMb,
    this.almacenamientoDisponibleMb,
    this.batteryPercent,
    this.batteryStatus,
    this.connectionType,
    this.batteryTemperature,
    this.mobileDataMb,
    this.mobileDataDayMb,
    this.mobileDataWeekMb,
    this.mobileDataLimitMb,
    this.wifiDataMb,
    this.wifiSsid,
    this.wifiRssi,
    this.wifiSignalPercent,
    this.wifiFrequency,
    this.wifiLinkSpeed,
    this.networkTechnology,
    this.carrierName,
    this.carrierId,
    this.roaming = false,
    this.applications = const [],
    this.sims = const [],
    required this.connected,
    required this.timestamp,
  });

  Map<String, dynamic> toBackendPayload() {
    return {
      'device_uuid': deviceId,
      'fabricante': fabricante,
      'modelo': modelo,
      'version_android': versionAndroid,
      'imei_1': imei1,
      'imei_2': imei2,
      'serial': serial,
      'android_sdk': androidSdk,
      'ram_total': ramTotalMb,
      'almacenamiento_total': almacenamientoTotalMb,
      'activo': connected,
      'ultimo_contacto': timestamp.toUtc().toIso8601String(),
    };
  }
}
