import json
import logging
import threading
import time

config_messages_period_seconds = 60


class MqttThermostatAdapter:

    def __init__(self, mqtt_conn, device):
        self.logger = logging.getLogger("not_so_dumb_home.mqtt_thermostat_adapter_%s" % device.get_name())
        self.device = device
        self.mqtt_conn = mqtt_conn
        topic_prefix = mqtt_conn.get_topic_prefix()
        device_id = device.get_id()
        self.device_topics_prefix = "%s/climate/%s" % (topic_prefix, device_id)

        self.use_ghost_thermostat =  self.device.using_ghost_thermostat()

        # Subscribe to the command topics
        self.mqtt_conn.subscribe("%s/setpoint" % self.device_topics_prefix, self.setpoint_command)
        self.mqtt_conn.subscribe("%s/mode" % self.device_topics_prefix, self.mode_command)
        self.mqtt_conn.subscribe(device.get_outdoor_temp_topic(), self.set_outdoor_temp_command)
        if self.use_ghost_thermostat:
            self.mqtt_conn.subscribe("%s_ghost/temp_high" % self.device_topics_prefix, self.temp_high_command)
            self.mqtt_conn.subscribe("%s_ghost/temp_low" % self.device_topics_prefix, self.temp_low_command)

        # Launch the periodic message threads
        config_msg_thread = threading.Thread(target=self.config_message_scheduler, args=())
        state_msg_thread = threading.Thread(target=self.state_message_scheduler, args=())
        config_msg_thread.start()
        state_msg_thread.start()

    def setpoint_command(self, client, userdata, message):
        self.logger.info("Received setpoint command")
        self.logger.debug("Message is: \"%s\"" % message.payload)
        try:
            new_setpoint = float(message.payload)
            self.device.set_value("setpoint", new_setpoint)
        except ValueError:
            self.logger.warning("Received unparseable setpoint command")
            pass
        time.sleep(2)
        self.send_state_msg()

    def mode_command(self, client, userdata, message):
        self.logger.info("Received mode command")
        self.logger.debug("Message is: \"%s\"" % message.payload)
        new_mode = message.payload.decode()
        if new_mode == "off":
            self.device.set_value("is_on", False)
        elif new_mode == "heat":
            self.device.set_value("is_on", True)
        else:
            self.logger.warning("Received incorrect mode command")
        time.sleep(2)
        self.send_state_msg()

    def temp_high_command(self, client, userdata, message):
        self.logger.info("Received temp_high command")
        self.logger.debug("Message is: \"%s\"" % message.payload)
        try:
            new_temp_high = float(message.payload)
            self.device.set_value("temp_high", new_temp_high)
        except ValueError:
            self.logger.warning("Received unparseable temp_high command")
            pass
        time.sleep(2)
        self.send_state_msg()

    def temp_low_command(self, client, userdata, message):
        self.logger.info("Received temp_low command")
        self.logger.debug("Message is: \"%s\"" % message.payload)
        try:
            new_temp_low = float(message.payload)
            self.device.set_value("temp_low", new_temp_low)
        except ValueError:
            self.logger.warning("Received unparseable temp_low command")
            pass
        time.sleep(2)
        self.send_state_msg()

    def set_outdoor_temp_command(self, client, userdata, message):
        self.logger.info("Received set outdoor temp command")
        self.logger.debug("Message is: \"%s\"" % message.payload)
        try:
            outdoor_temp = float(message.payload)
            self.device.set_value("outtemp", outdoor_temp)
        except ValueError:
            self.logger.warning("Received unparseable outdoor temp command")
            pass

    def config_message_scheduler(self):
        while True:
            self.send_config_message()
            time.sleep(config_messages_period_seconds)

    # Available:
    #   topic: /available
    #   online, offline
    # Mode:
    #   Si el trasto esta engegat
    #   topic estat: /state (json)
    #   topic comandes: /thermostatModeCmd
    #   off, heat
    # Action:
    #   Si el trasto esta escalfant o no
    #   topic: /state (json)
    #   off, heating
    # Temperatura actual:
    #   topic: /temperature
    # Setpoint:
    #   topic estat: /state (json)
    #   topic comands: /setpoint

    def send_config_message(self):
        self.logger.info("send_config_message")
        device_name = self.device.get_name()
        device_id = self.device.get_id()
        message = {}
        message["name"] = device_name
        message["unique_id"] = "%s" % device_id

        # Availability
        # message["availability_topic"] = "%s/available" % self.device_topics_prefix
        # message["payload_available"] = "online"
        # message["payload_not_available"] = "offline"

        # Mode
        message["mode_state_template"] = "{{value_json.mode}}"
        message["modes"] = ["off", "heat"]
        message["mode_command_topic"] = "%s/mode" % self.device_topics_prefix
        message["mode_state_topic"] = "%s/state" % self.device_topics_prefix

        # Action
        message["action_template"] = "{{value_json.action}}"
        message["action_topic"] = "%s/state" % self.device_topics_prefix

        # Temperature
        message["current_temperature_topic"] = "%s/state" % self.device_topics_prefix
        message["current_temperature_template"] = "{{value_json.current_temp}}"

        # Setpoint
        message["temperature_state_topic"] = "%s/state" % self.device_topics_prefix
        message["temperature_state_template"] = "{{value_json.setpoint}}"
        message["temperature_command_topic"] = "%s/setpoint" % self.device_topics_prefix

        # Other stuff
        message["min_temp"] = "18"
        message["max_temp"] = "25"
        message["temp_step"] = "0.5"

        self.logger.info("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s/config" % self.device_topics_prefix, json.dumps(message))

        if self.use_ghost_thermostat:
            message = {}
            message["name"] = "%s_ghost" % device_name
            message["unique_id"] = "%s_ghost" % device_id
            message["temp_step"] = "0.5"

            message["mode_state_template"] = "{{value_json.mode}}"
            message["modes"] = ["off"]
            message["mode_command_topic"] = "%s_ghost/mode" % self.device_topics_prefix
            message["mode_state_topic"] = "%s_ghost/state" % self.device_topics_prefix
            message["current_temperature_topic"] = "%s_ghost/state" % self.device_topics_prefix
            message["current_temperature_template"] = "{{value_json.current_temp}}"

            # Temperature high (setpoint when an ON command is received)
            message["temperature_high_state_topic"] = "%s_ghost/state" % self.device_topics_prefix
            message["temperature_high_state_template"] = "{{value_json.temp_high}}"
            message["temperature_high_command_topic"] = "%s_ghost/temp_high" % self.device_topics_prefix

            # Temperature low (setpoint when an OFF command is received)
            message["temperature_low_state_topic"] = "%s_ghost/state" % self.device_topics_prefix
            message["temperature_low_state_template"] = "{{value_json.temp_low}}"
            message["temperature_low_command_topic"] = "%s_ghost/temp_low" % self.device_topics_prefix

            self.logger.info("Sending MQTT config message: \"%s\"" % json.dumps(message))
            self.mqtt_conn.publish("%s_ghost/config" % self.device_topics_prefix, json.dumps(message))

    def state_message_scheduler(self):
        # Leave 5 seconds between startup (config message) and the first status message
        time.sleep(5)
        while True:
            self.send_state_msg()
            time.sleep(self.device.get_sampling_period())

    def send_state_msg(self):
        self.logger.info("send_state_message")
        message = {}
        is_on = self.device.get_value("is_on")
        if is_on:
            message["mode"] = "heat"
        else:
            message["mode"] = "off"
        message["current_temp"] = self.device.get_value("curtemp")
        message["setpoint"] = self.device.get_value("setpoint")
        # Action is for home-assistant compatiblity
        # isHeating is for legazy (Zabbix) compatibility
        if self.device.get_value("isheating") == 1:
            message["action"] = "heating"
            message["isheating"] = 1
        else:
            message["action"] = "off"
            message["isheating"] = 0
        self.logger.info("Sending MQTT status message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s/state" % self.device_topics_prefix, json.dumps(message))

        if self.use_ghost_thermostat:
            message = {}
            message["mode"] = "off"
            message["current_temp"] = 0
            message["temp_high"] = self.device.get_value("temp_high")
            message["temp_low"] = self.device.get_value("temp_low")
            self.logger.info("Sending MQTT status message: \"%s\"" % json.dumps(message))
            self.mqtt_conn.publish("%s_ghost/state" % self.device_topics_prefix, json.dumps(message))


