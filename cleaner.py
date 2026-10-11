import re
import zipfile

from calibre.utils.config import JSONConfig

# formats calibre's book container can open and write back
FORMATS = ('EPUB', 'AZW3')

prefs = JSONConfig('plugins/string_remover')
prefs.defaults['strings'] = []
prefs.defaults['case_sensitive'] = False
prefs.defaults['regex'] = False
prefs.defaults['clean_on_import'] = True
prefs.defaults['keep_original'] = True


def build_pattern(settings):
    strings = [s for s in settings['strings'] if s]
    if not strings:
        return None
    if not settings['regex']:
        # longest first, so a string is not shadowed by one of its own prefixes
        strings = [re.escape(s) for s in sorted(strings, key=len, reverse=True)]
    flags = 0 if settings['case_sensitive'] else re.IGNORECASE
    return re.compile('|'.join('(?:%s)' % s for s in strings), flags)


def local_name(el):
    return el.tag.rpartition('}')[2].lower()


def remove_element(el):
    ''' Remove el from the tree, keeping the text that follows it. '''
    parent = el.getparent()
    if el.tail:
        prev = el.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or '') + el.tail
        else:
            parent.text = (parent.text or '') + el.tail
    parent.remove(el)


def prune(el, body):
    ''' Remove el if it has no content left, then do the same for its ancestors. '''
    while (el is not None and el is not body and el.getparent() is not None
           and len(el) == 0 and not (el.text or '').strip()):
        parent = el.getparent()
        remove_element(el)
        el = parent


def clean_root(root, pattern):
    ''' Remove all matches from a parsed HTML file, return how many were removed. '''
    body = next((el for el in root.iter('*') if local_name(el) == 'body'), None)
    if body is None:
        return 0
    count = 0
    # a link pointing to or naming a match goes as a whole, together with the
    # wrappers (<p>, <div>, ...) that only existed to hold it
    for a in [el for el in body.iter('*') if local_name(el) == 'a']:
        if pattern.search(a.get('href') or '') or pattern.search(''.join(a.itertext())):
            parent = a.getparent()
            remove_element(a)
            prune(parent, body)
            count += 1
    for el in list(body.iter('*')):
        if local_name(el) in ('script', 'style'):
            continue
        for attr in ('text', 'tail'):
            value = getattr(el, attr)
            if value and pattern.search(value):
                value, n = pattern.subn('', value)
                setattr(el, attr, value)
                count += n
                if attr == 'text':
                    prune(el, body)
    return count


def may_contain(path, pattern):
    ''' Cheap check to avoid unpacking books that have no match anyway. '''
    if not path.lower().endswith('.epub'):
        return True
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.lower().endswith(('.html', '.xhtml', '.htm', '.xml')):
                    if pattern.search(zf.read(name).decode('utf-8', 'replace')):
                        return True
    except Exception:
        return True
    return False


def clean_file(path, pattern):
    ''' Remove all matches from the book at path in place, return how many were removed. '''
    from calibre.ebooks.oeb.base import OEB_DOCS
    from calibre.ebooks.oeb.polish.container import get_container
    from calibre.ptempfile import TemporaryDirectory
    with TemporaryDirectory('_string_remover') as tdir:
        container = get_container(path, tdir=tdir)
        count = 0
        for name, mime in list(container.mime_map.items()):
            if mime not in OEB_DOCS or not pattern.search(container.raw_data(name)):
                continue
            n = clean_root(container.parsed(name), pattern)
            if n:
                container.dirty(name)
                count += n
        if count:
            container.commit()
        return count
