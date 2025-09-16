#!/usr/bin/env python3
import datetime
import asyncio
import struct
import sys
import time

import bleak
import pynput.keyboard

LEGO_CHARACTERISTIC_UUID ="00001624-1212-efde-1623-785feabcd123"
SUBSCRIBE_IMU_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])
SUBSCRIBE_RGB_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x01, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])

class DataHandler:
    def __init__(self):
        self.prev_y = None
        self.keyboard = pynput.keyboard.Controller()

    def xyz(self, x, y, z):
        if y > 100 and self.prev_y is not None and self.prev_y < 100:
            self.keyboard.press(pynput.keyboard.Key.space)
            time.sleep(0.3)
            self.keyboard.release(pynput.keyboard.Key.space)
        self.prev_y = y
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}]\tx: {x}\ty: {y}\tz: {z}")


def make_handler(user_handler):
    def raw_handler(sender, data):
        if data[0] == 7:  # IMU data packet
            x, y, z = struct.unpack("bbb", data[4:7])
            user_handler(x, y, z)
    return raw_handler


async def discover():
    devices = await bleak.BleakScanner.discover()
    for d in devices:
        if d.name and "Mario" in d.name:
            return d
    return None


async def read_data(address, handler):
    async with bleak.BleakClient(address) as client:

        notification_handler = make_handler(handler)
        await client.start_notify(LEGO_CHARACTERISTIC_UUID, notification_handler)
        # subscribe to IMU + RGB
        await asyncio.sleep(0.1)

        await asyncio.sleep(0.1)
        await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_IMU_COMMAND)
        await asyncio.sleep(0.1)
        await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_RGB_COMMAND)

        try:
            while True:
                await asyncio.sleep(1)  # keep loop alive
        except asyncio.CancelledError:
            print("Disconnecting ...")


async def main():
    dev = await discover()
    if dev is None:
        print("No device found")
        sys.exit(1)
    print(f"Found: {dev.address} ({dev.name})")

    dh = DataHandler()
    try:
        await read_data(dev.address, dh.xyz)
    except KeyboardInterrupt:
        print("Shutting down ...")


if __name__ == "__main__":
    asyncio.run(main())