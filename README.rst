What
====

I'm exploring world of compilers and interpreters.

This is a simple concurrent virtual machine. It can run many internal threads in few real OS threads.

Python is chosen as fast prototyping language.


VM specification
================

This is a register based virtual machine. Thus, it has registers for storing values. Values are signed integer numbers.

There are 8 (without a reason) thread-local registers named r0, r1, ... r7.
And 8 global registers named g0, g1, ... g7.


Instructions:

`copy D S`
    copies value of thread-local register S to thread-local register D. Same as assembler instruction `mov`.
`gcopy D S`
    copies value of register S to register D. Any or both registers may be global.

    Copying from or to global register is special because it locks register for concurrent reading/writing.

`set R val`
    sets thread-local register R to some constant value, which may be a constant expression, like '3 + 5'.
`gset R val`
    sets global register R to some constant value.

`swap R1 R2`
    swaps values of two thread-local registers.

`eval D op R1 R2`
    puts result of evaluation `R1 op R2` into register D. All registers must be thread-local.

    See operators below.

`jump R`
    unconditionally jumps to instruction pointed by thread-local register R.
`jz A E`
    jumps to instruction A if register E is equal to zero.

    A may be a constant address or thread-local register. E must be thread-local register.
`jnz A E`
    same as `jz`, but tests for `E != 0`.
`addr R`
    puts current instruction address to thread-local register R.

`spawn D A`
    spawns new thread with starting instruction A. A may be a constant address or thread-local register.

    New thread's registers are copied from its parent.
    Puts id of new thread into register D.
`spawna D A`
    same as `spawn`, but VM deletes new thread when it does `tstop`.
    Name 'spawna' means SPAWN Automatically deleted thread.
`tself D`
    puts id of current thread into register D.
`tget D T S`
    inter-thread `copy` of register S in thread T into register D in current thread.
`twait T`
    stops current thread, until thread T is not stopped. When thread T does `tstop`, current thread resumes execution.
`tstop`
    stops current thread.
    Do this in main thread to gracefully shutdown VM.
`tdel T`
    deletes thread T. After this instruction, `tget _ T _` and `twait T` will crash VM.

`print R`
    prints the value in thread-local register R.

Operators:

math:
  -, +, \*, /. Math operators evaluate to integer number.

  `/` is integer division. Division by zero crashes the VM. Division is rounded towards zero.

logic:
  <, >, <=, >=, ==, !=. Logic operators evaluate to 1 for true and 0 for false.


Sample
======

This sample program prints GCD (greatest common denominator) of two integers supplied in g0 and g1.

    gcopy r0 g0
    gcopy r1 g1

    :start
    jz :done r1        # if b == 0, we're done

    eval r2 < r0 r1    # a < b?
    jz :sub r2         # continue if not
    swap r0 r1         # swap a and b if yes

    :sub
    eval r0 - r0 r1    # a = a - b
    jump :start

    :done
    print r0


This sample program concurrently calculates fib(x) of integer supplied in g0.

    jump :start

    :F-fib             # F- for "function" fib(x), x is r0
    eval r1 < r0 2     # x < 2?
    jnz :F-fib-done r1 # return x if yes

    eval r1 - r0 1     # a = x - 1
    eval r2 - r0 2     # b = x - 2

    copy r0 r1
    spawn r3 :F-fib    # spawn fib(a)
    copy r0 r2
    spawn r4 :F-fib    # spawn fib(b)

    twait r3
    tget r1 r3 r0      # a = wait for result of fib(a)
    tdel r3            # delete thread to avoid memory leaks
    twait r4
    tget r2 r4 r0      # b = wait for result of fib(b)
    tdel r4            # delete thread to avoid memory leaks

    eval r0 + r1 r2    # x = a + b

    :F-fib-done
    tstop

    :start
    gcopy r0 g0
    spawn r1 :F-fib
    twait r1
    tget r0 r1 r0
    print r0
    # not deleting thread because VM stops anyway
