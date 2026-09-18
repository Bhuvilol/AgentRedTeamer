import json

from agentredteamer.analysis import summarize

print(json.dumps(summarize(), indent=2))
