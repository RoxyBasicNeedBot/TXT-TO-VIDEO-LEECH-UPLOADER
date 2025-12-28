# Don't Remove Credit Tg - https://t.me/roxybasicneedbot1
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@roxybasicneedbot
# Ask Doubt on telegram https://t.me/roxybasicneedbot1

import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_LINK, ADMINS, OWNER_ID
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode, ChatMemberStatus

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)

# Welcome image file path
WELCOME_IMAGE_PATH = "welcome.jpg"

# Force Subscribe Check Function
async def is_subscribed(bot, user_id):
    if not FORCE_SUB_CHANNEL:
        return True
    
    try:
        member = await bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return True
        else:
            return False
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# Force Subscribe Decorator
def force_subscribe(func):
    async def wrapper(bot, message):
        if FORCE_SUB_CHANNEL:
            is_sub = await is_subscribed(bot, message.from_user.id)
            if not is_sub:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/roxybasicneedbot1")],
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_sub")]
                ])
                await message.reply_text(
                    f"<b>🔒 Access Denied!</b>\n\n"
                    f"You must join our channel to use this bot.\n\n"
                    f"👇 Click the button below to join:",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                return
        await func(bot, message)
    return wrapper

# Enhanced URL validation function
def is_valid_url(url):
    """Check if URL is valid and accessible"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def extract_url_from_line(line):
    """Extract and validate URL from a line of text"""
    line = line.strip()
    if not line:
        return None, None
    
    # Try to find URL in the line
    url_match = re.search(r'https?://[^\s]+', line)
    if url_match:
        url = url_match.group()
        # Extract title (everything before the URL)
        title = line.replace(url, '').strip()
        if not title:
            title = f"File_{hash(url) % 1000}"
        return title, url
    
    # If line doesn't contain http/https, check if it's a valid domain
    if '.' in line and not line.startswith('/'):
        # Assume it's a URL without protocol
        url = 'https://' + line
        if is_valid_url(url):
            return f"File_{hash(line) % 1000}", url
    
    return None, None

@bot.on_message(filters.command(["start"]))
@force_subscribe
async def start(bot: Client, m: Message):
    welcome_text = f"<b>👋 Hello {m.from_user.mention}!</b>\n\n<blockquote>📁 I am a bot for downloading files from your <b>.TXT</b> file and uploading them to Telegram.\n\n🚀 To get started, send /upload command and follow the steps.</blockquote>"
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Upload Files", callback_data="upload_files")
        ],
        [
            InlineKeyboardButton("🔔 Channel", url="https://t.me/roxybasicneedbot1"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/roxycontactbot")
        ]
    ])
    
    # Check if the welcome image file exists
    if os.path.exists(WELCOME_IMAGE_PATH):
        await m.reply_photo(
            photo=WELCOME_IMAGE_PATH, 
            caption=welcome_text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await m.reply_text(
            welcome_text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

@bot.on_callback_query()
async def callback_handler(bot: Client, query: CallbackQuery):
    data = query.data
    
    if data == "refresh_sub":
        if FORCE_SUB_CHANNEL:
            is_sub = await is_subscribed(bot, query.from_user.id)
            if is_sub:
                await query.message.delete()
                await bot.send_message(
                    query.from_user.id, 
                    "✅ **Subscription Verified!**\n\nYou can now use the bot. Send /start to begin."
                )
            else:
                await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
        else:
            await query.answer("✅ No subscription required!")
    
    elif data == "upload_files":
        await query.answer("Send /upload command to start!", show_alert=True)

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("**🛑 Stopped**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
@force_subscribe
async def upload(bot: Client, m: Message):
    editable = await m.reply_text('📤 Send your TXT file with links ⚡️')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)

    path = f"./downloads/{m.chat.id}"
    os.makedirs(path, exist_ok=True)

    try:
        with open(x, "r", encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split("\n")
        links = []
        
        for line in lines:
            title, url = extract_url_from_line(line)
            if title and url and is_valid_url(url):
                links.append([title, url])
        
        os.remove(x)
        
        if not links:
            await editable.edit("❌ **No valid links found in the file!**\n\nPlease make sure your file contains valid URLs.")
            return
            
    except Exception as e:
        await editable.edit(f"❌ **Error reading file:** {str(e)}")
        if os.path.exists(x):
            os.remove(x)
        return
    
    await editable.edit(f"📊 **Total Links Found:** {len(links)}\n\n📝 **Send starting number** (default: 1)")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("📝 **Enter your batch name:**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    
    await editable.edit("🎬 **Select video quality:**\n\n144, 240, 360, 480, 720, 1080")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    
    quality_map = {
        "144": "256x144", "240": "426x240", "360": "640x360",
        "480": "854x480", "720": "1280x720", "1080": "1920x1080"
    }
    res = quality_map.get(raw_text2, "UN")
    
    await editable.edit("💬 **Enter caption for files:**")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    MR = raw_text3
    
    await editable.edit("🖼 **Send thumbnail URL** (or send 'no' to skip):")
    input6 = await bot.listen(editable.chat.id)
    thumb_input = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = "no"
    if thumb_input.startswith(("http://", "https://")):
        try:
            getstatusoutput(f"wget '{thumb_input}' -O 'thumb.jpg'")
            if os.path.exists('thumb.jpg'):
                thumb = "thumb.jpg"
        except:
            thumb = "no"

    try:
        count = max(1, int(raw_text)) if raw_text.isdigit() else 1
    except:
        count = 1

    successful_downloads = 0
    failed_downloads = 0

    try:
        for i in range(count - 1, len(links)):
            if i >= len(links):
                break
            
            try:
                title, url = links[i]
                
                # Process URL for different platforms
                if "drive.google.com" in url:
                    url = url.replace("file/d/","uc?export=download&id=").replace("/view?usp=sharing","")
                elif "youtube.com/watch" in url or "youtu.be/" in url:
                    pass  # Keep as is for yt-dlp
                elif "visionias" in url:
                    try:
                        async with ClientSession() as session:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                            async with session.get(url, headers=headers) as resp:
                                text = await resp.text()
                                m3u8_match = re.search(r"(https://.*?playlist\.m3u8.*?)\"", text)
                                if m3u8_match:
                                    url = m3u8_match.group(1)
                    except:
                        pass
                
                name1 = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
                name = f'{str(count).zfill(3)}) {name1}'

                # Determine download strategy
                if "youtu" in url:
                    ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                    cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.%(ext)s"'
                elif url.endswith('.pdf'):
                    cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                else:
                    cmd = f'yt-dlp -f "best" "{url}" -o "{name}.%(ext)s"'

                cc = f'**📹 Video #{str(count).zfill(3)}**\n**📁 Title:** {name1}\n**📦 Batch:** {raw_text0}\n{MR}'
                cc1 = f'**📄 Document #{str(count).zfill(3)}**\n**📁 Title:** {name1}\n**📦 Batch:** {raw_text0}\n{MR}'
                
                # Show download progress
                prog = await m.reply_text(
                    f"⬇️ **Downloading...**\n\n"
                    f"📁 **Name:** `{name1}`\n"
                    f"🔗 **URL:** `{url[:50]}...`\n"
                    f"📊 **Progress:** {count}/{len(links)}"
                )
                
                try:
                    if "drive.google.com" in url:
                        filename = await helper.download(url, name)
                        if filename and os.path.exists(filename):
                            await bot.send_document(chat_id=m.chat.id, document=filename, caption=cc1)
                            os.remove(filename)
                            successful_downloads += 1
                    elif ".pdf" in url:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        expected_file = f"{name}.pdf"
                        if os.path.exists(expected_file):
                            await bot.send_document(chat_id=m.chat.id, document=expected_file, caption=cc1)
                            os.remove(expected_file)
                            successful_downloads += 1
                    else:
                        # Video download
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        
                        # Find downloaded file
                        possible_extensions = ['.mp4', '.mkv', '.avi', '.webm', '.mov']
                        filename = None
                        for ext in possible_extensions:
                            test_file = f"{name}{ext}"
                            if os.path.exists(test_file):
                                filename = test_file
                                break
                        
                        if filename and os.path.exists(filename):
                            await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                            successful_downloads += 1
                        else:
                            failed_downloads += 1
                            await prog.edit(f"❌ **Failed:** {name1}")
                            await asyncio.sleep(2)
                    
                    await prog.delete()
                    count += 1
                    time.sleep(1)
                    
                except FloodWait as e:
                    await m.reply_text(f"⚠️ **Rate limited. Waiting {e.x} seconds...**")
                    time.sleep(e.x)
                    continue
                except Exception as download_error:
                    failed_downloads += 1
                    await prog.edit(f"❌ **Error:** {str(download_error)[:100]}")
                    await asyncio.sleep(3)
                    continue

            except Exception as e:
                failed_downloads += 1
                await m.reply_text(f"❌ **Processing error:** {str(e)[:200]}")
                continue

    except Exception as e:
        await m.reply_text(f"❌ **Fatal error:** {str(e)}")

    # Final summary
    summary_text = (
        f"🎉 **Download Complete!**\n\n"
        f"✅ **Successful:** {successful_downloads}\n"
        f"❌ **Failed:** {failed_downloads}\n"
        f"📊 **Total:** {successful_downloads + failed_downloads}"
    )
    await m.reply_text(summary_text)

if __name__ == "__main__":
    bot.run()
