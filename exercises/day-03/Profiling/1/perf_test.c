#include <stdio.h>

long long calculate_sum(int n) {
    long long sum = 0;

    for (int i = 0; i < n; i++) {
        sum += i;
    }

    return sum;
}

int main() {
    long long result = calculate_sum(100000000);

    printf("Result: %lld\n", result);

    return 0;
}