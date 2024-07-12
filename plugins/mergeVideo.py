import asyncio
import os
import time

from bot import (LOGGER, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, delete_all, formatDB,
                 gDict, queueDB)
from config import Config
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helpers.display_progress import Progress
from helpers.ffmpeg_helper import MergeSub, MergeVideo, take_screen_shot
from helpers.rclone_upload import rclone_driver, rclone_upload
from helpers.uploader import uploadVideo
from helpers.utils import UserSettings
from PIL import Image
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


async def mergeNow(c: Client, cb: CallbackQuery, new_file_name: str):
    omess = cb.message.reply_to_message
    # LOGGER.info(omess.id)
    vid_list = list()
    sub_list = list()
    sIndex = 0
    await cb.message.edit("⭕ Pʀᴏᴄᴇssɪɴɢ...")
    duration = 0
    list_message_ids = queueDB.get(cb.from_user.id)["videos"]
    list_message_ids.sort()
    list_subtitle_ids = queueDB.get(cb.from_user.id)["subtitles"]
    # list_subtitle_ids.sort()
    LOGGER.info(Config.IS_PREMIUM)
    LOGGER.info(f"Videos: {list_message_ids}")
    LOGGER.info(f"Subs: {list_subtitle_ids}")
    if list_message_ids is None:
        await cb.answer("Queue Empty", show_alert=True)
        await cb.message.delete(True)
        return
    if not os.path.exists(f"downloads/{str(cb.from_user.id)}/"):
        os.makedirs(f"downloads/{str(cb.from_user.id)}/")
    input_ = f"downloads/{str(cb.from_user.id)}/input.txt"
    all = len(list_message_ids)
    n=1
    for i in await c.get_messages(
chat_id=cb.from_user.id, message_ids=list_message_ids ):
        media = i.video or i.document
        await cb.message.edit(f"📥 Sᴛᴀʀᴛɪɴɢ Dᴏᴡɴʟᴏᴀᴅ Oғ ... `{media.file_name}`")
        LOGGER.info(f"📥 Sᴛᴀʀᴛɪɴɢ Dᴏᴡɴʟᴏᴀᴅ Oғ ... {media.file_name}")
        await asyncio.sleep(5)
        file_dl_path = None
        sub_dl_path = None
        try:
            c_time = time.time()
            prog = Progress(cb.from_user.id, c, cb.message)
            file_dl_path = await c.download_media(
                message=media,
                file_name=f"downloads/{str(cb.from_user.id)}/{str(i.id)}/vid.mkv",  # fix for filename with single quote(') in name
                progress=prog.progress_for_pyrogram,
                progress_args=(f"🚀 Dᴏᴡɴʟᴏᴀᴅɪɴɢ: `{media.file_name}`", c_time, f"\n**Dᴏᴡɴʟᴏᴀᴅɪɴɢ: {n}/{all}**"),
            )
            n+=1
            if gDict[cb.message.chat.id] and cb.message.id in gDict[cb.message.chat.id]:
                return
            await cb.message.edit(f"Dᴏᴡɴʟᴏᴀᴅᴇᴅ sᴜᴄᴇssғᴜʟʟʏ ✅ ... `{media.file_name}`")
            LOGGER.info(f"Dᴏᴡɴʟᴏᴀᴅᴇᴅ Sᴜᴄᴇssғᴜʟʟʏ ✅ ... {media.file_name}")
            await asyncio.sleep(5)
        except UnknownError as e:
            LOGGER.info(e)
            pass
        except Exception as downloadErr:
            LOGGER.info(f"Fᴀɪʟᴇᴅ Tᴏ Dᴏᴡɴʟᴏᴀᴅ Eʀʀᴏʀ: {downloadErr}")
            queueDB.get(cb.from_user.id)["video"].remove(i.id)
            await cb.message.edit("❗Fɪʟᴇ Sᴋɪᴘᴘᴇᴅ!")
            await asyncio.sleep(4)
            continue

        if list_subtitle_ids[sIndex] is not None:
            a = await c.get_messages(
                chat_id=cb.from_user.id, message_ids=list_subtitle_ids[sIndex]
            )
            sub_dl_path = await c.download_media(
                message=a,
                file_name=f"downloads/{str(cb.from_user.id)}/{str(a.id)}/",
            )
            LOGGER.info("Gᴏᴛ Sᴜʙ: ", a.document.file_name)
            file_dl_path = await MergeSub(file_dl_path, sub_dl_path, cb.from_user.id)
            LOGGER.info("Aᴅᴅᴇᴅ Sᴜʙs")
        sIndex += 1

        metadata = extractMetadata(createParser(file_dl_path))
        try:
            if metadata.has("duration"):
                duration += metadata.get("duration").seconds
            vid_list.append(f"file '{file_dl_path}'")
        except:
            await delete_all(root=f"downloads/{str(cb.from_user.id)}")
            queueDB.update(
                {cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}}
            )
            formatDB.update({cb.from_user.id: None})
            await cb.message.edit("⚠️ Vɪᴅᴇᴏ Is Cᴏʀʀᴜᴘᴛᴇᴅ")
            return

    _cache = list()
    for i in range(len(vid_list)):
        if vid_list[i] not in _cache:
            _cache.append(vid_list[i])
    vid_list = _cache
    LOGGER.info(f"Tʀʏɪɴɢ Tᴏ Mᴇʀɢᴇ Vɪᴅᴇᴏs Usᴇʀ {cb.from_user.id}")
    await cb.message.edit("🔀 Tʀʏɪɴɢ Tᴏ Mᴇʀɢᴇ Vɪᴅᴇᴏs")
    with open(input_, "w") as _list:
        _list.write("\n".join(vid_list))
    merged_video_path = await MergeVideo(
        input_file=input_, user_id=cb.from_user.id, message=cb.message, format_="mkv"
    )
    if merged_video_path is None:
        await cb.message.edit("❌ Failed To Merge Video !")
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    try:
        await cb.message.edit("✅ Sᴜᴄᴇssғᴜʟʟʏ Mᴇʀɢᴇᴅ Vɪᴅᴇᴏ !")
    except MessageNotModified:
        await cb.message.edit("Sᴜᴄᴇssғᴜʟʟʏ Mᴇʀɢᴇᴅ Vɪᴅᴇᴏ ! ✅")
    LOGGER.info(f"Video Merged For: {cb.from_user.first_name} ")
    await asyncio.sleep(3)
    file_size = os.path.getsize(merged_video_path)
    os.rename(merged_video_path, new_file_name)
    await cb.message.edit(
        f"🔄 Rᴇɴᴀᴍᴇᴅ Mᴇʀɢᴇᴅ Vɪᴅᴇᴏ ᴛᴏ\n **{new_file_name.rsplit('/',1)[-1]}**"
    )
    await asyncio.sleep(3)
    merged_video_path = new_file_name
    if UPLOAD_TO_DRIVE[f"{cb.from_user.id}"]:
        await rclone_driver(omess, cb, merged_video_path)
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    if file_size > 2044723200 and Config.IS_PREMIUM == False:
        await cb.message.edit(
            f"Video is Larger than 2GB Can't Upload,\n\n Tell {Config.OWNER_USERNAME} to add premium account to get 4GB TG uploads"
        )
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    if Config.IS_PREMIUM and file_size > 4241280205:
        await cb.message.edit(
            f"Vɪᴅᴇᴏ ɪs ʟᴀʀɢᴇʀ ᴛʜᴀɴ 𝟺ɢʙ ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ,\n\n Tᴇʟʟ {Config.OWNER_USERNAME} ᴛᴏ ᴅɪᴇ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴏᴜɴᴛ"
        )
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    
    
    await cb.message.edit("🎥 Exᴛʀᴀᴄᴛɪɴɢ Vɪᴅᴇᴏ Dᴀᴛᴀ...")
    duration = 1
    try:
        metadata = extractMetadata(createParser(merged_video_path))
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as er:
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("⭕ Mᴇʀɢᴇᴅ Vɪᴅᴇᴏ Is Cᴏʀʀᴜᴘᴛᴇᴅ")
        return
    
    try:
        user = UserSettings(cb.from_user.id, cb.from_user.first_name)
        thumb_id = user.thumbnail
        if thumb_id is None:
            raise Exception
        video_thumbnail = f"downloads/{str(cb.from_user.id)}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=video_thumbnail)
    except Exception as err:
        LOGGER.info("Gᴇɴᴇʀᴀᴛɪɴɢ ᴛʜᴜᴍʙ")
        video_thumbnail = await take_screen_shot(
            merged_video_path, f"downloads/{str(cb.from_user.id)}", (duration / 2)
        )
    
    width = 1280
    height = 720
    try:
        thumb = extractMetadata(createParser(video_thumbnail))
        height = thumb.get("height")
        width = thumb.get("width")
        img = Image.open(video_thumbnail)
        if width > height:
            img.resize((320, height))
        elif height > width:
            img.resize((width, 320))
        img.save(video_thumbnail)
        Image.open(video_thumbnail).convert("RGB").save(video_thumbnail, "JPEG")
    except:
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("⭕ Mᴇʀɢᴇᴅ Vɪᴅᴇᴏ Is Cᴏʀʀᴜᴘᴛᴇᴅ")
        return
    
    await uploadVideo(
        c=c,
        cb=cb,
        merged_video_path=merged_video_path,
        width=width,
        height=height,
        duration=duration,
        video_thumbnail=video_thumbnail,
        file_size=os.path.getsize(merged_video_path),
        upload_mode=UPLOAD_AS_DOC[f"{cb.from_user.id}"],
    )
    
    await cb.message.delete(True)
    await delete_all(root=f"downloads/{str(cb.from_user.id)}")
    queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
    formatDB.update({cb.from_user.id: None})
    return



