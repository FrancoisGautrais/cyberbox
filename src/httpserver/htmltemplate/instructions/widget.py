from ..widget import mat_select, mat_input_text, mat_switch, mat_row
from ...utils import tuplist_to_dict

def inst_select(args, data):
    x=mat_select(args[0], args[1], args[2], False, data["user"]["mobile"]).html()
    print(x)
    return x

def inst_multiple_select(args, data):
    return mat_select(args[0], args[1], args[2],True, data["user"]["mobile"]).html()

def inst_input_text(args, data):
    return mat_input_text(*args).html()

def inst_checkbox(args, data): return mat_switch(*args).html()

def inst_row(args, data): return mat_row(*args).html()