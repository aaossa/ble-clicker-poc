"""Maps command names to key presses on the local machine (macOS or Linux)."""
import platform
import subprocess

# macOS key codes (System Events). Linux uses xdotool key names.
MAC_KEYS = {"right": 124, "left": 123, "home": 115, "end": 119, "tab": 48, "b": 11}
LINUX_KEYS = {"right": "Right", "left": "Left", "home": "Home", "end": "End", "tab": "Tab", "b": "b"}

MAC_MODS = {"ctrl": "control down", "cmd": "command down", "shift": "shift down", "alt": "option down"}
LINUX_MODS = {"ctrl": "ctrl", "cmd": "ctrl", "shift": "shift", "alt": "alt"}

# Each action is a (key, modifiers) tuple. Names must match the buttons in docs/index.html.
ACTIONS = {
    "next": ("right", ()),
    "prev": ("left", ()),
    "first": ("home", ()),
    "last": ("end", ()),
    "blank": ("b", ()),
    "tab_next": ("tab", ("ctrl",)),
    "tab_prev": ("tab", ("ctrl", "shift")),
}
# tab1..tab8 -> Cmd+N on macOS, Ctrl+N on Linux
for _n in range(1, 9):
    ACTIONS[f"tab{_n}"] = (str(_n), ("cmd",))


def press(key, mods, dry_run=False):
    system = platform.system()
    if system == "Darwin":
        using = ", ".join(MAC_MODS[m] for m in mods)
        suffix = f" using {{{using}}}" if mods else ""
        if key.isdigit():
            script = f'tell application "System Events" to keystroke "{key}"{suffix}'
        else:
            script = f'tell application "System Events" to key code {MAC_KEYS[key]}{suffix}'
        cmd = ["osascript", "-e", script]
    elif system == "Linux":
        combo = "+".join([LINUX_MODS[m] for m in mods] + [LINUX_KEYS.get(key, key)])
        cmd = ["xdotool", "key", combo]
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
    if dry_run:
        print("  [dry-run]", " ".join(cmd))
        return
    subprocess.run(cmd, check=True, capture_output=True, timeout=5)