class MqttPowermeterAdapter:
    def __init__(self, mqtt_conn, device):
        self.logger = logging.getLogger("not_so_dumb_home.mqtt_powermeter_adapter_%s" % device.get_name())
        self.device = device
        self.mqtt_conn = mqtt_conn
        topic_prefix = mqtt_conn.get_topic_prefix()
        device_id = device.get_id()
        self.device_topics_prefix = "%s/sensor/%s" % (topic_prefix, device_id)

        # Launch the periodic message threads
        config_msg_thread = threading.Thread(target=self.config_message_scheduler, args=())
        state_msg_thread = threading.Thread(target=self.state_message_scheduler, args=())
        config_msg_thread.start()
        state_msg_thread.start()

    def config_message_scheduler(self):
        while True:
            self.send_config_message()
            time.sleep(config_messages_period_seconds)

    def send_config_message(self):
        self.logger.info("send_config_message")
        device_name = self.device.get_name()
        device_id = self.device.get_id()
        # Power
        message = {}
        message["name"] = "%s - Power" % device_name
        message["unique_id"] = "%s_power" % device_id
        message["device_class"] = "power"
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.power}}"
        message["unit_of_measurement"] = "W"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_power/config" % self.device_topics_prefix, json.dumps(message))

        # Current
        message = {}
        message["name"] = "%s - Current" % device_name
        message["unique_id"] = "%s_current" % device_id
        message["device_class"] = "current"
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.current}}"
        message["unit_of_measurement"] = "A"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_current/config" % self.device_topics_prefix, json.dumps(message))

        # Energy
        message = {}
        message["name"] = "%s - Energy" % device_name
        message["unique_id"] = "%s_energy" % device_id
        message["device_class"] = "energy"
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.energy}}"
        message["unit_of_measurement"] = "Wh"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_energy/config" % self.device_topics_prefix, json.dumps(message))

        # Voltage
        message = {}
        message["name"] = "%s - Voltage" % device_name
        message["unique_id"] = "%s_voltage" % device_id
        message["device_class"] = "voltage"
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.voltage}}"
        message["unit_of_measurement"] = "V"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_voltage/config" % self.device_topics_prefix, json.dumps(message))

        # Power factor
        message = {}
        message["name"] = "%s - Power Factor" % device_name
        message["unique_id"] = "%s_pfactor" % device_id
        message["device_class"] = "power_factor"
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.power_factor}}"
        message["unit_of_measurement"] = "%"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.logger.debug("Topic is: \"%s\"" % "%s_pfactor/config" % self.device_topics_prefix)
        self.mqtt_conn.publish("%s_pfactor/config" % self.device_topics_prefix, json.dumps(message))

    def state_message_scheduler(self):
        # Leave 5 seconds between startup (config message) and the first status message
        time.sleep(5)
        while True:
            self.send_state_msg()
            time.sleep(self.device.get_sampling_period())

    def send_state_msg(self):
        self.logger.info("send_state_message")
        message = {}
        message["power"] = self.device.get_value("power")
        message["current"] = self.device.get_value("current")
        message["energy"] = self.device.get_value("acciae")
        message["voltage"] = self.device.get_value("volt")
        message["power_factor"] = self.device.get_value("pfactor")
        message["maxpower"] = self.device.get_value("maxpower")
        self.mqtt_conn.publish("%s/state" % self.device_topics_prefix, json.dumps(message))

