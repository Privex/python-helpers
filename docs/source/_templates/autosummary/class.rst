{{ name | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:

{% block methods %}
   .. automethod:: __init__
      :noindex:

{% if methods %}
Methods
^^^^^^^

.. rubric:: Methods

.. autosummary::
   :toctree: {{ name | lower }}
{% for item in methods %}
{%- if item not in inherited_members %}
    ~{{ name }}.{{ item }}
{%- endif %}
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
{%- if item not in inherited_members %}
    ~{{ name }}.{{ item }}
{%- endif %}
{%- endfor %}
{% endif %}
{% endblock %}
