from llama_cpp import Llama
from src.utils.config import CONTEXT_SIZE, LLM_MODEL_FILE_PATH


def get_llm_model():
    llm = Llama(
        model_path=LLM_MODEL_FILE_PATH,
        n_ctx=CONTEXT_SIZE,
        n_gpu_layers=-1,
        stream=True,
        verbose=False,
        embedding=False
    )
    return llm
