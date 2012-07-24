#!/usr/bin/python

import common

class SabertoothDriver(object):
    """A driver which controls motors via the Sabertooth 2x60 Motor Controller"""
    def __init__(self, arduino):
        self.arduino = arduino
        self.last

    def _convert_speed(self, speed):
        """We want to specify speeds from 0 to 100, but the sabertooth uses 0 to 63"""
        if speed > 100 or speed < -100:
            raise common.DriverError("Speed outside the allowed range")

        return speed * 63 / 100

    ###### the interface of the driver #####
    def reset(self):
        """Resets the controllers into a basic run state"""
        self.arduino.send_command('R')

    def stop(self):
        """Stops the robot"""
        self.arduino.send_command('X')

    def brake(self, speed):
        """Applies braking to the motors"""
        self.speed = 0

    def set_speed(self, speed, motor = 'both'):
        """sets the speed of one or both motors"""
        #easily handle setting both or a single motor
        controllers = self.controllers.values() if motor == 'both' else [self.controllers[motor]]
        for c in controllers:
            c.speed = self._convert_speed(speed)

    def get_speed(self, motor = 'both'):
        """Returns the current speed of a motor"""
        speeds = []
        controllers = self.controllers.values() if motor == 'both' else [self.controllers[motor]]
        for c in controllers:
            speed = self._convert_speed(c.speed)
            speeds.append(speed)

        return speeds

    speed = property(
            lambda self: self.get_speed('both'),
            lambda self, speed: self.set_speed(speed, 'both'))

    left = property(
            lambda self: self.get_speed('left')[0],
            lambda self, speed: self.set_speed(speed, 'left'))
    right = property(
            lambda self: self.get_speed('right')[0],
            lambda self, speed: self.set_speed(speed, 'right'))

    @property
    def status(self):
        status = {}
        for side, c in self.controllers.items():
            status[side] = c.status

        return status

def get_driver(arduino, **rest):
    if not arduino:
        raise common.DriverError("The sabertooth driver requires a connection to an onboard Arduino to function")

    return SabertoothDriver(arduino)
