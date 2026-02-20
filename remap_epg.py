import json
import requests
import xml.etree.ElementTree as ET

RULES_FILE = "rules.json"
OUT_FILE = "epg.xml"

def _get_first_display_name_text(ch: ET.Element) -> str | None:
    dn = ch.find("display-name")
    if dn is None or dn.text is None:
        return None
    return dn.text.strip()

def main():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = json.load(f)

    url = rules["source_epg_url"]
    map_dn_to_id = rules.get("map_display_name_to_id", {}) or {}
    set_display_name_to_new = bool(rules.get("set_display_name_to_new", False))
    keep_original_display_name = bool(rules.get("keep_original_display_name", False))

    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    # 建立 old_id -> new_id 映射（通过 display-name 识别）
    old_to_new = {}

    for ch in root.findall("channel"):
        old_id = ch.get("id")
        if not old_id:
            continue

        dn_text = _get_first_display_name_text(ch)
        if not dn_text:
            continue

        if dn_text in map_dn_to_id:
            new_id = map_dn_to_id[dn_text]
            old_to_new[old_id] = new_id
            ch.set("id", new_id)

            # 处理 display-name
            if set_display_name_to_new:
                if keep_original_display_name:
                    # 新增一个 display-name（保留旧的）
                    dn_new = ET.Element("display-name")
                    dn_new.set("lang", "zh")
                    dn_new.text = new_id
                    ch.append(dn_new)
                else:
                    # 直接覆盖第一个 display-name
                    dn = ch.find("display-name")
                    if dn is not None:
                        dn.text = new_id

    # programme 同步改 channel 引用
    for p in root.findall("programme"):
        old = p.get("channel")
        if old in old_to_new:
            p.set("channel", old_to_new[old])

    ET.ElementTree(root).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUT_FILE}. remapped_channels={len(old_to_new)}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
