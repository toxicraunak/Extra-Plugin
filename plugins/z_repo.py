import asyncio

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ChampuMusic import app
from ChampuMusic.utils.database import add_served_chat, get_assistant


start_txt = """**
✪ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 Tanji 𝗥𝗲𝗽𝗼𝘀 ✪


➲ ᴇᴀsʏ ʜᴇʀᴏᴋᴜ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ ✰  
➲ ɴᴏ ʙᴀɴ ɪssᴜᴇs ✰  
➲ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅʏɴᴏs ✰  
➲ 𝟸𝟺/𝟽 ʟᴀɢ-ғʀᴇᴇ ✰

► sᴇɴᴅ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍs!
**"""




@app.on_message(filters.command("dev"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ", url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
          InlineKeyboardButton("Tanji", url="https://t.me/toxictanji"),
          InlineKeyboardButton("𓆩 ˹Channel 𓆪", url="https://t.me/haxkx2"),
          ],
               [
                InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/toxictanji"),

],[
              InlineKeyboardButton("ᴍᴜsɪᴄ", url=f"https://github.com/toxicraunak/Hina-Baby2.0"),
              InlineKeyboardButton("Instagram 🧑🏻‍💻", url=f"https://www.instagram.com/bot_tanji?igsh=MW5yN280MmV6ejRicA=="),
              ],
[
              InlineKeyboardButton("𓆩Youtibe 𓆪", url=f"https://youtube.com/@haxkx?si=7-9TIg6QZOb6PIuX")
              ],
              [
              InlineKeyboardButton("Group", url=f"https://t.me/haxkx2_gc")
]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo=config.START_IMG_URL,
        caption=start_txt,
        reply_markup=reply_markup
    )


