import os
import re

from nonebot import get_bot
from aip import AipContentCensor
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino import R, Service
from hoshino.typing import CQEvent, MessageSegment
from asyncio import sleep
from datetime import datetime,timedelta
from .module import PicListener, porn_pic_index

sv = Service('色图打分')
_max = 10
EXCEED_NOTICE = f'您今天已经打了{_max}次分了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(60)
SEARCH_TIMEOUT = 30
cache = 'C:/bot/chuyin-go' 


pls = PicListener()

@sv.on_prefix('打分')
async def setu_score(bot,ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    if not _nlmt.check(uid):
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, f'您冲的太快了,{round(_flmt.left_time(uid))}秒后再来吧', at_sender=True)
        return
    ret = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    if not ret:
        if pls.get_on_off_status(gid):
            if uid == pls.on[gid]:
                await bot.finish(ev, f"您已经在打分模式下啦！\n如想退出打分模式请发送“退出打分”~")
            else:
                await bot.finish(ev, f"本群[CQ:at,qq={pls.on[gid]}]正在打分，请耐心等待~")
        pls.turn_on(gid, uid)
        await bot.send(ev, f"了解～请发送图片吧！\n如想退出打分模式请发送“退出打分”")
        await sleep(30)
        ct = 0
        while pls.get_on_off_status(gid):
            if datetime.now() < pls.timeout[gid] and ct<10:
                await sleep(30)
                if ct != pls.count[gid]:
                    ct = pls.count[gid]
                    pls.timeout[gid] = datetime.now()+timedelta(seconds=30)
            else:
                await bot.send(ev, f"[CQ:at,qq={pls.on[gid]}] 由于超时，已为您自动退出打分模式，以后要记得说“退出打分”来退出打分模式噢~")
                pls.turn_off(ev.group_id)
                return
    file = ret.group(1)
    #百度api无法直接从腾讯url获取图片,所以要下载到本地后再上传
    img = await get_bot().get_image(file=file)
    img_file = img['file']
    porn = porn_pic_index(img_file)
    if porn['code'] == 0:
        score = porn['value']
    else:
        code = porn['code']
        err = porn['msg']
        await bot.send(ev,f'错误:{code}\n{err}')
        return
    url = os.path.join(cache,img_file)
    await bot.send(ev,str(MessageSegment.image(f'file:///{os.path.abspath(url)}')+f'\n色图评分:{score}'))
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

@sv.on_message('group')
async def picmessage(bot, ev: CQEvent):
    ret = re.search(r"\[CQ:at,qq=(\d*)\]", str(ev.message))
    atcheck = False
    batchcheck = False
    if ret:
        if int(ret.group(1)) == int(ev.self_id):
            atcheck = True
    if pls.get_on_off_status(ev.group_id):
        if int(pls.on[ev.group_id]) == int(ev.user_id):
            batchcheck = True
    if not(batchcheck or atcheck):
        return
    uid = ev.user_id
    
    ret = re.search(r"\[CQ:image,file=(.*)?,url=(.*)\]", str(ev.message))
    if not ret:
        return
    file= ret.group(1)
    img = await get_bot().get_image(file=file)
    img_file = img['file']
    porn = porn_pic_index(img_file)
    if porn['code'] == 0:
        score = porn['value']
    else:
        code = porn['code']
        err = porn['msg']
        await bot.send(ev,f'错误:{code}\n{err}')
        return
    url = os.path.join(cache,img_file)
    await bot.send(ev,str(MessageSegment.image(f'file:///{os.path.abspath(url)}')+f'\n色图评分:{score}'))
    pls.turn_off(ev.group_id)
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

@sv.on_fullmatch('退出打分')
async def thanks(bot, ev: CQEvent):
    if pls.get_on_off_status(ev.group_id):
        if pls.on[ev.group_id]!=ev.user_id:
            await bot.send(ev, '不能替别人退出打分哦～')
            return
        pls.turn_off(ev.group_id)
        await bot.send(ev, '已退出')
        return
    await bot.send(ev, 'にゃ～')
