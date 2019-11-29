import jax
import jax.numpy as jnp
from jax.random import _is_prng_key
import numpy
import inspect
import copy
from functools import wraps


def add_fn(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, 'fn', staticmethod(wrapper))
        return func # returning func means func can still be used normally
    return decorator


def add_method(cls):
    # important we keep the self inside the function call !
    def decorator(func, name=''):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        if name == '':
            setattr(cls, func.__name__, wrapper)
        else:
            setattr(cls, name, wrapper)
        return func # returning func means func can still be used normally
    return decorator


def reset(item):
    if type(item) == list or type(item) == tuple:
        [reset(i) for i in item]
    elif hasattr(item, 'eval_value'):
        item.eval_value = None
    if hasattr(item, 'kwargs'):
        for i in item.kwargs.values():
            reset(i)




def getroots(item, roots = []):
    if type(item) == list or type(item) == tuple:
        return roots + sum([getroots(i, roots) for i in item], [])
    elif hasattr(item, 'roots'):
        return roots + item.roots
    else:
        return []


def get(item, tracker):
    if type(item) == list or type(item) == tuple:
        current = [get(i, tracker) for i in item]
        return current
    elif item in tracker:
        return tracker[item]
    elif hasattr(item, 'get'):
        item.get(tracker)
        return tracker[item]
    else:
        return item

def extract_variables(items, acc = []):
    if not isinstance(items, Tensor) and hasattr(items, '__len__'):
        for item in items:
            acc += getdepts(item, acc)
    elif isinstance(items, Variable):
        return [item]
    else:
        return []
    return acc

def extract_variables_placeholders(items, acc = []):
    if not isinstance(items, Tensor) and hasattr(items, '__len__'):
        for item in items:
            acc += getdepts(item, acc)
    elif isinstance(items, Variable) or isinstance(items, Placeholder):
        return [item]
    else:
        return []
    return acc



def isdep(item):
    v = isinstance(item, Variable)
    p = isinstance(item, Placeholder)
    return p or v


def isvar(item):
    if type(item) == list or type(item) == tuple:
        return numpy.sum([isvar(value) for value in item])
    else:
        cond1 = isinstance(item, Tensor)
        cond2 = type(item) == jax.interpreters.partial_eval.JaxprTracer
        cond3 = not callable(item)
        return (cond1 or cond2) and cond3


class Tensor:

    def __init__(self, shape, dtype, roots=[], copyof=None):
        self.copyof = copyof
        self.roots = roots
        self._shape = shape
        self._dtype = dtype

    @property
    def shape(self):
        return self._shape

    @property
    def dtype(self):
        return self._dtype

    @property
    def ndim(self):
        return len(self.shape)

    @property
    def T(self):
        pass

    def get(self, tracker=None):
        if self.copyof is not None:
            output = self.copyof.get(tracker)
            tracker[self] = output
            return output




class Op(Tensor):
    """an Op generates a Tensor object obtained from a function"""

    name = ''

    def __init__(self, *args, roots=[], **kwargs):
        self.kwargs = kwargs
        self.print_name = 'name=' + self.name

        # for convenience we only deal with kwargs, and thus transform
        # any given arg into a kwarg based on the function signature
        signature = list(inspect.signature(self.fn).parameters.keys())
        for arg, name in zip(args, signature[:len(args)]):
            self.kwargs.update({name: arg})
        kwargs = self.kwargs.copy()

        # set roots
        roots = getroots([i for i in kwargs.values()]) + roots
        roots = list(set(roots))

        # set shape and dtype:  we to use the automatic shape evaluation.
        # We take care of some problematic cases happening when a parameter
        # such as the shape in the reshape function is given. 
        # When trying to infer the shape, each function input is given as
        # a tracer to monitor internal computations. But those constant
        # parameters do not that support tracing, we thus have to infer
        # the shape using a tweaked function with them not as args/kwargs
        # the kwargs that are constant are moved into extra_kwargs
        extra_kwargs = {}
        for name, arg in list(kwargs.items()):
            if name == 'key' or not isvar(arg):
                extra_kwargs.update({name: arg})
                del kwargs[name]

        # now use the builin function to infer shape and dtype given a
        # lambda jax function
        self.kwargs, self.extra_kwargs = kwargs, extra_kwargs
        tree = jax.eval_shape(lambda **b: self.fn(**b, **self.extra_kwargs),
                              **self.kwargs)
        shape, dtype = tree.shape, tree.dtype

        super().__init__(shape, dtype, roots)


    def __repr__(self):
        return '(Op: ' + self.print_name + 'dtype=' + str(self.dtype) + \
               ', shape='+str(self.shape) + ')'

    def __str__(self):
        return self.__repr__()


    def get(self, tracker=None):
        if tracker is None:
            tracker = dict()
        if self in tracker:
            return tracker[self]

        # evaluate the function kwargs as explicit jax arrays
        kwargs = dict()
        for name, var in list(self.kwargs.items()):
            kwargs.update({name: get(var, tracker)})
        tracker[self] = self.fn(**kwargs, **self.extra_kwargs)
        return tracker[self]





