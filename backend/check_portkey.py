"""Check your Portkey setup and discover which models your key can use.

Fill in backend/.env with at least PORTKEY_API_KEY (or have it in your environment),
then run from the backend/ folder:
    .venv/Scripts/python check_portkey.py

It will:
  1. confirm your key is picked up,
  2. list the models your Portkey key can reach (use one of these as CHATBOT_MODEL),
  3. unless you pass --list-only, send one tiny test message to confirm end to end.
"""
from __future__ import annotations

import sys

from anthropic import Anthropic

from agent import (
    MODEL_NAME,
    PORTKEY_API_KEY,
    _portkey_base_url,
    _portkey_headers,
)


def main() -> int:
    list_only = "--list-only" in sys.argv

    if not PORTKEY_API_KEY:
        print("[X] PORTKEY_API_KEY is not set. Add it to backend/.env and try again.")
        return 1

    print(f"[OK] Portkey key found (...{PORTKEY_API_KEY[-4:]})")
    print(f"     Gateway URL : {_portkey_base_url()}")
    print(f"     Provider    : {_portkey_headers().get('x-portkey-provider', '(default)')}")

    client = Anthropic(
        api_key=PORTKEY_API_KEY,
        base_url=_portkey_base_url(),
        default_headers=_portkey_headers(),
    )

    print("\nModels your key can reach:")
    try:
        models = list(client.models.list())
        if not models:
            print("  (none returned - your course may pin the model; ask which name to use)")
        for m in models:
            print(f"  - {m.id}")
    except Exception as e:  # noqa: BLE001 - surface any gateway/auth error plainly
        print(f"  ! Could not list models: {type(e).__name__}: {e}")
        print("    (Some Portkey configs block model listing; you can still set")
        print("     CHATBOT_MODEL to the name your course gave and test below.)")

    if list_only:
        return 0

    if not MODEL_NAME:
        print("\nSet CHATBOT_MODEL in backend/.env to one of the names above, then re-run.")
        return 0

    print(f"\nTesting a message with CHATBOT_MODEL = {MODEL_NAME!r} ...")
    try:
        resp = client.messages.create(
            model=MODEL_NAME,
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'Boola Boola!' and nothing else."}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        print(f"[OK] Success - the model replied: {text.strip()!r}")
        print("\nYou're all set. Start the backend and the chat widget will use the agent.")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"[X] Test call failed: {type(e).__name__}: {e}")
        print("  - If it's a model error, pick a different name from the list above.")
        print("  - If it's an auth/routing error, your key may need a config id or")
        print("    virtual key (set PORTKEY_CONFIG or PORTKEY_VIRTUAL_KEY in .env).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
