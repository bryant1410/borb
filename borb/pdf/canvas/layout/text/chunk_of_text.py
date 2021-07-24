#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This implementation of LayoutElement represents one uninterrupted block of text
"""
import typing
from decimal import Decimal

from borb.io.read.types import Dictionary, Name
from borb.pdf.canvas.color.color import Color, X11Color
from borb.pdf.canvas.font.font import Font
from borb.pdf.canvas.font.glyph_line import GlyphLine
from borb.pdf.canvas.font.simple_font.font_type_1 import StandardType1Font
from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf.canvas.layout.layout_element import Alignment, LayoutElement
from borb.pdf.page.page import Page


class ChunkOfText(LayoutElement):
    """
    This implementation of LayoutElement represents one uninterrupted block of text
    """

    def __init__(
        self,
        text: str,
        font: typing.Union[Font, str] = "Helvetica",
        font_size: Decimal = Decimal(12),
        font_color: Color = X11Color("Black"),
        border_top: bool = False,
        border_right: bool = False,
        border_bottom: bool = False,
        border_left: bool = False,
        border_color: Color = X11Color("Black"),
        border_width: Decimal = Decimal(1),
        padding_top: Decimal = Decimal(0),
        padding_right: Decimal = Decimal(0),
        padding_bottom: Decimal = Decimal(0),
        padding_left: Decimal = Decimal(0),
        margin_top: typing.Optional[Decimal] = None,
        margin_right: typing.Optional[Decimal] = None,
        margin_bottom: typing.Optional[Decimal] = None,
        margin_left: typing.Optional[Decimal] = None,
        vertical_alignment: Alignment = Alignment.TOP,
        horizontal_alignment: Alignment = Alignment.LEFT,
        background_color: typing.Optional[Color] = None,
        parent: typing.Optional["LayoutElement"] = None,
    ):
        super().__init__(
            font_size=font_size,
            border_top=border_top,
            border_right=border_right,
            border_bottom=border_bottom,
            border_left=border_left,
            border_color=border_color,
            border_width=border_width,
            padding_top=padding_top,
            padding_right=padding_right,
            padding_bottom=padding_bottom,
            padding_left=padding_left,
            margin_top=margin_top or Decimal(0),
            margin_right=margin_right or Decimal(0),
            margin_bottom=margin_bottom or Decimal(0),
            margin_left=margin_left or Decimal(0),
            vertical_alignment=vertical_alignment,
            horizontal_alignment=horizontal_alignment,
            background_color=background_color,
            parent=parent,
        )
        self._text = text
        if isinstance(font, str):
            self._font: Font = StandardType1Font(font)
            assert self._font
        else:
            self._font = font
        self._font_color = font_color

    def get_text(self) -> str:
        """
        This function returns the text of this LayoutElement
        """
        return self._text

    def get_font(self) -> Font:
        """
        This function returns the Font of this LayoutElement
        """
        return self._font

    def _get_font_resource_name(self, font: Font, page: Page):
        # create resources if needed
        if "Resources" not in page:
            page[Name("Resources")] = Dictionary().set_parent(page)  # type: ignore [attr-defined]
        if "Font" not in page["Resources"]:
            page["Resources"][Name("Font")] = Dictionary()

        # insert font into resources
        font_resource_name = [
            k for k, v in page["Resources"]["Font"].items() if v == font
        ]
        if len(font_resource_name) > 0:
            return font_resource_name[0]
        else:
            font_index = len(page["Resources"]["Font"]) + 1
            page["Resources"]["Font"][Name("F%d" % font_index)] = font
            return Name("F%d" % font_index)

    def _write_text_bytes(self) -> str:
        hex_mode: bool = False
        for c in self._text:
            if ord(c) != self._font.unicode_to_character_identifier(c):
                hex_mode = True
                break
        if hex_mode:
            return self._write_text_bytes_in_hex()
        else:
            return self._write_text_bytes_in_ascii()

    def _write_text_bytes_in_hex(self) -> str:
        sOut: str = ""
        for c in self._text:
            cid: typing.Optional[int] = self._font.unicode_to_character_identifier(c)
            assert cid is not None, "Font %s can not represent '%s'" % (
                self._font.get_font_name(),
                c,
            )
            hex_rep: str = hex(int(cid))[2:]
            if len(hex_rep) % 2 == 1:
                hex_rep = "0" + hex_rep
            sOut += "".join(["<", hex_rep, ">"])
        return "".join(["[", sOut, "] TJ"])

    def _write_text_bytes_in_ascii(self) -> str:
        """
        This function escapes certain reserved characters in PDF strings.
        """
        sOut: str = ""
        for c in self._text:
            if c == "\r":
                sOut += "\\r"
            elif c == "\n":
                sOut += "\\n"
            elif c == "\t":
                sOut += "\\t"
            elif c == "\b":
                sOut += "\\b"
            elif c == "\f":
                sOut += "\\f"
            elif c in ["(", ")", "\\"]:
                sOut += "\\" + c
            elif 0 <= ord(c) < 8:
                sOut += "\\00" + oct(ord(c))[2:]
            elif 8 <= ord(c) < 32:
                sOut += "\\0" + oct(ord(c))[2:]
            else:
                sOut += c
        # default
        return "".join(["(", sOut, ") Tj"])

    def _do_layout_without_padding(self, page: Page, bounding_box: Rectangle):
        assert self._font
        rgb_color = self._font_color.to_rgb()
        COLOR_MAX = Decimal(255.0)
        assert self._font_size is not None
        content = """
            q
            BT
            %f %f %f rg
            /%s %f Tf            
            %f 0 0 %f %f %f Tm            
            %s
            ET            
            Q
        """ % (
            Decimal(rgb_color.red / COLOR_MAX),  # rg
            Decimal(rgb_color.green / COLOR_MAX),  # rg
            Decimal(rgb_color.blue / COLOR_MAX),  # rg
            self._get_font_resource_name(self._font, page),  # Tf
            Decimal(1),  # Tf
            float(self._font_size),  # Tm
            float(self._font_size),  # Tm
            float(bounding_box.x),  # Tm
            float(bounding_box.y + bounding_box.height - self._font_size),  # Tm
            self._write_text_bytes(),  # Tj
        )
        self._append_to_content_stream(page, content)
        encoded_bytes: bytes = [
            self._font.unicode_to_character_identifier(c) or 0 for c in self._text
        ]
        layout_rect = Rectangle(
            bounding_box.x,
            bounding_box.y + bounding_box.height - self._font_size,
            GlyphLine(
                encoded_bytes, self._font, self._font_size
            ).get_width_in_text_space(),
            self._font_size,
        )

        # set bounding box
        self.set_bounding_box(layout_rect)

        # return
        return layout_rect