from netra import Netra
from netra.dashboard import *
from dotenv import load_dotenv
import os

load_dotenv()

headers = f"x-api-key={os.getenv('NETRA_API_KEY')}"
Netra.init(app_name="sample-app", headers=headers)

result = Netra.dashboard.get_session_summary(
	filter=SessionFilterConfig(
		start_time="2026-01-01T00:00:00.000Z",
		end_time="2026-01-31T23:59:59.000Z",
		filters=[
			SessionFilter(
				field=SessionFilterField.TENANT_ID,
				operator=SessionFilterOperator.ANY_OF,
				type=SessionFilterType.ARRAY,
				value=["Unilever", "AceTech"]
			)
		]
	)
)

print(result)