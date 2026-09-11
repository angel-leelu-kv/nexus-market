import asyncio
import os
from typing import Dict, Optional
from uuid import uuid4

import requests
from dotenv import load_dotenv
from netra import Netra
from netra.config import Config
from netra.simulation import BaseTask, Simulation, TaskResult

load_dotenv()


# Dataset ID for AI Marketplace simulations
DATASET_ID = "b3bf21e1-623d-4cb8-84dc-405f2e6207eb"

# Backend URL for the marketplace agent (FastAPI)
BACKEND_URL = os.getenv("MARKETPLACE_BACKEND_URL", "http://localhost:3001")


def _marketplace_api_headers() -> dict:
    t = (os.environ.get("MARKETPLACE_API_BEARER_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {t}"} if t else {}


class MarketplaceChatAgent(BaseTask):
    """
    Simulation/evaluation task wrapper that calls the running backend agent via HTTP.

    Expected backend: `POST /api/chat` with JSON:
      { "message": str, "session_id": str (optional), "context": dict (optional) }
    """

    def __init__(self, backend_url: str = BACKEND_URL, timeout_s: int = 30):
        self.backend_url = backend_url.rstrip("/")
        self.timeout_s = timeout_s

    def run(self, message: str, session_id: Optional[str] = None,files=None) -> TaskResult:
        session_id = session_id or str(uuid4())
        payload: Dict[str, object] = {"message": message, "session_id": session_id}
        try:
            resp = requests.post(
                f"{self.backend_url}/api/chat",
                json=payload,
                headers=_marketplace_api_headers(),
                timeout=self.timeout_s,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    response_message = str(data.get("response", ""))
                    response_session_id = str(data.get("session_id") or session_id)
                    return TaskResult(message=response_message, session_id=response_session_id)

                return TaskResult(message=str(data), session_id=session_id)

            return TaskResult(message=f"Error: {resp.status_code}", session_id=session_id)
        except Exception as e:
            return TaskResult(message=f"Error: {str(e)}", session_id=session_id)


async def main():
    headers = f"x-api-key={os.getenv('NETRA_API_KEY')}"
    Netra.init(app_name="Simulation Pipeline", headers=headers, debug_mode=True)

    # Attach Simulation API to Netra (some SDK versions don't set this automatically).
    Netra.simulation = Simulation(Config(app_name="Simulation Pipeline", headers=headers, debug_mode=True))  # type: ignore[attr-defined]

    Netra.simulation.run_simulation(
        name="AI Marketplace Agent (Chat) v1",
        dataset_id=DATASET_ID,
        context={"Metadata": "AI Marketplace"},
        task=MarketplaceChatAgent(),
    )


if __name__ == "__main__":
    asyncio.run(main())
