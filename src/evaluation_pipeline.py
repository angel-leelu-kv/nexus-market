import asyncio
import os
import requests
from netra import Netra
from netra.evaluation import DatasetItem
from dotenv import load_dotenv

load_dotenv()

# Dataset ID for AI Marketplace evaluations
DATASET_ID = "d23e3258-19c5-440a-adc6-9588b6c34159"


def _marketplace_api_headers() -> dict:
    t = (os.environ.get("MARKETPLACE_API_BEARER_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {t}"} if t else {}


def get_marketplace_agent_response(input_data):
    """
    Task function that calls the AI marketplace agent.
    This is the function being evaluated.
    
    Returns the full agent response dict with:
    - response: str - The agent's text response
    - tools_used: List[str] - List of tool names that were called
    - session_id: str - Unique session identifier
    - ai_powered: bool - Whether AI was used
    """
    # Handle both string and dict inputs
    if isinstance(input_data, dict):
        query = input_data.get("question", input_data.get("input", str(input_data)))
    else:
        query = str(input_data)
    
    try:
        response = requests.post(
            "http://localhost:3001/api/chat",
            json={"message": query},
            headers=_marketplace_api_headers(),
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Return the full response dict so tools_used is available for evaluators
            return data
        else:
            return {"response": f"Error: {response.status_code}", "tools_used": [], "ai_powered": False}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "tools_used": [], "ai_powered": False}


async def main():
    headers = f"x-api-key={os.getenv('NETRA_API_KEY')}"
    Netra.init(app_name="NexusMarket", headers=headers, debug_mode=True)

    # Uncomment to create a new dataset
    # response = Netra.evaluation.create_dataset(
    #     name="ai-marketplace-eval-dataset",
    #     tags=["marketplace", "ai-agent", "tools"]
    # )
    # print(response)

    # Uncomment to add items to dataset
    # item1 = DatasetItem(
    #     input="Find me a logo designer under $500",
    #     expected_output="Here are logo design services under $500"
    # )
    # response = Netra.evaluation.add_dataset_item(dataset_id=DATASET_ID, item=item1)
    # print(response)

    # Uncomment to use custom evaluators
    # from netra.evaluation import BaseEvaluator, EvaluatorConfig, EvaluatorOutput, ScoreType
    #
    # class ToolUsageEvaluator(BaseEvaluator):
    #     def evaluate(self, context):
    #         output = context.get("output", "")
    #         has_results = any(word in output.lower() for word in ["found", "here", "service", "listing"])
    #         return EvaluatorOutput(
    #             evaluator_name="tool_usage",
    #             result=1 if has_results else 0,
    #             is_passed=has_results,
    #             reason="Agent returned relevant results" if has_results else "No relevant results found",
    #         )

    # Get dataset
    dataset = Netra.evaluation.get_dataset(dataset_id=DATASET_ID)
    print(f"✅ Dataset loaded: {DATASET_ID}")

    # Run evaluation test suite
    result = Netra.evaluation.run_test_suite(
        name="AI Marketplace Agent v1",
        data=dataset,
        task=get_marketplace_agent_response,
        # evaluators=[
        #     ToolUsageEvaluator(
        #         EvaluatorConfig(
        #             name="tool_usage",
        #             label="Tool Usage Evaluator",
        #             score_type=ScoreType.BINARY,
        #         )
        #     )
        # ]
    )

    print("\n" + "=" * 50)
    print("✅ EVALUATION COMPLETE")
    print("=" * 50)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
