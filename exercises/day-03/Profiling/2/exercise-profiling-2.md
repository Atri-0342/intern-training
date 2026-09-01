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

