"""Judge module for evaluating task completion."""
from dataclasses import dataclass


@dataclass
class Judgment:
    """Result of judge evaluation."""
    success: bool
    reason: str
    fix: str


JUDGE_PROMPT = """You are a judge. Evaluate if the candidate completed the task successfully.

Task: {task}
Success criteria: {criteria}
Candidate output: {output}

IMPORTANT: 
- A tool execution returning empty output often means SUCCESS (e.g., file creation, write succeed)
- Consider what the command was trying to do, not just the output
- Shell redirection (> file) typically succeeds with empty output
- If the output mentions success or the command matches the task goal, consider it success
- For code files: prefer to VERIFY by running the code, not just assuming it works

Respond in this format:
SUCCESS: true/false
REASON: (why it succeeded or failed)
FIX: (specific how to fix if failed)

VERIFICATION TIP: If unsure, ask the model to run a verification command (e.g., "cat filename", "python filename", "ls -la")."""


def judge(llm_client, task: str, criteria: str, output: str) -> Judgment:
    """Evaluate if a candidate meets success criteria.
    
    Args:
        llm_client: LLM client for making judgments
        task: The original task description
        criteria: Success criteria (e.g., "file exists", "output contains X")
        output: The candidate output to evaluate
        
    Returns:
        Judgment with success, reason, and fix
    """
    prompt = JUDGE_PROMPT.format(
        task=task,
        criteria=criteria,
        output=output[:2000],  # Limit output size
    )
    
    messages = [{"role": "user", "content": prompt}]
    response = llm_client.chat(messages)
    
    return _parse_judgment(response.content)


def _parse_judgment(text: str) -> Judgment:
    """Parse judge response into Judgment object."""
    success = False
    reason = "Evaluation failed"
    fix = "Please retry"
    
    for line in text.split("\n"):
        line = line.strip().upper()
        if line.startswith("SUCCESS:"):
            success = "TRUE" in line or "YES" in line
        elif line.startswith("REASON:"):
            reason = line[7:].strip()
        elif line.startswith("FIX:"):
            fix = line[4:].strip()
    
    return Judgment(success=success, reason=reason, fix=fix)


def get_default_criteria(output: str) -> str:
    """Get default success criteria when none provided.
    
    Heuristics:
    - Non-empty output → success
    - Exit code 0 → success
    - No error messages → success
    """
    if not output:
        return "Output is non-empty"
    
    if "error" in output.lower() or "failed" in output.lower():
        return "No error in output"
    
    return "Task completed successfully"