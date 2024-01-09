import base64
import html

from .data import *

class HtmlWriter:
    def __init__(self, publicationData: list[ContentChunk], maxWidth: str='920px', fontSize: str='15pt'):
        '''
        :param maxWidth Max width of text and images in document
        :param fontSize Size of rendered text in document
        '''
        self._outputBuffer = []

        self._output('<!DOCTYPE html>')
        self._output(f'<body style="font-family: Arial, sans-serif; width: {maxWidth}; margin: 0 auto; font-size: {fontSize}">')

        for datum in publicationData:
            if datum.type == MediaType.HTML:
                self._writeTag(datum.data)
            elif datum.type == MediaType.IMAGE:
                base64Img = base64.b64encode(datum.data).decode()
                self._output(f'<div><img style="display: block; max-width: {maxWidth}; margin: 0 auto" src="data:image/png;base64,{base64Img}"/></div>')

        self._output('</body>')

    def output(self) -> str:
        '''
        Returns generated output for provided PublicationResourceData input
        '''
        return '\n'.join(self._outputBuffer)

    def _writeTag(self, tag: HtmlTag):
        '''
        Recursively writes output for HtmlTag and its children
        '''
        self._output(f'<{tag.name}>')
        for child in tag.children:
            if type(child) == str:
                # Text
                text = html.escape(child)
                self._output(text)
            else:
                # Another tag
                self._writeTag(child)
        self._output(f'</{tag.name}>')

    def _output(self, text: str):
        '''
        Writes text to output buffer, automatically appends newline
        '''
        # The newline is appended when the output buffer is joined together
        self._outputBuffer.append(text)

    # To improve performance, avoid concating to the same string (requires a copy)
    # Store a list of strings instead
    _outputBuffer: list[str]