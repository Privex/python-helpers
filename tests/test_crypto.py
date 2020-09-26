"""
Test cases for the :py:mod:`privex.helpers.crypto` module

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import base64
import warnings
from os import path
from os.path import join
from tempfile import TemporaryDirectory
from tests.base import PrivexBaseCase

from privex.helpers import Mocker, stringify, plugin
MOD_LOAD_ERR = f"WARNING: `cryptography` package not installed (or other error loading privex.helpers.crypto). " \
               f"Skipping test case {__name__}."

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    warnings.warn('WARNING: Could not import pytest. You should run "pip3 install pytest" to ensure tests work best')
    from privex.helpers.mockers import pytest
    HAS_PYTEST = False

if plugin.HAS_CRYPTO:
    try:
        # noinspection PyUnresolvedReferences
        from privex.helpers import EncryptHelper, EncryptKeyMissing, EncryptionError, InvalidFormat, stringify
        # noinspection PyUnresolvedReferences
        from privex.helpers.crypto.KeyManager import KeyManager
    except ImportError:
        pytest.skip(MOD_LOAD_ERR, allow_module_level=True)
        if not HAS_PYTEST: raise ImportError(f"(ImportError in {__file__}) {MOD_LOAD_ERR}")
else:
    pytest.skip(MOD_LOAD_ERR, allow_module_level=True)
    if not HAS_PYTEST: raise ImportError("(plugin.HAS_CRYPTO = False) " + MOD_LOAD_ERR)


class CryptoBaseCase(PrivexBaseCase):
    fake_b64_key = stringify(base64.urlsafe_b64encode(b'not a key'))

    @staticmethod
    def _sign_verify(priv, pub):
        """Helper method to avoid duplicating sign+verify code for every algorithm"""
        km = KeyManager(priv)  # KeyManager with private key (public key interpolated from private key)
        km_pub = KeyManager(pub)  # KeyManager with only public key
        sig = km.sign('hello world')  # Sign 'hello world' with the private key
        # Verify the signature, these methods will raise InvalidSignature if it doesn't verify.
        km_pub.verify(signature=sig, message='hello world')  # Verify with pubkey-only instance
        km.verify(signature=sig, message='hello world')  # Verify with privkey-only instance


class TestEncryptHelper(CryptoBaseCase):
    """Test :py:class:`.EncryptHelper` key generation, encryption, decryption and more"""
    txt = 'This is a test.'

    def test_generate_key_enc_dec(self):
        """Test :py:meth:`.EncryptHelper.generate_key` key works for encryption and decryption"""
        key = EncryptHelper.generate_key()
        self.assertIs(type(key), str)
        eh = EncryptHelper(key)
        
        enc = eh.encrypt_str(self.txt)

        self.assertIs(type(enc), str)
        self.assertNotEqual(enc, self.txt)

        dec = eh.decrypt_str(enc)
        self.assertEqual(dec, self.txt)

    def test_invalid_key_decrypt(self):
        """Test that decrypt_str fails when using the wrong key"""
        eh = EncryptHelper(EncryptHelper.generate_key())
        enc = eh.encrypt_str(self.txt)
        # Make sure we can actually decrypt the data when using the original key
        self.assertEqual(eh.decrypt_str(enc), self.txt)

        # Now with a different key, decrypt_str should throw EncryptionError
        eh2 = EncryptHelper(EncryptHelper.generate_key())
        with self.assertRaises(EncryptionError):
            eh2.decrypt_str(enc)

    def test_corrupt_key_encrypt(self):
        """Test that encrypt_str fails when using a corrupted key"""
        eh = EncryptHelper('ThisIsNotAKey')
        with self.assertRaises(EncryptKeyMissing):
            eh.encrypt_str(self.txt)
    
    def test_password_key_diffsalt(self):
        """Test that password_key returns two different keys for passwords with different salts"""
        key1, kd1 = EncryptHelper.password_key('ExamplePass', 'hello')
        key2, kd2 = EncryptHelper.password_key('ExamplePass', 'world')
        self.assertNotEqual(key1, key2)
    
    def test_password_key_diffpass(self):
        """Test that password_key returns two different keys for two passwords with the same salt"""
        key1, kd1 = EncryptHelper.password_key('ExamplePass', 'world')
        key2, kd2 = EncryptHelper.password_key('OtherPass', 'world')
        self.assertNotEqual(key1, key2)
    
    def test_password_key_equal(self):
        """Test that password_key returns the same key when ran with the same arguments"""
        key1, kd1 = EncryptHelper.password_key('ExamplePass', 'hello')
        key2, kd2 = EncryptHelper.password_key('ExamplePass', 'hello')
        self.assertEqual(key1, key2)
    
    def test_password_key_gensalt(self):
        """Test that we can reproduce the same key from password_key's auto-generated salt"""
        key1, kd1 = EncryptHelper.password_key('Example')
        key2, kd2 = EncryptHelper.password_key('Example', kd1['salt'])
        self.assertEqual(key1, key2)

    def test_is_encrypted(self):
        """Test that is_encrypted returns True for encrypted data, and False for non-encrypted"""
        eh = EncryptHelper(EncryptHelper.generate_key())
        enc = eh.encrypt_str(self.txt)
        self.assertTrue(eh.is_encrypted(enc))
        self.assertFalse(eh.is_encrypted(self.txt))


