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
from privex.helpers import EncryptHelper, EncryptKeyMissing, EncryptionError, InvalidFormat
from privex.helpers.crypto.KeyManager import KeyManager
from tests.base import PrivexBaseCase


class TestEncryptHelper(PrivexBaseCase):
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


class TestKeyManager(PrivexBaseCase):
    """Test :py:class:`.KeyManager` asymmetric key generation and usage"""
    
    def test_rsa_gen(self):
        """Generate an RSA 2048 + 4096-bit key, check the pub/priv lengths, and confirm they're formatted correctly"""
        priv, pub = KeyManager.generate_keypair()
        self.assertAlmostEqual(len(priv), 1704, delta=64)
        self.assertAlmostEqual(len(pub), 380, delta=32)
        self.assertIn('---BEGIN PRIVATE', priv.decode('utf-8'))
        self.assertIn('ssh-rsa', pub.decode('utf-8'))
        
        priv, pub = KeyManager.generate_keypair(key_size=4096)
        self.assertEqual(len(priv), 3272)
        self.assertEqual(len(pub), 724)
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

    @staticmethod
    def _sign_verify(priv, pub):
        """Helper method to avoid duplicating sign+verify code for every algorithm"""
        km = KeyManager(priv)  # KeyManager with private key (public key interpolated from private key)
        km_pub = KeyManager(pub)  # KeyManager with only public key
        sig = km.sign('hello world')  # Sign 'hello world' with the private key
        # Verify the signature, these methods will raise InvalidSignature if it doesn't verify.
        km_pub.verify(signature=sig, message='hello world')  # Verify with pubkey-only instance
        km.verify(signature=sig, message='hello world')  # Verify with privkey-only instance
    
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
        
        
        






