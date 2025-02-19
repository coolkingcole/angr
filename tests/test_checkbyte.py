import angr

import logging
l = logging.getLogger("angr.tests")

import os
test_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'binaries', 'tests')

arches = ( "armel", "i386", "mips", "mipsel", "ppc64", "ppc", "x86_64" )
# TODO: arches += ( "armhf", )

def run_checkbyte(arch):
    p = angr.Project(os.path.join(test_location, arch, "checkbyte"), auto_load_libs=False)
    results = p.factory.simulation_manager().run(n=100) #, until=lambda lpg: len(lpg.active) > 1)

    assert len(results.deadended) == 2
    one = results.deadended[0].posix.dumps(1)
    two = results.deadended[1].posix.dumps(1)
    assert {one, two} == {b"First letter good\n", b"First letter bad\n"}

def test_checkbyte():
    for arch in arches:
        yield run_checkbyte, arch

if __name__ == "__main__":
    for r,a in test_checkbyte():
        r(a)
