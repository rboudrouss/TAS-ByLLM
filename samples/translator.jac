import from byllm.lib { Model }
import argparse;

glob llm = Model(model_name="ollama/llama3");

def translate_to(language: str, phrase: str) -> str by llm();

with entry {
    lang = "French";
    phrase = "Hello, how are you?";
    output = translate_to(language=lang, phrase=phrase);
    print(output);
}


