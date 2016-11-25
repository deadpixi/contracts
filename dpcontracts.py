#!/usr/bin/env python

"""
Introduction
============
This module provides a collection of decorators that makes it easy to
write software using contracts.

Contracts are a debugging and verification tool.  They are declarative
statements about what states a program must be in to be considered
"correct" at runtime.  They are similar to assertions, and are verified
automatically at various well-defined points in the program.  Contracts can
be specified on functions and on classes.

Contracts serve as a form of documentation and a way of formally
specifying program behavior.  Good practice often includes writing all of
the contracts first, with these contract specifying the exact expected
state before and after each function or method call and the things that
should always be true for a given class of object.

Contracts consist of two parts: a description and a condition.  The
description is simply a human-readable string that describes what the
contract is testing, while the condition is a single function that tests
that condition.  The condition is executed automatically and passed certain
arguments (which vary depending on the type of contract), and must return
a boolean value: True if the condition has been met, and False otherwise.

Preconditions and Postconditions
================================
Contracts on functions consist of preconditions and postconditions.
A precondition is declared using the `requires` decorator, and describes
what must be true upon entrance to the function. The condition function
is passed an arguments object, which as as its attributes the arguments
to the decorated function:

    >>> @require("`i` must be an integer", lambda args: isinstance(args.i, int))
    ... @require("`j` must be an integer", lambda args: isinstance(args.j, int))
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

Functions can also have postconditions, specified using the `ensure`
decorator.  Postconditions describe what must be true after the function
has successfully returned.  Like the `require` decorator, the `ensure`
decorator is passed an argument object.  It is also passed an additional
argument, which is the result of the function invocation.  For example:

    >>> @require("`i` must be a positive integer",
    ...          lambda args: isinstance(args.i, int) and args.i > 0)
    ... @require("`j` must be a positive integer",
    ...          lambda args: isinstance(args.j, int) and args.j > 0)
    ... @ensure("the result must be greater than either `i` or `j`",
    ...         lambda args, result: result > args.i and result > args.j)
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
the function's environments and effects:

    >>> names = set()
    >>> def exists_in_database(x):
    ...   return x in names
    >>> @require("`name` must be a string", lambda args: isinstance(args.name, str))
    ... @require("`name` must not already be in the database",
    ...          lambda args: not exists_in_database(args.name.strip()))
    ... @ensure("the normalized version of the name must be added to the database",
    ...         lambda args, result: exists_in_database(args.name.strip()))
    ... def add_to_database(name):
    ...     if name not in names and name != "Rob": # intentionally broken
    ...         names.add(name.strip())

    >>> add_to_database("James")
    >>> add_to_database("Marvin")
    >>> add_to_database("Marvin")
    Traceback (most recent call last):
    AssertionError: `name` must not already be in the database
    >>> add_to_database("Rob")
    Traceback (most recent call last):
    AssertionError: the normalized version of the name must be added to the database

All of the various calling conventions of Python are supported:

    >>> @require("`a` is an integer", lambda args: isinstance(args.a, int))
    ... @require("`b` is a string", lambda args: isinstance(args.b, str))
    ... @require("every member of `c` should be a boolean",
    ...          lambda args: all(isinstance(x, bool) for x in args.c))
    ... def func(a, b="Foo", *c):
    ...     pass

    >>> func(1, "foo", True, True, False)
    >>> func(b="Foo", a=7)
    >>> args = {"a": 8, "b": "foo"}
    >>> func(**args)
    >>> args = (1, "foo", True, True, False)
    >>> func(*args)
    >>> args = {"a": 9}
    >>> func(**args)
    >>> func(10)

A common contract is to validate the types of arguments. To that end,
there is an additional decorator, `types`, that can be used
to validate arguments' types:

    >>> class ExampleClass:
    ...     pass

    >>> @types(a=int, b=str, c=(type(None), ExampleClass)) # or types.NoneType, if you prefer
    ... @require("a must be nonzero", lambda args: args.a != 0)
    ... def func(a, b, c=38):
    ...     return " ".join(str(x) for x in [a, b])

    >>> func(1, "foo", ExampleClass())
    '1 foo'

    >>> func(1.0, "foo", ExampleClass) # invalid type for `a`
    Traceback (most recent call last):
    AssertionError: the types of arguments must be valid

    >>> func(1, "foo") # invalid type (the default) for `c`
    Traceback (most recent call last):
    AssertionError: the types of arguments must be valid

Contracts on Classes
====================
The `require` and `ensure` decorators can be used on class methods too,
not just bare functions:

    >>> class Foo:
    ...     @require("`name` should be nonempty", lambda args: len(args.name) > 0)
    ...     def __init__(self, name):
    ...         self.name = name

    >>> foo = Foo()
    Traceback (most recent call last):
    TypeError: __init__ missing required positional argument: 'name'

    >>> foo = Foo("")
    Traceback (most recent call last):
    AssertionError: `name` should be nonempty

Classes may also have an additional sort of contract specified over them:
the invariant.  An invariant, created using the `invariant` decorator,
specifies a condition that must always be true for instances of that class.
In this case, "always" means "before invocation of any method and after
its return" -- methods are allowed to violate invariants so long as they
are restored prior to return.

Invariant contracts are passed a single variable, a reference to the
instance of the class. For example:

    >>> @invariant("inner list can never be empty", lambda self: len(self.lst) > 0)
    ... @invariant("inner list must consist only of integers",
    ...            lambda self: all(isinstance(x, int) for x in self.lst))
    ... class NonemptyList:
    ...     @require("initial list must be a list", lambda args: isinstance(args.initial, list))
    ...     @require("initial list cannot be empty", lambda args: len(args.initial) > 0)
    ...     @ensure("the list instance variable is equal to the given argument",
    ...             lambda args, result: args.self.lst == args.initial)
    ...     @ensure("the list instance variable is not an alias to the given argument",
    ...             lambda args, result: args.self.lst is not args.initial)
    ...     def __init__(self, initial):
    ...         self.lst = initial[:]
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

    >>> nl = NonemptyList(["a", "b", "c"])
    Traceback (most recent call last):
    AssertionError: inner list must consist only of integers

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

Testing This Module
===================
This module has embedded doctests that are run with the module is invoked
from the command line.  Simply run the module directly to run the tests.

Contact Information and Licensing
=================================
This module has a home page at `GitHub <https://github.com/deadpixi/contracts>`_.

This module was written by Rob King (jking@deadpixi.com).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__all__ = ["ensure", "invariant", "require"]
__author__ = "Rob King"
__copyright__ = "Copyright (C) 2015-2016 Rob King"
__license__ = "LGPL"
__version__ = "$Id$"
__email__ = "jking@deadpixi.com"
__status__ = "Alpha"

from collections import namedtuple
from functools import wraps
from types import FunctionType

try:
    from inspect import getfullargspec

except ImportError: # Python 2 compatibility
    from inspect import getargspec
    def getfullargspec(f):
        result = list(getargspec(f))
        result.append([])
        result.append({})
        result.append({})
        return tuple(result)

def get_wrapped_func(func):
    while hasattr(func, '__contract_wrapped_func__'):
        func = func.__contract_wrapped_func__
    return func

def build_call(func, *args, **kwargs):
    """
    Build an argument dictionary suitable for passing via `**` expansion given
    function `f`, positional arguments `args`, and keyword arguments `kwargs`.
    """

    func = get_wrapped_func(func)
    named, vargs, _, defs, kwonly, kwonlydefs, _ = getfullargspec(func)

    nonce = object()
    actual = dict((name, nonce) for name in named)

    defs = defs or () 
    kwonlydefs = kwonlydefs or {}

    actual.update(kwonlydefs)
    actual.update(dict(zip(reversed(named), reversed(defs))))
    actual.update(dict(zip(named, args)))

    if vargs:
        actual[vargs] = tuple(args[len(named):])

    actual.update(kwargs)

    for name, value in actual.items():
        if value is nonce:
            raise TypeError("%s missing required positional argument: '%s'" % (func.__name__, name))

    return namedtuple('Args', actual.keys())(**actual)

def arg_count(func):
    named, vargs, _, defs, kwonly, kwonlydefs, _ = getfullargspec(func)
    return len(named) + len(kwonly) + (1 if vargs else 0)

def condition(description, predicate, precondition=False, postcondition=False, instance=False):
    assert isinstance(description, str), "contract descriptions must be strings"
    assert len(description) > 0, "contracts must have nonempty descriptions"
    assert isinstance(predicate, FunctionType), "contract predicates must be functions"
    assert precondition or postcondition, "contracts must be at least one of pre- or post-conditional"
    assert arg_count(predicate) == (1 if precondition or instance else 2), \
           "contract predicates must take the correct number of arguments"
    
    def require(f):
        wrapped = get_wrapped_func(f)

        @wraps(f)
        def inner(*args, **kwargs):
            rargs = build_call(f, *args, **kwargs) if not instance else args[0]

            if precondition:
                assert predicate(rargs), description

            result = f(*args, **kwargs)

            if instance:
                assert predicate(rargs), description

            elif postcondition:
                assert predicate(rargs, result), description

            return result

        inner.__contract_wrapped_func__ = wrapped
        return inner
    return require

def require(description, predicate):
    """
    Specify a precondition described by `description` and tested by
    `predicate`.
    """

    return condition(description, predicate, True, False)

def types(**requirements):
    """
    Specify a precondition based on the types of the function's
    arguments.
    """

    def predicate(args):
        for name, kind in sorted(requirements.items()):
            assert hasattr(args, name), "missing required argument `%s`" % name

            if not isinstance(kind, tuple):
                kind = (kind,)

            if not any(isinstance(getattr(args, name), k) for k in kind):
                return False

        return True

    return condition("the types of arguments must be valid", predicate, True)

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
        class InvariantContractor(c):
            pass

        for name, value in [(name, getattr(c, name)) for name in dir(c)]:
            if callable(value) and not isinstance(value, type):
                if name in ("__getitem__", "__setitem__", "__lt__", "__le__", "__eq__",
                            "__ne__", "__gt__", "__ge__", "__init__") or not name.startswith("__"):
                    setattr(InvariantContractor, name,
                            condition(description, predicate, name != "__init__", True, True)(value))
        return InvariantContractor
    return invariant

if not __debug__:
    def require(description, predicate):
        def func(f):
            return f
        return func

    def ensure(description, predicate):
        def func(f):
            return f
        return func

    def invariant(description, predicate):
        def func(c):
            return c
        return func

if __name__ == "__main__":
    import doctest
    doctest.testmod()
