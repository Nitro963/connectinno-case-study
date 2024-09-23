import enum


class ContentType(str, enum.Enum):
    json = 'json'
    html = 'html'
    xml = 'xml'
    attachment = 'attachment'
