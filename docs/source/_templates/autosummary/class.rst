{{ name | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

{% block methods %}
.. automethod:: __init__

{% if methods %}
Methods
^^^^^^^

.. rubric:: Methods

.. autosummary::
   :toctree: {{ name | lower }}
{% for item in methods %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block attributes %}
{% if attributes %}
Attributes
^^^^^^^^^^

.. rubric:: Attributes

.. autosummary::
   :toctree: {{ name | lower }}
{% for item in attributes %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}
