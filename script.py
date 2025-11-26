import ctypes
import struct
import time

# Load the CANAL library (adjust path as needed)
# On Windows, it might be a DLL; on Linux, a .so
canal = ctypes.CDLL('Canal.dll')

# Define some constants from CANAL API
CANAL_ERROR = -1  # just as example
CANAL_SUCCESS = 0

def is_bit_set(b, bit):
    return (b & (1 << bit)) != 0

# Prepare function prototypes

# long CanalOpen(const char *pConfigStr, unsigned long flags);
canal.CanalOpen.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
canal.CanalOpen.restype = ctypes.c_long

# long CanalClose(long handle);
canal.CanalClose.argtypes = [ctypes.c_long]
canal.CanalClose.restype = ctypes.c_long

# long CanalWrite(long handle, const struct CanalMsg *pMsg);
# struct CanalMsg is user-defined; define it in Python
class CanalMsg(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint32),
        ("obid", ctypes.c_uint32),
        ("id", ctypes.c_uint32),
        ("sizeData", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * 8),  # CAN data up to 8 bytes
        ("timestamp", ctypes.c_uint32)
    ]

canal.CanalSend.argtypes = [ctypes.c_long, ctypes.POINTER(CanalMsg)]
canal.CanalSend.restype = ctypes.c_long

# long CanalRead(long handle, struct CanalMsg *pMsg);
canal.CanalReceive.argtypes = [ctypes.c_long, ctypes.POINTER(CanalMsg)]
canal.CanalReceive.restype = ctypes.c_long

# Example: open the TouCAN device
# According to CANAL User Guide, config string: "0 ; serial ; bitrate"
# E.g. “0 ; 12345678 ; 125” for 125 kbps
config = b"0;00005502;125"  # modify serial and bitrate to your device
flags = 0  # no special flags

handle = canal.CanalOpen(config, flags)
if handle <= 0:
    raise RuntimeError(f"Failed to open CAN channel, handle={handle}")

print("CAN channel opened, handle =", handle)

try:
    # Create a CAN message to send
    msg = CanalMsg()
    msg.id = 0x123
    msg.flags = 0  # standard frame
    msg.timestamp = 0
    msg.sizeData = 4
    # Put some data bytes
    msg.data[0] = 0x11
    msg.data[1] = 0x22
    msg.data[2] = 0x33
    msg.data[3] = 0x44

    # Send the message
    res = canal.CanalSend(handle, ctypes.byref(msg))
    if res != CANAL_SUCCESS:
        print("Error writing message:", res)
    else:
        print("Message sent")

    # Read loop
    print("Starting read loop, Ctrl+C to stop")
    while True:
        read_msg = CanalMsg()
        res = canal.CanalReceive(handle, ctypes.byref(read_msg))
        if res == CANAL_SUCCESS:
            # Print details
            data = bytes(read_msg.data[:read_msg.sizeData])

            print(f"Received frame:", end=" ")

            if is_bit_set(msg.flags, 1):
                print("EXTENDED:", end=" ")
            else:
                print("STANDARD:", end=" ")

            print(f"ID=0x{read_msg.id:03X}", end=" ")

            print(f"DLC={read_msg.sizeData}  DATA="
                + " ".join(f"{read_msg.data[i]:02X}" for i in range(read_msg.sizeData))
            )

        else:
            # No message or error, depending on implementation
            # Sleep a little to avoid busy loop
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping")

finally:
    # Close the channel
    canal.CanalClose(handle)
    print("CAN channel closed")
