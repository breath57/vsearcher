# -*- encoding: utf-8 -*-
'''
@description: related decorators
@author: breath57
@email: breath57@163.com
'''
from inspect import ismethod
import warnings


class Maintain:
    """ Maintenance-related decorators """

    @classmethod
    def _decorate(cls, class_or_func, tip: str = None, category: str = None):
        """ Base decorator for custom decorators """
        def wrapper(*args, **kw):
            if tip:
                warnings.warn(
                    f'[{ "method" if ismethod(class_or_func) else "class"}: {class_or_func.__name__}] {tip}', category=category)
            class_or_func(*args, **kw)
        return wrapper

    @classmethod
    def deprecating(cls, class_or_func):
        """ indicates that this class_or_function will be deprecated """
        return cls._decorate(class_or_func, 'will be deprecated!')

    @classmethod
    def deprecated(cls, class_or_func):
        """ indicates that this class_or_function has been deprecated """
        return cls._decorate(class_or_func, 'has been deprecated!', DeprecationWarning)

    @classmethod
    def future(cls, class_or_func):
        """ indicates that this class or function can use in the future """
        return cls._decorate(class_or_func, 'can use in the future! but now, it is not completed!')
