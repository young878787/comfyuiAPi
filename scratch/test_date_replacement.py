import re
from datetime import datetime

def _resolve_filename_prefix_placeholders(api_format: dict) -> dict:
    import copy
    api_format = copy.deepcopy(api_format)
    now = datetime.now()
    
    def repl_date(match):
        fmt = match.group(1)
        py_fmt = fmt.replace("yyyy", "%Y").replace("yy", "%y") \
                    .replace("MM", "%m") \
                    .replace("dd", "%d") \
                    .replace("HH", "%H") \
                    .replace("hh", "%I") \
                    .replace("mm", "%M") \
                    .replace("ss", "%S")
        return now.strftime(py_fmt)

    for node_data in api_format.values():
        if not isinstance(node_data, dict):
            continue
        inputs = node_data.get("inputs")
        if isinstance(inputs, dict) and "filename_prefix" in inputs:
            prefix = inputs["filename_prefix"]
            if isinstance(prefix, str):
                # Replace %date:FORMAT%
                prefix = re.sub(r'%date:([^%]+)%', repl_date, prefix)
                # Replace %date% with default yyyy-MM-dd
                prefix = prefix.replace("%date%", now.strftime("%Y-%m-%d"))
                inputs["filename_prefix"] = prefix
                
    return api_format

# Test case
mock_workflow = {
    "46": {
        "inputs": {
            "filename_prefix": "Anima/%date:yyyy-MM-dd%/%date:yyyy-MM-dd%",
            "images": ["8", 0]
        },
        "class_type": "SaveImage"
    },
    "47": {
        "inputs": {
            "filename_prefix": "output_%date:yyyyMMdd_HHmmss%",
        }
    },
    "48": {
        "inputs": {
            "filename_prefix": "default_%date%",
        }
    }
}

result = _resolve_filename_prefix_placeholders(mock_workflow)
print("Original:")
print(mock_workflow["46"]["inputs"]["filename_prefix"])
print("\nResolved:")
print(result["46"]["inputs"]["filename_prefix"])
print(result["47"]["inputs"]["filename_prefix"])
print(result["48"]["inputs"]["filename_prefix"])
