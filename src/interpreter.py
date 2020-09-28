"""
Incomplete Interpreter for Java 8
warning [goto] statement is not working as expected
"""
from pprint import pprint


def get_index(offset, codes):
    index_cnt = 0
    offset_cnt = 0
    for op in codes:
        if offset_cnt >= offset:
            return index_cnt
        op_cnt = len(op["args"]) + 1
        offset_cnt += op_cnt
        index_cnt += 1
    raise Exception("offset error",offset,len(codes))


def get_constant_value(index, constants):
    c = constants[index - 1]
    # print(index,c)
    if c["tag"] == "CONSTANT_String":
        return get_constant_value(c["string_index"], constants)
    if c["tag"] == "CONSTANT_Class":
        return get_constant_value(c["name_index"], constants)
    if c["tag"] == "CONSTANT_Fieldref":
        return get_constant_value(c["name_and_type_index"], constants)
    if c["tag"] == "CONSTANT_Methodref":
        return get_constant_value(c["name_and_type_index"], constants)
    if c["tag"] == "CONSTANT_NameAndType":
        return get_constant_value(c["name_index"], constants)
    if c["tag"] == "CONSTANT_Utf8":
        return c["value"]
    raise NotImplementedError(c)


def getstatic(opcode, constants, stack):
    indexbyte1, indexbyte2 = opcode["args"]
    index = (indexbyte1 << 8) | indexbyte2
    value = get_constant_value(index, constants)
    stack.append(value)


def ldc(opcode, constants, stack):
    index = opcode["args"][0]
    value = get_constant_value(index, constants)
    stack.append(value)


def invokespecial(opcode, constants, frame):
    stack = frame["stack"]
    indexbyte1, indexbyte2 = opcode["args"]
    index = (indexbyte1 << 8) | indexbyte2
    method = get_constant_value(index, constants)
    stack.append(method)


def invokevirtual(opcode, constants, frame):
    stack = frame["stack"]
    indexbyte1, indexbyte2 = opcode["args"]
    index = (indexbyte1 << 8) | indexbyte2
    value = get_constant_value(index, constants)
    method_arg = ""
    if value == "append":
        method_arg = stack.pop()
        a = stack.pop()
        if a == "<init>":
            a = ""
        if isinstance(a,int) or isinstance(method_arg,int): #Hack don't want to read the spec
            result = str(a) + str(method_arg)
        else:
            result = method_arg + a
        stack.append(result)
        return
    if value == "toString":
        method_arg = stack.pop()
        _ = stack.pop() #object ref
        stack.append(method_arg)
        return
    if value == "println":
        method_arg = stack.pop()
        dest = stack.pop()
        # if dest == "out":
        print('\x1b[1;32m',method_arg,'\x1b[0m')
        return
    raise NotImplementedError(value, method_arg)


# https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-6.html#jvms-6.5.astore
def aload(opcode, constants, frame, index):
    locals = frame["locals"]
    variable = locals[index]
    frame["stack"].append(variable)


# https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-6.html#jvms-6.5.astore
def astore(opcode, constants, frame, index):
    variable = frame["stack"].pop()
    frame["locals"].insert(index, variable)


def iconst(opcode, constants, frame, index):
    stack = frame["stack"]
    stack.append(index)


def istore(opcode, constants, frame, index):
    stack = frame["stack"]
    var = stack.pop()
    frame["locals"][index] = var


def iinc(opcode, constants, frame):
    index, const = opcode["args"]
    frame["locals"][index] += const


def goto(opcode, constants, frame, codes):
    stack = frame["stack"]
    branchbyte1 , branchbyte2 = opcode["args"]
    branchoffset = (branchbyte1 << 8) | branchbyte2
    # work around
    index = get_index(84, codes) - 1  # pc+=1 and classfile 1 based
    print("[goto hardcoded]", branchoffset, index)
    frame["pc"] = index


def if_icmp(opcode, constants, frame, cond, codes):
    stack = frame["stack"]
    indexbyte1, indexbyte2 = opcode["args"]
    offset = (indexbyte1 << 8) | indexbyte2

    value1 = stack.pop()
    value2 = stack.pop()
    if cond(value1, value2):
        index = get_index(offset, codes) - 2  # pc+=1 and classfile 1 based
        print("passed, [goto]", offset, index)
        frame["pc"] = index
def bipush(opcode,constants,frame):
    stack = frame["stack"]
    arg = opcode["args"][0]
    stack.append(arg)
