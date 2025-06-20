from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

class CodeDescriber:
    def __init__(self,
                 model_name: str = "Qwen/Qwen2.5-Coder-0.5B",
                 device: int = -1):
        
        print(f"Loading model {model_name} on device={device}…")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Загружаем веса модели (в формате float16 на GPU, float32 на CPU)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device != -1 else torch.float32,
            low_cpu_mem_usage=True
        )
        
        if device != -1:
            self.model.to(f"cuda:{device}")

        self.generator = pipeline(
            task="text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device,
            torch_dtype=torch.float16 if device != -1 else torch.float32,
            use_cache=True
        )

    def describe(self,
                 user_promt: str,
                 max_new_tokens: int = 256,
                 temperature: float = 0.0) -> str:

        prompt = (
            "Напиши комментарий для кода.\n"
            "Используй формат docstring.\n"
            #"Используй формат Google-style docstring.\n"
            "В ответе должно быть только описание кода длиной строго не больше 128 токенов\n"
            "Дальше код который нужно описать:\n\n"
            f"{user_promt.strip()}\n"
            "```\n\nОписание:\n"
        )

        output = self.generator(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id
        )
        full_text = output[0]["generated_text"]
        return full_text[len(prompt):].strip()


if __name__ == "__main__":
    describer = CodeDescriber(model_name="Qwen/Qwen2.5-Coder-3B", device=-1)

    snippet = """
def square(x):
    \"""
    Возвращает квадрат числа x.
    \"""
    return x * x
"""

    print("Исходный код:")
    print(snippet.strip())
    print("\nСгенерированное описание:\n")

    description = describer.describe(snippet, max_new_tokens=100, temperature=0.0)
    print(description)
