from services.config.workout_config import PROMPT
import os


class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue):
        prompt = f"Event: {event}"

        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": prompt}
        ]

        self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
        )
        text = response.choices[0].message.content.strip()

        return text
    