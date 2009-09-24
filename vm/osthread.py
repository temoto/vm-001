import threading

from . import settings


class OSThread(threading.Thread):
    def __init__(self, vm):
        self._vm = vm
        self.vthreads = set()
        self.start_lock = threading.RLock()
        super(OSThread, self).__init__()
        self.daemon = True

    def add(self, vthread):
        vthread.owner = self
        self.vthreads.add(vthread)

    def ensure_start(self):
        try:
            self.start()
        except RuntimeError:
            pass

    def run(self):
        try:
            while self.scheduler_loop(): pass
        except Exception, e:
            raise

    def scheduler_loop(self):
        """This implements virtual thread scheduler.

        Current naive algorithm:
            Iterate all running vthreads:
                execute at most N instructions,
                switch.
        """

        activity = False
        for vt in tuple(self.vthreads):
            if vt.is_deleted:
                activity = True
                self.vthreads.remove(vt)
                break
            if not vt.is_running:
                continue
            for _ in xrange(settings.MAGIC_SCHEDULER_MAX_INSTRUCTIONS_IN_ROW):
                activity = True
                try:
                    old_ip = vt.ip
                    vt.step()
                    if vt.is_sleeping:
                        break
                    if vt.ip == old_ip:
                        vt.ip += 1
                except Exception, e:
                    do_continue = self._vm.handle_error(vt, e)
                    raise
                    if not do_continue:
                        print "OS thread error"
                        return False
                if vt.is_deleted or vt.is_sleeping or (not vt.is_running):
                    # next vthread
                    break

        return activity
