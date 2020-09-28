#!/usr/bin/env python3
"""
1. Generates JVM classfile based on spec https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html
2. Interprets the classfile
"""
from constants import CONSTANT_POOL_TAGS, ACCESS_FLAGS, METHOD_ACCESS_FLAGS, VERIFICATION_TYPE_INFO
from opcode import parse_codes
import logging
import sys
import interpreter
import json
import logging
import subprocess

SOURCE_FILE = "HelloWorld.java"
BUILD_DIR = "../build"
JAVA_HOME = "/Library/Java/JavaVirtualMachines/adoptopenjdk-8.jdk/Contents/Home/bin/"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    setup()
    parser = ByteCodeParser()
    classfile = parser.parse(file_path=BUILD_DIR+"/HelloWorld.class")
    # interpreter.run(classfile)


def setup():
    s = subprocess.run(["rm", "-rf", BUILD_DIR])
    s = subprocess.run(["mkdir", BUILD_DIR])
    s = subprocess.run([f"{JAVA_HOME}javac", SOURCE_FILE, "-d", BUILD_DIR])
    with open(BUILD_DIR+"/bytecode.txt", "w") as f:
        s = subprocess.run(
            [f"{JAVA_HOME}javap", "-verbose", BUILD_DIR+"/HelloWorld.class"], stdout=f)


