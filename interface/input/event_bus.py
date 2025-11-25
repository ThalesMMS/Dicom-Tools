"""Simple synchronous event/command bus used to decouple UI and engine."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, Dict, List, Optional


Callback = Callable[[Any], None]


@dataclass
class Command:
    name: str
    payload: Optional[Dict[str, Any]] = None


@dataclass
class Event:
    name: str
    payload: Optional[Dict[str, Any]] = None


class EventBus:
    """Pub/sub + command dispatch."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callback]] = defaultdict(list)
        self._command_handlers: DefaultDict[str, List[Callable[[Command], Optional[Event]]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callback) -> None:
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callback) -> None:
        callbacks = self._subscribers.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def emit(self, event: Event) -> None:
        for callback in list(self._subscribers.get(event.name, [])):
            callback(event)

    def register_command(self, name: str, handler: Callable[[Command], Optional[Event]]) -> None:
        self._command_handlers[name].append(handler)

    def dispatch(self, command: Command) -> List[Event]:
        events: List[Event] = []
        for handler in list(self._command_handlers.get(command.name, [])):
            maybe_event = handler(command)
            if isinstance(maybe_event, Event):
                events.append(maybe_event)
            elif isinstance(maybe_event, list):
                events.extend([ev for ev in maybe_event if isinstance(ev, Event)])
        for event in events:
            self.emit(event)
        return events
