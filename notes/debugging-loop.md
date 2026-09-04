# Debugging Loop

When I find a problem, I first look at what actually happened instead of immediately changing the code. I check the error message, the wrong output, and the line where the problem appears.

Then I make a hypothesis about what I think is causing the problem. I test it with a small check. For example, I used `p`, `pp`, and `w` in PDB to inspect values and understand how the program reached the failing line.

If the hypothesis is wrong, I discard it and try to understand the reason. If it is correct, I identify the actual reason and try to fix it.

After fixing the code, I run the program again to make sure the problem is gone.

## My Debugging Loop

1. Reproduce — Run the program and understand exactly what is going wrong.
2. Hypothesize — Make a reasonable guess about the cause instead of changing code randomly.
3. Investigate — Use errors, logs, PDB, breakpoints, and variable values to test the hypothesis.
4. Fix — Identify the root cause and make the right change.
5. Verify — Run the program again and confirm that the problem is actually solved.
