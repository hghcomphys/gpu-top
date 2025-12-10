import sys
from typing import Tuple

import pynvml

DeviceHandle = pynvml.struct_c_nvmlDevice_t


def get_devices() -> Tuple[DeviceHandle, ...]:
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        handles = tuple(pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(device_count))
        return handles
    except pynvml.NVMLError as error:
        print(f"GPU Not Detected! (Error: {error})")
        sys.exit(1)


def free_devices() -> None:
    pynvml.nvmlShutdown()
