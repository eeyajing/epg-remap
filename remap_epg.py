import json
import requests
import xml.etree.ElementTree as ET

RULES_FILE = "rules.json"
OUT_FILE = "epg.xml"

def get_first_display_name(ch: ET.Element) -> str | None:
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
    dn_to_newid = rules.get("map_display_name_to_new_id", {}) or {}
    also_alias = bool(rules.get("also_append_display_name_alias", True))

    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    # old numeric id -> new string id
    old_to_new = {}

    # 1) channel: locate by display-name, then rewrite id
    for ch in root.findall("channel"):
        old_id = ch.get("id")
        if not old_id:
            continue

        base_dn = get_first_display_name(ch)
        if not base_dn:
            continue

        new_id = dn_to_newid.get(base_dn)
        if not new_id:
            continue

        old_to_new[old_id] = new_id
        ch.set("id", new_id)

        # optionally add alias display-name = new_id
        if also_alias and not has_display_name(ch, new_id):
            dn_new = ET.Element("display-name")
            dn_new.set("lang", "zh")
            dn_new.text = new_id
            ch.append(dn_new)

    # 2) programme: rewrite channel reference
    for p in root.findall("programme"):
        cid = p.get("channel")
        if cid in old_to_new:
            p.set("channel", old_to_new[cid])

    # pretty output (optional, but nicer)
    try:
        ET.indent(root, space="  ")
    except Exception:
        pass

    ET.ElementTree(root).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUT_FILE}. remapped={len(old_to_new)}")

if __name__ == "__main__":
    main()
