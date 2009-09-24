import threading
import time

from . import error
from .osthread import OSThread
from . import settings
from .vthread import VThread


class VM(object):
    """Virtual machine.

    `code` is a list of `Instruction` instances.
    `run` blocks until main thread does `tstop` or reaches end of `code`.
    """

    def __init__(self, code=None, os_threads=1):
        # check arguments
        if os_threads < 1:
            raise ValueError("os_threads MUST be >= 1")

        # create global registers, init them to 0
        self.greg = [ 0 for _ in xrange(settings.NUM_GLOBAL_REGISTERS) ]

        self.code = code
        self.code.append( ('tstop',) )

        self.events = []
        # event registrations
        # (event name, arguments) -> set( VTids to wake up )
        self.event_regs = {}
        self.event_lock = threading.RLock()

        self.id_gen_lock = threading.RLock()
        self.next_id = 0

        self.vthread_lock = threading.RLock()

        # OS threads MUST be initialized before vthreads
        self.os_threads = set( OSThread(self) for _ in xrange(os_threads) )

        self.main_vthread = self.spawn(0)

    def gen_id(self):
        with self.id_gen_lock:
            self.next_id += 1
            return self.next_id

    def get_vthreads(self):
        result = set()
        for os_t in self.os_threads:
            result |= os_t.vthreads
        return result

    def reg_event(self, name, args, wake_vt_id):
        with self.event_lock:
            if name in ('vthread-stop', 'vthread-sleep', 'vthread-resume'):
                key = (name, args[0])
            if key in self.event_regs:
                vt_id_set = self.event_regs.get(key)
            else:
                vt_id_set = set()
                self.event_regs[key] = vt_id_set
            vt_id_set.add(wake_vt_id)

    def fire_event(self, name, *args):
        self.events.append( (name, args) )

    def process_event(self, name, args):
        vt_to_resume = set()
        with self.event_lock:
            if name in ('vthread-stop', 'vthread-sleep', 'vthread-resume'):
                key = (name, args[0])
            vt_id_set = self.event_regs.get(key, [])
            for vt_id in vt_id_set:
                vt = self.get_vthread_by_id(vt_id)
                #print "event %s %r: waking %d" % (name, args, vt.ident)
                vt_to_resume.add(vt)
        for vt in vt_to_resume:
            vt.resume()

    def get_vthread_by_id(self, vt_id):
        for os_t in self.os_threads:
            for vt in tuple(os_t.vthreads):
                if vt.ident == vt_id:
                    return vt
        raise error.Error("VThread with id %d not found", vt_id)

    def spawn(self, ip):
        """Spawns a new virtual thread with instruction pointer set to `ip`"""

        t = VThread(self, ip)

        # find least busy OS thread
        least_busy = None
        for os_t in self.os_threads:
            if least_busy is None \
               or len(os_t.vthreads) < len(least_busy.vthreads):
                least_busy = os_t

        least_busy.add(t)
        return t

    def handle_error(self, vt, err):
        print "Runtime error %r in vthread %s. IP: %d: %s" % (err, vt.ident, vt.ip, self.code[vt.ip])
        vt.stop()
        return False

    def run(self):
        self.main_vthread.resume()
        for os_t in self.os_threads:
            os_t.join()
#         while self.main_vthread.is_running:
#             print "Threads: ",
#             for os_t in self.os_threads:
#                 for vt in set(os_t.vthreads):
#                     print "<%d %s%s%s>" % (vt.ident,
#                                            "R" if vt.is_running else "",
#                                            "S" if vt.is_sleeping else "",
#                                            "D" if vt.is_deleted else "",),
            #print
#             event_pack = []
#             with self.event_lock:
#                 if self.events:
#                     event_pack = self.events[:]
#                     self.events[:] = []
#             for ev_name, ev_args in event_pack:
#                 self.process_event(ev_name, ev_args)
#             time.sleep(settings.MAGIC_MAIN_VTHREAD_POLL_INTERVAL)
