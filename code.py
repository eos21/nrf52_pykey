import time
from board import *
import digitalio
import usb_hid

import adafruit_ble
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode as _

ROWS = (P1_10, P0_28, P0_02, P0_29, P0_31, P0_30)
COLS = (P1_06, P0_09, P0_24, P0_22, P0_13, P0_20, P0_17, P0_15, P0_12, P1_09, P0_08, P0_05, P0_06, P1_13, P0_10, P1_11, P1_04, P0_03)

KEYMAP = (
    _.ESCAPE,       None,   _.F1,    _.F2,    _.F3,     _.F4,   None,    _.F5,    _.F6,     _.F7,   _.F8,  _.F9,    _.F10,     _.F11,     _.F12,          _.PRINT_SCREEN, _.SCROLL_LOCK, _.PAUSE,
    _.GRAVE_ACCENT, _.ONE,  _.TWO,   _.THREE, _.FOUR,   _.FIVE, _.SIX,   _.SEVEN, _.EIGHT, _.NINE, _.ZERO,  _.MINUS,    _.EQUALS, None,  _.BACKSPACE,     _.INSERT,  _.HOME, _.PAGE_UP,
    _.TAB,         None,  _.Q,    _.W,    _.E,    _.R,    _.T,    _.Y,    _.U,    _.I,    _.O,    _.P,   _.LEFT_BRACKET,_.RIGHT_BRACKET, _.BACKSLASH,     _.DELETE,  _.END,  _.PAGE_DOWN,
    _.CAPS_LOCK,   None,  _.A,    _.S,    _.D,    _.F,    _.G,    _.H,    _.J,    _.K,    _.L,    _.SEMICOLON,  _.QUOTE,    _.ENTER,None,                  None,     None,      None,   
    None,     _.LEFT_SHIFT, _.Z,    _.X,    _.C,    _.V,    _.B,    _.N,    _.M,   _.COMMA, _.PERIOD,   _.FORWARD_SLASH,    None, _.RIGHT_SHIFT, None,      None,     _.UP_ARROW,    None, 
    _.LEFT_CONTROL, _.LEFT_GUI, _.LEFT_ALT, None, None, None,  _.SPACE,  None, None, None,  _.RIGHT_ALT,  _.RIGHT_GUI,    _.COMMAND, _.RIGHT_CONTROL,None,   _.LEFT_ARROW, _.DOWN_ARROW, _.RIGHT_ARROW)


class Matrix:
    def __init__(self, rows=ROWS, cols=COLS):
        
        self.rows = []
        for pin in rows:
            io = digitalio.DigitalInOut(pin)
            io.direction = digitalio.Direction.INPUT
            io.pull = digitalio.Pull.DOWN 
            self.rows.append(io)
            
        self.cols = []        
        for pin in cols:
            io = digitalio.DigitalInOut(pin)
            io.direction = digitalio.Direction.OUTPUT
            io.drive_mode = digitalio.DriveMode.PUSH_PULL
            io.value = 0         
            self.cols.append(io)
            
        self.pressed_keys = []

    def scan(self):
        new_keys = []
        pressed_keys = []
        released_keys = self.pressed_keys
        #for r in range(len(self.rows)):
        for c in range(len(self.cols)):
            #self.rows[r].value = 1
            self.cols[c].value = 1
            #for c in range(len(self.cols)):
            for r in range(len(self.rows)):
                #if self.cols[c].value:
                if self.rows[r].value:
                    key = r * len(self.cols) + c
                    #key = c * len(self.rows) + r
                    pressed_keys.append(key)
                    if key in released_keys:
                        released_keys.remove(key)
                    else:
                        new_keys.append(key)
            #self.rows[r].value = 0
            self.cols[c].value = 0
        self.pressed_keys = pressed_keys
        return pressed_keys, released_keys, new_keys

def main():
    hid = HIDService()
    advertisement = ProvideServicesAdvertisement(hid)
    advertisement.appearance = 961
    ble = adafruit_ble.BLERadio()
    if ble.connected:
        for c in ble.connections:
            c.disconnect()
    ble.start_advertising(advertisement)
    advertising = True
    ble_keyboard = Keyboard(hid.devices)

    matrix = Matrix()
    usb_keyboard = Keyboard(usb_hid.devices)

    while True:
        pressed_keys, released_keys, new_keys = matrix.scan()
        if released_keys:
            released_keycodes = list(map(lambda i: KEYMAP[i], released_keys))
            print('released keys {}'.format(released_keycodes))

            usb_keyboard.release(*released_keycodes)
            if ble.connected:
                advertising = False
                ble_keyboard.release(*released_keycodes)
        if new_keys:
            new_keycodes = list(map(lambda i: KEYMAP[i], new_keys))
            print('new keys {}'.format(new_keycodes))
            usb_keyboard.press(*new_keycodes)
            if ble.connected:
                advertising = False
                ble_keyboard.press(*new_keycodes)

        if not ble.connected and not advertising:
            ble.start_advertising(advertisement)
            advertising = True

        time.sleep(0.001)

main()
