# Exercise 2 — Reverse Debugging with rr

## C Version — `corruption.c`

### Symptom

The program showed:

Student 0: id=1001
Student 1: id=1002

After curving the scores, Student 1's ID changed unexpectedly:
Student 0: id=1001
Student 1: id=1007

ERROR: Student 1's ID was corrupted! Expected 1002, got 1007

### Hypothesis

I thought the `curve_scores()` function was writing outside the `scores` array because the array has only 3 elements but the loop runs 4 times.

### Test

I used `rr` to record and replay the program:

rr record ./corruption
rr replay

Then I set a watchpoint on:

watch students[1].id

After continuing the program, the watchpoint showed:

Old value = 1002
New value = 1007

I checked the loop and found that `i` reached `3`.

### Root Cause

The `scores` array has only 3 elements:

int scores[3];

The valid indexes are `0`, `1`, and `2`.

However, the loop runs 4 times:
for (int i = 0; i < 4; i++) {
    students[student_idx].scores[i] += curve;
}

When `i` becomes `3`, it accesses:

students[0].scores[3]

This is outside the array and causes memory corruption. The adjacent `students[1].id` gets changed from `1002` to `1007`.

### Fix

Changed:
for (int i = 0; i < 4; i++)

to:

for (int i = 0; i < 3; i++)

Now the loop only accesses indexes `0`, `1`, and `2`.


## Python Version — `corruption.py`

### Symptom

When I converted the program to Python, it produced:

IndexError: list index out of range

### Hypothesis

I thought the loop was trying to access an index that does not exist in the scores list.

### Test

The scores list contains:

[85, 92, 78]

so the valid indexes are: 0, 1, 2

But:

range(4)

runs with:

0, 1, 2, 3

Therefore, the program tries to access index `3`.

### Root Cause

The loop was running 4 times.

Python detected the invalid access and raised:

IndexError: list index out of range

### Fix

Changed:

for i in range(4):

to:

for i in range(3):
