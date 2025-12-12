from __future__ import annotations

from typing import Generic, TypeVar
from dataclasses import dataclass, field
from typing import Any, Iterator, List

T = TypeVar("T")


@dataclass
class Buffer(Generic[T]):
    max_size: int
    _buffer: List[T] = field(default_factory=list)

    def append(self, item: T) -> None:
        self._buffer.append(item)
        if len(self._buffer) > self.max_size:
            self._buffer = self._buffer[-self.max_size :]

    def __iter__(self) -> Iterator[T]:
        for item in self._buffer:
            yield item

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def last(self) -> T:
        return self._buffer[-1]

    @property
    def first(self) -> T:
        return self._buffer[0]


