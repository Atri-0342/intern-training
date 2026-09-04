# Day 3 — Debugging Exercises

## Exercise 1 — Debug a sorting algorithm

### Symptom
The merge sort program returned:

[1, 5, 4, 3, 4, 5, 6, 9]

instead of the expected:

[1, 1, 2, 3, 4, 5, 6, 9]

### Hypothesis
At first, I suspected that the problem might be in the merge process or in how the remaining elements were being added after the while loop.

### Test
I used Python's PDB debugger and stepped through the `merge()` function. I inspected `left`, `right`, `i`, `j`, and `result` at different stages.

The first merges were correct, so I continued until reaching:

left = [1, 3]
right = [1, 4]

After selecting the first `1` from the left list, the values became:

i = 1
j = 0

The next comparison was:

left[i] = 3
right[j] = 1

The condition was false, so the program entered the `else` block.

### Root Cause
The code used:

result.append(right[i])

But `i` is the index for the left list. The right list must use `j`.

Therefore, the program selected `right[1]` (4) instead of `right[0]` (1).

### Fix
Changed:

result.append(right[i])

to:

result.append(right[j])

### Verification
After the fix, I ran:

python3 merge_sort.py

The output was:

[1, 1, 2, 3, 4, 5, 6, 9]

The program now produces the expected result.
