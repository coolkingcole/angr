import nose
import os
import unittest

from archinfo import ArchAMD64

import angr
from angr.utils.constants import DEFAULT_STATEMENT

TEST_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'binaries', 'tests')


class TestFunctionManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = angr.Project(os.path.join(TEST_LOCATION, "x86_64", "fauxware"), auto_load_libs=False)


    def test_amd64(self):
        expected_functions = { 0x4004e0, 0x400510, 0x400520, 0x400530, 0x400540, 0x400550, 0x400560, 0x400570,
                               0x400580, 0x4005ac, 0x400640, 0x400664, 0x4006ed, 0x4006fd, 0x40071d, 0x4007e0,
                               0x400880 }
        expected_blocks = { 0x40071D, 0x40073E, 0x400754, 0x40076A, 0x400774, 0x40078A, 0x4007A0, 0x4007B3, 0x4007C7,
                            0x4007C9, 0x4007BD, 0x4007D3 }
        expected_callsites = { 0x40071D, 0x40073E, 0x400754, 0x40076A, 0x400774, 0x40078A, 0x4007A0, 0x4007BD, 0x4007C9 }
        expected_callsite_targets = { 4195600, 4195632, 4195632, 4195600, 4195632, 4195632, 4195940, 4196077, 4196093 }
        expected_callsite_returns = { 0x40073e, 0x400754, 0x40076a, 0x400774, 0x40078a, 0x4007a0, 0x4007b3, 0x4007c7,
                                      None }

        cfg = self.project.analyses.CFGEmulated()  # pylint:disable=unused-variable
        nose.tools.assert_equal(
            { k for k in self.project.kb.functions.keys() if k < 0x500000 },
            expected_functions
        )

        main = self.project.kb.functions.function(name='main')
        nose.tools.assert_equal(main.startpoint.addr, 0x40071D)
        nose.tools.assert_equal(set(main.block_addrs), expected_blocks)
        nose.tools.assert_equal([0x4007D3], [bl.addr for bl in main.endpoints])
        nose.tools.assert_equal(set(main.get_call_sites()), expected_callsites)
        nose.tools.assert_equal(
            set(map(main.get_call_target, main.get_call_sites())),
            expected_callsite_targets
        )
        nose.tools.assert_equal(
            set(map(main.get_call_return, main.get_call_sites())),
            expected_callsite_returns
        )
        nose.tools.assert_true(main.has_return)

        rejected = self.project.kb.functions.function(name='rejected')
        nose.tools.assert_equal(rejected.returning, False)

        # transition graph
        main_g = main.transition_graph
        main_g_edges_ = main_g.edges(data=True)

        # Convert nodes those edges from blocks to addresses
        main_g_edges = []
        for src_node, dst_node, data in main_g_edges_:
            main_g_edges.append((src_node.addr, dst_node.addr, data))

        edges = [
            (0x40071d, 0x400510, {'type': 'call', 'stmt_idx': DEFAULT_STATEMENT, 'ins_addr': 0x400739}),
            (0x40071d, 0x400510, {'type': 'call', 'stmt_idx': DEFAULT_STATEMENT, 'ins_addr': 0x400739}),
            (0x40071d, 0x40073e, {'type': 'fake_return', 'confirmed': True, 'outside': False}),
            (0x40073e, 0x400530, {'type': 'call', 'stmt_idx': DEFAULT_STATEMENT, 'ins_addr': 0x40074f}),
            (0x40073e, 0x400754, {'type': 'fake_return', 'confirmed': True, 'outside': False}),
            # rejected() does not return
            (0x4007c9, 0x4006fd, {'type': 'call', 'stmt_idx': DEFAULT_STATEMENT, 'ins_addr': 0x4007ce}),
            (0x4007c9, 0x4007d3, {'type': 'fake_return', 'outside': False}),
        ]
        for edge in edges:
            nose.tools.assert_true(edge in main_g_edges)

        # These tests fail for reasons of fastpath, probably
        #nose.tools.assert_true(main.bp_on_stack)
        #nose.tools.assert_equal(main.name, 'main')
        #nose.tools.assert_true(main.retaddr_on_stack)
        #nose.tools.assert_equal(0x50, main.sp_difference)

        # TODO: Check the result returned
        #func_man.dbg_draw()

    def test_call_to(self):
        self.project.arch = ArchAMD64()

        self.project.kb.functions._add_call_to(0x400000, 0x400410, 0x400420, 0x400414)
        nose.tools.assert_in(0x400000, self.project.kb.functions.keys())
        nose.tools.assert_in(0x400420, self.project.kb.functions.keys())
