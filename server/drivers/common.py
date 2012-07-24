#!/usr/bin/python

class DriverError(Exception):
   """Used when the driver encounters an error executing the command"""
   pass

class ControllerError(DriverError):
    """Used to indicate an error inside a controller"""
    pass

SMCControllerErrors = {
        0:'safe start violation',
        1:'channel invalid',
        2:'serial error',
        3:'command timeout',
        4:'limit/kill switch',
        5:'low vin',
        6:'high vin',
        7:'over temperature',
        8:'motor driver error',
        9:'err line high',
        }


class SmcDriver(object):
    """A common driver which drives around using two SMC controllers"""
    def __init__(self, left, right):
        self.controllers = {
                'left':left,
                'right':right,
                }

    def _convert_brake(self, brake):
        """We want a breaking value from 1 to 100, but the pololu uses 1 to 32"""
        if brake < 1 or brake > 100:
            raise DriverError("Braking speed outside the normal range")

        return 1 if brake < 3 else int((brake - 3)/3)

    def _convert_speed(self, speed):
        """We want to specify speeds from 0 to 100, but the pololu uses 0 to 3200"""
        if speed > 100 or speed < -100:
            raise DriverError("Speed outside the normal range")

        return speed * 32

    ###### the interface of the driver #####
    def reset(self):
        """Resets the controllers into a basic run state"""
        for c in self.controllers.values():
            c.reset()

    def stop(self):
        """Stops the robot"""
        for c in self.controllers.values():
            c.stop()

    def brake(self, speed):
        """Applies braking to the motors"""
        for c in self.controllers.values():
            c.brake(self._convert_brake(speed))

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