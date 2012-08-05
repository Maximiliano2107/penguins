#!/usr/bin/python

import time
import traceback

class Sensor(object):
    """This class defines an interface that all sensors must implement"""
    pass

class ArduinoConnectedSensor(Sensor):
    """A sensor connected to the on-board arduino"""
    def __init__(self, arduino, key):
        Sensor.__init__(self)

        self.arduino = arduino
        self.key = key

    def _read(self):
        try:
            reading = self.arduino.sensor_readings[self.key]
            return reading
        except KeyError:
            return None

class VoltageSensor(ArduinoConnectedSensor):
    """An analog sensor for determining voltage; uses a voltage divider on the arduino"""
    def __init__(self, arduino, key, R1 = 1, R2 = 1):
        ArduinoConnectedSensor.__init__(self, arduino, key)

        self.voltage = None

        # resistors used on the divider, in ohms
        self.ratio = float(R1 + R2) / float(R2)

    def read(self):
        """reads the raw millivolt value from the arduino and scales it by the voltage divider ratio"""
        reading = self._read()
        if reading is None:
            self.voltage = None
        else:
            self.voltage = self.ratio * float(reading.data) * 5 / 1023

        return self.voltage

    @property
    def status(self):
        return {'value':self.voltage, 'units':'mV'}

class TemperatureSensor(ArduinoConnectedSensor):
    """A TMP36 connected to the arduino"""
    def __init__(self, arduino, key, scaling_function = lambda voltage: (voltage - 500) / 10):
        ArduinoConnectedSensor.__init__(self, arduino, key)
        self.scaling_function = scaling_function

    def read(self):
        reading = self._read()
        if reading is None:
            self.temperature = None
        else:
            mV = float(reading.data) * (5.0 / 1023) * 1000
            self.temperature = self.scaling_function(mV)

        return self.temperature

    @property
    def status(self):
        return {'value':self.temperature, 'units':'C'}

class Sonar(ArduinoConnectedSensor):
    """An LV-MaxSonar -EZ1 connected to the Arduino (via PWM)"""
    def __init__(self, arduino, key):
        ArduinoConnectedSensor.__init__(self, arduino, key)

    def read(self):
        reading = self._read()
        if reading is None:
            self.distance = None
        else:
            self.distance = int(reading.data)

        return self.distance

    @property
    def status(self):
        return {'value':self.distance, 'units':'"'}

class Encoder(ArduinoConnectedSensor):
    """A magnetic encoder reading the wheel speed via a hall effect sensor"""
    def __init__(self, arduino, key, magnets = 2, window = 10):
        ArduinoConnectedSensor.__init__(self, arduino, key)

        self.magnets = magnets
        self.window = window

        self.rpm = None
        self.readings = []

    def read(self):
        """Process the RPMs of the encoder"""
        # try adding a new reading from the sensor to the list of readings
        reading = self._read()
        if reading is not None and (len(self.readings) == 0 or reading.timestamp > self.readings[-1].timestamp):
            reading.data = int(reading.data)
            self.readings.append(reading)

        # get rid of stale readins that don't fit into the current window
        now = time.time()
        not_stale = 0
        while not_stale < len(self.readings) and self.readings[not_stale].timestamp < (now - self.window):
            not_stale += 1
        self.readings = self.readings[not_stale:]

        # count the number of pulses in the current window; pulse count is monotonically increasing
        if len(self.readings) < 2:
            pulses = 0
            time_period = self.window
        else:
            pulses = self.readings[-1].data - self.readings[0].data
            time_period = self.readings[-1].timestamp - now

        self.rpm = (pulses / self.magnets) * (60 / time_period)
        return self.rpm

    @property
    def status(self):
        return {'value':self.rpm, 'units':'RPM'}

class SensorReading(object):
    """Represents a reading from a sensor attached to the arduino"""
    def __init__(self,
            timestamp = time.time(),
            sensor_name = '',
            data = None):
        self.timestamp = timestamp
        self.sensor_name = sensor_name
        self.data = data

    def __repr__(self):
        return "SensorReading(timestamp=%f, sensor_name=%s, data=%s" % (
                self.timestamp,
                self.sensor_name,
                self.data)

