import base64
import binascii
import logging
from io import BufferedWriter, TextIOWrapper
from typing import Union, Tuple, Optional

import cryptography.exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKeyWithSerialization, RSAPublicKeyWithSerialization, \
    RSAPublicKey, RSAPrivateKey
from cryptography.hazmat.primitives.hashes import HashAlgorithm
from cryptography.hazmat.primitives.serialization import PublicFormat, PrivateFormat, Encoding, load_ssh_public_key, \
    load_pem_public_key, load_pem_private_key, load_der_private_key, load_der_public_key
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

from privex.helpers.common import byteify, stringify, empty
from privex.helpers.crypto.base import is_base64, auto_b64decode
from privex.helpers.exceptions import InvalidFormat, EncryptionError

log = logging.getLogger(__name__)

Text = Union[str, bytes]


class Format:
    """
    Key formatting / encoding helper for the :doc:`Cryptography <cryptography:index>` module
    
    Used by :class:`.KeyManager` to simplify serialization of public/private keys.
    """
    public_formats = {
        'subject':           PublicFormat.SubjectPublicKeyInfo,
        'pkcs1':             PublicFormat.PKCS1,
        'ssh':               PublicFormat.OpenSSH,
        'raw':               PublicFormat.Raw,
        'compressedpoint':   PublicFormat.CompressedPoint,
        'uncompressedpoint': PublicFormat.UncompressedPoint
    }
    private_formats = {
        'openssl': PrivateFormat.TraditionalOpenSSL,
        'pkcs1':   PrivateFormat.TraditionalOpenSSL,
        'pkcs8':   PrivateFormat.PKCS8,
        'raw':     PrivateFormat.Raw
    }
    encodings = {
        'pem':  Encoding.PEM,
        'der':  Encoding.DER,
        'ssh':  Encoding.OpenSSH,
        'raw':  Encoding.Raw,
        'x962': Encoding.X962
    }
    private_format: PrivateFormat
    public_format: PublicFormat
    public_encoding: Encoding
    private_encoding: Encoding

    def __init__(self, private_format, private_encoding, public_format='ssh', public_encoding='ssh'):
        self.private_format = self.get_format('private_format', private_format)
        self.public_format = self.get_format('public_format', public_format)
        self.private_encoding = self.get_format('encoding', private_encoding)
        self.public_encoding = self.get_format('encoding', public_encoding)

    @classmethod
    def get_format(cls, fmtype, key) -> Union[Encoding, PublicFormat, PrivateFormat]:
        if fmtype == 'encoding':
            f = cls.encodings
            if key not in f:
                raise InvalidFormat(f'The encoding type "{key}" is not a valid type. Choices: {f.keys()}')
            return f[key]
    
        if fmtype == 'public_format':
            f = cls.public_formats
            if key not in f:
                raise InvalidFormat(f'The public format type "{key}" is not a valid type. Choices: {f.keys()}')
            return f[key]
        if fmtype == 'private_format':
            f = cls.private_formats
            if key not in f:
                raise InvalidFormat(f'The private format type "{key}" is not a valid type. Choices: {f.keys()}')
            return f[key]


