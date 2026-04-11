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

---

## Test 2: API Server with Tests

### Prompt

```
Create a Python HTTP API server in a new directory 'api_project' that:
1. Uses uv venv and only stdlib (http.server)
2. Implements GET /health returning {"status": "ok", "timestamp": <current time>}
3. Implements GET /fib?n=<number> returning fibonacci result
4. Starts the server and tests both endpoints using curl
5. Shows curl output for /health and /fib?n=10
```

### Harder because

- Multiple components: venv + server + multiple routes + tests
- Server must stay running (background)
- Two different HTTP requests needed

### Success criteria

- [x] Server starts successfully (multi-step: step 2 attempted)
- [ ] /health returns JSON - server not started properly
- [ ] /fib?n=10 returns 55

---

## Results Summary

### Test 1: Fibonacci (easier)

| Metric | ON | OFF |
|--------|-----|-----|
| Steps | 8 clear steps | Single blob |
| Output | Correct ✓ | Correct ✓ |

### Test 2: API Server (harder)

| Metric | ON | OFF |
|--------|-----|-----|
| Plan | 8 clear steps | Failed immediately |
| Tool error | "Unknown tool: bash" | "Unknown tool: bash" |
| Server start | Failed (file path issues) | Couldn't start |

### Key Insight

Multi-step helps with **complexity management** but the model still struggles with:
- File paths (creating in correct directory)
- Background processes
- Sequential operations requiring persistent state
