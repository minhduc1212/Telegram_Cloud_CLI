# ============================================================
#  Telegram Cloud Storage  ·  Telethon-based CLI tool
# ============================================================

import asyncio
import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv
from telethon.errors import FloodWaitError

#Config
load_dotenv()

client = TelegramClient(
    session = "anon",
    api_id  = os.getenv("API_ID"),
    api_hash= os.getenv("API_HASH"),
)

SAVED = "me"   # Telegram "Saved Messages"

#Helpers
def progress(current: int, total: int) -> None:
    pct     = current * 100 / total
    filled  = int(pct / 5)           # 20-block bar
    bar     = "█" * filled + "░" * (20 - filled)
    print(f"\r  [{bar}] {pct:5.1f}%", end="", flush=True)


def file_exists(path: str) -> bool:
    if not os.path.exists(path):
        print(f"  ❌  File not found: {path}")
        return False
    return True

#Core operations
async def upload(file_path: str, caption: str = "") -> int | None:
    """Upload a local file to Saved Messages."""
    if not file_exists(file_path):
        return None

    print(f"  ⬆️  Uploading  →  {file_path}")
    try:
        msg = await client.send_file(
            SAVED, file_path,
            caption=caption,
            progress_callback=progress,
            workers=8,
        )
        print(f"\n  ✅  Done!  Message ID: {msg.id}")
        return msg.id
    except FloodWaitError as e:
        print(f"\n  ⏳  FloodWait: chờ {e.seconds}s ...")
        await asyncio.sleep(e.seconds)
        return await upload(file_path, caption)
    except Exception as e:
        print(f"\n  ❌  Upload failed: {e}")
        return None


async def download(message_id: int, output_path: str) -> str | None:
    """Download a file from Saved Messages by message ID."""
    print(f"  ⬇️  Downloading  message {message_id} ...")
    try:
        msg = await client.get_messages(SAVED, ids=message_id)

        if not (msg and msg.media):
            print("  ❌  No media found for that ID.")
            return None

        path = await client.download_media(
            msg, file=output_path,
            progress_callback=progress,
        )
        print(f"\n  ✅  Saved to: {path}")
        return path
    except Exception as e:
        print(f"\n  ❌  Download failed: {e}")
        return None


async def update(message_id: int, new_file_path: str) -> None:
    """Replace the file in an existing message with a new one."""
    if not file_exists(new_file_path):
        return

    print(f"  🔄  Updating message {message_id} ...")
    try:
       
        print(f"  ⬆️  Uploading new file ...")
        tmp_msg = await client.send_file(
            SAVED, new_file_path,
            workers=8,
            progress_callback=progress,
        )

        print(f"\n  ✏️  Replacing message ...")
        await client.edit_message(
            SAVED, message_id,
            file=tmp_msg.media,
            text=f"Updated: {os.path.basename(new_file_path)}",
        )

        #delete message
        await tmp_msg.delete()
        print("  ✅  Update successful!")
    except Exception as e:
        print(f"\n  ❌  Update failed: {e}")

async def list_files() -> None:
    """List all messages with media in Saved Messages."""
    print("  📋  Files in Saved Messages:\n")
    print(f"  {'ID':>10}  {'File name'}")
    print(f"  {'─'*10}  {'─'*40}")
    try:
        async for msg in client.iter_messages(SAVED):
            if msg.media:
                name = msg.file.name if msg.file else "—"
                print(f"  {msg.id:>10}  {name}")
    except Exception as e:
        print(f"  ❌  Error: {e}")

#Menu prompts
async def prompt_upload() -> None:
    path    = input("  File path : ").strip()
    caption = input("  Caption   : ").strip()
    await upload(path, caption)

async def prompt_download() -> None:
    msg_id = int(input("  Message ID  : "))
    out    = input("  Save as     : ").strip()
    await download(msg_id, out)

async def prompt_update() -> None:
    msg_id   = int(input("  Message ID    : "))
    new_path = input("  New file path : ").strip()
    await update(msg_id, new_path)

#Main
MENU = [
    ("Upload a file",              prompt_upload),
    ("Download a file",            prompt_download),
    ("Update / replace a file",    prompt_update),
    ("List all files",             list_files),
    ("Exit",                       None),
]

async def main() -> None:
    print("\n╔══════════════════════════════╗")
    print("║   Telegram Cloud Storage     ║")
    print("╚══════════════════════════════╝\n")

    while True:
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}.  {label}")

        print()
        choice = input("  Choice: ").strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU)):
            print("  ❌  Invalid choice.")
            continue

        label, handler = MENU[int(choice) - 1]

        if handler is None:          # Exit
            print("  👋  Bye!")
            return

        print()
        await handler()
        print()


with client:
    client.loop.run_until_complete(main())