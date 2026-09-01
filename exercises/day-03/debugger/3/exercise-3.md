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