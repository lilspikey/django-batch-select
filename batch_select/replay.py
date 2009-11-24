'''
Class that we can use to chain together several methods calls (in
the same fashion as we would with a QuerySet) and then "replay" them
later on a different object.
'''

def create_replay_method(name):
    def _replay_method(self, *args, **kwargs):
        cloned = self.clone()
        cloned._add_replay(name, *args, **kwargs)
        return cloned
    _replay_method.__name__ = name
    _replay_method.__doc__ = 'replay %s method on target object' % name
    return _replay_method

class ReplayMetaClass(type):
    def __new__(meta, classname, bases, class_dict):
        replay_methods = class_dict.get('__replayable__', [])
        for name in replay_methods:
            class_dict[name] = create_replay_method(name)
        return type.__new__(meta, classname, bases, class_dict)

class Replay(object):
    __metaclass__ = ReplayMetaClass
    
    def __init__(self):
        self._replays=[]
    
    def _add_replay(self, method_name, *args, **kwargs):
        self._replays.append((method_name, args, kwargs))
    
    def clone(self, *args, **kwargs):
        klass = self.__class__
        cloned = klass(*args, **kwargs)
        cloned._replays=self._replays[:]
        return cloned
    
    def replay(self, target):
        result = target
        for method_name, args, kwargs in self._replays:
            method = getattr(result, method_name)
            result = method(*args, **kwargs)
        return result
