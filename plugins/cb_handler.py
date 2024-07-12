import asyncio
import os
from config import Config
from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pyromod.types import ListenerTypes
from pyrogram.errors import FloodWait, UserNotParticipant
from pyromod.listen import Client

from helpers import database
from helpers.utils import UserSettings

from bot import (
    LOGGER,
    UPLOAD_AS_DOC,
    UPLOAD_TO_DRIVE,
    delete_all,
    formatDB,
    gDict,
    queueDB,
    showQueue,
    
)

from plugins.mergeVideo import mergeNow
from plugins.mergeVideoAudio import mergeAudio
from plugins.mergeVideoSub import mergeSub
from plugins.streams_extractor import streamsExtractor
from plugins.usettings import userSettings




        
@Client.on_callback_query()
async def callback_handler(c: Client, cb: CallbackQuery):
    #     await cb_handler.cb_handler(c, cb)
    # async def cb_handler(c: Client, cb: CallbackQuery):
    if cb.data == "merge":
        await cb.message.edit(
            text="Wʜᴇʀᴇ Dᴏ Yᴏᴜ Wᴀɴᴛ Tᴏ Uᴘʟᴏᴀᴅ?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📤 Tᴏ Tᴇʟᴇɢʀᴀᴍ", callback_data="to_telegram"
                        ),
                        InlineKeyboardButton("🌫️ Tᴏ Dʀɪᴠᴇ", callback_data="to_drive"),
                    ],
                    [InlineKeyboardButton("🚫 Cᴀɴᴄᴇʟ 🚫", callback_data="cancel")],
                ]
            ),
        )
        return
        
    elif cb.data == "to_drive":
        try:
            urc = await database.getUserRcloneConfig(cb.from_user.id)
            await c.download_media(
                message=urc, file_name=f"userdata/{cb.from_user.id}/rclone.conf"
            )
        except Exception :
            await cb.message.reply_text("Rclone not Found, Unable to upload to drive")
        if os.path.exists(f"userdata/{cb.from_user.id}/rclone.conf") is False:
            await cb.message.delete()
            await delete_all(root=f"downloads/{cb.from_user.id}/")
            queueDB.update(
                {cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}}
            )
            formatDB.update({cb.from_user.id: None})
            return
        UPLOAD_TO_DRIVE.update({f"{cb.from_user.id}": True})
        await cb.message.edit(
            text="Oᴋᴀʏ I'ʟʟ Uᴘʟᴏᴀᴅ Tᴏ Dʀɪᴠᴇ\nDᴏ Yᴏᴜ Wᴀɴᴛ Tᴏ Rᴇɴᴀᴍᴇ? Dᴇғᴀᴜʟᴛ Fɪʟᴇ Nᴀᴍᴇ Is **[@BoB_Files1]_merged.mkv**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👆 Dᴇғᴀᴜʟᴛ", callback_data="rename_NO"),
                        InlineKeyboardButton("✍️ Rᴇɴᴀᴍᴇ", callback_data="rename_YES"),
                    ],
                    [InlineKeyboardButton("🚫 Cᴀɴᴄᴇʟ 🚫", callback_data="cancel")],
                ]
            ),
        )
        return


   
    elif "refreshFsub" in cb.data:
        if Config.UPDATES_CHANNEL:
            try:
                user = await c.get_chat_member(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL), user_id=cb.message.chat.id)
                if user.status =="banned":
                    await cb.message.edit(
                        text="Sᴏʀʀʏ Sɪʀ, Yᴏᴜ Aʀᴇ Bᴀɴɴᴇᴅ Tᴏ Usᴇ Mᴇ. Cᴏɴᴛᴀᴄᴛ Mʏ Aᴅᴍɪɴ.",
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                try:
                    invite_link = await c.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    invite_link = await c.create_chat_invite_link(chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL))
                await cb.message.edit(
                    text="**Yᴏᴜ Sᴛɪʟʟ Dɪᴅɴ'ᴛ Jᴏɪɴ ☹️, Pʟᴇᴀsᴇ Jᴏɪɴ Mʏ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ Tᴏ Usᴇ Tʜɪs Bᴏᴛ!**\n\nOɴʟʏ Cʜᴀɴɴᴇʟ Sᴜʙsᴄʀɪʙᴇʀs Cᴀɴ Usᴇ Tʜᴇ Bᴏᴛ!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("🔄 Tʀʏ Aɢᴀɪɴ 🔄", callback_data="refreshFsub")
                            ]
                        ]
                    )
                    
                )
                return
            except Exception:
                await cb.message.edit(
                    text="Sᴏᴍᴇᴛʜɪɴɢ Wᴇɴᴛ Wʀᴏɴɢ. Cᴏɴᴛᴀᴄᴛ Mʏ Aᴅᴍɪɴ.",
                    disable_web_page_preview=True
                )
                return
            await cb.message.edit(
            text=f"Hɪ **⚡ I Aᴍ A Fɪʟᴇ/Vɪᴅᴇᴏ Mᴇʀɢᴇ Bᴏᴛ\n\n😎 I Cᴀɴ Mᴇʀɢᴇ Tᴇʟᴇɢʀᴀᴍ Fɪʟᴇs!, Aɴᴅ Uᴘʟᴏᴀᴅ Iᴛ Tᴏ Tᴇʟᴇɢʀᴀᴍ.\n\n/help Fᴏʀ Hᴏᴡ Tᴏ Uꜱᴇ\n\n**Oᴡɴᴇʀ: 🈲 @{Config.OWNER_USERNAME}**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📢", url="https://t.me/BoB_Files1")]]),
            disable_web_page_preview=True
        )
            
     
    elif cb.data == "to_telegram":
        UPLOAD_TO_DRIVE.update({f"{cb.from_user.id}": False})
        await cb.message.edit(
            text="Hᴏᴡ Dᴏ Yᴏu Wᴀɴᴛ Tᴏ Uᴘʟᴏᴀᴅ Fɪʟᴇ",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🎞️ Vɪᴅᴇᴏ", callback_data="video"),
                        InlineKeyboardButton("📁 Fɪʟᴇ", callback_data="document"),
                    ],
                    [InlineKeyboardButton("🚫 Cᴀɴᴄᴇʟ 🚫", callback_data="cancel")],
                ]
            ),
        )
        return
    

    elif cb.data == "document":
        UPLOAD_AS_DOC.update({f"{cb.from_user.id}": True})
        await cb.message.edit(
            text="Dᴏ Yᴏᴜ Wᴀɴᴛ Tᴏ Rᴇɴᴀᴍᴇ? Dᴇғᴀᴜʟᴛ Fɪʟᴇ Nᴀᴍᴇ Is **[@BoB_Files1]_merged.mkv**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👆 Dᴇғᴀᴜʟᴛ", callback_data="rename_NO"),
                        InlineKeyboardButton("✍️ Rᴇɴᴀᴍᴇ", callback_data="rename_YES"),
                    ],
                    [InlineKeyboardButton("🚫 Cᴀɴᴄᴇʟ 🚫", callback_data="cancel")],
                ]
            ),
        )
        return

    elif cb.data == "video":
        UPLOAD_AS_DOC.update({f"{cb.from_user.id}": False})
        await cb.message.edit(
            text="Dᴏ Yᴏᴜ Wᴀɴᴛ Tᴏ Rᴇɴᴀᴍᴇ? Dᴇғᴀᴜʟᴛ Fɪʟᴇ Nᴀᴍᴇ Is **[@BoB_Files1]_merged.mkv**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👆 Dᴇғᴀᴜʟᴛ", callback_data="rename_NO"),
                        InlineKeyboardButton("✍️ Rᴇɴᴀᴍᴇ", callback_data="rename_YES"),
                    ],
                    [InlineKeyboardButton("🚫 Cᴀɴᴄᴇʟ 🚫", callback_data="cancel")],
                ]
            ),
        )
        return

    elif cb.data.startswith("rclone_"):
        if "save" in cb.data:
            message_id = cb.message.reply_to_message.document.file_id
            LOGGER.info(message_id)
            await c.download_media(
                message=cb.message.reply_to_message,
                file_name=f"./userdata/{cb.from_user.id}/rclone.conf",
            )
            await database.addUserRcloneConfig(cb, message_id)
        else:
            await cb.message.delete()
        return

    elif cb.data.startswith("rename_"):
        user = UserSettings(cb.from_user.id, cb.from_user.first_name)
        if "YES" in cb.data:
            await cb.message.edit(
                "Cᴜʀʀᴇɴᴛ Fɪʟᴇɴᴀᴍᴇ: **[@BoB_Files1]_merged.mkv**\n\nSᴇɴᴅ Mᴇ Nᴇᴡ ғɪʟᴇ Nᴀᴍᴇ Wɪᴛʜᴏᴜᴛ Exᴛᴇɴsɪᴏɴ: Yᴏᴜ Hᴀᴠᴇ 60 Sᴇᴄᴏɴᴅ"
            )
            res: Message = await c.listen(chat_id=cb.message.chat.id, filters=filters.text, listener_type=ListenerTypes.MESSAGE, timeout=120, user_id=cb.from_user.id)
            if res.text:
                new_file_name = f"downloads/{str(cb.from_user.id)}/{res.text}.mkv"
                await res.delete(True)
            if user.merge_mode == 1:
                await mergeNow(c, cb, new_file_name)
            elif user.merge_mode == 2:
                await mergeAudio(c, cb, new_file_name)
            elif user.merge_mode == 3:
                await mergeSub(c, cb, new_file_name)

            return
        if "NO" in cb.data:
            new_file_name = (
                f"downloads/{str(cb.from_user.id)}/[@BoB_Files1]_merged.mkv"
            )
            if user.merge_mode == 1:
                await mergeNow(c, cb, new_file_name)
            elif user.merge_mode == 2:
                await mergeAudio(c, cb, new_file_name)
            elif user.merge_mode == 3:
                await mergeSub(c, cb, new_file_name)

    elif cb.data == "cancel":
        await delete_all(root=f"downloads/{cb.from_user.id}/")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("Sᴜᴄᴇssғᴜʟʟʏ Cᴀɴᴄᴇʟʟᴇᴅ")
        await asyncio.sleep(5)
        await cb.message.delete(True)
        return      
        
        
    elif cb.data.startswith("gUPcancel"):
        cmf = cb.data.split("/")
        chat_id, mes_id, from_usr = cmf[1], cmf[2], cmf[3]
        if int(cb.from_user.id) == int(from_usr):
            await c.answer_callback_query(
                cb.id, text="Gᴏɪɴɢ Tᴏ Cᴀɴᴄᴇʟ . . . 🛠", show_alert=False
            )
            gDict[int(chat_id)].append(int(mes_id))
        else:
            await c.answer_callback_query(
                callback_query_id=cb.id,
                text="⚠️ Oᴘᴘs ⚠️ \n I Gᴏᴛ A Fᴀʟsᴇ Vɪsɪᴛᴏʀ 🚸 !! \n\n 📛 Sᴛᴀʏ Aᴛ Yᴏᴜʀ Lɪᴍɪᴛs !!📛",
                show_alert=True,
                cache_time=0,
            )
        await delete_all(root=f"downloads/{cb.from_user.id}/")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    elif cb.data == "close":
        await cb.message.delete(True)
        try:
            await cb.message.reply_to_message.delete(True)
        except Exception as err:
            pass

    elif cb.data.startswith("showFileName_"):
        message_id = int(cb.data.rsplit("_", 1)[-1])
        LOGGER.info(queueDB.get(cb.from_user.id)["videos"])
        LOGGER.info(queueDB.get(cb.from_user.id)["subtitles"])
        sIndex = queueDB.get(cb.from_user.id)["videos"].index(message_id)
        m = await c.get_messages(chat_id=cb.message.chat.id, message_ids=message_id)
        if queueDB.get(cb.from_user.id)["subtitles"][sIndex] is None:
            try:
                await cb.message.edit(
                    text=f"File Name: {m.video.file_name}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ",
                                    callback_data=f"removeFile_{str(m.id)}",
                                ),
                                InlineKeyboardButton(
                                    "📜 Aᴅᴅ sᴜʙᴛɪᴛʟᴇ",
                                    callback_data=f"addSub_{str(sIndex)}",
                                ),
                            ],
                            [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back")],
                        ]
                    ),
                )
            except Exception:
                await cb.message.edit(
                    text=f"File Name: {m.document.file_name}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ",
                                    callback_data=f"removeFile_{str(m.id)}",
                                ),
                                InlineKeyboardButton(
                                    "📜 Aᴅᴅ sᴜʙᴛɪᴛʟᴇ",
                                    callback_data=f"addSub_{str(sIndex)}",
                                ),
                            ],
                            [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back")],
                        ]
                    ),
                )
            return
        else:
            sMessId = queueDB.get(cb.from_user.id)["subtitles"][sIndex]
            s = await c.get_messages(chat_id=cb.message.chat.id, message_ids=sMessId)
            try:
                await cb.message.edit(
                    text=f"File Name: {m.video.file_name}\n\nSubtitles: {s.document.file_name}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ Fɪʟᴇ",
                                    callback_data=f"removeFile_{str(m.id)}",
                                ),
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ Sᴜʙᴛɪᴛʟᴇ",
                                    callback_data=f"removeSub_{str(sIndex)}",
                                ),
                            ],
                            [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back")],
                        ]
                    ),
                )
            except Exception:
                await cb.message.edit(
                    text=f"File Name: {m.document.file_name}\n\nSubtitles: {s.document.file_name}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ Fɪʟᴇ",
                                    callback_data=f"removeFile_{str(m.id)}",
                                ),
                                InlineKeyboardButton(
                                    "❌ Rᴇᴍᴏᴠᴇ Sᴜʙᴛɪᴛʟᴇ",
                                    callback_data=f"removeSub_{str(sIndex)}",
                                ),
                            ],
                            [InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="back")],
                        ]
                    ),
                )
            return

    elif cb.data.startswith("addSub_"):
        sIndex = int(cb.data.split(sep="_")[1])
        vMessId = queueDB.get(cb.from_user.id)["videos"][sIndex]
        rmess = await cb.message.edit(
            text=f"Sᴇɴᴅ Mᴇ A Sᴜʙᴛɪᴛʟᴇ Fɪʟᴇ, Yᴏᴜ Hᴀᴠᴇ 60 Sᴇᴄᴏɴᴅ",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Bᴀᴄᴋ", callback_data=f"showFileName_{vMessId}"
                        )
                    ]
                ]
            ),
        )
        subs: Message = await c.listen(
            chat_id=cb.message.chat.id, filters=filters.document, listener_type=ListenerTypes.MESSAGE, timeout=120, user_id=cb.from_user.id
        )
        if subs is not None:
            media = subs.document or subs.video
            if media.file_name.rsplit(".")[-1] not in "srt":
                await subs.reply_text(
                    text=f"Pʟᴇᴀsᴇ Gᴏ Bᴀᴄᴋ Fɪʀsᴛ",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🔙 Bᴀᴄᴋ", callback_data=f"showFileName_{vMessId}"
                                )
                            ]
                        ]
                    ),
                    quote=True,
                )
                return
            queueDB.get(cb.from_user.id)["subtitles"][sIndex] = subs.id
            await subs.reply_text(
                f"Added {subs.document.file_name}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Bᴀᴄᴋ", callback_data=f"showFileName_{vMessId}"
                            )
                        ]
                    ]
                ),
                quote=True,
            )
            await rmess.delete(True)
            LOGGER.info("Aᴅᴅᴇᴅ Sᴜʙ Tᴏ Lɪsᴛ")
        return

    elif cb.data.startswith("removeSub_"):
        sIndex = int(cb.data.rsplit("_")[-1])
        vMessId = queueDB.get(cb.from_user.id)["videos"][sIndex]
        queueDB.get(cb.from_user.id)["subtitles"][sIndex] = None
        await cb.message.edit(
            text=f"Sᴜʙᴛɪᴛʟᴇ Rᴇᴍᴏᴠᴇᴅ Nᴏᴡ Gᴏ Bᴀᴄᴋ Oʀ Sᴇɴᴅ Nᴇxᴛ Vɪᴅᴇᴏ",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Bᴀᴄᴋ", callback_data=f"showFileName_{vMessId}"
                        )
                    ]
                ]
            ),
        )
        LOGGER.info("Sᴜʙ Rᴇᴍᴏᴠᴇᴅ Fʀᴏᴍ Lɪsᴛ")
        return

    elif cb.data == "back":
        await showQueue(c, cb)
        return

    elif cb.data.startswith("removeFile_"):
        sIndex = queueDB.get(cb.from_user.id)["videos"].index(
            int(cb.data.split("_", 1)[-1])
        )
        queueDB.get(cb.from_user.id)["videos"].remove(int(cb.data.split("_", 1)[-1]))
        await showQueue(c, cb)
        return

    elif cb.data.startswith("ch@ng3M0de_"):
        uid = cb.data.split("_")[1]
        user = UserSettings(int(uid), cb.from_user.first_name)
        mode = int(cb.data.split("_")[2])
        user.merge_mode = mode
        user.set()
        await userSettings(
            cb.message, int(uid), cb.from_user.first_name, cb.from_user.last_name, user
        )
        return

    elif cb.data == "tryotherbutton":
        await cb.answer(text="Tʀʏ Oᴛʜᴇʀ Bᴜᴛᴛᴏɴ → ☛")
        return

    elif cb.data.startswith("toggleEdit_"):
        uid = int(cb.data.split("_")[1])
        user = UserSettings(uid, cb.from_user.first_name)
        user.edit_metadata = False if user.edit_metadata else True
        user.set()
        await userSettings(
            cb.message, uid, cb.from_user.first_name, cb.from_user.last_name, user
        )
        return
    
    elif cb.data.startswith('extract'):
        edata = cb.data.split('_')[1]
        media_mid = int(cb.data.split('_')[2])
        try:
            if edata == 'audio':
                LOGGER.info('audio')
                await streamsExtractor(c,cb,media_mid,exAudios=True)
            elif edata == 'subtitle':
                await streamsExtractor(c,cb,media_mid,exSubs=True)
            elif edata == 'all':
                await streamsExtractor(c,cb,media_mid,exAudios=True,exSubs=True)
        except Exception as e:
            LOGGER.error(e)
