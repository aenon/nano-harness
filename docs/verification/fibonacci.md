# Verification Prompts

These prompts are designed to test multi-step planning capability.

## Test 1: Fibonacci with venv

### Prompt

```
Create a Python project that computes fibonacci numbers:
1. Create a new virtual environment using uv in a new directory called 'fibonacci_project'
2. Activate the venv and install no additional packages (use only stdlib)
3. Create a fibonacci.py file with a function fib(n) that returns the nth fibonacci number
   - Handle edge cases: fib(0) = 0, fib(1) = 1
   - Use iteration, not recursion
4. Run the program with these test cases and show the output:
   - fib(10)
   - fib(20)
   - fib(0)
   - fib(1)
```

### Expected behavior

| Feature | Expected |
|---------|----------|
| multi_step=false | LLM tries to do everything in one prompt, may fail or do partial |
| multi_step=true | LLM breaks into: create venv → write code → run tests |

### Success criteria

- [ ] Virtual environment created with `uv venv`
- [ ] fibonacci.py created with working fib() function
- [ ] Correct output: 55, 6765, 0, 1