from enum import Enum
from pathlib import Path

class MediaType(Enum):
    HTML = 1
    IMAGE = 2

class PublicationResourceInfo:
    '''
    Information about a publication resource (e.g., image, html files) in the manifest

    :param href Relative path to file, from location of package document
    :param type MediaType of file
    :param id Unique identifier used to reference this resource
    '''
    def __init__(self):
        self.href = ''
        self.type = MediaType.HTML
        self.id = ''

    href: str
    type: MediaType
    id: str

class ContainerData:
    '''
    Holds data retrieved from container.xml

    :param packageDocumentPaths Paths to package documents
    '''
    def __init__(self):
        self.packageDocumentPaths = []

    packageDocumentPaths: list[Path]

class PackageDocumentData:
    '''
    Holds data retrieved from package documents

    :param title Title of document
    :param creator Creators of document
    :param publicationResourceInfo Resources used in the document, in order of appearance
    '''
    def __init__(self):
        self.title = ''
        self.creator = []
        self.publicationResourceInfo = []

    title: str
    creator: list[str]
    publicationResourceInfo: PublicationResourceInfo

class HtmlTag:
    '''
    Holds a HTML tag

    :param name Name of this tag
    :param children Children of this tag, or inner text
    '''
    def __init__(self):
        self.name = ''
        self.children = []

    name: str
    children: list

class ContentChunk:
    '''
    Holds html/image data to be displayed in the rendered document

    :param data HtmlTag if HTML, image data if image
    :param type MediaType of data
    '''
    def __init__(self):
        self.data = None
        self.type = MediaType.HTML

    data: HtmlTag | bytes = None
    type: MediaType = MediaType.HTML