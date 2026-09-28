# Bugs covered by regression tests

## Missing bearer credentials returned the wrong status

Protected endpoints used FastAPI's default `HTTPBearer` error handling, so a
request without an `Authorization` header returned `403 Forbidden`. The API
contract requires unauthenticated requests to return `401 Unauthorized`.

The regression test is `test_authentication_and_authorization` in
`ScanFlow/tests/test_api.py`.


# Bugs

## Bug 1 - Addition function returned the wrong result

### What happened

The `add()` function was supposed to add two numbers, but it was using subtraction instead.

### Buggy code

def add(a, b):
    return a - b

# Hypothesis

The function might be using the wrong operation.

# Smallest test

Before fixing the function, I wrote a small test to reproduce the problem:

def test_add():
    assert add(2, 3) == 5

# What happened when the test ran

The test failed because:

Expected -> 5
Got -> -1

This confirmed that the bug was real.

# Root cause

The function used - instead of +.

# Fix
def add(a, b):
    return a + b

I ran the same test again:

test_add -> PASSED

# Flow

Bug happens -> write the smallest test -> test fails -> find the root cause -> fix the code -> run the same test again -> test passes -> keep the test as a regression test.