class ByteCodeParser():
    def __init__(self):
        pass

    def parse(self, file_path):
        """
        Parses a classfile and returns as a dict based on java8 spec. https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html#jvms-4.1
        """
        self.classfile = {}
        with open(file_path, "rb") as f:
            magic = self.__parse_magic(f)
            minor = to_int(f.read(2))
            major = to_int(f.read(2))
            constant_pool_count = to_int(f.read(2)) - 1  # 1 based index
            constants = self.__parse_constants(f, constant_pool_count)
            access_flags = ACCESS_FLAGS[f.read(2).hex()]
            this_class_index = to_int(f.read(2))
            this_class = self.classfile["constants"][this_class_index - 1]
            super_class_index = to_int(f.read(2))
            super_class = constants[super_class_index - 1]
            interfaces_count = to_int(f.read(2))
            interfaces = [self.__parse_interface(f)
                          for i in range(interfaces_count)]
            fields_count = to_int(f.read(2))
            fields = [self.__parse_field(f) for i in range(fields_count)]
            method_count = to_int(f.read(2))
            methods = [self.__parse_method(f) for i in range(method_count)]
        self.classfile = {
            "magic": magic,
            "major": major,
            "minor": minor,
            "constant_pool_count": constant_pool_count,
            "constants": constants,
            "access_flags": access_flags,
            "this_class": this_class,
            "super_class": super_class,
            "interfaces": interfaces,
            "fields": fields,
            "methods": methods
        }
        self.save()
        return self.classfile

    def __parse_magic(self, f):
        magic = f.read(4).hex()
        if magic != 'cafebabe':
            raise Exception("Invalid Class File, missing magic", f.name)
        return magic

    def __parse_constants(self, f, constant_pool_count):
        constants = []
        logger.info(f'pool_count {constant_pool_count}')
        for i in range(constant_pool_count):
            c = self.__parse_constant(f)
            logger.debug(f"#{i+1} ={c['tag']}")
            constants.append(c)
        self.classfile["constants"] = constants  # HACK
        return constants

    def __parse_constant(self, f) -> dict:
        """ parses cp_info https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html#jvms-4.4-140 """
        tag = CONSTANT_POOL_TAGS[to_int(f.read(1))]
        if tag in ("CONSTANT_Methodref", "CONSTANT_Fieldref", "CONSTANT_InterfaceMethodref"):
            class_index = to_int(f.read(2))  # CONSTANT_Class_info
            # CONSTANT_Fieldref_info, we currntly ignore special case for  '<' ('\u003c')
            name_and_type_index = to_int(f.read(2))
            return {
                "tag": tag,
                "class_index": class_index,
                "name_and_type_index": name_and_type_index
            }
        if tag == "CONSTANT_Class":
            name_index = to_int(f.read(2))
            return {
                "tag": tag,
                "name_index": name_index
            }
        if tag == "CONSTANT_String":
            string_index = to_int(f.read(2))
            return {
                "tag": tag,
                "string_index": string_index
            }
        if tag == "CONSTANT_Utf8":
            length = to_int(f.read(2))
            value = f.read(length)
            return {
                "tag": tag,
                "length": length,
                "value": value.decode("UTF8")
            }
        if tag == "CONSTANT_NameAndType":
            name_index = to_int(f.read(2))
            descriptor_index = to_int(f.read(2))
            return {
                "tag": tag,
                "name_index": name_index,
                "descriptor_index": descriptor_index
            }
        raise NotImplementedError(tag)

    def __parse_interface(self, f) -> dict:
        raise NotImplementedError("interface not implemented!")

    def __parse_field(self, f) -> dict:
        raise NotImplementedError("field not implemented!")

    def __parse_method(self, f) -> dict:
        """
        Handle parsing method_info https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html#jvms-4.6-200-A.1
        note, we currenlty ignore flags and rules
        """
        access_flags = f.read(2)
        name_index = to_int(f.read(2))
        name = self.get_constant_utf8(name_index)
        descriptor_index = to_int(f.read(2))
        descriptor = self.get_constant_utf8(descriptor_index)
        attributes_count = to_int(f.read(2))
        attributes = []
        for i in range(attributes_count):
            attribute = self.__parse_attribute(f)
            logger.debug(attribute)
            attributes.append(attribute)
        return {
            "access_flag_fix_me!": access_flags.hex(),
            "name": name,
            "descriptor": descriptor,
            "attributes": attributes
        }

    def __parse_attribute(self, f) -> dict:
        attribute_name_index = to_int(f.read(2))
        attribute_length = to_int(f.read(4))
        attribute_name = self.get_constant_utf8(attribute_name_index)
        if attribute_name == "LineNumberTable":
            line_number_table_length = to_int(f.read(2))
            line_number_table = []
            for i in range(line_number_table_length):
                start_pc = to_int(f.read(2))
                line_number = to_int(f.read(2))
                line_number_table.append(
                    {"start_pc": start_pc, "line_number": line_number})
            logger.debug("line_number_table",line_number_table)
            return {"attribute_name": attribute_name, "line_number_table": line_number_table}
        if attribute_name == "StackMapTable":
            number_of_entries = to_int(f.read(2))
            entries = []
            frame_type = ""
            for i in range(number_of_entries):
                frame_value = to_int(f.read(1))
                if 0 <= frame_value <= 63:
                    frame_type = "SAME"
                    # not working as expected, it should be CHOP
                    entries.append({"frame_type": frame_type,
                                    "frame_value": frame_value})
                    continue
                if 248 <= frame_value <= 250:
                    frame_type = "CHOP"
                    offset_delta = to_int(f.read(2))
                    entries.append(
                        {"frame_type": frame_type, "frame_value": frame_value, "offset_delta": offset_delta})
                    continue
                if 252 <= frame_value <= 254:
                    frame_type = "APPEND"
                    offset_delta = to_int(f.read(2))
                    verification_length = frame_value - 251
                    verification_locals = []
                    for i in range(verification_length):
                        verification = self.parse_verification_info(f)
                        verification_locals.append(verification)
                    entries.append({"frame_type": frame_type, "frame_value": frame_value,
                                    "offset_delta": offset_delta, "locals": verification_locals})
                    continue
                if frame_value == 255:
                    frame_type = "FULL_FRAME"
                    offset_delta = to_int(f.read(2))
                    number_of_locals = to_int(f.read(2))
                    verification_locals = []
                    for i in range(number_of_locals):
                        verification = self.parse_verification_info(f)
                        verification_locals.append(verification)
                    number_of_stack_items = to_int(f.read(2))
                    verification_stack = []
                    for i in range(number_of_stack_items):
                        verification = self.parse_verification_info(f)
                        verification_stack.append(verification)
                    entries.append({"frame_type": frame_type, "frame_value": frame_value,
                                    "offset_delta": offset_delta, "locals": verification_locals, "stack": verification_stack})
                    continue
                raise NotImplementedError(
                    attribute_name, "frame_type", frame_type, "frame_value", frame_value)
            return {"attribute_name": attribute_name, "entries": entries}

        if attribute_name == "Code":
            max_stack = to_int(f.read(2))
            max_locals = to_int(f.read(2))
            # logger.info(f"stack={max_stack},local={max_locals}")
            code_length = to_int(f.read(4))
            codes = parse_codes(code_length, f)

            exception_table_length = to_int(f.read(2))
            exception_table = []
            for i in range(exception_table_length):
                exception = {
                    "start_pc": to_int(f.read(2)),
                    "end_pc": to_int(f.read(2)),
                    "handler_pc": to_int(f.read(2)),
                    "catch_type": to_int(f.read(2)),
                }
                exception_table.append(exception)
            attributes_count = to_int(f.read(2))
            attributes = []
            for i in range(attributes_count):
                attribute = self.__parse_attribute(f)
                attributes.append(attribute)
            return {"attribute_name": attribute_name, "max_stack": max_stack, "max_locals": max_locals, "codes": codes, "exception_table": exception_table, "attributes": attributes}
        raise NotImplementedError(attribute_name)

    def __parse_verification_info(self, f):
        tag = VERIFICATION_TYPE_INFO[to_int(f.read(1))]
        if tag == "ITEM_Integer":
            return {"tag": tag, }
        if tag == "ITEM_Object":  # https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html#jvms-4.4.1
            cpool_index = to_int(f.read(2))
            cpool_value = self.get_constant_value(cpool_index)
            return {"tag": tag, "cpool_index": cpool_index, "cpool_value": cpool_value}
        raise NotImplementedError("unhandled verification tag", tag)

    def get_constant_utf8(self, constant_index):
        logger.debug(f"get_constant_utf8: {constant_index}")
        constants = self.classfile["constants"]
        c = constants[constant_index - 1]
        if c["tag"] != "CONSTANT_Utf8":
            raise Exception("invalid constants index", c)
        logger.debug(c["value"])
        return c["value"]

    def save(self):
        classfile = self.classfile
        with open(BUILD_DIR+"/classfile.json", "w") as f:
            f.write(json.dumps(classfile))
            logger.info(f"saved classfile: {BUILD_DIR}/classfile.json" )

    def get_constant_value(self, index):
        c = self.classfile["constants"][index - 1]
        # logger.info(index,c)
        if c["tag"] == "CONSTANT_String":
            return self.get_constant_value(c["string_index"])
        if c["tag"] == "CONSTANT_Class":
            return self.get_constant_value(c["name_index"])
        if c["tag"] == "CONSTANT_Fieldref":
            return self.get_constant_value(c["name_and_type_index"])
        if c["tag"] == "CONSTANT_Methodref":
            return self.get_constant_value(c["name_and_type_index"])
        if c["tag"] == "CONSTANT_NameAndType":
            return self.get_constant_value(c["name_index"])
        if c["tag"] == "CONSTANT_Utf8":
            return c["value"]
        raise NotImplementedError(c)


def to_int(b: bytes) -> int:
    if not b:
        raise Exception("EOF")
    return int.from_bytes(b, 'big', signed=False)


if __name__ == "__main__":
    main()
