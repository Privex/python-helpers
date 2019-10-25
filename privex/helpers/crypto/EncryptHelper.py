import binascii
import base64
import logging
from io import TextIOWrapper
from typing import Optional, Union, Tuple, Type
# characters that shouldn't be mistaken
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import KeyDerivationFunction
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from privex.helpers.crypto.base import is_base64
from privex.helpers.exceptions import EncryptKeyMissing, EncryptionError
from privex.helpers.common import empty, random_str, ALPHANUM

log = logging.getLogger(__name__)


class EncryptHelper:
    """
    Symmetric AES-128 encryption/decryption made painless - wrapper class for :py:class:`cryptography.fernet.Fernet`

    A wrapper class for the :py:class:`cryptography.fernet.Fernet` encryption system, designed to make usage of Fernet
    as painless as possible.

    The class :class:`.EncryptHelper` contains various methods for simplifying the use of the Python library
    :doc:`Cryptography <cryptography:index>` 's :py:class:`cryptography.fernet.Fernet` system.

    :py:meth:`.encrypt_str` / :py:meth:`.decrypt_str` facilitate painless encryption and decryption of data using AES-128 CBC.
    They can either be passed a 32-byte Fernet key (base64 encoded) as an argument, or leave the key as None and they'll try
    to use the key defined on the :class:`.EncryptHelper` instance at :py:attr:`.EncryptHelper.encrypt_key`

    **Basic usage:**

        >>> from privex.helpers import EncryptHelper
        >>> key = EncryptHelper.generate_key()     # Generates a 32-byte symmetric key, returned as a base64 encoded string
        >>> crypt = EncryptHelper(key)             # Create an instance of EncryptHelper, en/decrypting using ``key`` by default
        # Encrypts the string 'hello world' with AES-128 CBC using the instance's key, returned as a base64 string
        >>> enc = crypt.encrypt_str('hello world')
        >>> print(enc)
        gAAAAABc7ERTpu2D_uven3l-KtU_ewUC8YWKqXEbLEKrPKrKWT138MNq-I9RRtCD8UZLdQrcdM_IhUU6r8T16lQkoJZ-I7N39g==

        >>> crypt.is_encrypted(enc)       # Check if a string/bytes is encrypted (only works with data matching the key)
        True
        >>> data = crypt.decrypt_str(enc) # Decrypt the encrypted data using the same key, outputs as a string
        >>> print(data)
        hello world


    """
    encrypt_key: str
    """A base64 encoded :class:`.Fernet` key, used by default for functions such as :py:meth:`.encrypt_str`"""
    
    def __init__(self, encrypt_key: str, **kwargs):
        """
        Create an instance of :class:`.EncryptHelper` using the :py:class:`cryptography.fernet.Fernet` key ``encrypt_key``
        as the default key for encrypting/decrypting data.

        :param str encrypt_key: Base64 encoded Fernet key, used by default for encrypting/decrypting data
        """
        self.settings = {**dict(encrypt_key=encrypt_key), **kwargs}
        self.encrypt_key = encrypt_key
    
    @staticmethod
    def generate_key(output: Optional[Union[str, TextIOWrapper]] = None, mode='w') -> str:
        """
        Generate a compatible encryption key for use with :py:class:`cryptography.fernet.Fernet`

        **NOTE:** Regardless of whether or not the method is outputting the key to a filename / stream, this
        method will always return the encryption key as a string after completion. The key returning was redacted
        from the outputting examples to help readability.

        **Examples**

        With no arguments, it will simply return the key as a string.

            >>> EncryptHelper.generate_key()
            '6vJ_o8XQRmX_TgUFTWWV_U2vm71ThnpWsCIvgXFWg9s='

        If ``output`` is a ``str`` - it's assumed to be a filename, and the Fernet key will be outputted
        to the file ``output`` using ``open(output, mode)`` (where ``mode`` defaults to ``'w'``).

        Below, we call ``generate_key`` with the string **test.key.txt** - and we can then see the file was created
        and contains the Fernet key encoded with Base64.

            >>> EncryptHelper.generate_key('test.key.txt')
            >>> open('test.key.txt').read()
            'aRDR-gCrmrPrMr9hQnL4epIPl2Szbzfid_vSTO-rl20='

        If ``output`` is a file/stream object, the method ``output.write(key)`` will be called, where ``key``
        is the Fernet key as a string.

        Below, we open **test2.key.txt** in write mode manually, then pass the file stream object to generate_key, which
        writes the key to the file.

            >>> with open('test2.key.txt', 'w') as fp:
            ...     EncryptHelper.generate_key(fp)
            >>> open('test2.key.txt').read()
            'DAFEvRkwG7ws0ccjIv2QL_s5cpeWktqpbc7eSjL-V74='


        :param None output: Simply return the generated key
        :param str output: Output the generated key to the filename ``output`` using the open mode ``mode``
        :param TextIOWrapper output: Output the generated key to the file/stream object ``output`` using ``.write(key: str)``

        :param str mode: If you're passing a string filename as ``output`` - then this controls the ``open()`` mode, e.g. 'w', 'a', 'w+'

        :return str key: The generated Fernet key, encoded with Base64.
        """
        key = Fernet.generate_key().decode('utf-8')
        if type(output) is str:
            log.debug('Outputting Fernet key to file "%s" using open mode "%s"', output, mode)
            with open(output, mode) as fp:
                fp.write(key)
        elif isinstance(output, TextIOWrapper):
            log.debug('Outputting Fernet key to file stream object: "%s"', repr(output))
            output.write(key)
        return key
    
    @staticmethod
    def password_key(password, salt=None, kdf: Type[KeyDerivationFunction] = PBKDF2HMAC, **kwargs) -> Tuple[str, dict]:
        """
        Generate a :py:class:`cryptography.fernet.Fernet` key based on a password and salt. Key derivation is customisable.

        :param password: A password to generate the key from, as ``str`` or ``bytes``
        :param     salt: The salt to use when generating the key, as ``str`` or ``bytes``
                         If ``salt`` is a string, it can also be passed in base64 format.


        **Standard Usage with manual salt:**

        Call ``password_key`` with a password of your choice, and a salt of your choice (ideally at least 16 chars),
        and a tuple containing the Fernet key (base64 encoded), and key derivative configuration will be returned.

            >>> ek = EncryptHelper
            >>> key, kd = ek.password_key('MySecurePass', salt=b'Sup3rseCr3tsalt')
            >>> key
            'rJ_g-lBT7pxeu4MVrhfi5rAv9yLbX5pTm6vkJj_Mezc='
            >>> kd
            {'length': 32, 'salt': 'U3VwM3JzZUNyM3RzYWx0', 'backend': <...Backend object at 0x7fd1c0220eb8>,
            'algorithm': <...SHA256 object at 0x7fd1b0232278>, 'iterations': 100000, 'kdf': <class '...PBKDF2HMAC'>}

        You can see when we call the method a second time with the same password and salt, we get the same Fernet key.

            >>> key, kd = ek.password_key('MySecurePass', salt=b'Sup3rseCr3tsalt')
            >>> key
            'rJ_g-lBT7pxeu4MVrhfi5rAv9yLbX5pTm6vkJj_Mezc='

        Now we can simply initialise the class with this key, and start encrypting/decrypting data:

            >>> enc = EncryptHelper(key)
            >>> mydata = enc.encrypt_str('hello')
            >>> mydata
            'gAAAAABdsJrpZvQAhAEwAGk2GPeJMUjUdp1FHAg42ncArvvQjqGztLslgexF7dKWbJ8bhYNt9MBzzT0WR_XEvl1j5Q95UOVTsQ=='
            >>> enc.decrypt_str(mydata)
            'hello'

        **Automatic salt generation:**

        While it's strongly recommend that you pass your own ``salt`` (at least 16 bytes recommended), for convenience this
        method will automatically generate a 16 byte salt and return it as part of the dict (second tuple item) returned.

        First, we generate a key from the password ``helloworld``

            >>> ek = EncryptHelper
            >>> key, kd = ek.password_key('helloworld')
            >>> key
            '6asAQ0qTQtmjw54RBR_RVmwsyv6EgTY_lcnVgJAVKCQ='
            >>> kd
            {'length': 32, 'salt': 'bDU5MzJaaEhnZ1htSmlQeg==', 'backend': <...Backend object at 0x7ff968053860>,
             'algorithm': <...SHA256 object at 0x7ff9685f6160>, 'iterations': 100000, 'kdf': <class '...PBKDF2HMAC'>}

        If we call **password_key** again with ``helloworld``, you'll notice it outputs a completely different key.
        This is because no salt was specified, so it simply generated yet another salt.

            >>> ek.password_key('helloworld')[0]
            'BfesIzfEPodtHSyPrpnkK0iDipHikaE7T1uuFFPnqmc='

        To actually get the same Fernet key back, we have to either:

         * Pass the entire ``kd`` dictionary as kwargs (safest option, contains all params used for generation)

            >>> ek.password_key('helloworld', **kd)[0]
            '6asAQ0qTQtmjw54RBR_RVmwsyv6EgTY_lcnVgJAVKCQ='

         * Pass the generated salt from the ``kd`` object, alongside our password.

            >>> ek.password_key('helloworld', salt=kd['salt'])[0]
            '6asAQ0qTQtmjw54RBR_RVmwsyv6EgTY_lcnVgJAVKCQ='


        """
        had_salt = salt is not None
        # If we were passed a salt, and it was a string, then check if it appears to be Base64
        # If the salt was Base64, then decode it into bytes.
        salt = base64.urlsafe_b64decode(salt) if had_salt and type(salt) is str and is_base64(salt) else salt
        # Generate a salt if one wasn't passed, and ensure that ``salt`` is bytes
        salt = random_str(16, chars=ALPHANUM) if not had_salt else salt
        salt = bytes(salt, 'utf-8') if type(salt) is not bytes else salt
        
        password = bytes(password, 'utf-8') if type(password) is not bytes else password
        
        # Default kwargs to be passed to the key deriv function if user doesn't override them.
        defaults = dict(length=32, salt=salt, backend=default_backend())
        
        if kdf is PBKDF2HMAC:
            defaults = {**defaults, **dict(algorithm=hashes.SHA256(), iterations=100000)}
        if kdf is Scrypt:
            defaults = {**defaults, **dict(n=2 ** 20, r=8, p=1)}
        # Merge our defaults with the users kwargs, initialise the KDF, then derive a Fernet key from the password
        kdf_args = {**defaults, **kwargs}
        k = kdf(**kdf_args)
        key = base64.urlsafe_b64encode(k.derive(password)).decode('utf-8')
        # To assist with future runs of this function, we return a dict containing the name of the KDF class used,
        # the salt (base64 encoded for easy handling), plus all of the KDF kwargs including our defaults
        kdf_args['salt'] = base64.urlsafe_b64encode(salt).decode('utf-8')
        kdf_args['kdf'] = kdf
        return key, kdf_args
    
    @classmethod
    def from_password(cls, password: Union[str, bytes], salt: Union[str, bytes], **settings):
        """
        Create an instance of :class:`.EncryptHelper` (or inheriting class) from a password derived
        Fernet key, instead of a pre-generated Fernet key.

        See :py:meth:`.password_key` for more detailed usage information.

        **Example**

            >>> enc = EncryptHelper.from_password('MySecurePass', salt=b'Sup3rseCr3tsalt')
            >>> d = enc.encrypt('hello')
            >>> enc.decrypt(d)
            'hello'


        :param password: A password to generate the key from, as ``str`` or ``bytes``
        :param     salt: The salt to use when generating the key, as ``str`` or ``bytes``
                         If ``salt`` is a string, it can also be passed in base64 format.

        """
        key, _ = cls.password_key(password=password, salt=salt, **settings)
        return cls(encrypt_key=key)
    
    @classmethod
    def from_file(cls, obj: Union[str, TextIOWrapper], **settings):
        """
        Create an instance of :class:`.EncryptHelper` (or inheriting class) using a Fernet key loaded from a file,
        or stream object.

            >>> enc = EncryptHelper.from_file('/home/john/fernet.key')
            >>> d = enc.encrypt('hello')
            >>> enc.decrypt(d)
            'hello'

        :param str obj: Load the key from the filename ``obj``
        :param TextIOWrapper obj: Load the key from the file/stream object ``obj`` using ``.read()``
        """
        if isinstance(obj, TextIOWrapper):
            return cls(encrypt_key=obj.read(), **settings)
        with open(str(obj)) as fp:
            return cls(encrypt_key=fp.read(), **settings)
    
    def get_fernet(self, key: Union[str, bytes] = None) -> Fernet:
        """
        Used internally for getting Fernet instance with auto-fallback to :py:attr:`.encrypt_key` and exception handling.

        :param str key: Base64 Fernet symmetric key for en/decrypting data. If empty, will fallback to :py:attr:`.encrypt_key`
        :raises EncryptKeyMissing: Either no key was passed, or something is wrong with the key.
        :return Fernet f: Instance of Fernet using passed ``key`` or self.encrypt_key for encryption.
        """
        if empty(key) and empty(self.encrypt_key):
            raise EncryptKeyMissing('No key argument passed, and ENCRYPT_KEY is empty. Cannot encrypt/decrypt.')
        
        key = self.encrypt_key if empty(key) else key
        try:
            f = Fernet(key)
            return f
        except (binascii.Error, ValueError):
            raise EncryptKeyMissing('The passed ``key`` or self.encrypt_key is not a valid Fernet key')
    
    def is_encrypted(self, data: Union[str, bytes], key: Union[str, bytes] = None) -> bool:
        """
        Returns True if the passed ``data`` appears to be encrypted. Can only verify encryption if the same ``key``
        that was used to encrypt the data is passed.

        :param str data: The data to check for encryption, either as a string or bytes
        :param str key:  Base64 encoded Fernet symmetric key for decrypting data. If empty, fallback to :py:attr:`.encrypt_key`
        :raises EncryptKeyMissing: Either no key was passed, or something is wrong with the key.
        :return bool is_encrypted: True if the data is encrypted, False if it's not encrypted or wrong key used.
        """
        f = self.get_fernet(key)
        
        # Convert the passed data into bytes before trying to decode it
        data = str(data).encode('utf-8') if type(data) != bytes else data
        
        # Attempt to extract the Fernet timestamp from the passed data. If exceptions are raised, then it's not encrypted.
        try:
            ts = f.extract_timestamp(data)
            log.debug(f'data was encrypted, token timestamp is {ts}')
            return True
        except (InvalidSignature, InvalidToken, binascii.Error) as e:
            log.debug('data is not encrypted? exception was: %s %s', type(e), str(e))
            return False
    
    def _crypt_str(self, direction: str, data: Union[str, bytes], key: Union[str, bytes] = None) -> str:
        """
        Used internally by :py:meth:`.encrypt_str` and :py:meth:`.decrypt_str`

        :param str direction: Either 'encrypt' or 'decrypt'
        :param str data:      The data to encrypt or decrypt as either a string or bytes
        :param str key:       Base64 encoded Fernet symmetric key for encrypting/decrypting data.
        :return str data_out: Either the encrypted data as a base64 encoded string, or decrypted data as a plain string.
        """
        if direction not in ['encrypt', 'decrypt']:
            raise ValueError('_crypt_str direction must be "encrypt" or "decrypt"')
        
        f = self.get_fernet(key)
        
        # Handle encryption/decryption of ``data``
        try:
            # If ``data`` isn't already bytes, cast to a string and convert it to bytes before encrypting/decrypting
            data = str(data).encode('utf-8') if type(data) != bytes else data
            out = f.encrypt(data) if direction == 'encrypt' else f.decrypt(data)
            return out.decode()  # Return encrypted/decrypted data as a string, not bytes.
        except Exception:
            strdat = str(data) if type(data) != bytes else str(data.decode())
            log.exception(f'An exception occurred while trying to {direction} the data starting with "{strdat:.4}"...')
            raise EncryptionError(f'Failed to {direction} data... An admin must check the logs.')
    
    def encrypt_str(self, data: Union[str, bytes], key: Union[str, bytes] = None) -> str:
        """
        Encrypts a piece of data ``data`` passed as a string or bytes using Fernet with the passed 32-bit symmetric
        encryption key ``key``. Outputs the encrypted data as a Base64 string for easy storage.

        The ``key`` cannot just be a random "password", it must be a 32-byte key encoded with URL Safe base64. Use the
        method :py:meth:`.generate_key` to create a Fernet compatible encryption key.

        Under the hood, Fernet uses AES-128 CBC to encrypt the data, with PKCS7 padding and HMAC_SHA256 authentication.

        If the ``key`` parameter isn't passed, or is empty (None / ""), then it will attempt to fall back to
        ``self.encrypt_key`` - if that's also empty, EncryptKeyMissing will be raised.

        :param str data:  The data to be encrypted, in the form of either a str or bytes.
        :param str key:   A Fernet encryption key (base64) to be used, if left blank will fall back to :py:attr:`.encrypt_key`
        :raises EncryptKeyMissing: Either no key was passed, or something is wrong with the key.
        :raises EncryptionError:   Something went wrong while attempting to encrypt the data
        :return str encrypted_data:   The encrypted version of the passed ``data`` as a base64 encoded string.
        """
        
        return self._crypt_str('encrypt', data, key)
    
    def decrypt_str(self, data: Union[str, bytes], key: Union[str, bytes] = None) -> str:
        """
        Decrypts ``data`` previously encrypted using :py:meth:`.encrypt_str` with the same Fernet compatible ``key``, and
        returns the decrypted version as a string.

        The ``key`` cannot just be a random "password", it must be a 32-byte key encoded with URL Safe base64. Use the
        method :py:meth:`.generate_key` to create a Fernet compatible encryption key.

        Under the hood, Fernet uses AES-128 CBC to encrypt the data, with PKCS7 padding and HMAC_SHA256 authentication.

        If the ``key`` parameter isn't passed, or is empty (None / ""), then it will attempt to fall back to
        :py:attr:`.encrypt_key` - if that's also empty, EncryptKeyMissing will be raised.

        :param str data:  The base64 encoded data to be decrypted, in the form of either a str or bytes.
        :param str key:   A Fernet encryption key (base64) for decryption, if blank, will fall back to :py:attr:`.encrypt_key`
        :raises EncryptKeyMissing: Either no key was passed, or something is wrong with the key.
        :raises EncryptionError:   Something went wrong while attempting to decrypt the data
        :return str decrypted_data:   The decrypted data as a string
        """
        return self._crypt_str('decrypt', data, key)

