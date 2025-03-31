package com.example.myapplication_beacon2

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.ListView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.polidea.rxandroidble2.RxBleClient
import com.polidea.rxandroidble2.scan.ScanFilter
import com.polidea.rxandroidble2.scan.ScanSettings
import io.reactivex.android.schedulers.AndroidSchedulers
import io.reactivex.disposables.Disposable
import io.reactivex.schedulers.Schedulers
import com.example.myapplication_beacon2.Mqtt.MqttHandler
import com.polidea.rxandroidble2.scan.ScanResult
import org.json.JSONObject
import java.time.LocalDateTime

class Dataset : AppCompatActivity() {
    private lateinit var monitoringButton: Button
    private lateinit var beaconListView: ListView
    private lateinit var beaconCountTextView: TextView
    private lateinit var tbCounter: TextView
    private var isMonitoring = false
    private lateinit var rxBleClient: RxBleClient
    private var disposable: Disposable? = null

    // MQTT Handler
    private lateinit var mqttHandler: MqttHandler
    private val mqttTopic = "beaconData" //  topic

    // Aggiungo il MANUFACTURER_ID qui
    private val MANUFACTURER_ID = 0x0105

    // Variabile per il contatore
    private var count = 0

    // Handler per fermare la scansione dopo 10 secondi
    private val handler = Handler(Looper.getMainLooper())

    companion object {
        const val TAG = "Dataset"
        const val REQUEST_PERMISSION = 1
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.dataset)

        // Inizializza i vari elementi dell'interfaccia utente
        monitoringButton = findViewById(R.id.monitoringButton)
        beaconListView = findViewById(R.id.beaconList)
        beaconCountTextView = findViewById(R.id.beaconCount)
        tbCounter = findViewById(R.id.tbCounter)

        // Imposta il testo iniziale del conteggio dei beacon e del contatore
        beaconCountTextView.text = "Nessun beacon rilevato"
        tbCounter.text = count.toString()
        beaconListView.adapter =
            ArrayAdapter(this, android.R.layout.simple_list_item_1, arrayOf("--"))

        // Inizializza RxBleClient
        rxBleClient = RxBleClient.create(this)

        // Inizializza MQTT Handler
        mqttHandler =
            MqttHandler(mqttTopic) // Assicurati che MqttHandler sia configurato correttamente
        mqttHandler.setMqttCallBackAndConnect()

        // Controlla i permessi e richiedili se necessario
        checkBluetoothPermissions()

        // Imposta il listener per il pulsante di monitoraggio
        monitoringButton.setOnClickListener { monitoringButtonTapped() }
    }

    private fun checkBluetoothPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH) != PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADMIN) != PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(
                Manifest.permission.BLUETOOTH,
                Manifest.permission.BLUETOOTH_ADMIN,
                Manifest.permission.ACCESS_FINE_LOCATION
            ), 1)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_PERMISSION) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startScanning() // Avvia la scansione se il permesso è stato accordato
            } else {
                Log.e(TAG, "Permission denied")
            }
        }
    }

    private fun monitoringButtonTapped() {
        if (!isMonitoring) {
            startScanning()
        } else {
            stopScanning()
        }
    }

    private fun startScanning() {
        // Incrementa il contatore quando inizia il monitoraggio
        count++
        tbCounter.text = count.toString()
        val scanFilter = ScanFilter.Builder()
            .setManufacturerData(MANUFACTURER_ID, byteArrayOf()) // Filtra i beacon del produttore specificato
            .build()

        val scanSettings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)
            .build()



        disposable = rxBleClient.scanBleDevices(scanSettings, scanFilter)
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe({ scanResult: ScanResult ->
                // Ottieni i dati del beacon
                val macAddress = scanResult.bleDevice.macAddress
                val rssi = scanResult.rssi
                Log.d(TAG, "Rilevato beacon per dataset: $macAddress, RSSI: $rssi")

                // Crea il messaggio da inviare
                val timestamp = LocalDateTime.now().toString()
                val beaconData = JSONObject()
                beaconData.put("Posizione", count)
                beaconData.put("macAddress", macAddress)
                beaconData.put("RSSI", rssi)
                beaconData.put("timestamp", timestamp)
                // Invia i dati direttamente tramite MQTT
                mqttHandler.publishMessage(mqttTopic, beaconData.toString()) // Sostituisci con il tuo topic MQTT

            },
                { throwable: Throwable ->
                    Log.e(TAG, "Error during scan: ${throwable.message}")
                }
            )

        isMonitoring = true
        monitoringButton.text = "Stop Monitoring"

        // Avvia il timer per fermare la scansione dopo 10 secondi
        handler.postDelayed({
            stopScanning()
        }, 10000) // 10 secondi = 10000 millisecondi
    }

    private fun stopScanning() {
        disposable?.dispose()
        isMonitoring = false
        monitoringButton.text = "Start Monitoring"
    }


    override fun onDestroy() {
        super.onDestroy()
        stopScanning() // Assicurati di fermare la scansione
        if (::mqttHandler.isInitialized) {
            mqttHandler.disconnect()
            Log.d(TAG, "MQTT Client Disconnected")
        }
    }
}
