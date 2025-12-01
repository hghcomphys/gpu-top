from __future__ import annotations
import json
import os
from argparse import Namespace
from dataclasses import dataclass, asdict
from typing import Optional
import sys


GTOPRC = os.path.expanduser("~/.gtoprc")


@dataclass
class Config:
    device_gpu_index: int = 0
    update_time_interval: float = 1.0
    text_mode: bool = False
    generate_config: bool = False
    collector_buffer_size: int = 30
    collector_min_time_interval: float = 0.1
    visualizer_plot_size: Optional[tuple[int, int]] = None
    visualizer_plot_theme: Optional[str] = "pro"
    visualizer_plot_marker: Optional[str] = None
    visualizer_plot_bar: bool = False

    @classmethod
    def load(cls, path: str) -> Config:
        with open(path, "r") as f:
            data = json.load(f)
        print(f"Loading config from '{path}'.")
        return cls(**data)

    @classmethod
    def dump(cls, path: str) -> None:
        default_cfg = cls()
        with open(path, "w") as f:
            json.dump(asdict(default_cfg), f, indent=4)
        print(f"Generating default config into '{path}'.")

    @classmethod
    def from_parser(
        cls,
        args: Namespace,
        cfg: Optional[Config] = None,
    ) -> Config:
        if args.generate_config:
            Config.dump(GTOPRC)
            sys.exit()

        if cfg is None:
            cfg = get_config()
        return cls(
            **{
                **cfg.__dict__,
                **{k: v for k, v in vars(args).items() if v is not None},
            }
        )

    @property
    def visualizer_plot_time_interval(self) -> float:
        return self.update_time_interval * self.collector_buffer_size


def get_config():
    if os.path.exists(GTOPRC):
        return Config.load(GTOPRC)
    else:
        return Config()
