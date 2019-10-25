"""
Various small helper functions/classes often used by classes such as :py:mod:`.EncryptHelper` and :py:mod:`.KeyManager`

"""
import base64
from typing import Union

from privex.helpers import byteify


def is_base64(sb: Union[str, bytes], urlsafe: bool = True) -> bool:
    """
    Returns ``True`` if ``sb`` appears to be a Base64 encoded string/bytes, otherwise ``False``

    :param str|bytes sb: Data to check for base64 encoding
    :param bool urlsafe: (Default: ``True``) Use :py:func:`base64.urlsafe_b64encode` and decode, instead of
                         plain :py:func:`base64.b64encode` and decode.
    :return bool is_base64: ``True`` if data appears to be Base64, otherwise ``False``
    """
    b64_enc = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    b64_dec = base64.urlsafe_b64decode if urlsafe else base64.b64decode
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb = bytes(sb, 'ascii')
        if not isinstance(sb, bytes):
            raise ValueError("Argument 'sb' must be string or bytes")
        return b64_enc(b64_dec(sb)) == sb
    except Exception:
        return False


def auto_b64decode(data: Union[str, bytes], urlsafe: bool = True) -> bytes:
    """
    Determines if ``data`` is base64 encoded. If it is, then it will decode it and return the decoded bytes.
    Otherwise, it will return the original data as bytes.
    
    **Example usage**
    
        >>> a = b'dGVzdGluZw=='
        >>> b = 'hello world'
        >>> auto_b64decode(a)  # This is detected to be Base64 encoded, and so the decoded data is returned
        b'testing'
        >>> auto_b64decode(b)  # This does not appear to be Base64, and so is returned as normal (but as bytes)
        b'hello world'
    
    :param str|bytes data: Data to check for base64, and decode if required
    :param bool urlsafe: (Default: ``True``) Use :py:func:`base64.urlsafe_b64decode`, instead of
                         plain :py:func:`base64.b64decode`
    :return bytes data: If ``data`` was base64, this will be the decoded bytes. Otherwise, the original data as bytes.
    """
    data = byteify(data)
    b64_dec = base64.urlsafe_b64decode if urlsafe else base64.b64decode
    if is_base64(data):
        return b64_dec(data)
    return data

