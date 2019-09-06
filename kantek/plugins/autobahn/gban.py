"""Plugin to handle global bans"""
import asyncio
import datetime
import logging
from typing import Dict

from telethon import events
from telethon.events import NewMessage
from telethon.tl.custom import Message
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import Channel, InputReportReasonSpam, ChatBannedRights

from config import cmd_prefix
from utils import helpers
from utils.client import KantekClient
from utils.mdtex import MDTeXDocument, Section, KeyValueItem, Bold, Code

__version__ = '0.3.1'

tlog = logging.getLogger('kantek-channel-log')

DEFAULT_REASON = 'spam[gban]'


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}gban'))
async def gban(event: NewMessage.Event) -> None:
    """Command to globally ban a user."""

    chat: Channel = await event.get_chat()
    msg: Message = event.message
    client: KantekClient = event.client
    keyword_args, args = await helpers.get_args(event)
    fban = keyword_args.get('fban', True)
    chat_document = client.db.groups.get_chat(event.chat_id)
    db_named_tags: Dict = chat_document['named_tags']
    gban = db_named_tags.get('gban')
    verbose = False
    if gban == 'verbose' or event.is_private:
        verbose = True
    await msg.delete()
    if msg.is_reply:

        bancmd = db_named_tags.get('gbancmd')
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        if args:
            ban_reason = args[0]
        else:
            ban_reason = DEFAULT_REASON
        await client.gban(uid, ban_reason, fedban=fban)
        await client(ReportRequest(chat, [reply_msg.id], InputReportReasonSpam()))
        if chat.creator or chat.admin_rights:
            if bancmd == 'manual' or bancmd is None:
                await client(EditBannedRequest(
                    chat, uid, ChatBannedRights(
                        until_date=datetime.datetime(2038, 1, 1),
                        view_messages=True
                    )
                ))
            elif bancmd is not None:
                await reply_msg.reply(f'{bancmd} {ban_reason}')
                await asyncio.sleep(0.5)
            await reply_msg.delete()
    else:
        uids = []
        ban_reason = keyword_args.get('reason', DEFAULT_REASON)
        for arg in args:
            if isinstance(arg, int):
                uids.append(arg)
            else:
                ban_reason = arg
        for uid in uids:
            await client.gban(uid, ban_reason, fedban=fban)
            # sleep to avoid flooding the bots too much
            await asyncio.sleep(0.5)
        if verbose:
            await client.respond(event, MDTeXDocument(
                Section(Bold('GBanned Users'),
                        KeyValueItem(Bold('Reason'), ban_reason),
                        KeyValueItem(Bold('IDs'), Code(', '.join([str(uid) for uid in uids]))))))


@events.register(events.NewMessage(outgoing=True, pattern=f'{cmd_prefix}ungban'))
async def ungban(event: NewMessage.Event) -> None:
    """Command to globally unban a user."""
    msg: Message = event.message
    client: KantekClient = event.client
    keyword_args, args = await helpers.get_args(event)
    fban = keyword_args.get('fban', True)
    await msg.delete()
    if msg.is_reply:
        reply_msg: Message = await msg.get_reply_message()
        uid = reply_msg.from_id
        await client.ungban(uid, fedban=fban)
    else:
        for uid in args:
            await client.ungban(uid, fedban=fban)
