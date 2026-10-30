#!/usr/bin/env python3
"""BLE receiver for the phone PWA. Runs on the computer being controlled.

Requires: pip install bless
Usage: python3 ble_server.py [--dry-run] [--new-token] [--url https://host/path/]
"""
import argparse
import asyncio
import hmac
import queue
import secrets
import threading
from pathlib import Path

from actions import ACTIONS, press

SERVICE_UUID = "6f0b1c10-5d6b-4b53-9a43-5f1f3f2a0001"
CHAR_UUID = "6f0b1c10-5d6b-4b53-9a43-5f1f3f2a0002"
TOKEN_FILE = Path.home() / ".config" / "clicker" / "token"


def load_token(regenerate):
    if TOKEN_FILE.exists() and not regenerate:
        return TOKEN_FILE.read_text().strip()
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(4)  # 8 chars keeps "token|cmd" within a default BLE write
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


def handle_payload(data, token, dry_run):
    """Payload format: '<token>|<action>'. Returns a short status string."""
    try:
        supplied, _, name = bytes(data).decode("ascii").partition("|")
    except UnicodeDecodeError:
        return "bad payload"
    if not hmac.compare_digest(supplied, token):
        return "unauthorized"
    action = ACTIONS.get(name)
    if action is None:
        return f"unknown action {name!r}"
    press(*action, dry_run)
    return f"ok {name}"


def start_worker(token, dry_run):
    """Single worker thread keeps key presses in order and off the BLE callback."""
    jobs = queue.Queue()

    def run():
        while True:
            data = jobs.get()
            try:
                print(">", handle_payload(data, token, dry_run))
            except Exception as exc:
                print("  failed:", exc)

    threading.Thread(target=run, daemon=True).start()
    return jobs


def show_qr(url):
    try:
        import qrcode
    except ImportError:
        print("  (pip install qrcode to show a scannable QR)")
        return
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make()
    qr.print_ascii(invert=True)


async def serve(token, dry_run):
    from bless import BlessServer, GATTAttributePermissions, GATTCharacteristicProperties

    jobs = start_worker(token, dry_run)

    def on_write(characteristic, value, **kwargs):
        characteristic.value = value
        jobs.put(bytes(value))

    server = BlessServer(name="Clicker", loop=asyncio.get_running_loop())
    server.write_request_func = on_write

    await server.add_new_service(SERVICE_UUID)
    props = GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response
    # bless versions differ on the spelling of this permission
    writable = getattr(GATTAttributePermissions, "writable", None) or GATTAttributePermissions.writeable
    await server.add_new_characteristic(SERVICE_UUID, CHAR_UUID, props, None, writable)
    await server.start()
    print("Advertising as 'Clicker'. Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    finally:
        await server.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print key presses instead of sending them")
    parser.add_argument("--new-token", action="store_true", help="generate a new pairing token")
    parser.add_argument("--url", help="PWA URL; shows a QR that opens it with the token filled in")
    args = parser.parse_args()

    token = load_token(args.new_token)
    print(f"Pairing token: {token}")
    if args.url:
        link = f"{args.url.rstrip('/')}/#t={token}"
        print(link)
        show_qr(link)
    try:
        asyncio.run(serve(token, args.dry_run))
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
