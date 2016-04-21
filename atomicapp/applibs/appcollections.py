from collections import defaultdict
from collections import OrderedDict


class OrderedDefaultDict(OrderedDict, defaultdict):
    """
    Combines the power of two dictionaries i.e. OrderedDict and defaultdict
    from collections module, to make a OrderedDefaultDict.
    """
    def __init__(self, default_factory=None, *args, **kwargs):
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory
