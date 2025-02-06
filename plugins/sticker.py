import imghdr
import math
import os
import asyncio
from asyncio import gather
from traceback import format_exc
from typing import List

from PIL import Image
from pyrogram import Client, errors, filters, raw
from pyrogram.errors import (
    PeerIdInvalid,
    ShortnameOccupyFailed,
    StickerEmojiInvalid,
    StickerPngDimensions,
    StickerPngNopng,
    UserIsBlocked,
)
from pyrogram.file_id import FileId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import pyrogram
from uuid import uuid4
from ChampuMusic import app
from utils.error import capture_err

BOT_USERNAME = app.username

MAX_STICKERS = (
    120  # would be better if we could fetch this limit directly from telegram
)
SUPPORTED_TYPES = ["jpeg", "png", "webp"]
STICKER_DIMENSIONS = (512, 512)


async def get_sticker_set_by_name(
    client: Client, name: str
) -> raw.base.messages.StickerSet:
    try:
        return await client.invoke(
            raw.functions.messages.GetStickerSet(
                stickerset=raw.types.InputStickerSetShortName(short_name=name),
                hash=0,
            )
        )
    except errors.exceptions.not_acceptable_406.StickersetInvalid:
        return None


# Known errors: (I don't see a reason to catch them as we, for sure, won't face them right now):
# errors.exceptions.bad_request_400.PackShortNameInvalid -> pack name needs to end with _by_botname
# errors.exceptions.bad_request_400.ShortnameOccupyFailed -> pack's name
# is already in use


async def create_sticker_set(
    client: Client,
    owner: int,
    title: str,
    short_name: str,
    stickers: List[raw.base.InputStickerSetItem],
) -> raw.base.messages.StickerSet:
    return await client.invoke(
        raw.functions.stickers.CreateStickerSet(
            user_id=await client.resolve_peer(owner),
            title=title,
            short_name=short_name,
            stickers=stickers,
        )
    )


async def add_sticker_to_set(
    client: Client,
    stickerset: raw.base.messages.StickerSet,
    sticker: raw.base.InputStickerSetItem,
) -> raw.base.messages.StickerSet:
    return await client.invoke(
        raw.functions.stickers.AddStickerToSet(
            stickerset=raw.types.InputStickerSetShortName(
                short_name=stickerset.set.short_name
            ),
            sticker=sticker,
        )
    )


async def create_sticker(
    sticker: raw.base.InputDocument, emoji: str
) -> raw.base.InputStickerSetItem:
    return raw.types.InputStickerSetItem(document=sticker, emoji=emoji)


async def resize_file_to_sticker_size(file_path: str) -> str:
    im = Image.open(file_path)
    if (im.width, im.height) < STICKER_DIMENSIONS:
        size1 = im.width
        size2 = im.height
        if im.width > im.height:
            scale = STICKER_DIMENSIONS[0] / size1
            size1new = STICKER_DIMENSIONS[0]
            size2new = size2 * scale
        else:
            scale = STICKER_DIMENSIONS[1] / size2
            size1new = size1 * scale
            size2new = STICKER_DIMENSIONS[1]
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        im = im.resize(sizenew)
    else:
        im.thumbnail(STICKER_DIMENSIONS)
    try:
        os.remove(file_path)
        file_path = f"{file_path}.png"
        return file_path
    finally:
        im.save(file_path)


async def upload_document(
    client: Client, file_path: str, chat_id: int
) -> raw.base.InputDocument:
    media = await client.invoke(
        raw.functions.messages.UploadMedia(
            peer=await client.resolve_peer(chat_id),
            media=raw.types.InputMediaUploadedDocument(
                mime_type=client.guess_mime_type(file_path) or "application/zip",
                file=await client.save_file(file_path),
                attributes=[
                    raw.types.DocumentAttributeFilename(
                        file_name=os.path.basename(file_path)
                    )
                ],
            ),
        )
    )
    return raw.types.InputDocument(
        id=media.document.id,
        access_hash=media.document.access_hash,
        file_reference=media.document.file_reference,
    )


async def get_document_from_file_id(
    file_id: str,
) -> raw.base.InputDocument:
    decoded = FileId.decode(file_id)
    return raw.types.InputDocument(
        id=decoded.media_id,
        access_hash=decoded.access_hash,
        file_reference=decoded.file_reference,
    )


@app.on_message(filters.command("stickerid"))
@capture_err
async def sticker_id(_, message: Message):
    reply = message.reply_to_message

    if not reply:
        return await message.reply("ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ.")

    if not reply.sticker:
        return await message.reply("ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ.")

    await message.reply_text(f"`{reply.sticker.file_id}`")


@app.on_message(filters.command("getsticker"))
@capture_err
async def sticker_image(_, message: Message):
    r = message.reply_to_message

    if not r:
        return await message.reply("ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ.")

    if not r.sticker:
        return await message.reply("ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ.")

    m = await message.reply("sᴇɴᴅɪɴɢ..")
    f = await r.download(f"{r.sticker.file_unique_id}.png")

    await gather(
        *[
            message.reply_photo(f),
            message.reply_document(f),
        ]
    )

    await m.delete()
    os.remove(f)


@app.on_message(filters.command("kang"))
@capture_err
async def kang(client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ/image to kang it.")
    if not message.from_user:
        return await message.reply_text("ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴ ᴀᴅᴍɪɴ, ᴋᴀɴɢ sᴛɪᴄᴋᴇʀs ɪɴ ᴍʏ ᴘᴍ.")
    msg = await message.reply_text("ᴋᴀɴɢɪɴɢ sᴛɪᴄᴋᴇʀ..")

    # Find the proper emoji
    args = message.text.split()
    if len(args) > 1:
        sticker_emoji = str(args[1])
    elif message.reply_to_message.sticker and message.reply_to_message.sticker.emoji:
        sticker_emoji = message.reply_to_message.sticker.emoji
    else:
        sticker_emoji = "🤔"

    # Get the corresponding fileid, resize the file if necessary
    doc = message.reply_to_message.photo or message.reply_to_message.document
    try:
        if message.reply_to_message.sticker:
            sticker = await create_sticker(
                await get_document_from_file_id(
                    message.reply_to_message.sticker.file_id
                ),
                sticker_emoji,
            )
        elif doc:
            if doc.file_size > 10000000:
                return await msg.edit("ғɪʟᴇ sɪᴢᴇ ᴛᴏᴏ ʟᴀʀɢᴇ.")

            temp_file_path = await app.download_media(doc)
            image_type = imghdr.what(temp_file_path)
            if image_type not in SUPPORTED_TYPES:
                return await msg.edit("ғᴏʀᴍᴀᴛ ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ! ({})".format(image_type))
            try:
                temp_file_path = await resize_file_to_sticker_size(temp_file_path)
            except OSError as e:
                await msg.edit_text("sᴏᴍᴇᴛʜɪɴɢ ᴡʀᴏɴɢ ʜᴀᴘᴘᴇɴᴇᴅ.")
                raise Exception(
                    f"sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ ᴡʜɪʟᴇ ʀᴇsɪᴢɪɴɢ ᴛʜᴇ sᴛɪᴄᴋᴇʀ (ᴀᴛ {temp_file_path}); {e}"
                )
            sticker = await create_sticker(
                await upload_document(client, temp_file_path, message.chat.id),
                sticker_emoji,
            )
            if os.path.isfile(temp_file_path):
                os.remove(temp_file_path)
        else:
            return await msg.edit("ɴᴏᴘᴇ, ᴄᴀɴ'ᴛ ᴋᴀɴɢ ᴛʜᴀᴛ.")
    except ShortnameOccupyFailed:
        await message.reply_text("ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ɴᴀᴍᴇ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ")
        return

    except Exception as e:
        await message.reply_text(str(e))
        e = format_exc()
        return print(e)

    # Find an available pack & add the sticker to the pack; create a new pack if needed
    # Would be a good idea to cache the number instead of searching it every
    # single time...
    packnum = 0
    packname = "f" + str(message.from_user.id) + "_by_" + BOT_USERNAME
    limit = 0
    try:
        while True:
            # Prevent infinite rules
            if limit >= 50:
                return await msg.delete()

            stickerset = await get_sticker_set_by_name(client, packname)
            if not stickerset:
                stickerset = await create_sticker_set(
                    client,
                    message.from_user.id,
                    f"{message.from_user.first_name[:32]}'s kang pack",
                    packname,
                    [sticker],
                )
            elif stickerset.set.count >= MAX_STICKERS:
                packnum += 1
                packname = (
                    "f"
                    + str(packnum)
                    + "_"
                    + str(message.from_user.id)
                    + "_by_"
                    + BOT_USERNAME
                )
                limit += 1
                continue
            else:
                try:
                    await add_sticker_to_set(client, stickerset, sticker)
                except StickerEmojiInvalid:
                    return await msg.edit("[ERROR]: INVALID_EMOJI_IN_ARGUMENT")
            limit += 1
            break

        await msg.edit(
            "sᴛɪᴄᴋᴇʀ ᴋᴀɴɢᴇᴅ ᴛᴏ [ᴘᴀᴄᴋ](t.me/addstickers/{})\nEmoji: {}".format(
                packname, sticker_emoji
            )
        )
    except (PeerIdInvalid, UserIsBlocked):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Start", url=f"t.me/{BOT_USERNAME}")]]
        )
        await msg.edit(
            "ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ sᴛᴀʀᴛ ᴀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ ᴡɪᴛʜ ᴍᴇ.",
            reply_markup=keyboard,
        )
    except StickerPngNopng:
        await message.reply_text(
            "sᴛɪᴄᴋᴇʀs ᴍᴜsᴛ ʙᴇ ᴘɴɢ ғɪʟᴇs ʙᴜᴛ ᴛʜᴇ ᴘʀᴏᴠɪᴅᴇᴅ ɪᴍᴀɢᴇ ᴡᴀs ɴᴏᴛ ᴀ ᴘɴɢ"
        )
    except StickerPngDimensions:
        await message.reply_text("ᴛʜᴇ sᴛɪᴄᴋᴇʀ ᴘɴɢ ᴅɪᴍᴇɴsɪᴏɴs ᴀʀᴇ ɪɴᴠᴀʟɪᴅ.")

@app.on_message(filters.command("st"))
def generate_sticker(client, message):
    if len(message.command) == 2:
        sticker_id = message.command[1]
        try:
            client.send_sticker(message.chat.id, sticker=sticker_id)
        except Exception as e:
            message.reply_text(f"Error: {e}")
    else:
        message.reply_text("ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴛɪᴄᴋᴇʀ ɪᴅ ᴀғᴛᴇʀ /st ᴄᴏᴍᴍᴀɴᴅ.")

@app.on_message(filters.command("packkang"))
async def _packkang(app, message):
    txt = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ....")

    if not message.reply_to_message:
        await txt.edit('ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ!')
        return

    if not message.reply_to_message.sticker:
        await txt.edit('ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ!')
        return

    if len(message.command) < 2:
        pack_name = f'{message.from_user.first_name}_sticker_pack_by_@{BOT_USERNAME}'
    else:
        pack_name = message.text.split(maxsplit=1)[1]

    short_name = message.reply_to_message.sticker.set_name
    try:
        stickers = await app.invoke(
            raw.functions.messages.GetStickerSet(
                stickerset=raw.types.InputStickerSetShortName(short_name=short_name),
                hash=0
            )
        )
    except Exception as e:
        await txt.edit(f"ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴛɪᴄᴋᴇʀ sᴇᴛ: {str(e)}")
        return

    documents = stickers.documents
    if not documents:
        await txt.edit("sᴛɪᴄᴋᴇʀ sᴇᴛ ɪs ᴇᴍᴘᴛʏ ᴏʀ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ ғᴇᴛᴄʜᴇᴅ.")
        return

    sticks = []
    for document in documents:
        emoji = "🙂"
        for attribute in document.attributes:
            if isinstance(attribute, raw.types.DocumentAttributeSticker):
                emoji = attribute.alt or "🙂"
                break

        input_document = raw.types.InputDocument(
            id=document.id,
            access_hash=document.access_hash,
            file_reference=document.file_reference
        )
        sticks.append(
            raw.types.InputStickerSetItem(
                document=input_document,
                emoji=emoji
            )
        )

    short_name = f'sticker_pack_{str(uuid4()).replace("-", "")}_by_{app.me.username}'
    user_id = await app.resolve_peer(message.from_user.id)

    for attempt in range(3):
        try:
            await app.invoke(
                raw.functions.stickers.CreateStickerSet(
                    user_id=user_id,
                    title=pack_name,
                    short_name=short_name,
                    stickers=sticks,
                )
            )
            await txt.edit(
                f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴋᴀɴɢᴇᴅ ʟɪɴᴋ!\nᴛᴏᴛᴀʟ sᴛɪᴄᴋᴇʀs: {len(sticks)}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ᴘᴀᴄᴋ ʟɪɴᴋ", url=f"http://t.me/addstickers/{short_name}")]]
                )
            )
            return
        except Exception as e:
            if "Timeout" in str(e):
                if attempt < 2: 
                    await txt.edit(f"ʀᴇᴛʀʏɪɴɢ... ({attempt + 1}/3)")
                    await asyncio.sleep(5)
                else:
                    await txt.edit(f"ғᴀɪʟᴇᴅ ᴀғᴛᴇʀ 𝟹 ʀᴇᴛʀɪᴇs: {str(e)}")
            elif "FLOOD_WAIT_X" in str(e):
             await asyncio.sleep(e.value)
            else:
                await txt.edit(f"ᴇʀʀᴏʀ: {str(e)}")
                return

__MODULE__ = "Sᴛɪᴄᴋᴇʀ"
__HELP__ = """
**COMMANDS:**

• /stickerid , /stid - **ɢᴇᴛs ᴛʜᴇ ғɪʟᴇ ɪᴅ ᴏғ ᴀɴʏ ʀᴇᴘʟɪᴇᴅ sᴛɪᴄᴋᴇʀ.**
• /getsticker - **ɢᴇᴛs ᴛʜᴇ ɪᴍᴀɢᴇ ᴏғ ᴀɴʏ ʀᴇᴘʟɪᴇᴅ sᴛɪᴄᴋᴇʀ.**
• /kang - **ᴋᴀɴɢs ᴀɴʏ sᴛɪᴄᴋᴇʀ ɪɴ ᴛʜᴇ ʏᴏᴜ ᴘᴀᴄᴋ**
• /st - **ᴄʜᴇᴄᴋ sᴛɪᴄᴋᴇʀ ғʀᴏᴍ sᴛɪᴄᴋᴇʀ ɪᴅ**
• /packkang - **ᴋᴀɴɢ ᴡʜᴏʟᴇ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ**

**INFO:**

- ᴛʜɪs ʙᴏᴛ ᴀʟʟᴏᴡs ᴜsᴇʀs ᴛᴏ ɢᴇᴛ ᴛʜᴇ ғɪʟᴇ ɪᴅ ᴏʀ ᴛʜᴇ ɪᴍᴀɢᴇ ᴏғ ᴀɴʏ sᴛɪᴄᴋᴇʀ ᴛʜᴀᴛ ɪs ʀᴇᴘʟɪᴇᴅ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ, ᴀɴᴅ ᴀʟsᴏ ᴀʟʟᴏᴡs ᴜsᴇʀs ᴛᴏ ᴋᴀɴɢ ᴀɴʏ sᴛɪᴄᴋᴇʀ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ᴀᴅᴅ ɪᴛ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ.
"""
