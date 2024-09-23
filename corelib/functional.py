import asyncio
import contextlib
import functools
from itertools import chain
from typing import Callable, Any
from typing import Type


async def delay(coro, *args, seconds=1, **kwargs):
    await asyncio.sleep(seconds)
    return await coro(*args, **kwargs)


class Promise:
    """
    Base class for the proxy class created in the closure of the lazy function.
    It's used to recognize promises in code.
    """

    pass


def lazy(func, *resultclasses):  # NOSONAR
    """
    Turn any callable into a lazy evaluated callable. result classes or types
    is required -- at least one is needed so that the automatic forcing of
    the lazy evaluation code is triggered. Results are not memoized; the
    function is evaluated on every access.
    """

    @functools.total_ordering
    class __proxy__(Promise):  # noqa
        """
        Encapsulate a function call and act as a proxy for methods that are
        called on the result of that function. The function is not evaluated
        until one of the methods on the result is called.
        """

        __prepared = False

        def __init__(self, args, kw):
            self.__args = args
            self.__kw = kw
            if not self.__prepared:
                self.__prepare_class__()
            self.__class__.__prepared = True

        def __reduce__(self):
            return (
                _lazy_proxy_unpickle,
                (func, self.__args, self.__kw) + resultclasses,
            )

        def __repr__(self):
            return repr(self.__cast())

        @classmethod
        def __prepare_class__(cls):
            for resultclass in resultclasses:
                for type_ in resultclass.mro():
                    for method_name in type_.__dict__:
                        # All __promise__ return the same wrapper method, they
                        # look up the correct implementation when called.
                        if hasattr(cls, method_name):
                            continue
                        meth = cls.__promise__(method_name)
                        setattr(cls, method_name, meth)
            cls._delegate_bytes = bytes in resultclasses
            cls._delegate_text = str in resultclasses
            if cls._delegate_bytes and cls._delegate_text:
                raise ValueError(
                    'Cannot call lazy() with both bytes and text return types.'
                )
            if cls._delegate_text:
                cls.__str__ = cls.__text_cast
            elif cls._delegate_bytes:
                cls.__bytes__ = cls.__bytes_cast

        @classmethod
        def __promise__(cls, method_name):
            # Builds a wrapper around some magic method
            def __wrapper__(self, *args, **kw):
                # Automatically triggers the evaluation of a lazy value and
                # applies the given magic method of the result type.
                res = func(*self.__args, **self.__kw)
                return getattr(res, method_name)(*args, **kw)

            return __wrapper__

        def __text_cast(self):
            return func(*self.__args, **self.__kw)

        def __bytes_cast(self):
            return bytes(func(*self.__args, **self.__kw))

        def __bytes_cast_encoded(self):
            return func(*self.__args, **self.__kw).encode()

        def __cast(self):
            if self._delegate_bytes:
                return self.__bytes_cast()
            elif self._delegate_text:
                return self.__text_cast()
            else:
                return func(*self.__args, **self.__kw)

        def __str__(self):
            # object defines __str__(), so __prepare_class__() won't overload
            # a __str__() method from the proxied class.
            return str(self.__cast())

        def __eq__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()  # noqa
            return self.__cast() == other

        def __lt__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()  # noqa
            return self.__cast() < other

        def __hash__(self):
            return hash(self.__cast())

        def __mod__(self, rhs):
            if self._delegate_text:
                return str(self) % rhs
            return self.__cast() % rhs

        def __add__(self, other):
            return self.__cast() + other

        def __radd__(self, other):
            return other + self.__cast()

        def __deepcopy__(self, memo):
            # Instances of this class are effectively immutable. It's just a
            # collection of functions. So we don't need to do anything
            # complicated for copying.
            memo[id(self)] = self
            return self  # noqa

    @functools.wraps(func)
    def __wrapper__(*args, **kw):
        # Creates the proxy object, instead of the actual value.
        return __proxy__(args, kw)

    return __wrapper__


def _lazy_proxy_unpickle(func, args, kwargs, *resultclasses):
    return lazy(func, *resultclasses)(*args, **kwargs)


def as_suppressed(exec_type: Type[BaseException], f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        with contextlib.suppress(exec_type):
            return f(*args, **kwargs)

    return wrapper


class PipelineFunc:
    """
    A utility for calling functions in pipelines.
    """

    def __init__(self, func: Callable[..., Any], /, *args: Any, **kwargs: Any):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        if not self.args and not self.kwargs:
            return repr(self.func)
        func_arg = [self.func.__name__]
        return _function_repr('f', func_arg, self.args, self.kwargs)

    def __ror__(self, other: Any) -> Any:
        found_placeholder = False

        def is_placeholder(x):
            if isinstance(x, PipelineArg):
                nonlocal found_placeholder
                found_placeholder = True
                return True
            else:
                return False

        args = [
            x._PipelineArg__transform(other) if is_placeholder(x) else x
            for x in self.args
        ]
        kwargs = {
            k: x._PipelineArg__transform(other) if is_placeholder(x) else x
            for k, x in self.kwargs.items()
        }

        if not found_placeholder:
            args = [other, *args]

        return self.func(*args, **kwargs)


class PipelineArg:
    def __init__(
        self,
        transform: Callable[[Any], Any] = lambda x: x,
        repr: str = 'X',  # noqa
    ):
        # Use private variables to minimize the number of names that
        # `__getattr__()` can conflict with.
        self.__transform = transform
        self.__repr = repr

    def __repr__(self) -> str:
        return self.__repr

    def __getattr__(self, attr: str) -> 'PipelineArg':
        return PipelineArg(
            transform=lambda x: getattr(self.__transform(x), attr),
            repr=f'{self.__repr}.{attr}',
        )

    def __getitem__(self, key: str) -> 'PipelineArg':
        return PipelineArg(
            transform=lambda x: self.__transform(x)[key],
            repr=f'{self.__repr}[{key}]',
        )

    def __call__(self, *args: Any, **kwargs: Any) -> 'PipelineArg':
        return PipelineArg(
            transform=lambda x: self.__transform(x)(*args, **kwargs),
            repr=_function_repr(self.__repr, [], args, kwargs),
        )


def _function_repr(func, verbatim_args, args, kwargs):
    kwarg_reprs = [f'{k}={v!r}' for k, v in kwargs.items()]
    arg_reprs = map(repr, args)
    args_kwargs_repr = ', '.join(chain(verbatim_args, arg_reprs, kwarg_reprs))
    return f'{func}({args_kwargs_repr})'


pipeline_func = PipelineFunc
X = PipelineArg()

__all__ = [
    'delay',
    'as_suppressed',
    'pipeline_func',
    'X',
    'lazy',
]
