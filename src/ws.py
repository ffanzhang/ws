#!/usr/bin/env python3

import sys
import operator
from enum import Enum, unique


@unique
class Stage(Enum):
    IMP = 0
    CMD = 1
    PARAM = 2
    UNKNOWN = 3


@unique
class Mode(Enum):
    STACK = 0
    ARITH = 1
    HEAP = 2
    FLOW = 3
    IO = 4
    UNKNOWN = 5


@unique
class StackCmds(Enum):
    PUSH = 0
    DUPL = 1
    SWAP = 2
    DISC = 3


@unique
class ArithCmds(Enum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3
    MOD = 4


@unique
class HeapCmds(Enum):
    PUT = 0
    GET = 1


@unique
class FlowCmds(Enum):
    MARK = 0
    CALL = 1
    JUMP = 2
    JZER = 3
    JNEG = 4
    ENDS = 5
    ENDP = 6


@unique
class IOCmds(Enum):
    OTC = 0
    OTN = 1
    RDC = 2
    RDN = 3


@unique
class Token(Enum):
    S = ' '
    T = '\t'
    L = '\n'


class Trie:
    _c = ''
    _children = {}
    _identifier = None

    def __init__(self, c):
        self._c = c
        self._children = {}
        self._identifier = None

    def addChild(self, c):
        if c not in self._children.keys():
            self._children[c] = Trie(c)

    def getChild(self, c):
        return self._children.get(c, None)

    def setIdentifier(self, identifier):
        self._identifier = identifier

    def getIdentifier(self):
        return self._identifier

    def __str__(self):
        s = "{\""
        if self._c in ' \t\n':
            s += str(Token(self._c))
        else:
            s += self._c
        s += "\":"

        s += "["
        li = []
        if len(self._children) > 0:
            for k in self._children.keys():
                li.append(str(self._children[k]))
        else:
            li.append(str(self._identifier))
        s += ','.join(li)
        s += "]"
        s += "}"
        return s


def setupTrie(d):
    trie = Trie('^')
    for key, value in d.items():
        p = trie
        for k in key:
            p.addChild(k)
            p = p.getChild(k)
        p.setIdentifier(value)
    return trie


modes = {
    ' ': Mode.STACK,
    '\t ': Mode.ARITH,
    '\t\t': Mode.HEAP,
    '\n': Mode.FLOW,
    '\t\n': Mode.IO
}

stackCmds = {
    ' ': StackCmds.PUSH,
    '\n ': StackCmds.DUPL,
    '\n\t': StackCmds.SWAP,
    '\n\n': StackCmds.DISC,
}

arithCmds = {
    '  ': ArithCmds.ADD,
    ' \t': ArithCmds.SUB,
    ' \n': ArithCmds.MUL,
    '\t ': ArithCmds.DIV,
    '\t\t': ArithCmds.MOD
}

heapCmds = {' ': HeapCmds.PUT, '\t': HeapCmds.GET}

flowCmds = {
    '  ': FlowCmds.MARK,
    ' \t': FlowCmds.CALL,
    ' \n': FlowCmds.JUMP,
    '\t ': FlowCmds.JZER,
    '\t\t': FlowCmds.JNEG,
    '\t\n': FlowCmds.ENDS,
    '\n\n': FlowCmds.ENDP
}

ioCmds = {
    '  ': IOCmds.OTC,
    ' \t': IOCmds.OTN,
    '\t ': IOCmds.RDC,
    '\t\t': IOCmds.RDN
}

impTrie = setupTrie(modes)
stackTrie = setupTrie(stackCmds)
arithTrie = setupTrie(arithCmds)
heapTrie = setupTrie(heapCmds)
flowTrie = setupTrie(flowCmds)
ioTrie = setupTrie(ioCmds)

modeToTrie = {
    Mode.STACK: stackTrie,
    Mode.ARITH: arithTrie,
    Mode.HEAP: heapTrie,
    Mode.FLOW: flowTrie,
    Mode.IO: ioTrie
}

#code = sys.stdin.read()
imp = []
par = []
stk = []
labels = {}
mode = Mode.UNKNOWN
cmd = None

it = impTrie
cmdTrie = None
stage = Stage.IMP
token_charset = '\t\n '

def arith_op(stack, arith_method):
    try:
        a, b = stack[-1], stack[-2]
        stack.pop()
        stack.pop()
        stack.append(arith_method(a, b))
    except IndexError:
        raise Exception("Arith Exception")

def process(code, stage, it):
    for i, e in enumerate(code):
        if e not in token_charset:
            continue

        if Stage.IMP == stage:
            it = it.getChild(e)
            if it != None:
                mode = it.getIdentifier()
                if mode != None:
                    cmdTrie = modeToTrie.get(mode, None)
                    it = cmdTrie
                    stage = Stage.CMD
            else:
                raise Exception("Parse IMP error")

        elif Stage.CMD == stage:
            it = it.getChild(e)
            if it != None:
                cmd = it.getIdentifier()
                if cmd != None:
                    if StackCmds.PUSH == cmd:
                        par.clear()
                        stage = Stage.PARAM
                    elif StackCmds.DUPL == cmd:
                        if len(stk) > 0:
                            stk.append(stk[-1])
                        stage = Stage.IMP
                        it = impTrie
                    elif StackCmds.SWAP == cmd:
                        if len(stk) >= 2:
                            stk[-1], stk[-2] = stk[-2], stk[-1]
                        stage = Stage.IMP
                        it = impTrie
                    elif StackCmds.DISC == cmd:
                        if len(stk) > 0:
                            stk.pop()
                        stage = Stage.IMP
                        it = impTrie
                    elif IOCmds.OTC == cmd:
                        print(chr(stk[-1]), end='')
                        stage = Stage.IMP
                        it = impTrie
                    elif IOCmds.OTN == cmd:
                        print(stk[-1], end='')
                        stage = Stage.IMP
                        it = impTrie
                    elif ArithCmds.ADD == cmd:
                        arith_op(stk, operator.add)
                        stage = Stage.IMP
                        it = impTrie
                    elif ArithCmds.SUB == cmd:
                        arith_op(stk, operator.sub)
                        stage = Stage.IMP
                        it = impTrie
                    elif ArithCmds.MUL == cmd:
                        arith_op(stk, operator.mul)
                        stage = Stage.IMP
                        it = impTrie
                    elif ArithCmds.DIV == cmd:
                        arith_op(stk, operator.floordiv)
                        stage = Stage.IMP
                        it = impTrie
                    elif ArithCmds.MOD == cmd:
                        arith_op(stk, operator.mod)
                        stage = Stage.IMP
                        it = impTrie
                    elif FlowCmds.MARK == cmd:
                        stage = Stage.PARAM
                    elif FlowCmds.ENDP == cmd:
                        return
                    else:
                        raise Exception("Not Implemented {}".format(cmd))
            else:
                raise Exception("Parse CMD error")

        elif Stage.PARAM == stage:
            if e != '\n':
                par.append(e)
            else:
                s = ''.join(list(map(lambda x: '0' if x == ' ' else '1', par)))
                if len(s) > 0:
                    num = int(s, 2)
                    if StackCmds.PUSH == cmd:
                        stk.append(num)
                    if FlowCmds.MARK == cmd:
                        labels[s] = i + 1
                par.clear()
                stage = Stage.IMP
                it = impTrie


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: ./ws.py <path_of_ws_program>, or python/3 ws.py <path_of_ws_program>"
        )
    else:
        path = sys.argv[1]
        with open(path, 'r') as f:
            code = f.read()
            process(code, stage, it)
