
from transformers import pipeline, logging
import torch

from typing import List, Dict
import json
from rich import print

from .dbRetriever import DBRetriever

from .outputJsonifier import clean_incomplete_and_trailing_comma

from .prompts import AV_PAIRS_EXTRACTION_INSTRUCTION

logging.set_verbosity_error()

class AVExtractor():
    def __init__(self, dbRetriever: DBRetriever|None, products_path: None|str, model: str="Sayantan54321/model_ff", temperature: float =0.1):
        self.pipe = pipeline(
            task="text-generation",
            model=model,
            device=0,
            torch_dtype=torch.bfloat16,
            temperature=temperature,
            pad_token_id=128001,
            clean_up_tokenization_spaces=False)
        
        self.conversation = self.reset_conversation()
        self.dbRetriever = dbRetriever
        self.products: Dict[str, Dict[str, List[str]]] = {}
        if products_path:
            with open(products_path, "r") as f:
                self.products = json.loads(f.read())
        
    def query_llama_model(self, messages: List[Dict[str, str]]):
        tries = 0
        response = ""
        json_obj = ""
        
        tries = 5
        while tries:
            response: str = self.pipe(messages)[0]["generated_text"][-1]['content']
            json_obj = clean_incomplete_and_trailing_comma(response)
            if json_obj:
                break
            else:
                tries -= 1
        
        return response, json_obj
    
    def reset_conversation(self):
        return [{"role": "system", "content": AV_PAIRS_EXTRACTION_INSTRUCTION}]
    
    def chat(self):
        while True:
            user_input = input("You: ")
            
            if user_input.lower() == "exit":
                print("Ending conversation.")
                break
            
            if user_input.lower() == "reset":
                print("Conversation reset.")
                self.conversation = self.reset_conversation()  # Reset the conversation to only include the instruction
                continue
            
            message = {'role': 'user', 'content': user_input}
            self.conversation.append(message)

            response, json_obj = self.query_llama_model(messages=self.conversation)
            print("AI:", response)
            print("JSON:", json_obj)
            
            if self.dbRetriever:
                new_json_obj, matched_products = self.dbRetriever.main(json_obj)
                print(f"Cleaned JSON: {new_json_obj}")
                if self.products:
                    for i in matched_products[:10]:
                        print(i)
                        print(self.products[i[0]]['Display_title'][0])
                        print(self.products[i[0]]['Item_url'][0])
                        print(self.products[i[0]]['Image_url'][0])
                else:
                    for i in matched_products[:10]:
                        print(i)
                    
            
            self.conversation.append({'role': 'assistant', 'content': response})
            
if __name__ == "__main__":
    avextractor = AVExtractor(None, None)
    avextractor.chat()
    