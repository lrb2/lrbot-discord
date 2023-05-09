class RaisedException(Exception):
    '''
    Base class for all exceptions manually raised by lrbot.
    This exception should never be called directly.
    '''
    pass

class InvalidArgs(RaisedException):
    pass

class InvalidFiles(RaisedException):
    pass