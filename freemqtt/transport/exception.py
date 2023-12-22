# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#
from typing import Optional

class TransportClosedError(IOError):
    """Exception raised by `IOStream` methods when the stream is closed.

    Note that the close callback is scheduled to run *after* other
    callbacks on the stream (to allow for buffered data to be processed),
    so you may see this error before you see the close callback.

    The ``real_error`` attribute contains the underlying error that caused
    the stream to close (if any).

    .. versionchanged:: 4.3
       Added the ``real_error`` attribute.
    """

    def __init__(self, real_error: Optional[BaseException] = None) -> None:
        super().__init__("Stream is closed")
        self.real_error = real_error
