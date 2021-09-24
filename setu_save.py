from asyncio.events import set_child_watcher
from logging import exception
import re
import os, shutil
from time import time
from nonebot import *

from asyncio import sleep
from datetime import datetime,timedelta

from nonebot import get_bot
from .setu import SetuNumber
from hoshino import R, Service, priv
from hoshino.typing import CQEvent

sm = SetuNumber()
SEARCH_TIMEOUT = 300 #连续对话等待时间
setu_folder = R.img('setu/').path
obot = get_bot()
sv = Service('setu_save')
head = ''            #你go-cqhttp.exe所在的文件夹,记得最后加斜杠
res = setu_folder

def mymovefile(file):
    srcfile = head + file
    name = os.path.basename(srcfile)
    dstfile = res
    shutil.move(srcfile,dstfile)
    return name         #移动文件




class PicListener:
    def __init__(self):
        self.on = {}
        self.count = {}
        self.timeout = {}

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def turn_on(self, gid, uid):
        self.on[gid] = uid
        self.timeout[gid] = datetime.now()+timedelta(seconds=SEARCH_TIMEOUT)
        self.count[gid] = 0

    def turn_off(self, gid):
        self.on[gid] = None
        self.count[gid] = None
        self.timeout[gid] = None

    def count_plus(self, gid):
        self.count[gid] += 1



pls=PicListener()


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
        file_url = mymovefile(file_road)
        sm.add_setu(file_url)
        id = sm.get_setu_id(file_url)
        await bot.send(ev, f'图片已保存,编号为{id}')
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
        file_url = mymovefile(file_road)
        sm.add_setu(file_url)
        id = sm.get_setu_id(file_url)
        await bot.send(ev, f'图片已保存,编号为{id}')
    except:
        await bot.send(ev, '图片保存失败')

@sv.on_prefix('退出存图')
async def thanks(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '您没有权限')
        return
    pls.turn_off(ev.group_id)
    await bot.send(ev, '已退出')
    return