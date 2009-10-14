import time

from . import error
from . import parser
from . import settings


class VThread(object):
    """Thread for virtual machine.

    Holds state for thread-local registers."""

    def __init__(self, vm, ip):
        # create registers, init their values to 0
        self.reg = [ 0 for _ in xrange(settings.NUM_REGISTERS) ]

        # owner machine
        self._vm = vm
        # owner OSThread
        self.owner = None

        # instruction pointer
        self.ip = ip

        self.is_running = False
        self.is_sleeping = False
        self.is_deleted = False

        self.ident = self._vm.gen_id()

    def sleep(self):
        self.is_running = True
        self.is_sleeping = True
        #self._vm.fire_event('vthread-sleep', self.ident)

    def stop(self):
        self.is_running = False
        self.is_sleeping = False
        #self._vm.fire_event('vthread-stop', self.ident)

    def resume(self):
        self.is_running = True
        self.is_sleeping = False
        #self._vm.fire_event('vthread-resume', self.ident)
        self.owner.ensure_start()

    def step(self):
        instr = self._vm.code[self.ip]
        print "VT %s does %r" % (self.ident, instr)
        name, args = instr[0], instr[1:]
        handler = getattr(self, "_do_%s" % name, None)
        if handler is None:
            raise error.UnknownInstruction(name)
        handler(*args)

    def delete(self):
        if self.is_running or self.is_sleeping:
            self.stop()
        self.is_deleted = True

    def _wait_vthread(self, vt_id):
        other_vt = self._vm.get_vthread_by_id(vt_id)
        if other_vt.is_running:
            self.is_sleeping = True
            #self._vm.reg_event('vthread-stop', [vt_id], self.ident)
        else:
            self.is_sleeping = False

    def _do_copy(vt, dest, src):
        dest, src = map(parser.local_reg, (dest, src))
        vt.reg[dest] = vt.reg[src]

    def _do_gcopy(vt, dest, src):
        (dest_is_local, dest), (src_is_local, src) = map(parser.reg, (dest, src))
        if src_is_local:
            src_value = vt.reg[src]
        else:
            src_value = vt._vm.greg[src]
        if dest_is_local:
            vt.reg[dest] = src_value
        else:
            vt._vm.greg[dest] = src_value

    def _do_set(vt, r, val):
        r = parser.local_reg(r)
        vt.reg[r] = val

    def _do_swap(vt, r1, r2):
        r1, r2 = map(parser.local_reg, (r1, r2))
        v1, v2 = vt.reg[r1], vt.reg[r2] # read values
        vt.reg[r1] = v2
        vt.reg[r2] = v1

    def _do_eval(vt, dest, op, r1, r2):
        dest, r1, r2 = map(parser.local_reg, (dest, r1, r2))
        op_map = {
            '<': lambda a, b: 1 if a < b else 0,
            '-': lambda a, b: a - b,
            '+': lambda a, b: a + b,
        }
        op_handler = op_map[op]
        result = op_handler(vt.reg[r1], vt.reg[r2])
#        print "VT %s eval result: %d" % (vt.ident, result)
        vt.reg[dest] = result

    def _do_jump(vt, addr):
        vt.ip = addr

    def _do_jz(vt, addr, r):
        r = parser.local_reg(r)
        if vt.reg[r] == 0:
            vt.ip = addr

    def _do_jnz(vt, addr, r):
        r = parser.local_reg(r)
        if vt.reg[r] != 0:
            vt.ip = addr

    def _do_spawn(vt, r, addr):
        r = parser.local_reg(r)
        new_vt = vt._vm.spawn(addr)
#        print "VT %s spawned new vthread at %d, new vtid: %d" % (vt.ident, addr, new_vt.ident)
        new_vt.reg[:] = vt.reg[:]
        vt.reg[r] = new_vt.ident
        new_vt.resume()

    def _do_tget(vt, dest, t, src):
        dest, t, src = map(parser.local_reg, (dest, t, src))
        other_vt = vt._vm.get_vthread_by_id(vt.reg[t])
        vt.reg[dest] = other_vt.reg[src]

    def _do_twait(vt, t):
        t = parser.local_reg(t)
        vt._wait_vthread(vt.reg[t])

    def _do_tstop(vt):
        vt.stop()

    def _do_tdel(vt, t):
        t = parser.local_reg(t)
        other_vt = vt._vm.get_vthread_by_id(vt.reg[t])
        other_vt.delete()

    def _do_print(vt, r):
        r = parser.local_reg(r)
        print "VT %s r%d: %d" % (vt.ident, r, vt.reg[r])
