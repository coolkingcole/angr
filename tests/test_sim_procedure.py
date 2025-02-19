import os
import angr
import claripy
import nose
from angr.codenode import BlockNode, HookNode, SyscallNode

BIN_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'binaries')

def test_ret_float():
    class F1(angr.SimProcedure):
        def run(self):
            return 12.5

    p = angr.load_shellcode(b'X', arch='i386')

    p.hook(0x1000, F1(prototype='float (x)();'))
    p.hook(0x2000, F1(prototype='double (x)();'))

    s = p.factory.call_state(addr=0x1000, ret_addr=0, prototype='float(x)()')
    succ = s.step()
    nose.tools.assert_equal(len(succ.successors), 1)
    s2 = succ.flat_successors[0]
    nose.tools.assert_false(s2.regs.st0.symbolic)
    nose.tools.assert_equal(s2.solver.eval(s2.regs.st0.raw_to_fp()), 12.5)

    s = p.factory.call_state(addr=0x2000, ret_addr=0, prototype='double(x)()')
    succ = s.step()
    nose.tools.assert_equal(len(succ.successors), 1)
    s2 = succ.flat_successors[0]
    nose.tools.assert_false(s2.regs.st0.symbolic)
    nose.tools.assert_equal(s2.solver.eval(s2.regs.st0.raw_to_fp()), 12.5)

    p = angr.load_shellcode(b'X', arch='amd64')

    p.hook(0x1000, F1(prototype='float (x)();'))
    p.hook(0x2000, F1(prototype='double (x)();'))

    s = p.factory.call_state(addr=0x1000, ret_addr=0, prototype='float(x)()')
    succ = s.step()
    nose.tools.assert_equal(len(succ.successors), 1)
    s2 = succ.flat_successors[0]
    res = s2.registers.load('xmm0', 4).raw_to_fp()
    nose.tools.assert_false(res.symbolic)
    nose.tools.assert_equal(s2.solver.eval(res), 12.5)

    s = p.factory.call_state(addr=0x2000, ret_addr=0, prototype='double(x)()')
    succ = s.step()
    nose.tools.assert_equal(len(succ.successors), 1)
    s2 = succ.flat_successors[0]
    res = s2.registers.load('xmm0', 8).raw_to_fp()
    nose.tools.assert_false(res.symbolic)
    nose.tools.assert_equal(s2.solver.eval(res), 12.5)

def test_syscall_and_simprocedure():
    bin_path = os.path.join(BIN_PATH, 'tests', 'cgc', 'CADET_00002')
    proj = angr.Project(bin_path, auto_load_libs=False)
    cfg = proj.analyses.CFGFast(normalize=True)

    # check syscall
    node = cfg.get_any_node(proj.loader.kernel_object.mapped_base + 1)
    func = proj.kb.functions[node.addr]

    nose.tools.assert_true(node.is_simprocedure)
    nose.tools.assert_true(node.is_syscall)
    nose.tools.assert_false(node.to_codenode().is_hook)
    nose.tools.assert_false(proj.is_hooked(node.addr))
    nose.tools.assert_true(func.is_syscall)
    nose.tools.assert_true(func.is_simprocedure)
    nose.tools.assert_equal(type(proj.factory.snippet(node.addr)), SyscallNode)

    # check normal functions
    node = cfg.get_any_node(0x80480a0)
    func = proj.kb.functions[node.addr]

    nose.tools.assert_false(node.is_simprocedure)
    nose.tools.assert_false(node.is_syscall)
    nose.tools.assert_false(proj.is_hooked(node.addr))
    nose.tools.assert_false(func.is_syscall)
    nose.tools.assert_false(func.is_simprocedure)
    nose.tools.assert_equal(type(proj.factory.snippet(node.addr)), BlockNode)

    # check hooked functions
    proj.hook(0x80480a0, angr.SIM_PROCEDURES['libc']['puts']())
    cfg = proj.analyses.CFGFast(normalize=True)# rebuild cfg to updated nodes
    node = cfg.get_any_node(0x80480a0)
    func = proj.kb.functions[node.addr]

    nose.tools.assert_true(node.is_simprocedure)
    nose.tools.assert_false(node.is_syscall)
    nose.tools.assert_true(proj.is_hooked(node.addr))
    nose.tools.assert_false(func.is_syscall)
    nose.tools.assert_true(func.is_simprocedure)
    nose.tools.assert_equal(type(proj.factory.snippet(node.addr)), HookNode)


if __name__ == '__main__':
    test_ret_float()
    test_syscall_and_simprocedure()
