package com.example.myapplication_beacon2

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.example.myapplication_beacon2.Mqtt.MqttHandler
import com.polidea.rxandroidble2.RxBleClient
import com.polidea.rxandroidble2.scan.ScanFilter
import com.polidea.rxandroidble2.scan.ScanSettings
import io.reactivex.android.schedulers.AndroidSchedulers
import io.reactivex.disposables.Disposable
import io.reactivex.schedulers.Schedulers
import org.json.JSONObject
import java.time.LocalDateTime

class BeaconScanService : Service() {

    private lateinit var rxBleClient: RxBleClient
    private var bleScanDisposable: Disposable? = null
    private val MANUFACTURER_ID = 0x0105 // ID del produttore desiderato
    private lateinit var mqttHandler: MqttHandler // Aggiungi MqttHandler qui
    private val mqttTopic ="beaconSend"   //rssi/1

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(1, createNotification())

        // Inizializza RxBleClient
        rxBleClient = RxBleClient.create(this)
        // Inizializza MqttHandler
        mqttHandler = MqttHandler(mqttTopic)
        // Collega e imposta il callback MQTT
        mqttHandler.setMqttCallBackAndConnect()
        Log.d("Mqtt ", "Mqtt connesso")
        startScanning()
    }

    private fun startScanning() {
        val scanFilter = ScanFilter.Builder()
            .setManufacturerData(MANUFACTURER_ID, byteArrayOf())
            .build()

        val scanSettings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES) // Attiva un callback per ogni annuncio Bluetooth trovato che corrisponde ai criteri del filtro.
            .build()

        bleScanDisposable = rxBleClient.scanBleDevices(scanSettings, scanFilter)
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe({ scanResult ->
                val macAddress = scanResult.bleDevice.macAddress
                val rssi = scanResult.rssi
                Log.d("Beacon", "Rilevato beacon: $macAddress, RSSI: $rssi")

                val timestamp = LocalDateTime.now().toString()
                val beaconData = JSONObject().apply {
                    put("timestamp", timestamp)
                    put("macAddress", macAddress)
                    put("RSSI", rssi)
                }

                // Invia i dati RSSI tramite MQTT

                mqttHandler.publishMessage(mqttTopic, beaconData.toString())

            }, { throwable ->
                Log.e("Beacon", "Errore durante la scansione: ${throwable.message}")
            })
    }

    private fun createNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            notificationIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE // Aggiunto FLAG_IMMUTABLE qui
        )

        return Notification.Builder(this, "beacon_service_channel")
            .setContentTitle("Beacon Scanning")
            .setContentText("Scanning for beacons...")
            .setSmallIcon(R.drawable.ic_launcher_foreground) // Assicurati di avere un'icona di notifica
            .setContentIntent(pendingIntent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                "beacon_service_channel",
                "Beacon Service Channel",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        super.onDestroy()
        bleScanDisposable?.dispose() // Ferma la scansione
    }
}
