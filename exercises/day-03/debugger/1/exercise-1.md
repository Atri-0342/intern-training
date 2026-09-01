Debug a sorting algorithm: The following pseudocode implements merge sort but contains a bug. 
Implement it in a language of your choice, then use a debugger (gdb, lldb, pdb, or your IDE’s debugger) 
to find and fix the bug.

function merge_sort(arr):
    if length(arr) <= 1:
        return arr
    mid = length(arr) / 2
    left = merge_sort(arr[0..mid])
    right = merge_sort(arr[mid..end])
    return merge(left, right)

function merge(left, right):
    result = []
    i = 0, j = 0
    while i < length(left) AND j < length(right):
        if left[i] <= right[j]:
            append result, left[i]
            i = i + 1
        else:
            append result, right[i]
            j = j + 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
Test vector: merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) should return [1, 1, 2, 3, 4, 5, 6, 9]. 
Use breakpoints and step through the merge function to find where the incorrect element is being selected.


### Symptom

The program produced:

[1, 5, 4, 3, 4, 5, 6, 9]

But the expected result is:

[1, 1, 2, 3, 4, 5, 6, 9]