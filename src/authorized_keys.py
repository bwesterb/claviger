""" Lenient parser for authorized_keys. """
from six.moves import range

import six

import base64
import struct

class InvalidLineError(Exception):
    def __init__(self, line, message):
        super(InvalidLineError, self).__init__(message)
        self.line = line
    def __str__(self):
        return "{0}: {1}".format(
                            repr(self.line), self.message)

class ParseError(Exception):
    pass

class CouldNotParseLine(Exception):
    pass

class Line(object):
    def __init__(self, raw_line):
        self._raw_line = raw_line
    def store(self, f):
        f.write(self._raw_line)
    @property
    def raw_line(self):
        return self._raw_line

class Comment(Line):
    pass

class InvalidLine(Line):
    pass

class Entry(Line):
    def __init__(self, options, keytype, key, comment, raw_line=None):
        super(Entry, self).__init__(raw_line)
        self._options = options
        self._keytype = keytype
        self._key = key
        self._comment = comment
        if raw_line is None:
            self._update_rawline()

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, v):
        self._options = v
        self._update_rawline()

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, v):
        self._key = v
        self._update_rawline()

    @property
    def keytype(self):
        return self._keytype

    @keytype.setter
    def keytype(self, v):
        self._keytype = v
        self._update_rawline()

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, v):
        self._comment = v
        self._update_rawline()

    def _update_rawline(self):
        ret = ''
        if self._options:
            ret += self._options + ' '
        ret += '{0} {1}'.format(self._keytype, self._key)
        if self._comment:
            ret += ' ' + self._comment
        self._raw_line = ret

    @staticmethod
    def parse(raw_line):
        # An entry consists of three or four fields:
        #   [options] keytype key comment
        # The options field may contain spaces within quotes.  First
        # find where it ends.
        l = raw_line.strip()
        in_quote = False
        after_slash = False
        i = 0
        while i < len(l):
            if l[i] == ' ' and not in_quote:
                break
            if l[i] == '"' and not after_slash:
                in_quote = not in_quote
            elif l[i] == '\\':
                after_slash = True
            else:
                after_slash = False
            i += 1
        first_field, rest = l[:i], l[i:].strip()
        # Now the hard part: how to distinguish between options and keytype.
        # The trick: key actually also encodes keytype.
        # First case: first_field is keytype
        if check_key(rest.split(' ')[0], first_field):
            bits = rest.split(' ', 1)
            return Entry(keytype=first_field,
                         key=bits[0],
                         options=None,
                         comment=(None if len(bits) == 1 else bits[1].strip()),
                         raw_line=raw_line)
        # We are in the second case:
        bits = rest.split(' ', 1)
        if not len(bits) == 2:
            raise CouldNotParseLine("Missing key field")
        keytype = bits[0]
        last_fields = bits[1].strip().split(' ', 1)
        key = last_fields[0]
        if not check_key(key, keytype):
            raise CouldNotParseLine("key field is malformed")
        return Entry(options=first_field,
                     key=key,
                     keytype=keytype,
                     comment=(None if len(last_fields) == 1
                                 else last_fields[1].strip()),
                     raw_line=raw_line)

def check_key(b64key, keytype):
    """ Check whether key seems to be a valid base64-encoded string
        with the given keytype. """
    try:
        key = base64.b64decode(b64key)
    except TypeError:
        return False
    if len(key) < 5:
        return False
    keytype_len = struct.unpack('>I', key[:4])[0]
    if keytype_len != len(keytype):
        return False
    if not key[4:].startswith(keytype):
        return False
    return True
    
class AuthorizedKeysFile(object):
    def __init__(self, lines):
        self.lines = lines
    def get(self, key):
        """ Returns the first occurance of key """
        for line in self.lines:
            if not isinstance(line, Entry):
                continue
            if line.key == key:
                return key
    def contains(self, key):
        """ Checks whether a key occurs """
        for line in self.lines:
            if not isinstance(line, Entry):
                continue
            if line.key == key:
                return True
        return False
    def remove(self, key):
        """ Removes all occurances of the given key. """
        self.lines = [line for line in self.lines
                        if not isinstance(line, Entry) or
                                line.key != key]
    def removeAllKeys(self):
        """ Remove all keys, but leave the other entries. """
        self.lines = [line for line in self.lines
                        if not isinstance(line, Entry)]
    def add(self, options, keytype, key, comment):
        self.lines.append(Entry(options, keytype, key, comment))
    @property
    def entries(self):
        """ Returns a list of all entries """
        return [line for line in self.lines if isinstance(line, Entry)]
    def store(self, f):
        """ Writes to file-like object f. """
        for line in self.lines:
            line.store(f)
            f.write('\n')
    def __bytes__(self):
        f = six.BytesIO()
        self.store(f)
        return f.getvalue()
    __str__ = __bytes__

def parse(file_or_str, ignoreInvalidLines=True):
    """ Parse authorized_keys from file-like-object or string f.
        
        If ignoreInvalidLines is set (default), the parser will ignore
        lines it cannot succesfully parse. """
    parsed_lines = []
    if isinstance(file_or_str, six.binary_type):
        f = six.BytesIO(file_or_str)
    else:
        f = file_or_str
    while True:
        l = f.readline()
        if not l:
            break
        if l.endswith('\n'):
            l = l[:-1]
        stripped_line = l.strip()
        if stripped_line.startswith('#') or not stripped_line:
            parsed_lines.append(Comment(l))
            continue
        try:
            parsed_lines.append(Entry.parse(l))
        except CouldNotParseLine as e:
            if not ignoreInvalidLines:
                raise InvalidLineError(l, e.message)
            parsed_lines.append(InvalidLine(l))
    return AuthorizedKeysFile(parsed_lines)

