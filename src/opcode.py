OPCODES = {
    "10": ("bipush",1),
    "19": ("aload", 1),
    "2a": ("aload_0", 0),
    "2b": ("aload_1",0),
    "2c": ("aload_2",0),
    "2d": ("aload_3",0),
    "07": ("iconst_4", 0),
    "b7": ("invokespecial", 2),
    "01": ("aconst_null", 0),
    "b0": ("areturn", 0),
    "b1": ("return", 0),
    "03": ("iconst_0", 0),
    "36": ("istore",1),
    "3c": ("istore_1", 0),
    "3d": ("istore_2", 0),
    "b8": ("invokestatic", 2),
    "02": ("iconst_m1", 0),
    "3a": ("astore",1),
    "4d": ("astore_2", 0),
    "4e": ("astore_3", 0),
    "3e": ("istore_3", 0),
    "15": ("iload", 1),
    "1c": ("iload_2", 0),
    "1d": ("iload_3", 0),
    "a0": ("if_icmpne", 2),
    "a2": ("if_icmpge", 2),
    "32": ("aaload", 0),
    "b2": ("getstatic", 2),
    "bb": ("new", 2),
    "04": ("iconst_1", 0),
    "59": ("dup", 0),
    "05": ("iconst_2", 0),
    "12": ("ldc", 1),
    "06": ("iconst_3", 0),
    "b6": ("invokevirtual", 2),
    "1b": ("iload_1", 0),
    "08": ("iconst_5", 0),
    "09": ("lconst_0", 0),
    "0a": ("lconst_1", 0),
    "a4": ("if_icmple", 2),
    "0b": ("fconst_0", 0),
    "84": ("iinc", 2),
    "a7": ("goto", 2),
    "ff": ("impdep2", 0),  # reserved ?
    "3b": ("istore_0", 0),
    "14": ("ldc2_w", 0),
    "1a":( "iload_0",0),
    "68":( "imul",0),
    "60":( "iadd",0),
    "0c":( "fconst_1",0),
    "4c":("astore_1",0)
}


def parse_codes(code_length, f):
    codes = []
    i = 0
    while i < code_length:
        op, consumed = parse_op(f)
        codes.append(op)  # less than length 1 at a time?
        i += consumed
    return codes


def parse_op(f):
    b = f.read(1)
    h = b.hex()
    args_length = 0
    if h not in OPCODES:
        raise NotImplementedError("opcode", b.hex())
    op,args_length = OPCODES[h]
    args = []
    for _ in range(args_length):
        arg = to_int(f.read(1))
        args.append(arg)
    return {"op": op, "args": args}, args_length + 1
    


def to_int(b: bytes) -> int:
    if not b:
        raise Exception("EOF")
    return int.from_bytes(b, 'big', signed=False)
