from llama_cpp import Llama


class AnswerCreator:

    def __init__(self):
        self.instructions = {"chat": "", "mistakes": ""}
        self.model = Llama.from_pretrained(
            repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
            filename="Meta-Llama-3.1-8B-Instruct-IQ2_M.gguf"
        )

    def create_answer(self, message: str):
        try:
            output = self.model.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You're talking to a Russian student and helping him look for mistakes in his speech during the dialogue. Give short answer."
                    },
                    {
                        "role": "user",
                        "content": f"{message}"
                    }
                ]
            )

            return output['choices'][0]['message']['content']
        except Exception as e:
            return "Что-то пошло не так при генерации ответа. Прошу прощения"