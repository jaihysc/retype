from .data import *

class Optimizer:
    def __init__(self, content: list[ContentChunk]):
        # Traverse the data
        for chunk in content:
            if chunk.type == MediaType.HTML:
                tag: HtmlTag = chunk.data
                self._traverseHtmlTag(tag)

    def _traverseHtmlTag(self, tag: HtmlTag):
        # Merge HtmlTag with multiple consecutive string children into one string,
        # avoids an extra space when rendered

        # if a string encountered, add to strBuffer,
        # once end of children or HtmlNode encountered, store strBuffer and clear it, then store HtmlNode
        newChildren: list = []
        strBuffer: list[str] = []
        for child in tag.children:
            if type(child) == str:
                strBuffer.append(child)
            else:
                if len(strBuffer) > 0:
                    newChildren.append(''.join(strBuffer))
                    strBuffer.clear()
                self._traverseHtmlTag(child)
        if len(strBuffer) > 0:
            newChildren.append(''.join(strBuffer))

        tag.children = newChildren