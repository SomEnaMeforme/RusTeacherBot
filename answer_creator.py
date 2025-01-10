from llama_cpp import Llama


class AnswerCreator:

    def __init__(self):
        self.llm = Llama.from_pretrained(
            repo_id="nimbXnumb/model-project",
            filename="unsloth.Q4_K_M.gguf",
        )

    def create_answer(self, message: str):
        output = self.llm(
            f"Правильное произношение для: {message}",
            max_tokens=128,
            echo=True
        )
        dict = output['choices']
        text = dict[0]['text']
        return text



