from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from argparse import Namespace


@dataclass
class Config:
    device_gpu_index: int = 0
    update_time_interval: float = 1.0
    text_mode: bool = False
    collector_buffer_size: int = 30
    collector_min_time_interval: float = 0.1
    visualizer_plot_size: Optional[tuple[int, int]] = None
    visualizer_plot_theme: Optional[str] = "pro"
    visualizer_plot_marker: Optional[str] = None
    visualizer_plot_bar: bool = False

    @classmethod
    def from_parser(
        cls,
        args: Namespace,
        cfg: Optional[Config] = None,
    ) -> Config:
        if cfg is None:
            cfg = get_default_config()
        return cls(
            **{
                **cfg.__dict__,
                **{k: v for k, v in vars(args).items() if v is not None},
            }
        )

    @property
    def visualizer_plot_time_interval(self) -> float:
        return self.update_time_interval * self.collector_buffer_size


def get_default_config():
    return Config()