class TestKeyManagerGeneration(CryptoBaseCase):
    def test_rsa_gen(self):
        """Generate an RSA 2048 + 4096-bit key, check the pub/priv lengths, and confirm they're formatted correctly"""
        priv, pub = KeyManager.generate_keypair()
        self.assertAlmostEqual(len(priv), 1704, delta=64)
        self.assertAlmostEqual(len(pub), 380, delta=32)
        self.assertIn('---BEGIN PRIVATE', priv.decode('utf-8'))
        self.assertIn('ssh-rsa', pub.decode('utf-8'))
        
        priv, pub = KeyManager.generate_keypair(key_size=4096)
        self.assertAlmostEqual(len(priv), 3272, delta=64)
        self.assertAlmostEqual(len(pub), 724, delta=32)
        self.assertIn('---BEGIN PRIVATE', priv.decode('utf-8'))
        self.assertIn('ssh-rsa', pub.decode('utf-8'))
    
    def test_ecdsa_gen(self):
        """Generate an ECDSA keypair, check the pub/priv lengths, and confirm they're formatted correctly"""
        priv, pub = KeyManager.generate_keypair('ecdsa')
        self.assertAlmostEqual(len(priv), 306, delta=16)
        self.assertAlmostEqual(len(pub), 204, delta=16)
        self.assertIn('---BEGIN PRIVATE', priv.decode('utf-8'))
        self.assertEqual('ecdsa-', pub.decode('utf-8')[0:6])
    
    def test_ed25519_gen(self):
        """Generate an Ed25519 keypair, check the pub/priv lengths, and confirm they're formatted correctly"""
        priv, pub = KeyManager.generate_keypair('ed25519')
        self.assertAlmostEqual(len(priv), 119, delta=16)
        self.assertAlmostEqual(len(pub), 80, delta=16)
        self.assertIn('---BEGIN PRIVATE', priv.decode('utf-8'))
        self.assertEqual('ssh-ed25519', pub.decode('utf-8')[0:11])

    def test_output_keypair(self):
        """Test outputting a keypair to files creates files, and file contents match the returned priv/pub"""
        with TemporaryDirectory() as d:
            priv_file, pub_file = join(d, 'id_rsa'), join(d, 'id_rsa.pub')
            priv, pub = KeyManager.output_keypair(priv=priv_file, pub=pub_file)
            self.assertTrue(path.exists(priv_file), msg=f"Test file exists: {priv_file}")
            self.assertTrue(path.exists(pub_file), msg=f"Test file exists: {pub_file}")
            
            with open(priv_file) as fp:
                data = fp.read().strip()
                key = priv.decode().strip()
                self.assertEqual(key, data, msg='Test private key file contents match returned priv key')
            with open(pub_file) as fp:
                data = fp.read().strip()
                key = pub.decode().strip()
                self.assertEqual(key, data, msg='Test public key file contents match returned pub key')
            

