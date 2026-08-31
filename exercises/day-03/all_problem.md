Exercises
Debugging
Debug a sorting algorithm: The following pseudocode implements merge sort but contains a bug. Implement it in a language of your choice, then use a debugger (gdb, lldb, pdb, or your IDE’s debugger) to find and fix the bug.

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
    append remaining elements from left and right
    return result
Test vector: merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) should return [1, 1, 2, 3, 4, 5, 6, 9]. Use breakpoints and step through the merge function to find where the incorrect element is being selected.

Install rr and use reverse debugging to find a corruption bug. Save this program as corruption.c:

#include <stdio.h>

typedef struct {
    int id;
    int scores[3];
} Student;

Student students[2];

void init() {
    students[0].id = 1001;
    students[0].scores[0] = 85;
    students[0].scores[1] = 92;
    students[0].scores[2] = 78;

    students[1].id = 1002;
    students[1].scores[0] = 90;
    students[1].scores[1] = 88;
    students[1].scores[2] = 95;
}

void curve_scores(int student_idx, int curve) {
    for (int i = 0; i < 4; i++) {
        students[student_idx].scores[i] += curve;
    }
}

int main() {
    init();
    printf("=== Initial state ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    curve_scores(0, 5);

    printf("\n=== After curving ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    if (students[1].id != 1002) {
        printf("\nERROR: Student 1's ID was corrupted! Expected 1002, got %d\n",
               students[1].id);
        return 1;
    }
    return 0;
}
Compile with gcc -g corruption.c -o corruption and run it. Student 1’s ID gets corrupted, but the corruption happens in a function that only touches student 0. Use rr record ./corruption and rr replay to find the culprit. Set a watchpoint on students[1].id and use reverse-continue after the corruption to find exactly which line of code overwrote it.

Debug a memory error with AddressSanitizer. Save this as uaf.c:

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int main() {
    char *greeting = malloc(32);
    strcpy(greeting, "Hello, world!");
    printf("%s\n", greeting);

    free(greeting);

    greeting[0] = 'J';
    printf("%s\n", greeting);

    return 0;
}
First compile and run without sanitizers: gcc uaf.c -o uaf && ./uaf. It may appear to work. Now compile with AddressSanitizer: gcc -fsanitize=address -g uaf.c -o uaf && ./uaf. Read the error report. What bug does ASan find? Fix the issue it identifies.

Use strace (Linux) or dtruss (macOS) to trace the system calls made by a command like ls -l. What system calls is it making? Try tracing a more complex program and see what files it opens.

Use an LLM to help debug a cryptic error message. Try copying a compiler error (especially from C++ templates or Rust) and asking for an explanation and fix. Try putting some of the output from strace or the address sanitizer into it.

Profiling
Use perf stat to get basic performance statistics for a program of your choice. What do the different counters mean?

Profile with perf record. Save this as slow.c:

#include <math.h>
#include <stdio.h>

double slow_computation(int n) {
    double result = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < 1000; j++) {
            result += sin(i * j) * cos(i + j);
        }
    }
    return result;
}

int main() {
    double r = 0;
    for (int i = 0; i < 100; i++) {
        r += slow_computation(1000);
    }
    printf("Result: %f\n", r);
    return 0;
}
Compile with debug symbols: gcc -g -O2 slow.c -o slow -lm. Run perf record -g ./slow, then perf report to see where time is spent. Try generating a flame graph using the flamegraph scripts.

Use hyperfine to benchmark two different implementations of the same task (e.g., find vs fd, grep vs ripgrep, or two versions of your own code).

Use htop to monitor your system while running a resource-intensive program. Try using taskset to limit which CPUs a process can use: taskset --cpu-list 0,2 stress -c 3. Why doesn’t stress use three CPUs?

A common issue is that a port you want to listen on is already taken by another process. Learn how to discover that process: First execute python -m http.server 4444 to start a minimal web server on port 4444. On a separate terminal run ss -tlnp | grep 4444 to find the process. Terminate it with kill <PID>.