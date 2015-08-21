#!/usr/bin/env python3

"""
Introduction
============
This module provides a collection of decorators that makes it easy to write
software using contracts.

Contracts are a debugging and verification tool.  They are declarative
statements about what states a program must be in to be considered "correct"
at runtime.  They are similar to assertions, but are verified automatically
at various points in the program.  Contracts can be specified on functions
and on classes.

Contracts serve as a form of documentation and a way of formally specifying
program behavior.  Good practice often includes writing all of the contracts
first, with these contract specifying the exact expected state before and
after each function or method call and the things that should always be
true for a given class of object.

Contracts consist of two parts: a description and a condition.  The
description is simply a human-readable string that describes what the
contract is testing, while the condition is a single function that tests
that condition.  The condition is executed automatically and with certain
names predefined, and must return a boolean value: True if the condition
has been met, and False otherwise.

Preconditions and Postconditions
================================
Contracts on functions consist of preconditions and postconditions.
A precondition is declared using the `requires` decorator, and describes what
must be true upon entrance to the function.  Within the condition function,
the arguments to the decorated function are available.  For example:

    >>> @require("`i` must be an integer", lambda: isinstance(i, int))
    ... @require("`j` must be an integer", lambda: isinstance(j, int))
    ... def add2(i, j):
    ...   return i + j

Note that an arbitrary number of preconditions can be stacked on top of
each other.

These decorators have declared that the types of both arguments must be
integers.  Calling the `add2` function with the correct types of arguments
works:

    >>> add2(1, 2)
    3

But calling with incorrect argument types (violating the contract) fails
with an AssertionError:

    >>> add2("foo", 2)
    Traceback (most recent call last):
    AssertionError: `i` must be an integer

Functions can also have postconditions, specified using the `ensures`
decorator.  Postconditions describe what must be true after the function has
successfully returned.  Within the condition functions, the special variable
`__result__` is set to the return value of the function; the values of the
function arguments are also available.  For example:

    >>> @require("`i` must be a positive integer", lambda: isinstance(i, int) and i > 0)
    ... @require("`j` must be a positive integer", lambda: isinstance(j, int) and j > 0)
    ... @ensure("the result must be greater than either `i` or `j`", lambda: __result__ > i and __result__ > j)
    ... def add2(i, j):
    ...     if i == 7:
    ...        i = -7 # intentionally broken for purposes of example
    ...     return i + j

We can now call the function and ensure that everything is working correctly:

    >>> add2(1, 3)
    4

Except that the function is broken in unexpected ways:

    >>> add2(7, 4)
    Traceback (most recent call last):
    AssertionError: the result must be greater than either `i` or `j`

The function specifying the condition doesn't have to be a lambda; it can be
any function, and pre- and postconditions don't have to actually reference
the arguments or results of the function at all.  They can simply check
that the function's environments and effects:

    >>> names = set()
    >>> def exists_in_database(x):
    ...   return x in names
    >>> @require("`name` must be a string", lambda: isinstance(name, str))
    ... @require("`name` must not already be in the database", lambda: not exists_in_database(name.strip()))
    ... @ensure("the normalized version of the name must be added to the database", lambda: exists_in_database(name.strip()))
    ... def add_to_database(name):
    ...     if name not in names:
    ...         names.add(name.strip())

    >>> add_to_database("James")
    >>> add_to_database("Marvin")
    >>> add_to_database("Marvin")
    Traceback (most recent call last):
    AssertionError: `name` must not already be in the database

All of the various calling conventions of Python are supported:

    >>> @require("`a` is an integer", lambda: isinstance(a, int))
    ... @require("`b` is a string", lambda: isinstance(b, str))
    ... @require("every member of `c` should be a boolean", lambda: all(isinstance(x, bool) for x in c))
    ... def func(a, *c, b="Foo"):
    ...     pass

    >>> func(1, True, True, False, b="foo")
    >>> func(b="Foo", a=18)
    >>> args = {"a": 8, "b": "foo"}
    >>> func(**args)
    >>> args = (1, True, True, False)
    >>> func(*args, b="bar")

Contracts on Classes
====================
The `require` and `ensure` decorators can be used on class methods too,
not just bare functions:

    >>> class Foo:
    ...     @require("`name` should be nonempty", lambda: len(name) > 0)
    ...     def __init__(self, name):
    ...         self.name = name

    >>> foo = Foo()
    Traceback (most recent call last):
    TypeError: __init__ missing 1 required positional argument: 'name'

    >>> foo = Foo("")
    Traceback (most recent call last):
    AssertionError: `name` should be nonempty

Classes may also have an additional sort of contract specified over them:
the invariant.  An invariant, created using the `invariant` decorator,
specifies a condition that must always be true for instances of that class.
In this case, "always" means "before invocation of any method and after
its return" -- methods are allowed to violate invariants so long as they
are restored prior to return.

The special name `__invariant__` is set to a reference to the instance
variable in question.  For example:

    >>> @invariant("inner list can never be empty", lambda: len(__instance__.lst) > 0)
    ... class NonemptyList:
    ...     @require("initial list must be a list", lambda: isinstance(initial, list))
    ...     @require("initial list cannot be empty", lambda: len(initial) > 0)
    ...     def __init__(self, initial):
    ...         self.lst = initial
    ...
    ...     def get(self, i):
    ...         return self.lst[i]
    ...
    ...     def pop(self):
    ...         self.lst.pop()
    ...
    ...     def as_string(self):
    ...         # Build up a string representation using the `get` method,
    ...         # to illustrate methods calling methods with invariants.
    ...         return ",".join(str(self.get(i)) for i in range(0, len(self.lst)))

    >>> nl = NonemptyList([1,2,3])
    >>> nl.pop()
    >>> nl.pop()
    >>> nl.pop()
    Traceback (most recent call last):
    AssertionError: inner list can never be empty

Violations of invariants are ignored in the following situations:

    - before calls to __init__ and __new__ (since the object is still
      being initialized)

    - before and after calls to any method whose name begins with "__",
      except for methods implementing arithmetic and comparison operations
      and container type emulation (because such methods are private and
      expected to manipulate the object's inner state, plus things get hairy
      with certain applications of `__getattr(ibute)?__`)

    - before and after calls to methods added from outside the initial
      class definition (because invariants are processed only at class
      definition time)

Also note that if a method invokes another method on the same object,
all of the invariants will be tested again:

    >>> nl = NonemptyList([1,2,3])
    >>> nl.as_string() == '1,2,3'
    True

Contracts and Debugging
=======================
Contracts are a documentation and testing tool; they are not intended
to be used to validate user input or implement program logic.  Indeed,
running Python with `__debug__` set to False (e.g. by calling the Python
intrepreter with the "-O" option) disables contracts.
"""