def iadd(opcode,constants,frame):
    stack = frame["stack"]
    value1 = stack.pop()
    value2 = stack.pop()
    stack.append(value1+value2)

# https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-6.html#jvms-6.5.new
def new(opcode, constants, frame):
    # todo, heap should be used
    indexbyte1, indexbyte2 = opcode["args"]
    index = (indexbyte1 << 8) | indexbyte2
    value = get_constant_value(index, constants)
    frame["stack"].append(value)


def dup(opcode, constants, frame):
    stack = frame["stack"]
    d = stack[len(stack)-1] #from first or last?
    stack.append(d)

# Frame and Run Time Data
# https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-2.html#jvms-2.5


def run(classfile):
    frame = {
        "locals": [None for _ in range(5)],  # should be set from max locals
        "stack": [],
        "pc": 0

    }  # replace datatype stack
    methods = classfile["methods"]
    constants = classfile["constants"]
    for m in methods:
        name = m["name"]
        if name == "<init>":
            continue
        if name == "main":
            # pprint(m)
            attributes = m['attributes']
            for attribute in attributes:
                if attribute['attribute_name'] != "Code":
                    raise NotImplementedError("interpreter failed")
                print("code block detected, attempting to run.")
                codes = attribute["codes"]
                while frame["pc"] < len(codes):
                    pprint(frame)
                    opcode = codes[frame["pc"]]
                    op = opcode["op"]
                    print(op,opcode["args"])
                    if op == "getstatic":
                        getstatic(opcode, constants, frame["stack"])
                    elif op == "bipush":
                        bipush(opcode, constants, frame)
                    elif op == "ldc":
                        ldc(opcode, constants, frame["stack"])
                    elif op == "iadd":
                        iadd(opcode, constants, frame)
                    elif op == "invokevirtual":
                        invokevirtual(opcode, constants, frame)
                    elif op == "istore":
                        istore(opcode, constants, frame, index=opcode["args"][0])
                    elif op == "istore_1":
                        istore(opcode, constants, frame, index=1)
                    elif op == "istore_2":
                        istore(opcode, constants, frame, index=2)
                    elif op == "iload":
                        aload(opcode, constants, frame, index=opcode["args"][0])  # hack
                    elif op == "iload_2":
                        aload(opcode, constants, frame, index=2)  # hack
                    elif op == "iconst_0":
                        iconst(opcode, constants, frame, index=0)
                    elif op == "iconst_2":
                        iconst(opcode, constants, frame, index=2)
                    elif op == "iconst_3":
                        iconst(opcode, constants, frame, index=3)
                    elif op == "iconst_4":
                        iconst(opcode, constants, frame, index=4)
                    elif op == "if_icmpne":
                        if_icmp(opcode, constants, frame,
                                cond=lambda x, y: x != y, codes=codes)
                    elif op == "if_icmpge":
                        if_icmp(opcode, constants, frame,
                                cond=lambda x, y: x >= y, codes=codes)
                    elif op == "if_icmple":
                        if_icmp(opcode, constants, frame,
                                cond=lambda x, y: x <= y, codes=codes)
                    elif op == "goto":
                        goto(opcode, constants, frame, codes=codes)
                    elif op == "astore":
                        astore(opcode, constants, frame, index=opcode["args"][0])
                    elif op == "astore_1":
                        astore(opcode, constants, frame, index=1)
                    elif op == "astore_2":
                        astore(opcode, constants, frame, index=2)
                    elif op == "astore_3":
                        astore(opcode, constants, frame, index=2)
                    elif op == "iload_1":
                        aload(opcode, constants, frame, index=1)
                    elif op == "aload":
                        aload(opcode, constants, frame, index=opcode["args"][0])
                    elif op == "aload_1":
                        aload(opcode, constants, frame, index=1)
                    elif op == "aload_2":
                        aload(opcode, constants, frame, index=2)
                    elif op == "aload_3":
                        aload(opcode, constants, frame, index=3)
                    elif op == "new":
                        new(opcode, constants, frame)
                    elif op == "iinc":
                        iinc(opcode, constants, frame)
                    elif op == "dup":
                        dup(opcode, constants, frame)
                    elif op == "invokespecial":
                        invokespecial(opcode, constants, frame)
                    elif op == "return":
                        break
                    else:
                        raise NotImplementedError(opcode)
                    frame["pc"] = frame["pc"] + 1