class MqttGasoilmeterAdapter:
    def __init__(self, mqtt_conn, device):
        self.logger = logging.getLogger("not_so_dumb_home.mqtt_gasoilmeter_adapter_%s" % device.get_name())
        self.device = device
        self.mqtt_conn = mqtt_conn
        topic_prefix = mqtt_conn.get_topic_prefix()
        device_id = device.get_id()
        self.device_topics_prefix = "%s/sensor/%s" % (topic_prefix, device_id)

        # Launch the periodic message threads
        config_msg_thread = threading.Thread(target=self.config_message_scheduler, args=())
        state_msg_thread = threading.Thread(target=self.state_message_scheduler, args=())
        config_msg_thread.start()
        state_msg_thread.start()

    def config_message_scheduler(self):
        while True:
            self.send_config_message()
            time.sleep(config_messages_period_seconds)

    def send_config_message(self):
        self.logger.info("send_config_message")
        device_name = self.device.get_name()
        device_id = self.device.get_id()

        # Level
        message = {}
        message["name"] = "%s - Level" % device_name
        message["unique_id"] = "%s_level" % device_id
        # There is no device class for measuring liters
        # (https://www.home-assistant.io/integrations/sensor/#device-class)
        # so let's just remove his value and leave it as default "Generic sensor"
        #message["device_class"] = ""
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.level}}"
        message["unit_of_measurement"] = "L"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_level/config" % self.device_topics_prefix, json.dumps(message))

        # Percentage
        message = {}
        message["name"] = "%s - Percentage" % device_name
        message["unique_id"] = "%s_percentage" % device_id
        # There is no device class for measuring liters
        # (https://www.home-assistant.io/integrations/sensor/#device-class)
        # so let's just remove his value and leave it as default "Generic sensor"
        #message["device_class"] = ""
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.percentage}}"
        message["unit_of_measurement"] = "%"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_percentage/config" % self.device_topics_prefix, json.dumps(message))

        # Capacity
        message = {}
        message["name"] = "%s - Capacity" % device_name
        message["unique_id"] = "%s_capacity" % device_id
        # There is no device class for measuring liters
        # (https://www.home-assistant.io/integrations/sensor/#device-class)
        # so let's just remove his value and leave it as default "Generic sensor"
        # message["device_class"] = ""
        message["state_topic"] = "%s/state" % self.device_topics_prefix
        message["value_template"] = "{{value_json.capacity}}"
        message["unit_of_measurement"] = "L"
        self.logger.debug("Sending MQTT config message: \"%s\"" % json.dumps(message))
        self.mqtt_conn.publish("%s_capacity/config" % self.device_topics_prefix, json.dumps(message))


    def state_message_scheduler(self):
        # Leave 5 seconds between startup (config message) and the first status message
        time.sleep(5)
        while True:
            self.send_state_msg()
            time.sleep(self.device.get_sampling_period())

    def send_state_msg(self):
        self.logger.info("send_state_message")
        message = {}
        message["level"] = self.device.get_value("level")
        message["percentage"] = self.device.get_value("percentage")
        message["capacity"] = self.device.get_value("capacity")
        self.mqtt_conn.publish("%s/state" % self.device_topics_prefix, json.dumps(message))