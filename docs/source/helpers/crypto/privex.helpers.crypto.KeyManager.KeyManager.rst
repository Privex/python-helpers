KeyManager
==========

.. currentmodule:: privex.helpers.crypto.KeyManager

.. autoclass:: KeyManager
   :members:

   .. automethod:: __init__
      :noindex:

   .. rubric:: Methods

   .. autosummary::
      :toctree: keymanager

      ~KeyManager.__init__
      ~KeyManager.decrypt
      ~KeyManager.encrypt
      ~KeyManager.export_key
      ~KeyManager.export_private
      ~KeyManager.export_public
      ~KeyManager.generate_keypair
      ~KeyManager.generate_keypair_raw
      ~KeyManager.identify_algorithm
      ~KeyManager.load_key
      ~KeyManager.load_keyfile
      ~KeyManager.output_keypair
      ~KeyManager.sign
      ~KeyManager.verify

Attributes
----------

   .. rubric:: Attributes

   .. autosummary::
      :toctree: keymanager

       ~KeyManager.backend
       ~KeyManager.combined_key_types
       ~KeyManager.curves
       ~KeyManager.default_formats
       ~KeyManager.default_gen
       ~KeyManager.generators
       ~KeyManager.private_key_types
       ~KeyManager.public_key_types
       ~KeyManager.raw_priv_types
       ~KeyManager.raw_pub_types
       ~KeyManager.type_name_map

