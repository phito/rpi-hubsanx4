from hubsan import Hubsan
import RPi.GPIO as GPIO
import a7105
import curses, curses.panel
import time
import sys

class StdOutWrapper:
    text = ""
    def write(self,txt):
        self.text += txt
        self.text = '\n'.join(self.text.split('\n')[-30:])
    def get_text(self,beg,end):
        return '\n'.join(self.text.split('\n')[beg:end])

precision = 0.02
quad = None
selection = 0
std_wrapper = StdOutWrapper()

def display(stdscr):
    global std_wrapper
    stdscr.clear()
    stdscr.addstr(0, 0, 'Throttle:')
    stdscr.addstr(0, 11, '< {0:.2f} >'.format(quad.throttle), curses.A_REVERSE if selection == 0 else 0)
    stdscr.addstr(1, 0, 'Yaw:')
    stdscr.addstr(1, 11, '< {0:.2f} >'.format(quad.yaw), curses.A_REVERSE if selection == 1 else 0)
    stdscr.addstr(2, 0, 'Pitch:')
    stdscr.addstr(2, 11, '< {0:.2f} >'.format(quad.pitch), curses.A_REVERSE if selection == 2 else 0)
    stdscr.addstr(3, 0, 'Roll:')
    stdscr.addstr(3, 11, '< {0:.2f} >'.format(quad.roll), curses.A_REVERSE if selection == 3 else 0)
    stdscr.addstr(4, 0, 'Leds:')
    stdscr.addstr(4, 11, '< {0} >'.format(quad.leds), curses.A_REVERSE if selection == 4 else 0)
    stdscr.addstr(5, 0, 'Flips:')
    stdscr.addstr(5, 11, '< {0} >'.format(quad.flips), curses.A_REVERSE if selection == 5 else 0)

    stdscr.refresh()

def main(stdscr):
    global selection
    curses.curs_set(0)
    stdscr.nodelay(True)
    while True:
        display(stdscr)
        event = stdscr.getch()

        if event == curses.KEY_DOWN:
            if selection < 5: selection += 1
        elif event == curses.KEY_UP:
            if selection > 0: selection -= 1
        elif event == curses.KEY_LEFT:
            if selection == 0: quad.throttle -= precision
            if selection == 1: quad.yaw -= precision
            if selection == 2: quad.pitch -= precision
            if selection == 3: quad.roll -= precision
            if selection == 4: quad.leds = not quad.leds
            if selection == 5: quad.flips = not quad.flips
        elif event == curses.KEY_RIGHT:
            if selection == 0: quad.throttle += precision
            if selection == 1: quad.yaw += precision
            if selection == 2: quad.pitch += precision
            if selection == 3: quad.roll += precision
            if selection == 4: quad.leds = not quad.leds
            if selection == 5: quad.flips = not quad.flips
        elif event == ord('q'):
            break
        elif event == ord('s'):
            # emergency stop
            quad.throttle = 0.0
            quad.yaw = 0.5
            quad.pitch = 0.5
            quad.roll = 0.5
            quad.leds = True
            quad.flips = False


if __name__ == "__main__":
    a7105.init()
    quad = Hubsan()
    quad.bind()
    curses.wrapper(main)
    quad.stop()
