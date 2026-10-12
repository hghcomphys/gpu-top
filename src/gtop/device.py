import sys
from typing import Tuple

import pynvml

DeviceHandle = pynvml.struct_c_nvmlDevice_t
pynvml_available = True


def get_devices() -> Tuple[DeviceHandle, ...]:
    global pynvml_available
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        handles = tuple(pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(device_count))
        return handles
    except pynvml.NVMLError as error:
        print(f"GPU Not Detected! (Error: {error})")
        pynvml_available = False
        sys.exit(1)


def free_devices() -> None:
    global pynvml_available
    if pynvml_available:
        pynvml.nvmlShutdown()
