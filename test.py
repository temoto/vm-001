from vm import VM


code_test = [
    ('print', 'r0'),
    ('print', 'r2'),
    ('set',   'r2', 90),
    ('print', 'r2'),
    ('copy',  'r0', 'r2'),
    ('print', 'r0'),
]

code_gcd = [
    ('gcopy', 'r0', 'g0'),
    ('gcopy', 'r1', 'g1'),
    #:start
    ('jz',    8,  'r1'),

    ('eval',  'r2', '<', 'r0', 'r1'),
    ('jz',    6,   'r2'),
    ('swap',  'r0', 'r1'),

    #:sub
    ('eval',  'r0', '-', 'r0', 'r1'),
    ('jump',  2),

    #:done
    ('print', 'r0'),
]

code_fib_concurrent = [
    ('jump',  20),

    #:F-fib
    ('set',   'r1', 2),
    ('eval',  'r1', '<', 'r0', 'r1'),
    ('jnz',   19,   'r1'),

    ('set',   'r1', 1),
    ('eval',  'r1', '-', 'r0', 'r1'),
    ('set',   'r2', 2),
    ('eval',  'r2', '-', 'r0', 'r2'),

    ('copy',  'r0', 'r1'),
    ('spawn', 'r3', 1),
    ('copy',  'r0', 'r2'),
    ('spawn', 'r4', 1),

    ('twait', 'r3'),
    ('tget',  'r1', 'r3', 'r0'),
    ('tdel',  'r3'),
    ('twait', 'r4'),
    ('tget',  'r2', 'r4', 'r0'),
    ('tdel',  'r4'),

    ('eval',  'r0', '+', 'r1', 'r2'),

    #:F-fib-done
    ('tstop',),

    #:start
    ('gcopy', 'r0', 'g0'),
    ('spawn', 'r1', 1),
    ('twait', 'r1'),
    ('tget',  'r0', 'r1', 'r0'),
    ('print', 'r0'),
]


def main():
    print "---"
    print "Simple test"
    print
    vm = VM(code_test)
    vm.run()

    print "---"
    print "GCD"
    print
    vm = VM(code_gcd)
    vm.greg[0] = 9
    vm.greg[1] = 12
    vm.run()

    print "---"
    print "Concurrent fibonacci"
    print
    vm = VM(code_fib_concurrent, 4)
    vm.greg[0] = 17
    vm.run()


if __name__ == '__main__': main()
