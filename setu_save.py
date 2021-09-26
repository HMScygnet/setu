import re
import os, shutil

from asyncio import sleep
from datetime import datetime,timedelta
from nonebot import get_bot
from .module import SetuNumber, PicListener, porn_pic_index
from hoshino import Service, priv, R
from hoshino.typing import CQEvent

sm = SetuNumber()
pls=PicListener()

SEARCH_TIMEOUT = 300
obot = get_bot()
sv = Service('setu_save')
head = '' #
res = R.img('setu/').path

def mymovefile(file):
    srcfile = head + file
    name = os.path.basename(srcfile)
    dstfile = res
    shutil.move(srcfile,dstfile)
    return name         #移动文件

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

@sv.on_prefix('存图')
async def start_finder(bot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    ret = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '只有超级管理员才能存图哦')
        return
    if not ret:
        if pls.get_on_off_status(gid):
            if uid == pls.on[gid]:
                await bot.finish(ev, f"您已经在存图模式下啦！\n如想退出搜图模式请发送“退出存图”~")
        pls.turn_on(gid, uid)
        await bot.send(ev, f"了解～请发送图片吧！\n如想退出存图模式请发送“退出存图”")
        await sleep(SEARCH_TIMEOUT)
        ct = 0
        while pls.get_on_off_status(gid):
            if datetime.now() < pls.timeout[gid] and ct<10:
                await sleep(SEARCH_TIMEOUT)
                if ct != pls.count[gid]:
                    ct = pls.count[gid]
                    pls.timeout[gid] = datetime.now()+timedelta(seconds=SEARCH_TIMEOUT)
            else:
                await bot.send(ev, f"由于超时，已为您自动退出存图模式")
                pls.turn_off(ev.group_id)
                return
    url = ret.group(1)
    try:
        img = await obot.get_image(file = url)
        file_road = img['file']
        file_name = mymovefile(file_road)
        porn = porn_pic_index(file_name)
        if porn['code'] == 0:
            score = porn['value']
            sm.add_setu(file_name,score)
        else:
            msg = porn['msg']
            await bot.send(ev, f'获取分数失败,{msg}')
            return
        id = sm.get_setu_id(file_name)
        await bot.send(ev, f'图片已保存,编号为{id},色图评分:{score}')
    except:
        await bot.send(ev, '图片保存失败')

@sv.on_message('group')
async def picmessage(bot, ev: CQEvent):
    mid= ev.message_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        return
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
    
    if pls.get_on_off_status(ev.group_id):
        pls.count_plus(ev.group_id)
    url = ret.group(1)
    try:
        img = await obot.get_image(file = url)
        file_road = img['file']
        porn = porn_pic_index(file_road)
        file_name = mymovefile(file_road)
        if porn['code'] == 0:
            score = porn['value']
            sm.add_setu(file_name,score)
        else:
            msg = porn['msg']
            await bot.send(ev, f'获取积分失败,{msg}')
            return
        id = sm.get_setu_id(file_name)
        await bot.send(ev, f'图片已保存,编号为{id},色图评分:{score}')
    except Exception as e:
        await bot.send(ev, f'图片保存失败{e}')

@sv.on_prefix('退出存图')
async def thanks(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '您没有权限')
        return
    pls.turn_off(ev.group_id)
    await bot.send(ev, '已退出')
    return

#群聊存图容易被屏蔽,私聊存图好一点
@obot.on_message('private')
async def private_setu(ctx):
    uid=int(ctx["sender"]["user_id"])
    sid=int(ctx["self_id"])
    gid = 0
    ret = re.match(r"\[CQ:image,file=(.*?),url=(.*?)\]", str(ctx['message']))
    if not uid == 619275505:
        return
    if not ret:
        return
    url = ret.group(1)
    try:
        img = await obot.get_image(file = url)
        file_road = img['file']
        porn = porn_pic_index(file_road)
        file_name = mymovefile(file_road)
        if porn['code'] == 0:
            score = porn['value']
            sm.add_setu(file_name,score)
        else:
            msg = porn['msg']
            await obot.send_msg(self_id=sid, user_id=uid, group_id=gid, message=f'获取分数失败,{msg}')
            return
        id = sm.get_setu_id(file_name)
        await obot.send_msg(self_id=sid, user_id=uid, group_id=gid, message=f'图片已保存,编号为{id},色图评分:{score}')
    except Exception as e:
        await obot.send_msg(self_id=sid, user_id=uid, group_id=gid, message=f'图片保存失败{e}')
