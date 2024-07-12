# (c) @AbirHasan2005

import asyncio
from config import Config
import pyrogram
from pyrogram import Client,filters, enums
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


async def ForceSub(c: Client, m: Message):
    try:
        invite_link = await c.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
    except FloodWait as e:
        await asyncio.sleep(e.x)
        invite_link = await c.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
    except Exception as err:
        print(f"Uɴᴀʙʟᴇ Tᴏ Dᴏ Fᴏʀᴄᴇ Sᴜʙsᴄʀɪʙᴇ Tᴏ {Config.UPDATES_CHANNEL}\n\nError: {err}")
        return 200
    try:
        user = await c.get_chat_member(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL), user_id=m.from_user.id)
        if user.status == "kicked":
            await c.send_message(
                chat_id=m.from_user.id,
                text="Sᴏʀʀʏ Sɪʀ, Yᴏᴜ Aʀᴇ Bᴀɴɴᴇᴅ Tᴏ Usᴇ Mᴇ. Cᴏɴᴛᴀᴄᴛ Mʏ Aᴅᴍɪɴ @Sujan_BotZ.",
                disable_web_page_preview=True,
                parse_mode="Markdown",
                
            )
            return 400
    except UserNotParticipant:
        await c.send_message(
            chat_id=m.from_user.id,
            text="**Pʟᴇᴀsᴇ Jᴏɪɴ Mʏ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ Tᴏ Usᴇ Tʜɪs Bᴏᴛ!**\n\n Oɴʟʏ Cʜᴀɴɴᴇʟ Sᴜʙsᴄʀɪʙᴇʀs Cᴀɴ Usᴇ Tʜᴇ Bᴏᴛ!",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🤖 Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ", url=invite_link.invite_link)
                    ],
                    [
                        InlineKeyboardButton("🔄 Rᴇғʀᴇsʜ 🔄", callback_data="refreshFsub")
                    ]
                ]
            )
            
        )
        return 400
    except Exception:
        await c.send_message(
            chat_id=m.from_user.id,
            text="Sᴏᴍᴇᴛʜɪɴɢ Wᴇɴᴛ Wʀᴏɴɢ. Cᴏɴᴛᴀᴄᴛ Mʏ Aᴅᴍɪɴ.",
            disable_web_page_preview=True,
            parse_mode="Markdown",
        )
        return 400
    return 200
