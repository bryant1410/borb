from typing import Optional, List, Any

from ptext.object.canvas.font.cid_font_type_0 import CIDFontType0
from ptext.object.canvas.font.cid_font_type_2 import CIDFontType2
from ptext.object.canvas.font.font_type_0 import FontType0
from ptext.object.canvas.font.font_type_1 import FontType1
from ptext.object.canvas.font.font_type_3 import FontType3
from ptext.object.canvas.font.true_type_font import TrueTypeFont
from ptext.object.event_listener import EventListener
from ptext.primitive.pdf_dictionary import PDFDictionary
from ptext.primitive.pdf_name import PDFName
from ptext.primitive.pdf_null import PDFNull
from ptext.primitive.pdf_object import PDFObject
from ptext.tranform.base_transformer import BaseTransformer, TransformerContext


class DefaultFontDictionaryTransformer(BaseTransformer):
    def can_be_transformed(self, object: PDFObject) -> bool:
        return (
            isinstance(object, PDFDictionary)
            and PDFName("Type") in object
            and object[PDFName("Type")] == PDFName("Font")
        )

    def transform(
        self,
        object_to_transform: PDFObject,
        parent_object: PDFObject,
        context: Optional[TransformerContext] = None,
        event_listeners: List[EventListener] = [],
    ) -> Any:

        # convert dictionary like structure
        subtype_name = object_to_transform[PDFName("Subtype")].name

        font_obj = None
        if subtype_name == "TrueType":
            font_obj = TrueTypeFont()
        elif subtype_name == "Type0":
            font_obj = FontType0()
        elif subtype_name == "Type1":
            font_obj = FontType1()
        elif subtype_name == "Type3":
            font_obj = FontType3()
        elif subtype_name == "CIDFontType0":
            font_obj = CIDFontType0()
        elif subtype_name == "CIDFontType2":
            font_obj = CIDFontType2()
        else:
            print("Unsupported font type %s" % subtype_name)

        # set parent
        if font_obj is not None:
            font_obj.set_parent(parent_object)

        # add listener(s)
        for l in event_listeners:
            font_obj.add_event_listener(l)

        # convert key/value pair(s)
        for k, v in object_to_transform.items():
            if k == PDFName("Parent"):
                continue
            v = self.get_root_transformer().transform(v, font_obj, context, [])
            if v != PDFNull():
                font_obj[k.name] = v

        # return
        return font_obj