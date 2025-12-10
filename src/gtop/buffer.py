from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, List


@dataclass
class Buffer:
    max_size: int
    _buffer: List = field(default_factory=list)

    def append(self, item: Any) -> None:
        self._buffer.append(item)
        if len(self._buffer) > self.max_size:
            self._buffer = self._buffer[-self.max_size :]

    def __iter__(self) -> Iterator[Any]:
        for item in self._buffer:
            yield item

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def last(self) -> Any:
        return self._buffer[-1]

    @property
    def first(self) -> Any:
        return self._buffer[0]


