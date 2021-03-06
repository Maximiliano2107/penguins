#!/usr/bin/env python
"""Linux joystick I/O support.

Reads and decodes raw events from a joystick using the joystick API [1], and
stores them in a more usable format.

[1] http://www.kernel.org/doc/Documentation/input/joystick-api.txt
"""

import commands
import select
import struct
import threading

__author__ = 'Jered Wierzbicki'

class JoystickError(Exception):
    """Used to signify a joystick problem"""
    pass

class RawEvent(object):
    """An event reported by the joystick driver."""

    # Number of bytes per event.
    BYTES = 8

    # Event types:
    BUTTON = 1  # Button press.
    AXIS = 2  # Movement on some axis (a delta).
    INIT = 128  # Synthetic mask for first

    def __init__(self, time=0, value=0, event_type=0, number=0):
        self.time = time
        self.value = value
        self.event_type = event_type
        self.number = number

    @staticmethod
    def Unpack(data):
        """Unpacks data from the joystick.

        Args:
            data: A string with raw joystick input.

        Returns:
            A RawEvent with decoded data.
        """
        time, value, event_type, number = struct.unpack('=LhBB', data)
        return RawEvent(time=time, value=value, event_type=event_type,
                        number=number)

    def __repr__(self):
        return 'RawEvent(time=%d, value=%d, event_type=%d, number=%d)' % (
                self.time, self.value, self.event_type, self.number)


def Normalize(v, calibration):
    """Normalizes v to a value between -1 and 1."""
    v_min, v_zero, v_max = calibration
    # Maybe use a quadratic bezier curve here or something instead.
    if v < v_zero:
        # -1.0 at v_min approaching 0 at v_zero.
        return max(-1.0, -float(abs(v - v_zero)) / float(abs(v_min - v_zero)))
    else:
        # 0 at v_zero and 1.0 at v_max.
        return min(1.0, float(abs(v - v_zero)) / float(abs(v_max - v_zero)))


class Profile(object):
    """Describes how to interpret joystick events for a particular joystick."""

    def __init__(self,
                 steering_axis=-1, left=0, center=0, right=0,
                 drive_axis=-1, forward=0, still=0, reverse=0,
                 stop_button=-1, horn_button=-1, go_button=-1):
        """Creates a joystick profile.

        Args:
            steering_axis: The axis which controls direction.
            left: Steering value for all the way to the left.
            center: Steering value for straight ahead.
            right: Steering value for all the way to the right.
            drive_axis: The axis which controls speed.
            forward: Drive value for full ahead.
            still: Drive value for stand still.
            reverse: Drive value for full reverse.
            stop_button: The button that means stop.
            horn_button: The button that means honk.
            go_button: The button that starts the penguin.
        """
        self.steering_axis = steering_axis
        self.steering = (left, center, right)
        self.drive_axis = drive_axis
        self.drive = (forward, still, reverse)
        self.stop_button = stop_button
        self.horn_button = horn_button
        self.go_button = go_button

    def interpret(self, event):
        """Interprets a raw event as a comand."""
        # Ignore init events.
        if event.event_type == RawEvent.BUTTON:
            if event.number == self.stop_button and event.value:
                return commands.Stop()
            elif event.number == self.horn_button and event.value:
                return commands.Horn()
            elif event.number == self.go_button and not event.value:
                return commands.Go()
        elif event.event_type == RawEvent.AXIS:
            if event.number == self.steering_axis:
                return commands.Steer(Normalize(event.value, self.steering))
            elif event.number == self.drive_axis:
                return commands.Drive(Normalize(event.value, self.drive))


class NESController(Profile):
    """An USB NES controller."""

    def __init__(self):
        Profile.__init__(self,
            steering_axis=3, left=-32767, center=0, right=32767,
            drive_axis=4, forward=32767, still=0, reverse=-32767,
            stop_button=2, horn_button=1, go_button=9)


class Listener(threading.Thread):
    """Listens for and queues joystick events."""

    def __init__(self, device_path):
        threading.Thread.__init__(self, name='joystick-listener')
        self.setDaemon(True)
        self.device = open(device_path, 'rb', 0)
        self.events_lock = threading.Lock()
        self.last_event = None
        self._stop = threading.Event()

    def stop(self):
        """Signals that the listener thread should stop."""
        self._stop.set()

    def run(self):
        """Listens for and queues joystick events."""
        while not self._stop.isSet():
            rlist, _, _ = select.select([self.device], [], [], 0.05)
            if not rlist:
                # Spin to check for stop signal.
                continue

            data = self.device.read(RawEvent.BYTES)
            event = RawEvent.Unpack(data)
            self.events_lock.acquire()
            self.last_event = event
            self.events_lock.release()
        self.device.close()

    def get_event(self):
        """Pops and returns the oldest queued event."""
        self.events_lock.acquire()
        try:
            event = self.last_event
            self.last_event = None
            return event
        finally:
            self.events_lock.release()


class Joystick(object):
    """Wraps a joystick device."""

    def __init__(self, device_path, profile):
        """Initializes the joystick driver.

        Args:
            device_path: Path to the device file for the joystick.
            profile: The profile to use to interpret raw events.

        Raises:
            IOError: If the device could not be opened.
        """
        self.listener = Listener(device_path)
        self.listener.start()
        self.profile = profile

    def get_event(self):
        """Returns True iff the joystick has pending events."""
        if not self.listener.is_alive():
            raise JoystickError("listener has terminated")

        event = self.listener.get_event()
        if event:
            return self.profile.interpret(event)

    def close(self):
        """Close the joystick device."""
        self.listener.stop()
        self.listener.join(timeout=2)


if __name__ == '__main__':
    js = Joystick('/dev/input/js0', NESController())
    try:
        while True:
            ev = js.get_event()
            if ev:
                print ev
    finally:
        js.close()
