import paho.mqtt.client as mqtt
import logging
import traceback
from . import mqtt_adapters as adapters

logger = logging.getLogger("not_so_dumb_home.mqtt_connection")


class MqttConnection:
    mqtt_client = ""
    mqtt_topic_prefix = ""

    def on_connect(self, mqttClient, userdata, flags, rc):
        logger.info("Connected to MQTT server - On Connect")
        try:
            if self.parent_on_connect:
                self.parent_on_connect()
        except:
            print(traceback.format_exc())
        logger.debug("On connect finished")

    def on_disconnect(self, mqttClient, userdata, rc):
        logger.info("Disconnected from MQTT server")

    def on_message(self, mqttClient, userdata, msg):
        logger.debug("On Message")
        try:
            if self.parent_on_message:
                self.parent_on_message()
        except:
            print(traceback.format_exc())
        logger.debug("On message finished")

    def subscribe(self, topic, callback):
        self.mqtt_client.subscribe(topic, qos=1)
        self.mqtt_client.message_callback_add(topic, callback)

    def __init__(self, config, instance_name, parent_on_connect, parent_on_message):
        logger.debug("Initializing MQTT client")
        # Read MQTT config and connect to server
        mqtt_host = config["host"]
        mqtt_port = config["port"]
        self.mqtt_topic_prefix = config["topic_prefix"]
        mqtt_ssl = config["ssl"]
        auth_type = config["auth"]
        username = config["username"]
        password = config["password"]
        self.parent_on_connect = parent_on_connect
        self.parent_on_message = parent_on_message

        # Sanity check
        if auth_type not in ["none", "password", "clientcert"]:
            logger.error("Error: Auth options: none, password, clientcert. Got \"%s\"" % auth_type)

        mqtt_port = int(config["port"])
        if mqtt_port < 1 or mqtt_port > 65535:
            raise ValueError("Error: MQTT port must be a number between 1 and 65535")

        self.mqtt_client = mqtt.Client(client_id=instance_name, clean_session=True)
        self.mqtt_client.enable_logger()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message

        if auth_type == "password":
            logger.debug("Using password authentication")
            self.mqtt_client.username_pw_set(username, password)

        if mqtt_ssl == "yes":
            logger.debug("Using SSL")
            mqtt_cacert = config["cacert"]
            mqtt_clientcert = None
            mqtt_clientkey = None
            if auth_type == "clientcert":
                logger.debug("Using client certificate authentication")
                mqtt_clientcert = config["clientcert"]
                mqtt_clientkey = config["clientkey"]
            self.mqtt_client.tls_set(mqtt_cacert, certfile=mqtt_clientcert, keyfile=mqtt_clientkey)
        logger.debug("Now connecting to MQTT server")
        self.mqtt_client.connect(mqtt_host, port=mqtt_port, keepalive=60)

    def get_topic_prefix(self):
        return self.mqtt_topic_prefix

    def loop_forever(self):
        logger.debug("Looping forever to receive MQTT messages")
        self.mqtt_client.loop_forever()

    def new_adapter(self, device):
        device_type = device.get_type()
        if device_type == "thermostat":
            logger.info("Registering new thermostat")
            return adapters.MqttThermostatAdapter(self, device)
        elif device_type == "powermeter":
            logger.info("Registering new power meter")
            return adapters.MqttPowermeterAdapter(self, device)
        else:
            raise ValueError("Unknown device type: %s" % device_type)

    def publish(self, topic, message):
        try:
            self.mqtt_client.publish(topic, message, qos=1)
        except:
            print(traceback.format_exc())
