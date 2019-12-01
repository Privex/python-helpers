import attr

__all__ = [
    'AttribDictable'
]


@attr.s
class AttribDictable:
    """
    A small mixin class for :py:func:`attr.s` classes, allowing them to behave like dictionaries, and
    support casting into dictionaries using ``dict(x)``.
    
    Usage::
        
        >>> import attr
        >>> from privex.helpers import AttribDictable
        >>>
        >>> @attr.s
        >>> class Example(AttribDictable):
        ...     hello = attr.ib(type=str)
        ...     testing = attr.ib(type=bool, default=True)
        ...
        >>> x = Example(hello='world')
        >>> x['hello']
        'world'
        >>> x['hello'] = 'lorem ipsum'
        >>> dict(x)
        {'hello': 'lorem ipsum', 'testing': True}
        
    
    """
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __iter__(self):
        """Handle casting via ``dict(myclass)``"""
        for k, v in attr.asdict(self).items():
            yield k, v
    
    def __getitem__(self, key):
        """
        When the instance is accessed like a dict, try returning the matching attribute.
        If the attribute doesn't exist, raise :class:`KeyError`
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)
    
    def __setitem__(self, key, value):
        return setattr(self, key, value)
