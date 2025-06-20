import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from llama_index import ServiceContext

def My_Service_Context(model_name):
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    class LocalLLMPredictor:
        def __init__(self, model, tokenizer):
            self.model = model
            self.tokenizer = tokenizer

        def predict(self, prompt):
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model(**inputs)
            return outputs.logits.detach().numpy()

    class LocalPromptHelper:
        def __init__(self, predictor):
            self.predictor = predictor

        def get_embedding(self, prompt):
            # Implement a method to get the embedding from the local model
            # This will depend on the specific model and tokenizer you're using
            pass
        
    service_context = ServiceContext.from_defaults(
            llm_predictor=LocalLLMPredictor(model, tokenizer),
            prompt_helper=LocalPromptHelper(LocalLLMPredictor(model, tokenizer))
    )
    return service_context