__all__ = ["ensure", "invariant", "require"]
__author__ = "Rob King"
__copyright__ = "Copyright (C) 2015 Rob King"
__license__ = "LGPL"
__version__ = "$Id$"
__email__ = "jking@deadpixi.com"
__status__ = "Alpha"

from functools import wraps
from types import FunctionType

try:
    from inspect import getfullargspec

except ImportError:
    from inspect import getargspec
    def getfullargspec(f):
        result = list(getargspec(f))
        result.append([])
        result.append({})
        result.append({})
        return tuple(result)

def build_call(f, *args, **kwargs):
    """
    Build an argument dictionary suitable for passing via `**` expansion given
    function `f`, positional arguments `args`, and keyword arguments `kwargs`.
    """

    while hasattr(f, '__wrapped_func__'):
        f = f.__wrapped_func__

    named, vargs, varkw, defs, kwonly, kwonlydefs, _ = getfullargspec(f)

    nonce = object()
    actual = {name: nonce for name in named}

    defs = defs or [] 
    kwonlydefs = kwonlydefs or {}

    actual.update(dict(zip(reversed(args), reversed(defs))))
    actual.update(kwonlydefs)

    for name, arg in zip(named, args):
        actual[name] = arg

    if vargs:
        actual[vargs] = args[len(named):]

    actual.update(kwargs)

    for name in named:
        if actual[name] is nonce:
            raise TypeError("%s missing 1 required positional argument: '%s'" % (f.__name__, name))

    return actual

def condition(description, predicate, precondition=False, postcondition=False, method=False):
    assert isinstance(description, str) and len(description) > 0
    assert isinstance(predicate, FunctionType) and hasattr(predicate, "__code__") and hasattr(predicate, "__globals__")
    assert precondition or postcondition

    def require(f):
        @wraps(f)
        def inner(*args, **kwargs):
            assert not method or len(args) > 0

            scope = predicate.__globals__.copy()
            scope.update(build_call(f, *args, **kwargs))
            if method:
                scope["__instance__"] = args[0]
           
            if precondition:
                assert eval(predicate.__code__, scope), description
            result = f(*args, **kwargs)
            if postcondition:
                scope["__result__"] = result
                assert eval(predicate.__code__, scope), description

            return result

        inner.__wrapped_func__ = f
        return inner
    return require


def require(description, predicate):
    """
    Specify a precondition described by `description` and tested by
    `predicate`.
    """

    return condition(description, predicate, True, False)

def ensure(description, predicate):
    """
    Specify a precondition described by `description` and tested by
    `predicate`.
    """

    return condition(description, predicate, False, True)

def invariant(description, predicate):
    """
    Specify a class invariant described by `descriptuon` and tested
    by `predicate`.
    """

    def invariant(c):
        class Wrapper(c):
            pass

        for name, value in [(name, getattr(c, name)) for name in dir(c)]:
            if callable(value) and not isinstance(value, type):
                if name in ("__getitem__", "__setitem__", "__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__") or not name.startswith("__"):
                    setattr(Wrapper, name, condition(description, predicate, name != "__init__", True, True)(value))
        return Wrapper
    return invariant

if not __debug__:
    def require(description, predicate):
        def require(f):
            return f
        return require

    def ensure(description, predicate):
        def ensure(f):
            return f
        return ensure

    def invariant(description, predicate):
        def invariant(c):
            return c
        return invariant

if __name__ == "__main__":
    import doctest
    doctest.testmod()
