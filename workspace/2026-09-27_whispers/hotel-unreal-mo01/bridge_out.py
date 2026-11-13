"""Parse a ue_bridge.py run result: the bridge prints one JSON document; its "output" holds the script's prints.
    python ue_bridge.py run x.py | python bridge_out.py TAG [out.json]   -> the JSON after 'TAG ' on its first line
"""
import sys, json
raw = sys.stdin.read(); tag = sys.argv[1] + " "
doc = json.loads(raw[raw.index("{"):])
text = doc.get("output") or ""
i = text.find(tag)
if i < 0:
    print("NO", sys.argv[1], "|", (doc.get("result") or "")[-1500:]); sys.exit(1)
j = min(k for k in (text.find("{", i), text.find("[", i)) if k >= 0)
data, _ = json.JSONDecoder().raw_decode(text[j:])
if len(sys.argv) > 2:
    json.dump(data, open(sys.argv[2], "w"), indent=1)
print(json.dumps(data)[:200000])
