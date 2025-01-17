#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This implementation of EventListener acts as a filter for other EventListener implementations.
    It only allows events to pass if they occur in a given Rectangle.
"""
import typing

from borb.pdf.canvas.event.chunk_of_text_render_event import ChunkOfTextRenderEvent
from borb.pdf.canvas.event.event_listener import Event, EventListener
from borb.pdf.canvas.event.image_render_event import ImageRenderEvent
from borb.pdf.canvas.geometry.rectangle import Rectangle


class LocationFilter(EventListener):
    """
    This implementation of EventListener acts as a filter for other EventListener implementations.
    It only allows events to pass if they occur in a given Rectangle.
    """

    def __init__(self, rectangle: Rectangle):
        self._rectangle = rectangle
        self._listeners: typing.List[EventListener] = []

    def add_listener(self, listener: "EventListener") -> "LocationFilter":
        """
        This methods add an EventListener to this (meta)-EventListener
        """
        self._listeners.append(listener)
        return self

    def _event_occurred(self, event: "Event") -> None:
        # filter ChunkOfTextRenderEvent
        if isinstance(event, ChunkOfTextRenderEvent):
            bb: typing.Optional[Rectangle] = event.get_bounding_box()
            assert bb is not None
            if self._rectangle.x < bb.x < (
                self._rectangle.x + self._rectangle.width
            ) and self._rectangle.y < bb.y < (
                self._rectangle.y + self._rectangle.height
            ):
                for l in self._listeners:
                    l._event_occurred(event)
            return

        # filter ImageRenderEvent
        if isinstance(event, ImageRenderEvent):
            if self._rectangle.get_x() < event.get_x() < (
                self._rectangle.get_x() + self._rectangle.get_width()
            ) and self._rectangle.get_y() < event.get_y() < (
                self._rectangle.get_y() + self._rectangle.get_height()
            ):
                for l in self._listeners:
                    l._event_occurred(event)
            return

        # default
        for l in self._listeners:
            l._event_occurred(event)
