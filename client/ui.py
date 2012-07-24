#!/usr/bin/python

import curses
import time

BASE_SPEED = 30
TURN_SPEED = 40

class CursesUI(object):
    """A curses UI or talking to a driver via client"""
    def __init__(self, client):
        """Initializes ncurses"""
        self.client = client

        #initialize ncurses
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)

        curses.curs_set(0)
        curses.halfdelay(1)

        #lets do everything else in a try so we can clean up
        try:
            #initialize the windows
            self.windows = {'stdscr':self.stdscr}

            left = curses.newwin(30, 40, 0, 0)
            left.box()
            self.add_title(left, " Left Motor Status ")
            self.windows['left'] = left

            right = curses.newwin(30, 40, 0, 41)
            right.box()
            self.add_title(right, " Right Motor Status ")
            self.windows['right'] = right

            result = curses.newwin(3, 81, 31, 0)
            result.box()
            self.add_title(result, " Last Result ")
            self.windows['result'] = result

        except:
            self.cleanup()
            raise

        self._last_key = -1

    def cleanup(self):
        """Clean up ncurses"""
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()

        curses.endwin()

    def write_line(self, window, linenum, line, align = 'left', left_margin = 1, right_margin = 1, nopad = False):
        """Writes a line in the specified window"""
        h, w = window.getmaxyx()
        if linenum > h:
            return

        #truncate the string to fit perfectly inside the window
        if not nopad:
            length = w - left_margin - right_margin
            align_fun = {
                    'left':line.ljust,
                    'right':line.rjust,
                    'center':line.center,
                    }
            line = align_fun[align](length)

        window.addstr(linenum, left_margin, line)

    def add_title(self, window, title):
        self.write_line(window, 0, title, left_margin = 3, nopad = True)

    def write_result(self, result):
        self.write_line(self.windows['result'], 1, str(result))

    def update_status(self):
        """puts the current status into the status windows"""
        status = self.client.status
        windows = {'right':self.windows['right'], 'left':self.windows['left']}
        for side, s in status.items():
            linenum = 1
            for key in s:
                if key == 'errors':
                    continue
                else:
                    line = "%s %s" % (key[:30].ljust(30), s[key])
                    self.write_line(windows[side], linenum, line)
                    linenum += 1

            for error, value in s['errors'].items():
                line = "error %s %s" % (error[:24].ljust(24), value)
                self.write_line(windows[side], linenum, line)
                linenum += 1

    def run(self):
        """The main loop"""
        while True:
            for window in self.windows.values():
                window.refresh()

            c = self.stdscr.getch()
            if c == self._last_key:
                continue

            if c == ord('q'):
                break
            elif c == ord('s'):
                self.update_status()
                self.write_result('Status updated')
            elif c == ord('r'):
                self.write_result(self.client.reset())
            elif c == ord('b'):
                self.write_result(self.client.brake(100))
            elif c == ord('x'):
                self.write_result(self.client.stop())

            #movement commands
            elif c == curses.KEY_UP:
                self.write_result('Moving at speed: %s' % BASE_SPEED)
                self.client.set_speed(BASE_SPEED)
            elif c == curses.KEY_LEFT:
                self.write_result('Turning left at speed: %s' % TURN_SPEED)
                self.client.left = -TURN_SPEED
                self.client.right = TURN_SPEED
            elif c == curses.KEY_RIGHT:
                self.write_result('Turning right at speed: %s' % TURN_SPEED)
                self.client.left = TURN_SPEED
                self.client.right = -TURN_SPEED
            elif c == curses.KEY_DOWN:
                self.write_result('Moving at speed: %s' % BASE_SPEED)
                self.client.set_speed(-BASE_SPEED)

            #no command recieved
            elif c == -1:
                self.write_result(self.client.brake(100))
            else:
                self.write_result('Unknown key: "%d"' % c)

            #save the last key we hit
            self._last_key = c
            if c != ord('s'):
                self.update_status()