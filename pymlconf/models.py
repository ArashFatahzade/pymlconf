import abc
import copy
from collections import OrderedDict, Iterable

from .errors import ConfigKeyError, ConfigurationAlreadyInitializedError, \
    ConfigurationNotInitializedError
from .yaml_helper import load_string
from .proxy import ObjectProxy


def isiterable(o):
    if isinstance(o, (bytes, str, type)):
        return False
    return isinstance(o, Iterable)


class Mergable(metaclass=abc.ABCMeta):
    """Base class for all configuration nodes, so all configuration nodes are
    mergable
    """

    def __init__(self, data=None, context=None):
        """
        :param data: Initial value to constract a mergable instance. It can be
                     ``yaml string`` or python dictionary. default: None.
        :type data: list or dict

        :param context: dictionary to format the yaml before parsing in
                        pre-processor.
        :type context: dict

        """
        self.context = context if context else {}
        if data:
            self.merge(data)

    @abc.abstractmethod
    def can_merge(self, data):
        """
        Determines whenever can merge with the passed argument or not.

        :param data: An object to test.
        :type data: any

        :returns: bool
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _merge(self, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def copy(self):
        """
        When implemented, returns copy of current config instance.

        :returns: :class:`.Mergable`
        """
        raise NotImplementedError()

    # FIXME: Remove this function
    @classmethod
    @abc.abstractmethod
    def empty(cls):
        """
        When implemented, returns an empty instance of drived :class:`.Mergable` class.

        :returns: :class:`.Mergable`
        """
        raise NotImplementedError()

    @classmethod
    def make_mergable_if_possible(cls, data, context):
        """
        Makes an object mergable if possible. Returns the virgin object if cannot convert it to a mergable instance.

        :returns: :class:`.Mergable` or type(data)

        """
        if isinstance(data, dict):
            return MergableDict(data=data, context=context)
        elif isiterable(data):
            return MergableList(
                data=[cls.make_mergable_if_possible(i, context) for i in data],
                context=context
            )
        else:
            return data

    def merge(self, *args):
        """
        Merges this instance with new instances, in-place.

        :param \*args: Configuration values to merge with current instance.
        :type \*args: iterable

        """
        for data in args:
            if isinstance(data, str):
                to_merge = load_string(data, self.context)
                if not to_merge:
                    continue
            else:
                to_merge = data

            if not self.can_merge(to_merge):
                raise TypeError(
                    'Cannot merge myself:%s with %s. data: %s' \
                    % (type(self), type(data), data)
                )

            self._merge(to_merge)

    def _ensure_namespaces(self, *namespaces):
        if namespaces:
            ns = namespaces[0]
            if ns not in self:
                self[ns] = ConfigNamespace(context=self.context)
            # noinspection PyProtectedMember
            return getattr(self, ns)._ensure_namespaces(*namespaces[1:])
        else:
            return self


class MergableDict(OrderedDict, Mergable):
    """
    Configuration node that represents python dictionary data.
    """

    def __init__(self, *args, **kwargs):
        OrderedDict.__init__(self)
        Mergable.__init__(self, *args, **kwargs)

    def can_merge(self, data):
        return data is not None and isinstance(data, dict)

    def _merge(self, data):
        for k in list(data.keys()):
            v = data[k]

            if k in self \
                    and isinstance(self[k], Mergable) \
                    and self[k].can_merge(v):
                self[k].merge(v)
            else:
                if isinstance(v, Mergable):
                    self[k] = v.copy()
                else:
                    self[k] = Mergable.make_mergable_if_possible(copy.deepcopy(v), self.context)

    def __getattr__(self, key):
        if key in self:
            return self.get(key)
        raise ConfigKeyError(key)

    def __setattr__(self, key, value):
        if key not in self:
            self.__dict__[key] = value
        else:
            self[key] = value

    def copy(self):
        return ConfigDict(self, context=self.context)

    @classmethod
    def empty(cls):
        return cls()


class ConfigurationNamespace(MergableDict):
    """
    Configuration node that represents the configuration namespace node.
    """


class MergableList(list, Mergable):
    """
    Configuration node that represents the python list data.
    """

    def __init__(self, *args, **kwargs):
        list.__init__(self)
        Mergable.__init__(self, *args, **kwargs)

    def can_merge(self, data):
        return data and hasattr(data, '__iter__')

    def _merge(self, data):
        del self[:]
        self.extend(data)

    def copy(self):
        return ConfigList(self, context=self.context)

    @classmethod
    def empty(cls):
        return cls()


class Root(MergableDict):
    """
    The main class which exposes pymlconf package.

    Example::

        from pymlconf import Root
        from os import path
        config =  Root('''
            server:
                host: localhost
                port: 4455
        ''')

        print config.server.host
        print config.server.port

    """

    def load_file(self, filename):
        """
        load file which contains yaml configuration entries.and merge it by
        current instance

        :param files: files to load and merge into existing configuration
                      instance
        :type files: list

        """
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)

        loaded_yaml = load_yaml(f, self.context)
        if loaded_yaml:
            node.merge(loaded_yaml)


class DeferredRoot(ObjectProxy):
    _instance = None

    def __init__(self):
        super().__init__(self._get_instance)

    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            raise ConfigurationNotInitializedError(
                'Configuration manager object is not initialized yet.'
            )
        return cls._instance

    @classmethod
    def _set_instance(cls, v):
        cls._instance = v

    def load(self, force=False, **kw):
        """
        Initialize the configuration manager

        :param force: force initialization even if it's already initialized
        :return:
        """

        instance = self._get_instance()
        if not force and instance is not None:
            raise ConfigurationAlreadyInitializedError(
                'Configuration manager object is already initialized.'
            )

        self._set_instance(ConfigManager(**kw))

