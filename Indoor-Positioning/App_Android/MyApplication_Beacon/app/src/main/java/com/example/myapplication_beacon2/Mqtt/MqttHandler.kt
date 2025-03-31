package com.example.myapplication_beacon2.Mqtt

import android.util.Log
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended
import org.eclipse.paho.client.mqttv3.MqttClient
import org.eclipse.paho.client.mqttv3.MqttConnectOptions
import org.eclipse.paho.client.mqttv3.MqttException
import org.eclipse.paho.client.mqttv3.MqttMessage

class MqttHandler(val topicId: String) {


    companion object {
        private const val TAG = "MqttHandler"
        //const val CLIENT_USER_NAME = "iotrobotic"  //imposto io
        //const val CLIENT_PASSWORD = "iotrobotic"   //imposto io per il broker MQTT

        //const val MQTT_HOST = "tcp://127.0.0.1:1883"
        const val MQTT_HOST = "tcp://test.mosquitto.org:1883" //imposto io per il broker MQTT

        const val CONNECTION_TIMEOUT = 120 //secondi
        const val CONNECTION_KEEP_ALIVE_INTERVAL = 60
        const val CONNECTION_CLEAN_SESSION = true //broker non memorizza i messaggi ricevuti
        const val CONNECTION_RECONNECT = true
        const val QOS = 0
    }


    //creo un oggetto  MqttClient
    private val client: MqttClient

    private var messageCallback: MessageCallback? = null

    fun setMessageCallback(callback: MessageCallback) {
        this.messageCallback = callback
    }

    //sezione di inizializzazione dell'oggetto client
    init {
        val serverUri = MQTT_HOST  //uri del broker MQTT
        val clientId: String = MqttClient.generateClientId() //id del client MQTT
//      Set up the persistence layer
//      val persistence = MemoryPersistence()
//
//      Initialize the MQTT client
//      client = MqttClient(brokerUrl, clientId, persistence)
        client = MqttClient(serverUri, clientId, null)
    }

    //setto eventi di callback per Client
    fun setMqttCallBackAndConnect() {
        Log.d(TAG, "setMqttCallBackAndConnect: ")

        //Setto le funzioni di callback
        client.setCallback(object : MqttCallbackExtended {

            //connessione persa
            override fun connectionLost(cause: Throwable?) {
                Log.w(TAG, "connectionLost: ")
            }

            //messaggio arrivato
            override fun messageArrived(topic: String?, message: MqttMessage?) {
                Log.d(TAG, "messageArrived: ")
                val payload =
                    message?.payload?.toString(Charsets.UTF_8)  // estratto il payload del messaggio per ulteriori elaborazioni
                setOnMessageReceived(topic, payload) //elaboro il messaggio estratto
            }

            //metodo viene chiamato quando la consegna di un messaggio MQTT è stata completata
            override fun deliveryComplete(token: IMqttDeliveryToken?) {
                Log.d(TAG, "deliveryComplete: ")
            }

            //metodo chiamato quando la connessione al broker MQTT è stata effettuata
            override fun connectComplete(reconnect: Boolean, serverURI: String?) {
                Log.d(TAG, "connectComplete: ")
                serverURI?.let {    //se serverURI non è nullo passa il valore al log
                    Log.d(TAG, "connectComplete serverURI: $it")
                }

//                if (reconnect) {
//                    // This is a reconnection
//                } else {
//                    // This is a new connection
//                }

                //sottoscritto a un topic specifico chiamando la funzione
                subscribe(topicId, QOS)
            }
        })

        // chiamo funzione connect per connettersi effettivamente al broker MQTT.
        connect()
    }


    //connessione al Broker Mqtt
    private fun connect() {
        try {
            Log.d(TAG, "connect: ")
            // opzioni di connessione
            val mqttConnectOptions = MqttConnectOptions()
            mqttConnectOptions.isAutomaticReconnect = CONNECTION_RECONNECT
            mqttConnectOptions.isCleanSession = CONNECTION_CLEAN_SESSION
            //  mqttConnectOptions.userName = CLIENT_USER_NAME
            //    mqttConnectOptions.password = CLIENT_PASSWORD.toCharArray()
            mqttConnectOptions.connectionTimeout = CONNECTION_TIMEOUT
            mqttConnectOptions.keepAliveInterval = CONNECTION_KEEP_ALIVE_INTERVAL

            //chiamo metodo connect() del client MQTT
            client.connect(mqttConnectOptions)
        } catch (ex: MqttException) {
            //gestione eccezioni
            handleConnectionFailure(ex)
        }
    }

    //gestione eccezione
    private fun handleConnectionFailure(cause: Throwable?) {
        Log.w(TAG, "Failed to connect: ${Log.getStackTraceString(cause)}")
        // Implement your retry or error handling strategy here
        //messageCallback?.onConnectionFailure()
    }

    private fun setOnMessageReceived(topic: String?, message: String?) {
        Log.d(TAG, "setOnMessageReceived: Received message on topic $topic: $message")

        // Handle the received message
        messageCallback?.onMessageReceived(topic, message)
    }

    //Pubblicazione di messaggi su un topic MQTT utilizzando il client MQTT associato
    fun publish(topic: String, msg: String, qos: Int = 0) {
        try {
            val mqttMessage = MqttMessage(msg.toByteArray())
            client.publish(topic, mqttMessage.payload, qos, false)
            Log.d(TAG, "Message published to topic `$topic`: $msg")
        } catch (e: MqttException) {
            Log.w(TAG, "Error publishing to $topic: " + e.message, e)
            // Handle publishing failure
        }
    }


    //funzione per sottoscrivere un topic
    fun subscribe(subscriptionTopic: String, qos: Int = QOS) {
        try {
            Log.d(TAG, "subscribe: called")
            client.subscribe("/$subscriptionTopic", qos)
//            client.subscribe(
//                subscriptionTopic,
//                qos
//            ) { topic, message ->
//                val payload = message?.payload?.toString(Charsets.UTF_8)
//                setOnMessageReceived(topic, payload)
//                Log.d(TAG, "subscribe: $payload")
//            }
        } catch (ex: MqttException) {
            Log.w(TAG, "Exception on subscribing to topic '$subscriptionTopic'", ex)
            // Handle subscription failure
        }
    }


    fun isConnected(): Boolean {
        return client.isConnected
    }

    fun disconnect() {
        try {
            client.disconnect()
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }


    // Definizione della classe MessageCallback
    interface MessageCallback {
        // Metodo chiamato quando un messaggio MQTT è ricevuto
        fun onMessageReceived(topic: String?, message: String?)

        // Metodo chiamato in caso di fallimento della connessione MQTT
        fun onConnectionFailure()
    }

    fun publishMessage(topic: String, message: String) {
        if (client.isConnected) {  // Verifica che il client sia connesso
            try {
                val mqttMessage = MqttMessage(message.toByteArray())
                client.publish(topic, mqttMessage)
                Log.d(TAG, "Message published to topic `$topic`: $message")
            } catch (ex: MqttException) {
                Log.e(TAG, "Errore MQTT durante la pubblicazione su $topic", ex)
            }
        } else {
            Log.w(TAG, "Publish failed: MQTT client not connected")
        }
    }


}


