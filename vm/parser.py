"""Instructions parser.

Instruction is a tuple(name, *arguments). Examples of valid instructions:

>>> ('gcopy', 'r0', 'g3')
>>> ('print', 'r4')
>>> ('tstop',)
"""

from . import error


def reg(s):
    """Parses "r\\d" or "g\\d" into (is_local, \\d).

    Raises RegisterParseError.

    >>> _parse_reg("r4")
    (True, 4)
    >>> _parse_reg("g0")
    (False, 0)
    """

    try:
        is_local = s.startswith("r")
        is_global = s.startswith("g")
    except Exception:
        raise error.RegisterParseError(s)
    if not (is_local or is_global):
        raise error.RegisterParseError(s)
    try:
        r = int(s[1:])
        return (is_local, r)
    except TypeError, ValueError:
        raise error.RegisterParseError(s)

def local_reg(s):
    is_local, r = reg(s)
    if is_local:
        return r
    else:
        raise error.LocalRegisterParseError(s)

def global_reg(s):
    is_local, r = reg(s)
    if not is_local:
        return r
    else:
        raise error.GlobalRegisterParseError(s)

def line(s):
    parts = s.split()
    name, args = parts[0], parts[1:]
    # parse and check arguments
    # for these instructions first argument must be thread-local register
    if name in set(['copy', 'set', 'swap', 'addr', 'eval', 'spawn', 'spawna', 'tself', 'tget', 'twait', 'tdel', 'print']):
        is_local, args[0] = reg(args[0])
        assert is_local
    # for these, first argument must be any register
    if name in set(['gcopy', 'gset']):
        args[0] = reg(args[0])
    # for these, second argument must be local register
    if name in set(['copy', 'swap', 'tget']):
        is_local, args[1] = reg(args[1])
        assert is_local
    # for these, second argument must be any register
    if name in set(['gcopy', 'gset']):
        args[1] = reg(args[1])
    # parse constants
    if name in set(['jump', 'jz', 'jnz']):
        args[0] = int(args[0])
    if name in set(['set', 'gset', 'spawn', 'spawna']):
        args[1] = int(args[1])
    # eval is a bit special complex instruction
    if name == 'eval':
        is_local, args[2] = reg(args[2]) # first operand
        assert is_local
        is_local, args[3] = reg(args[3]) # second operand
        assert is_local
    # and tget
    if name == 'tget':
        is_local, args[2] = reg(args[2]) # the other vthread's register
        assert is_local
    # build the instruction
    return tuple( [name] + args )

def text(s):
    return map(line, s.splitlines())
