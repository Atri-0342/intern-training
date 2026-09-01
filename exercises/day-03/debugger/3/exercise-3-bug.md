# Exercise 3 — AddressSanitizer

## `uaf.c` — Use-After-Free

### Symptom

Running the program without sanitizers:

gcc uaf.c -o uaf && ./uaf

produced:

Hello, world!
J$Ǧ

The program appeared to run, but the second output was corrupted.

### Hypothesis

I thought the problem might be caused by using `greeting` after we free the memory.

### Test

I compiled the program with AddressSanitizer:

gcc -fsanitize=address -g uaf.c -o uaf && ./uaf

ASan reported:

AddressSanitizer: heap-use-after-free
It also showed that the memory had been freed at:

which was:

free(greeting)
greeting[0] = 'J';

### Root Cause

The program freed the memory:

free(greeting);

and then tried to use it:

greeting[0] = 'J';

This is called a **use-after-free** bug.

### Fix

I moved `free(greeting)` after the last use of `greeting`:

greeting[0] = 'J';
printf("%s\n", greeting);

free(greeting);

After the fix, running with AddressSanitizer produced:

Hello, world!
Jello, world!

with no AddressSanitizer error.