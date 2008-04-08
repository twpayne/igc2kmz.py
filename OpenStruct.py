class OpenStruct:

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  def __getattr__(self, key):
    if self.__dict__.has_key(key):
      return self.__dict__[key]
    else:
      raise AttributeError, key

  def __setattr__(self, key, value):
    self.__dict__[key] = value
    return value

  def __repr__(self):
    return 'OpenStruct(%s)' % ', '.join(['%s=%s' % (key, repr(value)) for key, value in self.__dict__.items()])
