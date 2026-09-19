from __future__ import annotations
import os

class OptionalLLM:
    """Optional extraction helper. It never acts as the policy source of truth."""
    def __init__(self):
        self.enabled=bool(os.getenv('OPENAI_API_KEY'))
        self.client=None
        if self.enabled:
            try:
                from openai import OpenAI
                self.client=OpenAI(api_key=os.environ['OPENAI_API_KEY'])
            except Exception:
                self.enabled=False
    def extract_decision_dimensions(self, case: dict):
        if not self.enabled: return None
        prompt=("Extract only a concise JSON list of policy decision dimensions for this synthetic claim. "
                "Do not make any coverage conclusion and do not add outside insurance knowledge.\n"+str(case))
        try:
            r=self.client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),messages=[{'role':'user','content':prompt}],temperature=0)
            return r.choices[0].message.content
        except Exception:
            return None
