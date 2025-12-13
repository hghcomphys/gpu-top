import argparse
import threading
import time

from gtop.buffer import Buffer
from gtop.config import Config
from gtop.device import free_devices, get_devices
from gtop.metrics import GpuMetrics
from gtop.dashboard import Dashboard


def app(
    cfg: Config,
    stop_event: threading.Event,
) -> None:
    buffer = Buffer(max_size=cfg.buffer_size)
    visualizer = Dashboard()
    handles = get_devices()
    start_time = time.time()
    while not stop_event.is_set():
        all_device_metrics = GpuMetrics.collect(handles, start_time, cfg)
        buffer.append(all_device_metrics)
        visualizer.show(buffer, cfg)
        if len(buffer) > 1:
            if stop_event.wait(cfg.update_time_interval):
                break


def main():
    cfg = Config.from_parser(args=parse_arguments())
    stop_event = threading.Event()
    thread = threading.Thread(target=app, args=(cfg, stop_event))
    thread.start()
    try:
        while True:
            # if keyboard.is_pressed('q'):
            #     stop_event.set()
            #     break
            time.sleep(0.05)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        thread.join()
        free_devices()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="A basic CLI tool to Monitor GPU status."
    )
    parser.add_argument(
        "--device-index",
        "-d",
        type=int,
        default=0,
        help="GPU index to monitor (default: 0)",
    )
    parser.add_argument(
        "--update-time-interval",
        "-u",
        type=float,
        default=1.0,
        help="Time interval between updates in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--text-mode",
        "-t",
        action="store_true",
        help="Enable text mode (default: False)",
    )
    parser.add_argument(
        "--generate-config",
        "-g",
        action="store_true",
        help="Generate default config '~/.gtoprc' file (default: False)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
