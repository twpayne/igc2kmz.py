class OpenStruct(object):

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  def __repr__(self):
    return 'OpenStruct(%s)' % ', '.join(['%s=%s' % (key, repr(value)) for key, value in self.__dict__.items()])
