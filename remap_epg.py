import json
import requests
import xml.etree.ElementTree as ET

RULES_FILE = "rules.json"
OUT_FILE = "epg.xml"

def load_rules():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    rules = load_rules()

    source_url = rules["source_epg_url"]
    keep_ids = set(rules.get("keep_channel_ids", []) or [])
    rename_map = rules.get("rename_channel_id", {}) or {}

    resp = requests.get(source_url, timeout=60)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    do_filter = len(keep_ids) > 0
    new_root = ET.Element("tv")
    for k, v in root.attrib.items():
        new_root.set(k, v)

    for ch in root.findall("channel"):
        cid = ch.get("id")
        if cid is None:
            continue
        if do_filter and cid not in keep_ids:
            continue
        if cid in rename_map:
            ch.set("id", rename_map[cid])
        new_root.append(ch)

    for prog in root.findall("programme"):
        cid = prog.get("channel")
        if cid is None:
            continue
        if do_filter and cid not in keep_ids:
            continue
        if cid in rename_map:
            prog.set("channel", rename_map[cid])
        new_root.append(prog)

    ET.ElementTree(new_root).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUT_FILE} (filter={do_filter}, rename={len(rename_map)})")

if __name__ == "__main__":
    main()