class TestKeyManagerLoad(CryptoBaseCase):
    """Test :py:class:`.KeyManager` asymmetric key loading"""
    
    def test_load_invalid(self):
        """Initialise KeyManager with an invalid key to confirm it raises InvalidFormat"""
        with self.assertRaises(InvalidFormat):
            KeyManager('-----THIS IS NOT --- A ___ KEY')
    
    def test_rsa_load(self):
        """Generate and attempt to load an RSA keypair"""
        priv, pub = KeyManager.generate_keypair()
        # If the keys were invalid, KeyManager should raise InvalidFormat and fail the test
        KeyManager(priv)
        KeyManager(pub)
    
    def test_ecdsa_load(self):
        """Generate and attempt to load an ECDSA keypair"""
        priv, pub = KeyManager.generate_keypair('ecdsa')
        # If the keys were invalid, KeyManager should raise InvalidFormat and fail the test
        KeyManager(priv)
        KeyManager(pub)
    
    def test_ed25519_load(self):
        """Generate and attempt to load an Ed25519 keypair"""
        priv, pub = KeyManager.generate_keypair('ed25519')
        # If the keys were invalid, KeyManager should raise InvalidFormat and fail the test
        KeyManager(priv)
        KeyManager(pub)

    def test_load_keyfile_sign_verify_rsa(self):
        """
        Generate a key pair + save to disk, then load the keypair from disk. Confirm that the keys on disk definitely
        match the returned tuple by running signature verification.
        
        Uses KeyManager with both the public/private keys from disk, and the output_keypair returned public/private keys
        """
        with TemporaryDirectory() as d:
            # Generate and output an RSA key to id_rsa and id_rsa.pub
            priv_file, pub_file = join(d, 'id_rsa'), join(d, 'id_rsa.pub')
            priv, pub = KeyManager.output_keypair(priv=priv_file, pub=pub_file)
            # Load the returned private + public key bytes
            km_ret, km_ret_pub = KeyManager(priv), KeyManager(pub)
            
            # Load the private/public keys from the files
            km = KeyManager.load_keyfile(priv_file)
            self.assertTrue(isinstance(km, KeyManager))
            
            km_pub = KeyManager.load_keyfile(pub_file)
            self.assertTrue(isinstance(km_pub, KeyManager))
            
            # Sign 'hello world' with both the returned private key, and the id_rsa file loaded from disk
            sig = km.sign('hello world')
            sig_ret = km_ret.sign('hello world')
            
            # Make sure the keys are the same by verifying the signature (signed by the keys from disk) with
            # KeyManager instances using the public/private keys loaded from disk + returned public/private keys
            km.verify(sig, 'hello world')
            km_pub.verify(sig, 'hello world')
            km_ret.verify(sig, 'hello world')
            km_ret_pub.verify(sig, 'hello world')
            
            # Same as above, but verifying the signature made by the KeyManager using the returned private key
            km.verify(sig_ret, 'hello world')
            km_ret.verify(sig_ret, 'hello world')
            km_pub.verify(sig_ret, 'hello world')
            km_ret_pub.verify(sig_ret, 'hello world')

    def test_load_keyfile_noexist(self):
        """Test :py:meth:`.KeyManager.load_keyfile` raises :class:`FileNotFoundError` with non-existent path"""
        with TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                KeyManager.load_keyfile(join(d, 'non_existent'))

    def test_load_keyfile_corrupt_public(self):
        """Test :py:meth:`.KeyManager.load_keyfile` raises :class:`.InvalidFormat` with corrupted public key"""
    
        with TemporaryDirectory() as d:
            keyfile = join(d, 'corrupt_key')
            with open(keyfile, 'w') as fp:
                fp.write('ssh-rsa AAAAThisIsNotARealKey')
            with self.assertRaises(InvalidFormat):
                KeyManager.load_keyfile(keyfile)

    def test_load_keyfile_corrupt_public_2(self):
        """
        Test :py:meth:`.KeyManager.load_keyfile` raises :class:`.InvalidFormat` with corrupted public key
        (but with valid b64)
        """
    
        with TemporaryDirectory() as d:
            keyfile = join(d, 'corrupt_key')
            with open(keyfile, 'w') as fp:
                fp.write(f'ssh-rsa {self.fake_b64_key}')
            with self.assertRaises(InvalidFormat):
                KeyManager.load_keyfile(keyfile)
    
    def test_load_keyfile_corrupt_private(self):
        """Test :py:meth:`.KeyManager.load_keyfile` raises :class:`.InvalidFormat` with corrupted PEM private key"""
    
        with TemporaryDirectory() as d:
            keydata = "-----BEGIN PRIVATE KEY-----\n"
            keydata += self.fake_b64_key
            keydata += "\n-----END PRIVATE KEY-----\n"
            
            keyfile = join(d, 'corrupt_key')
            with open(keyfile, 'w') as fp:
                fp.write(keydata)
            with self.assertRaises(InvalidFormat):
                KeyManager.load_keyfile(keyfile)


class TestKeyManagerSignVerifyEncrypt(CryptoBaseCase):
    """Test :py:class:`.KeyManager` asymmetric key signing/verification, and encryption/decryption"""

    def test_rsa_sign_verify(self):
        """Attempt to sign and verify a message using an RSA keypair using :py:meth:`._sign_verify` test helper"""
        priv, pub = KeyManager.generate_keypair()
        self._sign_verify(priv, pub)

    def test_ecdsa_sign_verify(self):
        """Attempt to sign and verify a message using an ECDSA keypair using :py:meth:`._sign_verify` test helper"""
        priv, pub = KeyManager.generate_keypair('ecdsa')
        self._sign_verify(priv, pub)

    def test_ed25519_sign_verify(self):
        """Attempt to sign and verify a message using an Ed25519 keypair using :py:meth:`._sign_verify` test helper"""
        priv, pub = KeyManager.generate_keypair('ed25519')
        self._sign_verify(priv, pub)
    
    def test_rsa_encrypt_decrypt(self):
        priv, pub = KeyManager.generate_keypair()
        km, km_pub = KeyManager(priv), KeyManager(pub)
        msg = 'hello world'
        enc = km.encrypt(msg)          # Encrypt `msg` using private key KeyManager instance
        enc_pub = km_pub.encrypt(msg)  # Encrypt `msg` using public key KeyManager instance
        # Confirm that the encrypted data is actually different from the original message
        self.assertNotEqual(enc, msg)
        self.assertNotEqual(enc_pub, msg)
        # Confirm decrypting the two encrypted `bytes` vars (and decoding to str) matches the original message
        self.assertEqual(km.decrypt(enc).decode('utf-8'), msg)
        self.assertEqual(km.decrypt(enc_pub).decode('utf-8'), msg)
        
    
        