class KeyManager:
    """
    Asymmetric key handling class - Generate, save, and load asymmetric keys, with signatures + encryption made easy.
    
    A wrapper around :py:mod:`cryptography.hazmat.primitives.asymmetric` to make generation, saving, loading,
    AND usage of asymmetric keys easy.
    
    **Basic Usage**
    
    Using :py:meth:`.output_keypair` - you can generate a key pair, and output it at the same time::
    
        >>> priv, pub = KeyManager.output_keypair('id_rsa', 'id_rsa.pub')
        >>> pub
        b'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDbzCL+Dn8B9jS404mETt8fb6+TJek1afFthSBi2qZ0iL8dbv/Go0ig...'
    
    If you don't want to output the key pair to a file, you can also just generate one and have the private/public
    keys purely returned as bytes::
    
    
        >>> priv, pub = KeyManager.generate_keypair(alg='ed25519')
        >>> priv
        b'-----BEGIN PRIVATE KEY-----
        MC4CAQAwBQYDK2VwB.....T2YxW/Xkz3PkMHrrYBvI0LbUPky
        -----END PRIVATE KEY-----'
        >>> pub
        b'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICJ9OK6v2UGfCgWxzGdPlCQIps+lffLTWwuMLPdqfco6'
    
    
    **Loading a key for signature/encryption operations**
    
    You can load a private or public key directly from the string/bytes returned by :py:meth:`.generate_keypair`
    like so::
    
        >>> km = KeyManager(priv)
    
    Alternatively, you can load a key straight from disk using :py:meth:`.load_keyfile` - which will automatically
    detect the asymmetric algorithm, encoding/output format, and key type (public/private) and
    return a :class:`.KeyManager` instance::
    
        >>> km = KeyManager.load_keyfile('id_rsa.pub')
        
    **Automatic public key generation**
    
    If you load a **private key**, then the constructor will automatically generate the matching **public key** for
    you, so that you can use all signature/encryption methods available for your key algorithm.
    
    If you load a **public key**, then you will only be able to use methods which are available to public keys, such
    as :py:meth:`.verify` and :py:meth:`.encrypt` - you will NOT be able to use :py:meth:`.sign` or :py:meth:`.decrypt`
    
    **Manually accessing the public/private key class instances**
    
    If you need to access the raw cryptography PublicKey/PrivateKey instances, you can access them via the two
    attributes :py:attr:`.public_key` and :py:attr:`.private_key` after creating a KeyManager instance::
    
        >>> km.public_key
        <cryptography.hazmat.backends.openssl.rsa._RSAPublicKey object at 0x7f953848c438>
        >>> km.private_key
        <cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey object at 0x7f95381c1ef0>
    
    **Signing, verification, and en/decryption**
    
    Once you have a :class:`.KeyManager` instance, you can now use the signing, verification, and en/decryption
    methods using the loaded key.
    
    Most key algorithms support signing and verification, which can be done using :py:meth:`.sign`
    and :py:meth:`.verify` respectively.
    
    Sensible values for things like padding/hash algorithms are set by default, so you can simply call :py:meth:`.sign`
    with just a message, and :py:meth:`.verify` with just the signature + message::
    
        >>> sig = km.sign('hello world')
        >>> km.verify(signature=sig, message='hello world')  # Raises InvalidSignature if it was invalid
        True
    
    With RSA keys, you can also :py:meth:`.encrypt` using the public key, and :py:meth:`.decrypt` using
    the private key::
    
        >>> msg = km.encrypt('my secret message')
        >>> km.decrypt(msg)
        b'my secret message'
    
    """
    backend = default_backend()
    
    default_gen = dict(
        rsa=dict(key_size=2048, public_exponent=65537, backend=backend),
        ecdsa=dict(curve=ec.SECP384R1(), backend=backend),
        ed25519=dict(),
    )
    """A map of key algorithms to their generator's default kwargs"""

    Format = Format
    """A class alias, allowing for access to the Format class via a class attribute"""
    default_formats = {
        'rsa': dict(private_format='pkcs8', private_encoding='pem'),
        'ecdsa': dict(private_format='pkcs8', private_encoding='pem'),
        'ed25519': dict(private_format='pkcs8', private_encoding='pem'),
    }
    """Default :class:`.Format` formatting options for serialising each key algorithm"""
    
    generators = {
        'rsa': (rsa.generate_private_key, dict(encryption_algorithm=serialization.NoEncryption())),
        'ecdsa': (ec.generate_private_key, dict(encryption_algorithm=serialization.NoEncryption())),
        'ed25519': (Ed25519PrivateKey.generate, dict(encryption_algorithm=serialization.NoEncryption())),
    }
    """
    Maps each key algorithm to a tuple containing the algorithm's generation function, and any extra kwargs
    needed for generating a private key
    """

    # noinspection PyProtectedMember
    curves = ec._CURVE_TYPES
    """An alias for Cryptography's map of string curve names (e.g. ``secp521r1``) to their respective classes"""
    
    private_key_types = Union[
        RSAPrivateKeyWithSerialization, ec.EllipticCurvePrivateKeyWithSerialization,
        Ed25519PrivateKey
    ]
    """
    The cryptography library doesn't have a standard parent type for private keys, so we need a Union to hold
    the various private key types for return types, type/instance comparison etc.
    """
    public_key_types = Union[
        RSAPublicKeyWithSerialization, ec.EllipticCurvePublicKeyWithSerialization,
        Ed25519PublicKey
    ]
    """Same as :py:attr:`.private_key_types` but for public key types."""
    
    combined_key_types = Union[private_key_types, public_key_types]
    """A Union which just combines :py:attr:`.private_key_types` and :py:attr:`.public_key_types` into one type."""
    
    raw_pub_types = public_key_types.__args__
    """This extracts the actual class types from the Union[] for isinstance() checks"""
    raw_priv_types = private_key_types.__args__
    """This extracts the actual class types from the Union[] for isinstance() checks"""

    public_key: Optional[public_key_types]
    """
    When the class is initialised, this instance attribute holds a cryptography public key class instance, or None
    if we don't have a public key available.
    """
    
    private_key: Optional[private_key_types]
    """
    When the class is initialised, this instance attribute holds a cryptography private key class instance, or None
    if we don't have a private key available.
    """
    
    type_name_map = {
        RSAPublicKey: 'rsa', RSAPrivateKey: 'rsa',
        RSAPublicKeyWithSerialization: 'rsa', RSAPrivateKeyWithSerialization: 'rsa',
        Ed25519PrivateKey: 'ed25519', Ed25519PublicKey: 'ed25519',
        ec.EllipticCurvePublicKey: 'ecdsa', ec.EllipticCurvePrivateKey: 'ecdsa',
        ec.EllipticCurvePrivateKeyWithSerialization: 'ecdsa', ec.EllipticCurvePublicKeyWithSerialization: 'ecdsa',
    }
    """Maps public/private key types to their associated algorithm name for type/instance identification"""
    
    def __init__(self, key: Union[Text, private_key_types, public_key_types], password: Text = None):
        """
        Create an instance of :class:`.KeyManager` using the public/private key data ``key``
        
        If you want to load the key from a file instead of passing it's data / key class instance, then
        you should use :py:meth:`.load_keyfile` instead to create the class instance.
        
        You do NOT need to initialize this class if you're simply using the class methods / static methods such as
        :py:meth:`.generate_keypair` or :py:meth:`.load_key` - only to use the normal instance methods which
        require a loaded public/private key, such as :py:meth:`.sign`
        
        :param key: The public/private key data, as either a string, bytes, or one of the various private key class
                    instances or public key class instances
                    (see :py:attr:`.public_key_types` and :py:attr:`.private_key_types`)
         
        :param str|bytes password: If your key data is encrypted, pass the password in this argument to decrypt it.
        """
        self.public_key, self.private_key = None, None
        k = key
        # If the key is a string, or bytes, then de-serialise the key into an object
        if type(key) in [str, bytes]:
            k, ktype = self.load_key(key, password=password)
        else:   # Otherwise, figure out whether it's a private key, or a public key.
            if isinstance(key, self.raw_priv_types):
                ktype = 'private'
            elif isinstance(key, self.raw_pub_types):
                ktype = 'public'
            else:
                raise InvalidFormat('Could not identify key type...')
        
        if ktype == 'public':
            self.public_key = k
        else:
            self.private_key = k
            self.public_key = k.public_key()
    
    def sign(self, message: Text, pad=None, hashing: HashAlgorithm = hashes.SHA256()) -> bytes:
        """
        Generate a signature for a given message using the loaded :py:attr:`.private_key`. The signature is
        Base64 encoded to allow for easy storage and transmission of the signature, and can later be verified
        by :py:meth:`.verify` using :py:attr:`.public_key`
        

        
            >>> km = KeyManager.load_keyfile('id_rsa')
            >>> sig = km.sign('hello world')        # Sign 'hello world' using the id_rsa private key
            >>> try:
            ...     km.verify(sig, 'hello world')   # Verify it using the public key (automatically generated)
            ...     print('Signature is valid')
            >>> except cryptography.exceptions.InvalidSignature:
            ...     print('Signature IS NOT VALID!')
        
        Alternatively, you can manually run :py:func:`base64.urlsafe_b64decode` to decode the signature back into
        raw bytes, then you can verify it using the ``verify`` method of a ``cryptography`` public key instance,
        such as :class:`.Ed25519PublicKey` or :class:`.RSAPublicKey`
        
        :param str|bytes message: The message to verify, e.g. ``hello world``
        :param pad: (RSA only) An instance of a cryptography padding class, e.g. :class:`.padding.PSS`
        :param HashAlgorithm hashing: (ECDSA/RSA) Use this hashing method for padding/signatures
        :raises cryptography.exceptions.InvalidSignature: When the signature does not match the message
        :return bytes sig: A base64 urlsafe encoded signature
        """
        message = byteify(message)
        if isinstance(self.private_key, Ed25519PrivateKey):
            return base64.urlsafe_b64encode(self.private_key.sign(data=message))
        
        if isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            return base64.urlsafe_b64encode(self.private_key.sign(message, ec.ECDSA(hashing)))
        
        # Fallback: RSA with padding
        if not pad:
            pad = padding.PSS(mgf=padding.MGF1(hashing), salt_length=padding.PSS.MAX_LENGTH)
        return base64.urlsafe_b64encode(self.private_key.sign(data=message, padding=pad, algorithm=hashing))
    
    def verify(self, signature: Text, message: Text, pad=None, hashing: HashAlgorithm = hashes.SHA256()) -> bool:
        """
        Verify a signature against a given message using an asymmetric public key.
        
            >>> km = KeyManager.load_keyfile('id_rsa')
            >>> sig = km.sign('hello world')    # Sign 'hello world' using the id_rsa private key
            >>> try:
            ...     km.verify(sig, 'hello world')   # Verify it using the public key (automatically generated)
            ...     print('Signature is valid')
            >>> except cryptography.exceptions.InvalidSignature:
            ...     print('Signature IS NOT VALID!')
        
        :param str|bytes signature: The binary, or base64 urlsafe encoded signature to check ``message`` against
        :param str|bytes message: The message to verify, e.g. ``hello world``
        :param pad: (RSA only) An instance of a cryptography padding class, e.g. :class:`.padding.PSS`
        :param HashAlgorithm hashing: (ECDSA/RSA) Use this hashing method for padding/signatures
        :raises cryptography.exceptions.InvalidSignature: When the signature does not match the message
        :return bool is_valid: ``True`` if signature is valid, otherwise raises InvalidSignature.
        """
        signature, message = auto_b64decode(signature), byteify(message)
        
        if isinstance(self.public_key, Ed25519PublicKey):
            return self.public_key.verify(signature=signature, data=message)
        
        if isinstance(self.public_key, ec.EllipticCurvePublicKey):
            return self.public_key.verify(signature=signature, data=message, signature_algorithm=ec.ECDSA(hashing))
        
        # Fallback: RSA with padding
        if not pad:
            pad = padding.PSS(mgf=padding.MGF1(hashing), salt_length=padding.PSS.MAX_LENGTH)
        self.public_key.verify(signature=signature, data=message, padding=pad, algorithm=hashing)
        return True
    
    def encrypt(self, message: Text, pad=None, hashing: HashAlgorithm = hashes.SHA256()) -> bytes:
        """
        Encrypt a message using the loaded :py:attr:`.public_key` - returns the ciphertext as base64 encoded
        bytes.
        
        NOTE: **Only works for RSA public keys**

        :param str|bytes message: The message to encrypt, e.g. ``hello world``
        :param pad: (RSA only) An instance of a cryptography padding class, e.g. :class:`.padding.PSS`
        :param HashAlgorithm hashing: (ECDSA/RSA) Use this hashing method for padding/signatures
        :return bytes ciphertext: The encrypted version of ``message`` - encoded with Base64 for easy storage/transport
        """
        message = byteify(message)
        
        if not isinstance(self.public_key, (RSAPublicKey, RSAPublicKeyWithSerialization)):
            raise InvalidFormat('KeyManager.encrypt is only supported for RSA keys.')
        if not pad:
            pad = padding.OAEP(mgf=padding.MGF1(hashing), algorithm=hashing, label=None)
        return base64.urlsafe_b64encode(self.public_key.encrypt(plaintext=message, padding=pad))

    def decrypt(self, message: Text, pad=None, hashing: HashAlgorithm = hashes.SHA256()) -> bytes:
        """
        Decrypt a message using the loaded :py:attr:`.private_key` - returns the decrypted message as bytes.
        
        NOTE: **Only works for RSA private keys**
        
        :param str|bytes message: The ciphertext to decrypt, as base64 or raw bytes
        :param pad: (RSA only) An instance of a cryptography padding class, e.g. :class:`.padding.PSS`
        :param HashAlgorithm hashing: (ECDSA/RSA) Use this hashing method for padding/signatures
        :return bytes decoded: The decrypted version of ``message`` as bytes
        """
        message = auto_b64decode(message)
    
        if not isinstance(self.private_key, (RSAPrivateKey, RSAPrivateKeyWithSerialization)):
            raise InvalidFormat('KeyManager.decrypt is only supported for RSA keys.')
        if not pad:
            pad = padding.OAEP(mgf=padding.MGF1(hashing), algorithm=hashing, label=None)
        return self.private_key.decrypt(ciphertext=message, padding=pad)
    
    @classmethod
    def identify_algorithm(cls, key: combined_key_types) -> str:
        """
        Identifies a cryptography public/private key instance, such as :class:`.RSAPrivateKey`
        and returns the algorithm name that can be used with other KeyManager methods,
        e.g. ``'rsa'`` or ``'ed25519'``
        
        
        Example::
            
            >>> priv, pub = KeyManager.generate_keypair_raw(alg='ecdsa', curve=ec.SECP521R1)
            >>> KeyManager.identify_algorithm(priv)
            'ecdsa'
            >>> priv, pub = KeyManager.generate_keypair_raw()
            >>> KeyManager.identify_algorithm(priv)
            'rsa'
            >>> KeyManager.identify_algorithm(pub)
            'rsa'


        :param combined_key_types key: A cryptography public/private key instance
        :return str algorithm: The name of the algorithm used by this key
        """
        for ktype, kname in cls.type_name_map.items():
            if isinstance(key, ktype):
                return kname
        raise InvalidFormat('Could not identify key type...')

    def export_public(self, **kwargs) -> bytes:
        """
        Serialize the cryptography public key instance loaded into :class:`.KeyManager` into storable bytes.
        
        This method works whether you've instantiated KeyManager with the public key directly, or the private key,
        as the public key is automatically interpolated from the private key by :py:meth:`.__init__`

        Example::
        
            >>> km = KeyManager.load_keyfile('id_ed25519.pub')
            >>> km.export_public()
            b'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA6vtKgeNSBERSY1xmr47Ve3uyRALxPR+qOeFeUHrUaf'
            
        :keyword dict format: Override some or all of the default format/encoding for the keys.
                              Dict Keys: private_format,public_format,private_encoding,public_encoding
        :keyword Format format: If passed a :class:`.Format` instance, then this instance will be used for serialization
                                instead of merging defaults from :py:attr:`.default_formats`
        :return bytes key: The serialized key.
        """
        if empty(self.public_key):
            raise EncryptionError('Cannot export public key as self.public_key is missing!')
        # alg = self.identify_algorithm(self.public_key)
        return self.export_key(self.public_key, **kwargs)

    def export_private(self, **kwargs) -> bytes:
        """
        Serialize the cryptography private key instance loaded into :class:`.KeyManager` into storable bytes.
        
        This method requires that you've instantiated KeyManager with the private key. It will raise a
        :class:`.EncryptionError` exception if the :py:attr:`.private_key` instance attribute is empty.
        
        Example::

            >>> km = KeyManager.load_keyfile('id_ed25519')
            >>> print(km.export_private().decode())
            -----BEGIN PRIVATE KEY-----
            MC4CAQAwBQYDK2VwBCIEIOeLS2XOcQz11VUnzh6KIZaNtT10YfzHv779zjm95XSy
            -----END PRIVATE KEY-----


        :keyword dict format: Override some or all of the default format/encoding for the keys.
                              Dict Keys: private_format,public_format,private_encoding,public_encoding
        :keyword Format format: If passed a :class:`.Format` instance, then this instance will be used for serialization
                                instead of merging defaults from :py:attr:`.default_formats`
        :return bytes key: The serialized key.
        """
        if empty(self.private_key):
            raise EncryptionError('Cannot export private key as self.private_key is missing!')
        # alg = self.identify_algorithm(self.private_key)
        return self.export_key(self.private_key, **kwargs)
    
    @staticmethod
    def _load_der_key(data: bytes, password: Optional[bytes] = None):
        """Attempt to de-serialise a DER formatted private/public key. Raises :class:`.InvalidFormat` if it fails."""
        try:
            key = load_der_private_key(data, password=password, backend=default_backend())
            return key, 'private'
        except (ValueError, TypeError, cryptography.exceptions.UnsupportedAlgorithm):
            pass
        try:
            key = load_der_public_key(data, backend=default_backend())
            return key, 'public'
        except (ValueError, TypeError, cryptography.exceptions.UnsupportedAlgorithm):
            raise InvalidFormat('Not a DER key, or is corrupted...')
    
    @staticmethod
    def _load_pkcs12_key(data: bytes, password: Optional[bytes] = None):
        """Attempt to de-serialise PKCS12 key data. Raises :class:`.InvalidFormat` if it fails."""
        try:
            key, cert, ad_certs = load_key_and_certificates(data, password=password, backend=default_backend())
            return key, 'private', cert, ad_certs
        except (ValueError, TypeError, cryptography.exceptions.UnsupportedAlgorithm):
            raise InvalidFormat('Not a PKCS12 key, or is corrupted...')
    
    @classmethod
    def load_key(cls, data: Text, password: bytes = None) -> Tuple[combined_key_types, str]:
        """
        Load a private/public key from a string or bytes ``data`` containing the key in some format, such as PEM
        or OpenSSH. Use :py:meth:`.load_keyfile` to load a key from a file + auto-instantiate KeyManager with it.
        
        **Example:**
        
            >>> key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG3v6guHpI/j7AIl3F/EWMSReX8fH8MOSq1bC3ZuEjjC'
            >>> KeyManager.load_key(key)
            (<cryptography.hazmat.backends.openssl.ed25519._Ed25519PublicKey object at 0x7fa118289ba8>, 'public')
        
        
        :param str|bytes data: The public/private key data, as a string or bytes
        :param str|bytes password: If your key data is encrypted, pass the password in this argument to decrypt it.
        :raises InvalidFormat: When the key could not be identified, is not supported, or is corrupted
        :return tuple key_data: A tuple containing an instance of the key, and a string ``public`` or ``private``
                                Example: ``(<_Ed25519PublicKey object>, 'public')``
        """
        data = stringify(data)
        password = None if not password else byteify(password)
        try:
            if data[0:4] == 'ssh-' or data[0:6] == 'ecdsa-':
                return load_ssh_public_key(byteify(data), backend=default_backend()), 'public'
            if '-----BEGIN PUBLIC' in data:
                return load_pem_public_key(byteify(data), backend=default_backend()), 'public'
            if '-----BEGIN PRIVATE' in data:
                return load_pem_private_key(byteify(data), password=password, backend=default_backend()), 'private'
        except binascii.Error as e:
            raise InvalidFormat(f'Error while decoding key - possibly corrupted base64 encoding. '
                                f'Original exception: {type(e)} {str(e)}')
        except ValueError as e:
            raise InvalidFormat(f'Error while decoding key - key may be corrupted. '
                                f'Original exception: {type(e)} {str(e)}')
        ##
        # If we couldn't identify the key as PEM or OpenSSH, then fallback to attempting to load it as DER / PKCS12
        ##
        data = byteify(data)
        
        try:   # Try loading the key as a DER key
            key, ktype = cls._load_der_key(data=data, password=password)
            return key, ktype
        except InvalidFormat:
            pass

        try:   # Try loading the key as PKCS12
            key, ktype, _, _ = cls._load_pkcs12_key(data=data, password=password)
            return key, ktype
        except InvalidFormat:
            pass
        
        # Otherwise we have no idea what to do with this key. Time to give up.
        raise InvalidFormat('Unknown key format...')

    @classmethod
    def load_keyfile(cls, filename: Text, password: Text = None):
        """
        Returns an instance of :class:`.KeyManager` using a public/private key loaded from disk, instead of
        from string/bytes key data.
        
        Example::
        
            >>> km = KeyManager.load_keyfile('id_rsa')
            >>> d = km.encrypt('hello world')
            >>> km.decrypt(d)
            b'hello world'
        
        
        :param str|bytes filename: The file location where the key is stored
        :param str|bytes password: If the key is encrypted, specify the password to decrypt it
        :raises InvalidFormat: When the key could not be identified, is not supported, or is corrupted
        :raises FileNotFoundError: The given ``filename`` couldn't be found.
        :return KeyManager cls: An instance of :class:`.KeyManager` (or child class) initialised with the key
        """
        filename = stringify(filename)
        with open(filename, 'r') as fp:
            data = fp.read()
        return cls(key=data, password=password)
    
    @classmethod
    def generate_keypair_raw(cls, alg='rsa', **kwargs) -> Tuple[private_key_types, public_key_types]:
        """
        Generate a key pair, returning private + public key instances from the cryptography module.
        
        Example::
        
            >>> priv, pub = KeyManager.generate_keypair_raw(alg='rsa', key_size=1024)
            >>> priv.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.PKCS8)
            b'-----BEGIN PRIVATE KEY-----\\nMIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAMjkl
             ...Pw6eZGFwBEYY\\n-----END PRIVATE KEY-----\\n'
             
            >>> priv, pub = KeyManager.generate_keypair_raw(alg='ecdsa', curve=ec.SECP521R1)
            >>> pub.public_bytes(encoding=Encoding.OpenSSH, format=PublicFormat.OpenSSH)
            b'ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1...dJCxguBQnb1hL6aDH4fHCjpy6A=='
        
        
        
        :param str alg: The algorithm to generate a key for, e.g. ``'rsa'``
        :param kwargs: All kwargs are forwarded to the matching generator in :py:attr:`.generators`
        :return tuple keys: A tuple containing a private key instance, and public key instance
        """
        gen_args = {**cls.default_gen[alg], **kwargs}
        gen = cls.generators[alg][0]
    
        priv = gen(**gen_args)
        pub = priv.public_key()
        return priv, pub
    
    @classmethod
    def generate_keypair(cls, alg='rsa', **kwargs) -> Tuple[bytes, bytes]:
        """
        Generate a key pair, returning private + public key as serialized bytes based on :py:attr:`.default_formats`
        and the kwarg ``format`` if it's present.
        
        By default, private keys are generally returned in PKCS8 format with PEM encoding, while
        public keys are OpenSSH format and OpenSSH encoding.
        
        Example::
        
            >>> priv, pub = KeyManager.generate_keypair(alg='rsa', key_size=2048)
            >>> priv
            b'-----BEGIN PRIVATE KEY-----\\nMIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAMjkl
             ...Pw6eZGFwBEYY\\n-----END PRIVATE KEY-----\\n'
             
            >>> priv, pub = KeyManager.generate_keypair(alg='ecdsa', curve=ec.SECP521R1)
            >>> pub
            b'ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1...dJCxguBQnb1hL6aDH4fHCjpy6A=='
        
        
        To override the formatting/encoding::
        
            >>> priv, pub = KeyManager.generate_keypair(
            ...     alg='ecdsa', format=dict(private_format='openssl', private_encoding='der')
            ... )
            >>> priv
            b'0\\x81\\xa4\\x02\\x01\\x01\\x040u\\x1e\\x8cI\\xcd\\xfa\\xc8\\x97\\x83\\xf8\\xed\\x1f\\xe5\\xbd...'
        
        
        :param str alg: The algorithm to generate a key for, e.g. ``'rsa'``
        :param kwargs: All kwargs are forwarded to the matching generator in :py:attr:`.generators`
        :keyword int key_size: (for `rsa` and similar algorithms) Number of bits for the RSA key. Minimum of 512 bits.
        :keyword dict format: Override some or all of the default format/encoding for the keys.
                      Dict Keys: private_format,public_format,private_encoding,public_encoding
        :return:
        """
        # noinspection PyTypeChecker
        fmt = kwargs.pop('format') if 'format' in kwargs else {}
        
        priv, pub = cls.generate_keypair_raw(alg=alg, **kwargs)

        s_priv = cls.export_key(priv, format=fmt, alg=alg)
        s_pub = cls.export_key(pub, format=fmt, alg=alg)

        return s_priv, s_pub

    @classmethod
    def export_key(cls, key: combined_key_types, **kwargs) -> bytes:
        """
        Export/serialize a given public/private key object as bytes.
        
        Uses the default formatting arguments for the detected algorithm from :py:meth:`.identify_algorithm`, but
        you can also force it to treat it as a certain algorithm by passing ``alg``
        
        Uses default formatting options by looking up the algorithm in :py:attr:`.default_formats`
        
        Uses the private key serialization arguments for the detected algorithm out of :py:attr:`.generators`
        
        Example::
            
            >>> priv, pub = KeyManager.generate_keypair_raw('ed25519')
            >>> key = KeyManager.export_key(pub)
            >>> print(key.decode())
            -----BEGIN PRIVATE KEY-----
            MC4CAQAwBQYDK2VwBCIEIOeLS2XOcQz11VUnzh6KIZaNtT10YfzHv779zjm95XSy
            -----END PRIVATE KEY-----
        
        :param str alg: An algorithm name as a string, e.g. ``rsa`` or ``ed25519``
        :param combined_key_types key: An instance of a public/private key type listed in :py:attr:`.combined_key_types`
        :keyword dict format: Override some or all of the default format/encoding for the keys.
                              Dict Keys: private_format,public_format,private_encoding,public_encoding
        :keyword Format format: If passed a :class:`.Format` instance, then this instance will be used for serialization
                                instead of merging defaults from :py:attr:`.default_formats`
        :keyword str alg: Use this algorithm name e.g. ``'rsa'`` instead of detecting using :meth:`.identify_algorithm`
        :return bytes key: The serialized key.
        """
        alg = kwargs.pop('alg', cls.identify_algorithm(key))
        fmt_args = cls.default_formats[alg]
        priv_args = cls.generators[alg][1]
        _fmt = kwargs.get('format', {})
        fmt: Format = _fmt if isinstance(_fmt, Format) else Format(**{**fmt_args, **_fmt})

        if isinstance(key, cls.raw_priv_types):
            return key.private_bytes(encoding=fmt.private_encoding, format=fmt.private_format, **priv_args)
        elif isinstance(key, cls.raw_pub_types):
            return key.public_bytes(encoding=fmt.public_encoding, format=fmt.public_format)
        else:
            raise InvalidFormat(f'export_key expected a cryptography private/public key instance. got: {type(key)}')

    @classmethod
    def output_keypair(cls, priv: Union[str, BufferedWriter], pub: Union[str, TextIOWrapper],
                       *args, **kwargs) -> Tuple[bytes, bytes]:
        """
        Similar to :py:meth:`.generate_keypair` - except this also writes the private key and public key to the
        file locations and/or byte streams specified in the first two arguments (``priv`` and ``pub``)
        
        **Example**
        
        Generate a 4096-bit RSA key pair, and output the private key to the file ``id_rsa`` ,
        and the public key to ``id_rsa.pub``.
        
        The generated keypair is also returned as a tuple pair (bytes) containing the private and public key::
        
            >>> priv, pub = KeyManager.output_keypair('id_rsa', 'id_rsa.pub', alg='rsa', key_size=4096)
        
        
        :param str|BufferedWriter priv: File location to save private key, or writable byte stream
        :param str|BufferedWriter pub: File location to save public key, or writable byte stream
        :param args: All additional args are forwarded to :py:meth:`.generate_keypair`
        :param kwargs: All kwargs are forwarded to :py:meth:`.generate_keypair`
        
        """
        privkey, pubkey = cls.generate_keypair(*args, **kwargs)
        
        if isinstance(priv, BufferedWriter):
            priv.write(privkey)
        else:
            with open(str(priv), 'wb') as fp:
                fp.write(privkey)

        if isinstance(pub, BufferedWriter):
            pub.write(pubkey)
        else:
            with open(str(pub), 'wb') as fp:
                fp.write(pubkey)
        
        return privkey, pubkey
