from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Tuple

import plotext

from gtop.buffer import Buffer
from gtop.config import Config
from gtop.metrics import GpuMetrics

PlotHandle = Any


@dataclass
class Dashboard:
    plt: PlotHandle = plotext

    def show(
        self,
        inputs: Buffer,
        cfg: Config,
    ) -> None:
        if len(inputs) < 2:
            return

        if cfg.text_mode:
            self.show_textmode(inputs)
            return

        plt = self.plt
        plt.clt()
        # plt.cld()
        plt.theme(cfg.dashboard_theme)
        terminal_size = os.get_terminal_size()
        num_processes = len(inputs.last[cfg.device_index].processes)

        plt.subplots(1, 2)
        self._show_device_info(inputs.last, plt, cfg)
        plt.plotsize(
            min(100, terminal_size[0]),
            min(15, terminal_size[1] // 3 * 2),
        )
        plt.subplot(1, 1)
        if cfg.dashboard_plot_bar:
            self._bar_plot_utilization(inputs.last, plt, cfg)
        else:
            self._plot_utilization(inputs, plt, cfg)
        plt.subplot(1, 2)
        if cfg.dashboard_plot_bar:
            self._bar_plot_pci_throughput(inputs.last, plt, cfg)
        else:
            self._plot_pci_throughput(inputs, plt, cfg)
        plt.show()
        # ---
        plt.subplots(1, 1)
        plt.plotsize(
            min(100, terminal_size[0]),
            max(5, min(5 * num_processes, terminal_size[1] // 3 - 2)),
        )
        plt.subplot(1, 1)
        self._show_processes(inputs.last, plt, cfg)
        plt.show()

    @classmethod
    def _plot_utilization(
        cls,
        inputs: Buffer,
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        timestamps = cls.get_shifted_timestamps(
            [input[cfg.device_index].timestamp for input in inputs],
            cfg,
        )
        utilization_values = [input[cfg.device_index].utilization for input in inputs]
        memory_values = [
            input[cfg.device_index].memory_used_percent for input in inputs
        ]
        plt.plot(
            timestamps,
            utilization_values,
            label="UTL",
            marker=cfg.dashboard_plot_marker,
        )
        plt.plot(
            timestamps,
            memory_values,
            label="MEM",
            marker=cfg.dashboard_plot_marker,
        )
        plt.xlabel("Time (s)")
        plt.ylabel("Utilization (%)")
        plt.ylim(0, 100)
        plt.xlim(-cfg.dashboard_plot_time_interval, 0)

    @classmethod
    def _plot_pci_throughput(
        cls,
        inputs: Buffer,
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        timestamps = cls.get_shifted_timestamps(
            [input[cfg.device_index].timestamp for input in inputs], cfg
        )
        pci_rx_values = [input[cfg.device_index].pci_rx for input in inputs]
        pci_tx_values = [input[cfg.device_index].pci_tx for input in inputs]
        plt.plot(
            timestamps,
            pci_rx_values,
            label="RX",
            marker=cfg.dashboard_plot_marker,
        )
        plt.plot(
            timestamps,
            pci_tx_values,
            label="TX",
            marker=cfg.dashboard_plot_marker,
        )
        plt.xlabel("Time (s)")
        plt.ylabel("PCI Throughput (MB/s)")
        plt.ylim(0, max(1, max(pci_tx_values + pci_rx_values) * 1.2))
        plt.xlim(-cfg.dashboard_plot_time_interval, 0)

    @classmethod
    def _bar_plot_utilization(
        cls,
        all_device_metrics: Tuple[GpuMetrics, ...],
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        metrics = all_device_metrics[cfg.device_index]
        names = [
            "MEM",
            "UTL",
        ]
        values = [
            metrics.memory_used_percent,
            metrics.utilization,
        ]
        plt.bar(
            names,
            values,
            orientation="h",
            width=2 / 5,
            marker=cfg.dashboard_plot_marker,
        )
        plt.ylabel("GPU Utilization (%)")
        plt.xlim(0, 100)

    @classmethod
    def _bar_plot_pci_throughput(
        cls,
        all_device_metrics: Tuple[GpuMetrics, ...],
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        metrics = all_device_metrics[cfg.device_index]
        names = [
            "TX",
            "RX",
        ]
        values = [
            metrics.pci_tx,
            metrics.pci_rx,
        ]
        plt.bar(
            names,
            values,
            orientation="h",
            width=2 / 5,
            marker=cfg.dashboard_plot_marker,
        )
        plt.ylabel("PCI Throughput (MB/s)")
        plt.xlim(0, max(1, max(metrics.pci_tx, metrics.pci_rx) * 1.2))

    @classmethod
    def _show_device_info(
        cls,
        all_device_metrics: Tuple[GpuMetrics, ...],
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        metrics = all_device_metrics[cfg.device_index]
        device_info = (
            (
                f"[{cfg.device_index}] {metrics.name}"
                f" | VRAM: {metrics.memory_total:0.0f} MB"
            )
            + (
                f" | PWR: {metrics.power_usage:0.1f} Watts"
                if metrics.power_usage > 0
                else ""
            )
            + (f" | TEMP: {metrics.temperature:0.1f} °C")
            # + (f" | UTL: {metrics.utilization:0.2f} [%]")
            # + (f" | MEM: {metrics.memory_used:0.2f} [%]")
        )
        # plt.title(device_info)
        print(device_info)

    @classmethod
    def _show_processes(
        cls,
        all_device_metrics: Tuple[GpuMetrics, ...],
        plt: PlotHandle,
        cfg: Config,
    ) -> None:
        metrics = all_device_metrics[cfg.device_index]
        processes_str = (
            f"{'PID':8}"
            f" {'DEV':5}"
            f" {'USER':10}"
            f" {'MEM[MB]':10}"
            f" {'CPU[%]':8}"
            f" {'H-MEM[MB]':10}"
            f" {'CMD':20}"
            "\n"
        )
        for p in metrics.processes:
            processes_str += (
                f"{p.pid:<8}"
                f" {p.device:<5}"
                f" {p.user:<10}"
                f" {p.memory:<10.0f}"
                f" {p.cpu_usage:<8.0f}"
                f" {p.host_memory:<10.0f}"
                f" {p.command[:20]:<20}"
                "\n"
            )
        plt.text(processes_str, 0, 1, color="orange")
        plt.xticks([])
        plt.yticks([])
        plt.ylim(0, 1)
        plt.yaxes(False, False)

    @classmethod
    def get_shifted_timestamps(
        cls,
        timestamps: list[float],
        cfg: Config,
    ) -> list[float]:
        timestamps = [
            time - timestamps[0] - cfg.dashboard_plot_time_interval for time in timestamps
        ]
        if len(timestamps) < cfg.get_buffer_size():
            timestamps = [time - timestamps[-1] for time in timestamps]
        return timestamps

    @classmethod
    def show_textmode(
        cls,
        inputs: Buffer,
    ) -> None:
        print(inputs.last)
