""""""
# 3rd Party
from fastapi import HTTPException

class ReverseProxyServerException(HTTPException):
    """"""
    pass

class ReverseProxyServerUnHandledError(ReverseProxyServerException):
    """"""
    pass

class ReverseProxyServerUpStreamRequestError(ReverseProxyServerException):
    """"""
    pass

class ReverseProxyServerTimeoutError(ReverseProxyServerException):
    """"""
    pass

class ReverseProxyServerAuthFailed(ReverseProxyServerException):
    """"""
    pass

class UpStreamRequestBufferSizeExceededError(ReverseProxyServerException):
    """"""
    pass