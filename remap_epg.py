import json
import requests
import xml.etree.ElementTree as ET

RULES_FILE = "rules.json"
OUT_FILE = "epg.xml"

def first_display_name_text(ch: ET.Element) -> str | None:
    dn = ch.find("display-name")
    if dn is None or dn.text is None:
        return None
    return dn.text.strip()

def has_display_name(ch: ET.Element, text: str) -> bool:
    for dn in ch.findall("display-name"):
        if (dn.text or "").strip() == text:
            return True
    return False

def main():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = json.load(f)

    url = rules["source_epg_url"]
    alias_map = rules.get("add_display_name_alias", {}) or {}

    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    added = 0
    for ch in root.findall("channel"):
        base = first_display_name_text(ch)
        if not base:
            continue
        alias = alias_map.get(base)
        if not alias:
            continue
        if has_display_name(ch, alias):
            continue

        dn_new = ET.Element("display-name")
        dn_new.set("lang", "zh")
        dn_new.text = alias
        ch.append(dn_new)
        added += 1

    ET.ElementTree(root).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUT_FILE}. display-name aliases added={added}")

if __name__ == "__main__":
    main()
