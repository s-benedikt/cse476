import re
import random
from typing import Optional, Dict, Any

from .api import call_model_chat_completions


def getAnswer(text: str):           
    """
    Checks in reverse for keyword. If not found, returns last number.
    """

    pattern = r"-?\d+\.\d+|-?\d+/\d+|-?\d+" # pattern to match all floats, fractions, or integers

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()] 

    # check in reverse for keyword
    for ln in reversed(lines):
        if ln.lower().startswith("final:"):
            # strip junk
            tail = ln.split(":", 1)[1].strip()
            # get number
            m = re.search(pattern, tail)
            return m.group(0) if m else None

    # fallback returns last number
    matches = re.findall(pattern, text)
    if matches:
        answer = matches[-1]
        return answer
    return None

class Agent:
    def __init__(self, max_calls: int = 12, sc_samples: int = 5, rng: Optional[random.Random] = None,): 
        ...
