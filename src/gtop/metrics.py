from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol, Tuple

import psutil
import pynvml

from gtop.config import Config
from gtop.device import DeviceHandle

MILLIWATTS_TO_WATTS = 0.001
KB_TO_MB = 1.0 / 1024
KB_TO_GB = (1.0 / 1024) ** 2
B_TO_MB = (1.0 / 1024) ** 2
B_TO_GB = (1.0 / 1024) ** 3


@dataclass(frozen=True)
class GpuMetrics:
    name: str
    device_index: int
    timestamp: float
    pci_tx: float
    pci_rx: float
    utilization: float
    memory_used: float
    memory_total: float
    temperature: float
    power_usage: float
    processes: Tuple[GpuProcess, ...]

    @classmethod
    def collect(
        cls,
        handles: Tuple[DeviceHandle, ...],
        start_time: float,
        cfg: Config,
    ) -> Tuple[GpuMetrics, ...]:
        all_device_metrics = []
        for index, handle in enumerate(handles):
            now = time.time() - start_time
            gpu_name = GpuInfoMetric(handle).collect()
            tx, rx = PciThroughputMetric(handle).collect()
            utilization = GpuUtilizationMetric(handle).collect()
            mem_used, mem_total = GpuMemoryMetric(handle).collect()
            temperature = GpuTemperatureMetric(handle).collect()
            power_usage = GpuPowerUsageMetric(handle).collect()
            processes = GpuComputeRunningProcesses(handle).collect()

            all_device_metrics.append(
                GpuMetrics(
                    name=gpu_name,
                    device_index=index,
                    timestamp=max(now, cfg.min_time_interval),
                    pci_tx=tx,
                    pci_rx=rx,
                    utilization=utilization,
                    memory_used=mem_used,
                    memory_total=mem_total,
                    temperature=temperature,
                    power_usage=power_usage,
                    processes=processes,
                )
            )
        return tuple(all_device_metrics)

    @property
    def memory_used_percent(self) -> float:
        return self.memory_used / self.memory_total * 100

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            "("
            f"Device={self.device_index}"
            f", Time={self.timestamp:0.2f} [s]"
            f", UTL={self.utilization:0.2f} [%]"
            f", MEM={self.memory_used:0.2f} [%]"
            f", PCI-RX={self.pci_rx:0.2f} [MB/s]"
            f", PCI-TX={self.pci_tx:0.2f} [MB/s]"
            ")"
        )


class MetricInterface(Protocol):
    def collect(self) -> Any: ...


@dataclass(frozen=True)
class GpuProcess:
    pid: str
    device: int
    user: str
    memory: float
    cpu_usage: float
    host_memory: float
    command: str


@dataclass
class GpuComputeRunningProcesses(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> Tuple[GpuProcess, ...]:
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
        gpu_processes = []
        for p in processes:
            try:
                ps = psutil.Process(p.pid)
                gpu_processes.append(
                    GpuProcess(
                        pid=p.pid,
                        device=int(pynvml.nvmlDeviceGetIndex(self.handle)),
                        user=ps.username(),
                        memory=p.usedGpuMemory * B_TO_MB,
                        command=" ".join(ps.cmdline()),
                        cpu_usage=ps.cpu_percent(interval=0.1),
                        host_memory=ps.memory_info().rss * B_TO_MB,
                    )
                )
            except psutil.NoSuchProcess:
                continue
        return tuple(gpu_processes)




@dataclass
class GpuInfoMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> str:
        return pynvml.nvmlDeviceGetName(self.handle)


@dataclass
class GpuTemperatureMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> float:
        return pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)


@dataclass
class GpuPowerUsageMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> float:
        try:
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
            return power_mw * MILLIWATTS_TO_WATTS
        except pynvml.NVMLError:
            return -1.0


@dataclass
class PciThroughputMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> Tuple[float, float]:
        tx = (
            pynvml.nvmlDeviceGetPcieThroughput(
                self.handle,
                pynvml.NVML_PCIE_UTIL_TX_BYTES,
            )
            * KB_TO_MB
        )
        rx = (
            pynvml.nvmlDeviceGetPcieThroughput(
                self.handle,
                pynvml.NVML_PCIE_UTIL_RX_BYTES,
            )
            * KB_TO_MB
        )
        return tx, rx


@dataclass
class GpuUtilizationMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> float:
        util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
        return float(util.gpu)


@dataclass
class GpuMemoryMetric(MetricInterface):
    handle: DeviceHandle

    def collect(self) -> Tuple[float, float]:
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        mem_used = float(mem_info.used) * KB_TO_GB
        mem_total = float(mem_info.total) * KB_TO_GB
        return mem_used, mem_total
