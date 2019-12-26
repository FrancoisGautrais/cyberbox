from src.httpserver.filecache import filecache
from ..htmlgen import html_gen_fd
import  copy
def inst_include(args, data):
    x=copy.deepcopy(data)
    with filecache.open(args[0]) as f:
        if len(args)>1:
            x.update(args[1])
        return html_gen_fd(f, x)

def inst_get(args, data):
    acc=data
    for x in args:
        acc=acc[x]
    return acc
#
# set(k ,k2, .., kn, value)
#
def inst_set(args, data):
    inst_get(args[:-2], data)[args[-2]]=args[-1]

def inst_cat(args, data):
    acc=""
    for x in args:
        acc+=str(x)
    return  acc

def inst_kv(args, data):
    return (args[0], args[1])

def inst_list(args, data):
    return args

def inst_object(args, data):
    obj={}
    for x in args:
        obj[x[0]]=x[1]
    return obj


def inst_if(args, data):
    x = args[0]
    if x: return args[1]
    elif len(args)>2: return args[2]
    return ""

def inst_not(args, data):
    return not args[0]

def inst_eq(args, data): return not args[0] == args[1]
def inst_diff(args, data): return not args[0] != args[1]
def inst_inf(args, data): return not args[0] < args[1]
def inst_infeq(args, data): return not args[0] <= args[1]
def inst_sup(args, data): return not args[0] > args[1]
def inst_supeq(args, data): return not args[0] >= args[1]