

def inst_include(args, data):
    with open(args[0]) as f:
        return f.read()

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


