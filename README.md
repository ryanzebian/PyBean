# PyBean
JVM ByteCode disassembler and interpreter implemented in python3 

## Warning
There be dragons. Not all the specification has been implemented.       
## Setup
1. Python3 installed.
2. install [Java8](https://openjdk.java.net/install/) running and set `JAVA_HOME` variable in [src/pybean.py](src/pybean.py)
```bash
computer:Pybean$ make
cd src/ && python3 pybean.py
INFO:__main__:pool_count 46
INFO:__main__:saved classfile: ../build/classfile.json
code block detected, attempting to run.
...           
invokevirtual [0, 10]
{'locals': [None, 6, 'World!', 'Hello', None, None, None],
 'pc': 23,
 'stack': ['out', 'java/lang/StringBuilder', 'Hello World!6']}

 Hello World!6 
```



## JVM Specification
https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-4.html
