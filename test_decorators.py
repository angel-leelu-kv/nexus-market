
class CustomLiteLlm:

    def __init__(self, model: str):
        self.model = model
    
    def _test_hello():
        return "hello"

    def test_world():
        return "world"



custom_llm = CustomLiteLlm(model="gpt-4o")