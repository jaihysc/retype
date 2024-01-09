import bs4
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from .data import *

class Parser:
    '''
    Used for parsing the epub file and extracting its contents
    '''
    def __init__(self, path):
        '''
        Opens and parses the epub file at the provided path

        :param path Path to a file (a string), a file-like object or a path-like object
        '''
        self._container = None
        self._packageDocuments = []
        self._documentContents = []
        self._zip = None

        # Read epub
        self._zip = ZipFile(path, 'r')

        # Read container.xml
        with self._openFile(Path('META-INF/container.xml')) as file:
            self._container = self._parseContainer(ElementTree.parse(file).getroot())

        # Load package documents
        for packageDocumentPath in self._container.packageDocumentPaths:
            with self._openFile(packageDocumentPath) as file:
                packageDocument: PackageDocumentData = self._parsePackageDocument(ElementTree.parse(file).getroot())
                self._packageDocuments.append(packageDocument)

            # Load publication resources for last package document
            for info in self._packageDocuments[-1].publicationResourceInfo:
                publicationResourcePath = self._toAbsolutePath(packageDocumentPath, info.href)
                try:
                    with self._openFile(publicationResourcePath) as file:
                        if info.type == MediaType.HTML:
                            publicationData = self._parsePublicationResourceHtml(publicationResourcePath, file.read())
                            # Add parsed PublicationData to master list
                            for datum in publicationData:
                                self._documentContents.append(datum)
                        elif info.type == MediaType.IMAGE:
                            chunk = ContentChunk()
                            chunk.data = file.read()
                            chunk.type = MediaType.IMAGE
                            self._documentContents.append(chunk)
                except FileNotFoundError as e:
                    print(f"Error parsing publication resource: '{str(e)}', continuing")

    def __del__(self):
        if self._zip:
            self._zip.close()

    def content(self) -> list[ContentChunk]:
        '''
        Retrieves ContentChunk for parsed EPUB describing the html files and images
        '''
        return self._documentContents

    # XML parsing methods

    def _parseContainer(self, root: ElementTree.Element) -> ContainerData:
        '''
        Parses ElementTree for container.xml

        :param root Root node for ElementTree
        '''
        data = ContainerData()

        rootfiles = root[0]
        for rootfile in rootfiles:
            data.packageDocumentPaths.append(Path(rootfile.get('full-path')))

        return data

    def _parsePackageDocument(self, root: ElementTree.Element) -> PackageDocumentData:
        '''
        Parses ElementTree for package document

        :param root Root node for ElementTree
        '''
        data = PackageDocumentData()

        metadata = root[0]
        manifest = root[1]
        spine = root[2]

        # Parse metadata
        for child in metadata:
            tag = self._stripXmlNamespace(child.tag)
            if tag == 'title':
                data.title = child.text
            elif tag == 'creator':
                data.creator.append(child.text)

        # Parse manifest

        # Maps PublicationResource id to PublicationResource
        foundPublicationResources: dict[str, PublicationResourceInfo] = {}
        for item in manifest:
            info = PublicationResourceInfo()

            if type(item.attrib['href']) != str:
                raise TypeError('Bad href')
            info.href = item.attrib['href']

            if type(item.attrib['id']) != str:
                raise TypeError('Bad id')
            info.id = item.attrib['id']

            # Parse media type
            if type(item.attrib['media-type']) != str:
                raise TypeError('Bad media-type')

            mediaType = item.attrib['media-type']
            if mediaType.startswith('image/'):
                info.type = MediaType.IMAGE
            else:
                info.type = MediaType.HTML

            foundPublicationResources[info.id] = info

        # Parse spine
        for itemref in spine:
            idref = itemref.attrib['idref']
            data.publicationResourceInfo.append(foundPublicationResources[idref])

        return data

    def _parsePublicationResourceHtml(self, publicationResourcePath: Path, html: str) -> list[ContentChunk]:
        '''
        Parses publication resource in HTML string for content

        :param publicationResourcePath Absolute path to the current publication resource
        :param html HTML to parse
        '''
        chunks = []

        soup = bs4.BeautifulSoup(html, 'html.parser')
        for soupTag in soup.find_all(['img', 'image', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            chunk = ContentChunk()

            if soupTag.name == 'img' or soupTag.name == 'image':
                # Search for a possible key referencing the image
                imageSourceKeys = ['src', 'xlink:href']
                for key in imageSourceKeys:
                    if key in soupTag.attrs:
                        imageSourceKey = key
                        break

                # Tag is image, load the image
                with self._openFile(self._toAbsolutePath(publicationResourcePath, soupTag[imageSourceKey])) as file:
                    chunk.data = file.read()
                chunk.type = MediaType.IMAGE
            else:
                # BeautifulSoup Tag is HTML, save the tag as our own tag class
                htmlTag = HtmlTag()
                htmlTag.name = soupTag.name
                for soupTagChild in soupTag.children:
                    self._generateHtmlTagFromSoupTag(soupTagChild, htmlTag)

                chunk.data = htmlTag
                chunk.type = MediaType.HTML

            chunks.append(chunk)

        return chunks

    def _generateHtmlTagFromSoupTag(self, soupTag: bs4.Tag, parentHtmlTag: HtmlTag):
        '''
        Recursively converts BeautifulSoup Tag to HtmlTag, keeping only specific tags

        HtmlTag generated for soupTag is attached onto parentHtmlTag
        '''
        if type(soupTag) == bs4.NavigableString:
            parentHtmlTag.children.append(soupTag.get_text())
        else:
            # Only keep specific tags
            if soupTag.name in ['strong', 'em']:
                htmlTag = HtmlTag()
                htmlTag.name = soupTag.name
                parentHtmlTag.children.append(htmlTag)

                parentHtmlTag = htmlTag # For recursion step, change parent

            # Generate HtmlTag for children
            for soupTagChild in soupTag.children:
                self._generateHtmlTagFromSoupTag(soupTagChild, parentHtmlTag)

    # Helpers

    def _openFile(self, path: Path):
        '''
        Opens file in EPUB at path, returns file
        '''
        # Must resolve the path to remove ../
        # however, resolve() also prepends the directory of the python file, remove it using relative_to
        absolutePath = path.resolve().relative_to(Path('.').resolve())
        # zip.open method takes string file path in posix format only
        finalPath = absolutePath.as_posix()

        try:
            return self._zip.open(finalPath)
        except KeyError:
            raise FileNotFoundError(f"No item named '{finalPath}' in the archive")

    def _stripXmlNamespace(self, text: str) -> str:
        '''
        Removes the namespace in element tag
        e.g., {http://test.org}title -> title
        '''
        return text.rpartition('}')[2]

    def _toAbsolutePath(self, basePath: str | Path, path: str | Path) -> Path:
        '''
        Resolve relative path in EPUB to an absolute path with given base file path
        '''
        path: Path = Path(path)
        if not Path(path).is_absolute():
            path = Path(basePath).parent / Path(path)
        return path

    # Data

    _container: ContainerData
    _packageDocuments: list[PackageDocumentData]
    _documentContents: list[ContentChunk] # Extracted relevent content from the document

    _zip: ZipFile # The zip file being read