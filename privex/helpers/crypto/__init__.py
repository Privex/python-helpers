"""
Cryptography related helper classes/functions

**Dependencies**

Requires the ``cryptography`` Python package:

.. code-block:: bash

    # Either install privex-helpers with the `crypto` extra
    pipenv install 'privex-helpers[crypto]'  # Using pipenv if you have it
    pip3 install 'privex-helpers[crypto]'    # Using standard pip3
    
    # Or manually install the `cryptography` library.
    pipenv install cryptography   # Using pipenv if you have it
    pip3 install cryptography     # Using standard pip3

**Summary**

Some of the most useful parts of this module include :py:mod:`.EncryptHelper` and :py:mod:`.KeyManager` - these
two components cover both symmetric (shared key) encryption/decryption, as well as asymmetric (public/private key)
keypair generation, signing, verification, as well as encryption/decryption with RSA.


 * :py:mod:`.EncryptHelper` - Painless symmetric encryption / decryption with AES-128
 * :py:mod:`.KeyManager` - Painless generation of asymmetric keys, with signing/verification and en/decryption support


**EncryptHelper - Painless symmetric encryption with AES-128**

:py:mod:`.EncryptHelper` is a wrapper class designed to make it extremely easy to use asymmetric encryption and
decryption. At it's core is the :py:class:`cryptography.fernet.Fernet` encryption system, and the class is
designed to make usage of Fernet as painless as possible.

**Basic Usage of EncryptHelper**::

    >>> from privex.helpers import EncryptHelper
    >>> key = EncryptHelper.generate_key() # Generates a 32-byte symmetric key, returned as a base64 encoded string
    >>> key_out = EncryptHelper.generate_key('my_key.txt')  # Generates and saves a key to my_key.txt, then returns it.
    >>> crypt = EncryptHelper(key)         # Create an instance of EncryptHelper, en/decrypting using ``key`` by default
    # Encrypts the string 'hello world' with AES-128 CBC using the instance's key, returned as a base64 string
    >>> enc = crypt.encrypt_str('hello world')
    >>> print(enc)
    gAAAAABc7ERTpu2D_uven3l-KtU_ewUC8YWKqXEbLEKrPKrKWT138MNq-I9RRtCD8UZLdQrcdM_IhUU6r8T16lQkoJZ-I7N39g==

    >>> crypt.is_encrypted(enc)       # Check if a string/bytes is encrypted (only works with data matching the key)
    True
    >>> data = crypt.decrypt_str(enc) # Decrypt the encrypted data using the same key, outputs as a string
    >>> print(data)
    hello world

**KeyManager - Painless generation of asymmetric keys, with signing/verification and en/decryption support**

While the :doc:`Cryptography <cryptography:index>` library is a brilliant library with many features, and a good
security track record - it's asymmetric key features require a ridiculous amount of scaffolding to make them usable
in a project.

That's where :py:mod:`.KeyManager` comes in.

Watch how simple it is to generate and save two types of asymmetric keys (RSA and Ed25519), and put them
to use with signatures and encryption.

First, let's generate a keypair and save it to disk. Without any algorithm related configuration options, it will
simply generate an RSA 2048 private and public key, and save them to the current working directory. For convenience,
it will also return the private and public key, so you can make use of them immediately after generating them.

    >>> rsa_priv, rsa_pub = KeyManager.output_keypair('id_rsa', 'id_rsa.pub')

Now, let's make an Ed25519 key - an algorithm quickly becoming common for SSH keys thanks to it's extremely small
public + private keys that could practically fit in an SMS message.

    >>> ed_priv, ed_pub = KeyManager.output_keypair('id_ed25519', 'id_ed25519.pub', alg='ed25519')

To use the signature / encryption functionality, first we have to load a key into :class:`.KeyManager`. There's
two ways you can do this. The first is simply passing the key as a string/bytes into the constructor. The second is
loading the key from disk (useful if you're using an existing key you have saved as a file).

Loading keys::

    # Example 1. Let's just pass our Ed25519 private key bytes straight into KeyManager.
    >>> km_ed = KeyManager(ed_priv)
    # Example 2. For the RSA key, we'll load it from a file
    >>> km_rsa = KeyManager.load_keyfile('id_rsa')

Now let's sign a message with each key, and then verify the message::

    # Sign the message "hello world" with both our Ed25519 and RSA private key.
    >>> msg = 'hello world'
    >>> sig_ed = km_ed.sign(msg)
    >>> sig_rsa = km_rsa.sign(msg)
    # Now we can verify the signature using the public keys (automatically re-generated from the private key)
    >>> km_ed.verify(signature=sig_ed, message=msg)
    True
    >>> km_rsa.verify(signature=sig_rsa, message=msg)
    True
    # If the signature was invalid, e.g. if we pass the RSA signature to the Ed25519 KeyManager...
    >>> km_ed.verify(sig_rsa, 'hello world')
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
            raise InvalidSignature
        cryptography.exceptions.InvalidSignature
    # So we can see that the signatures actually work :)

For RSA keys, we can also do encryption and decryption of small messages::

    >>> enc = km_rsa.encrypt(msg)
    # For easy storage/transmission, the encrypted data is base64 encoded. This ensures you can transmit the
    # encrypted message cleanly over email, HTTP etc. without the bytes getting garbled.
    >>> enc
    b'Sf1PC_TViZdA4lq7PwSnRTLbWX20vcCtkLyQWazE9EfM9_AIn6pNTHG...
    # Now when we run `decrypt`, we get back our original message of "hello world"
    # Note: decrypt supports both raw bytes as well as base64 encoded data and will automatically detect whether
    # or not it has to decode base64.
    >>> km_rsa.decrypt(enc)
    b'hello world'

 
**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
from privex.helpers.crypto.EncryptHelper import EncryptHelper
from privex.helpers.crypto.base import is_base64, auto_b64decode
from privex.helpers.crypto.KeyManager import KeyManager, Format