class RandomOp(Op):
    """
    This class creates a :obj:`Tensor` object that given a function (see below)
    and its inputs can be used as a Node in the graph construction. This class
    is specialized to deal with random functions, if the function does not
    take a jax.PRNGKey as first argument, then it should not be used.

    Notes:
        This class is not meant to be used by the user. To create your own
        callable node, see :class:`RandomOp`.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    Examples:
        >>> node = RandomTensor(jax.random.bernoulli, 0, args=(0.5, (3, 3)))
        >>> print(node)
        (RandomTensor : name=custom, dtype=bool, shape=(3, 3))
        >>> node + 2
        (Tensor, dtype=int32, shape=(3, 3))
    """

    def __init__(self, *args, seed=None, **kwargs):
        if seed is None:
            seed = 0
        self.seed = seed
        key = jax.random.PRNGKey(seed)
        super().__init__(key, *args, **kwargs, roots=[self])

    def __repr__(self):
        return '(RandomTensor: ' + self.descr + self.print_name + 'dtype='\
                +  str(self.dtype) + ', shape='+str(self.shape) + ')'

    def get(self, tracker=None):
        if tracker is None:
            tracker = dict()
        elif self in tracker:
            return tracker[self]

        # argument list
        if 'rng' in tracker:
            key = jax.random.PRNGKey(self.seed+tracker['rng'])
        else:
            key = jax.random.PRNGKey(self.seed)

        # kwarg dictionnary
        kwargs = dict()
        for name, var in self.kwargs.items():
            kwargs.update({name: get(var, tracker)})
        if 'key' in self.extra_kwargs:
            del self.extra_kwargs['key']
        tracker[self] = self.fn(key, **kwargs, **self.extra_kwargs)
        return tracker[self]






class SubTensor(Tensor):

    def __init__(self, shape, dtype, index, parent, roots, name=''):
        self.parent = parent
        self.index = index
        super().__init__(shape, dtype, roots=roots)

    def get(self, tracker=None):
        return self.parent.get(tracker)[self.index]



class Tuple(tuple):

    def __new__ (cls, fn, shapes=None, dtypes=None, args=[], kwargs={}):
        trees = jax.eval_shape(lambda *a, **b: fn(*a, **b), *args,
                              **kwargs)
        items = [SubTensor(t.shape, t.dtype, i, None, roots=[])
                      for i, t in enumerate(trees)]

        return super(Tuple, cls).__new__(cls, tuple(items))

    def __init__(self, fn_or_list, shapes=None, dtypes=None, args=[], kwargs={}):

        self.args = args
        self.kwargs = kwargs
        self.fn = fn_or_list
        self.name = ''
        # set roots
        roots = list()
        for value in kwargs.values():
            if hasattr(value, 'roots'):
                roots += value.roots
        for value in args:
            if hasattr(value, 'roots'):
                roots += value.roots

        roots = list(set(roots))
        for item in self:
            item.parent = self

        # now use the built-in function to infer shape and dtype given a
        # lambda jax function
        self.args, self.kwargs = args, kwargs

    def get(self, tracker=None):
        if tracker is None:
            tracker = dict()
        if self in tracker:
            return tracker[self]

        # kwarg dictionnary
        args = list()
        for var in self.args:
            args.append(get(var, tracker))

        kwargs = dict()
        for name, var in self.kwargs.items():
            kwargs.update({name: get(var, tracker)})

        # we add the list object itself into the dictionnary first
        tracker[self] = tuple(self.fn(*args, **kwargs))

        # then we add each element of the list into the dictionnary
        for i in range(len(self)):
            tracker[self[i]] = tracker[self][i]

        return tracker[self]



class Variable(Tensor):

    def __init__(self, value, name='', trainable=True):
        self.trainable = trainable
        self.name = name
        if 1:#not isinstance(value, jax.interpreters.xla.DeviceArray):
            self.value = value
            self.init_value = copy.deepcopy(self.value)
            if numpy.isscalar(value):
                shape = ()
                dtype = type(value)
            else:
                shape = self.value.shape
                dtype = self.value.dtype
#        else:
#            self.value = value
#            shape = value.shape
#            dtype = value.dtype
        super().__init__(shape, dtype, roots=[self])

    def reset(self):
        self.value = self.init_value

    def __repr__(self):
        return '(Variable: ' + self.name + 'dtype=' + str(self.dtype) + \
               ', shape='+str(self.shape) + ', trainable='+str(self.trainable) + ')'

    def get(self, tracker):
        if self not in tracker:
            tracker[self] = self.value
        return tracker[self]


class Placeholder(Tensor):

    def __init__(self, shape, dtype, name=''):
        self.name = name
        super().__init__(shape, dtype, roots=[self])

    def __repr__(self):
        return '(Placeholder: ' + self.name + 'dtype=' + str(self.dtype) + \
               ', shape='+str(self.shape) + ')'

    def get(self, tracker):
        if self not in tracker:
            raise ValueError(' no value given for placeholder {}'.format(self))
        return tracker[self]

def placeholder_like(item, name=''):
    return Placeholder(item.shape, item.dtype, name=name)


def theanofn_to_jaxfn(*args, _fn, **kwargs):
    # treat the args
    pargs = list()
    for arg in args:
        pargs.append(placeholder_like(arg))
    # treat the kwargs
    pkwargs = dict()
    for name, var in kwargs.items():
        pkwargs[name] = placeholder_like(var)
    output = _fn(*pargs, **pkwargs)
    feed_dict = list(zip(pargs, args)) + list(zip(pkwargs.values(),
                                                  kwargs.values()))
    return output.get(dict(feed_dict))

