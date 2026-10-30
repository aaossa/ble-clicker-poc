# ble-clicker-poc

Proof of concept: use an Android phone as a presentation clicker for a Mac (or Linux) over **Bluetooth only**. The phone UI is a PWA that works offline once installed.

```
Phone (Chrome, PWA)  --BLE write-->  Computer (Python GATT server)  --keys-->  PDF / slides / browser
```

- **`docs/`**: the PWA (published with GitHub Pages). It uses Web Bluetooth to write commands like `next` or `prev`.
- **`ble_server.py`**: runs on the computer. Advertises a BLE service, checks a pairing token, and presses keys.
- **`actions.py`**: maps command names to key presses (`osascript` on macOS, `xdotool` on Linux).

## Setup

1. **Install the PWA (needs internet once).** On the phone, open <https://aaossa.github.io/ble-clicker-poc/> in Chrome and choose *Install app*. It then opens offline.
2. **Run the receiver on the computer.**
   ```
   pip3 install -r requirements.txt
   python3 ble_server.py
   ```
   It prints a pairing token (also saved to `~/.config/clicker/token`). Allow Bluetooth for your terminal if the OS asks.
3. **Connect from the phone.** Open the app, paste the token, tap **Connect**, and pick `Clicker` in the list.

Optional: `python3 ble_server.py --url https://aaossa.github.io/ble-clicker-poc/` also shows a QR (uses `qrcode`) that opens the app with the token filled in.

Other flags: `--dry-run` prints key presses instead of sending them, and `--new-token` regenerates the token.

## Requirements and limits

- **Phone**: Android with Chrome. Web Bluetooth is not available on iPhone.
- **Computer**: macOS (grant Accessibility permission to the terminal) or Linux with `xdotool` (X11).
- Chrome always shows a device chooser, so you tap the computer once per connection.
- Key presses go to the focused window, so open your PDF or slides in full screen first.
- `Tab 1` / `Tab 2` send Cmd+1 / Cmd+2 (Ctrl on Linux), which switch browser tabs by position.

## Status

Untested on real hardware: `bless` on macOS, and Web Bluetooth inside the installed PWA. The pairing token only stops casual misuse. BLE traffic is not encrypted, so don't treat this as secure.

## Adding actions

Add an entry to `ACTIONS` in `actions.py` and a button with a matching `data-cmd` in `docs/index.html`. Commands must stay short (the token plus the name must fit in 20 bytes).
