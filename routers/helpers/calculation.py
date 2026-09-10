def calculate_accuracy(hit300: int, hit100: int, hit50: int, misses: int) -> float:
    total_hits = hit300 + hit100 + hit50 + misses
    if total_hits == 0:
        return 0.0
    return (hit300 * 300 + hit100 * 100 + hit50 * 50) / (total_hits * 300) * 100

def id_to_mods(mod_id: int) -> str:
    # Convert mod ID to mod names (this is a simplified version)
    mods = []
    if mod_id & 1:
        mods.append("NF")  # No Fail
    if mod_id & 2:
        mods.append("EZ")  # Easy
    if mod_id & 8:
        mods.append("HD")  # Hidden
    if mod_id & 16:
        mods.append("HR")  # Hard Rock
    if mod_id & 32:
        mods.append("SD")  # Sudden Death
    if mod_id & 64:
        mods.append("DT")  # Double Time
    if mod_id & 128:
        mods.append("RX")  # Relax
    if mod_id & 256:
        mods.append("HT")  # Half Time
    if mod_id & 512:
        mods.append("NC")  # Nightcore (treated as DT)
    if mod_id & 1024:
        mods.append("FL")  # Flashlight
    return "".join(mods) if mods else "None"