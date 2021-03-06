# Written by Jan "Duchy" Neduchal 2018
import serial
import platform
import sys
import time
import hashlib #sha256
from config import * #passwords
from tkinter import Tk #clipboard
import getpass # password prompt

from Crypto.Random import random
from Crypto.Cipher import AES
import base64

BLOCK_SIZE=32

def copy_to_clipboard(string):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(string)
    r.update() # stays in clipboard
    r.destroy()

def decrypt(encrypted, passphrase):
    IV = Random.new().read(BLOCK_SIZE)
    aes = AES.new(passphrase, AES.MODE_CFB, IV)
    return aes.decrypt(base64.b64decode(encrypted))

def xor(a,b):
    xored = []
    for i in range(max(len(a), len(b))):
        xored_value = ord(a[i%len(a)]) ^ ord(b[i%len(b)])
        xored.append(hex(xored_value)[2:])
    return ''.join(xored)

def hash_SHA256(pw):
    hash_object = hashlib.sha256(str.encode(pw))
    hex_dig = hash_object.hexdigest()
    return hex_dig

def OScheck():
    name = platform.platform()
    if name.startswith("Windows"):
        return "windows"
    if name.startswith("Darwin"):
        return "osx"
    if name.startswith("Linux"):
        return "linux"

def main():
    ard = serial.Serial()
    ard.baudrate = 115200
    if OScheck() == "windows":
        ard.port = "COM3"
    elif OScheck() == "linux":
        ard.port = "/dev/ttyUSB0"
    elif OScheck() == "osx":
        ard.port = "/dev/cu.usbmodem1411"
    print("Starting on port "+ard.port)
    ard.timeout = 10
    while ard.is_open == False:
        try:
            ard.open()
        except:
            print("Invalid port, enter it manually.")
            ard.port = input("> ")
    print("CONNECTED")
    print("Enter your password")
    password = getpass.getpass("> ")
    print("Authenticating please stand-by..")
    password = hash_SHA256(password)
    ard.write(password)
    time.sleep(0.2)
    for i in range(3):
        try:
            response = ard.readline().decode('ASCII')
            break
        except TypeError:
            print("Getting ACK timed out")
            print("Try number "+ i)
    if response == "ACK-OK":
        print("Got ACK-OK.. Authenticated!")
    else:
        print("Wrong password!")
        ard.close()
        sys.exit(-1)
    while True:
        print("Listening for RFID tag UID to decrypt the passwords")
        response = ard.readline().decode('ASCII')
        if response == "TERM":
            print("Connection was terminated!")
            print("Restart the Arduino to continue...")
            ard.close()
            sys.exit(0)
        elif len(response) == 8: # 4 bytes only
            print("Detected UID")
            SECRET = xor(hash_SHA256(response), password)
            if len(pass_dict) != 0:
                print("Which password do you want to decrypt?")
                print(pass_dict.keys())
                print("(type q to scan another UID)")
                to_decrypt = input("> ")
                if to_decrypt == "q":
                    continue
            else:
                print("Password list has no entries")
                print("Quitting..")
                ard.close()
                sys.exit(-1)
            plaintext = decrypt(pass_dict[to_decrypt], SECRET)
            copy_to_clipboard(plaintext)
        else:
            print("Failed to load an UID")
            continue
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
