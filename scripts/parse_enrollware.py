def guess_family_from_label(text: str) -> str:
    t = text.lower()
    if "bls" in t and "heartsaver" not in t:
        return "BLS"
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "heartsaver" in t or "first aid" in t or "cpr aed" in t:
        return "First Aid / CPR / AED"
    return "Other"


def guess_brand_from_label(text: str) -> str | None:
    t = text.lower()
    if "american heart association" in t or "aha" in t:
        return "AHA"
    if "american red cross" in t or "arc " in t:
        return "Red Cross"
    if "hsi" in t:
        return "HSI"
    return None
