class Error(Exception): pass

class ParseError(Error): pass

class RegisterParseError(ParseError): pass

class GlobalRegisterParseError(RegisterParseError): pass

class LocalRegisterParseError(RegisterParseError): pass

class UnknownInstruction(Error): pass
