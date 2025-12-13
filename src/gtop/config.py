from __future__ import annotations
import json
import os
from argparse import Namespace
from dataclasses import dataclass, asdict
from typing import Optional
import sys


GTOPRC = os.path.expanduser("~/.gputoprc")


@dataclass
class Config:
    buffer_size: int = 30
    text_mode: bool = False
    device_index: int = 0
    update_time_interval: float = 1.0
    min_time_interval: float = 0.1
    generate_config: bool = False
    dashboard_theme: Optional[str] = "pro"
    dashboard_plot_marker: Optional[str] = None
    dashboard_plot_bar: bool = False

    @classmethod
    def load(cls, path: str) -> Config:
        with open(path, "r") as f:
            data = json.load(f)
        print(f"Loading configuration from '{path}'.")
        return cls(**data)

    @classmethod
    def dump(cls, path: str) -> None:
        default_cfg = cls()
        with open(path, "w") as f:
            json.dump(asdict(default_cfg), f, indent=4)
        print(f"Generating default configuration '{path}'.")

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
    def plot_time_interval(self) -> float:
        return self.update_time_interval * self.buffer_size


def get_config():
    if os.path.exists(GTOPRC):
        return Config.load(GTOPRC)
    else:
        return Config()
