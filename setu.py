import os
import random
import asyncio
from nonebot.exceptions import CQHttpError
from datetime import datetime, timedelta
import sqlite3
import time
import hoshino
import traceback
import nonebot
import re
import hashlib
from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import MessageSegment

db_path = os.path.join(os.path.dirname(__file__), 'setu.db')
_flmt = FreqLimiter(30)        #涩图冷却时间
PIC_SHOW_TIME = 40             #涩图撤回时间

sv = Service('setu', manage_priv=priv.SUPERUSER, enable_on_default=True, visible=False)
setu_folder = R.img('setu/').path

class SetuNumber:
    def __init__(self):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.create_table()

    def _connect(self):
        return sqlite3.connect(db_path)

    def create_table(self):
        try:
            c = self._connect()
            c.execute('''CREATE TABLE IF NOT EXISTS SETU
            (ID      integer NOT NULL PRIMARY KEY AUTOINCREMENT,
             URL     TEXT    NOT NULL);''')
            c.commit()
            c.close()
        except:
            raise Exception('创建表发生错误')
    
    def add_setu(self,URL):
        try:
            c = self._connect()
            c.execute("INSERT INTO SETU (ID,URL) \
            VALUES (NULL,?)",(URL,))
            c.commit()
            c.close()  
        except:
            raise Exception('更新表发生错误')

    def get_setu_url(self,ID):
        try:
            c = self._connect()
            r = c.execute("SELECT URL FROM SETU WHERE ID=?",(ID,)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')

    def get_setu_id(self,URL):
        try:
            c = self._connect()
            r = c.execute("SELECT ID FROM SETU WHERE URL=?",(URL,)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')

    def delete_setu(self,ID):
        try:
            c = self._connect()
            c.execute("DELETE from SETU where ID=?;",(ID,))
            c.commit()
            c.close()
        except:
            raise Exception('删除表发生错误')
sm = SetuNumber()

def setu_gener():
    while True:
        filelist = os.listdir(setu_folder)
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, filename)):
                yield R.img('setu/', filename)

setu_gener = setu_gener()

def get_setu():
    return setu_gener.__next__()

async def send_msg(msg_list,ev):
    result_list = []
    for msg in msg_list:
        try:
            result_list.append(await hoshino.get_bot().send(ev, msg))
        except:
            hoshino.logger.error('[ERROR]图片发送失败')
            await hoshino.get_bot().send(ev, f'涩图太涩,发不出去力...')
        await asyncio.sleep(1)
    return result_list


@sv.on_prefix(['本地涩图','本地色图','涩图','色图'])
async def setu(bot, ev):
    arg = ev.message.extract_plain_text().split()
    msg_list = []
    result_list = []
    if arg:
        num = int(arg[0])
    else:
        num = 1
    max_num = 3
    uid = ev['user_id']
    gid = ev['group_id']

    if not _flmt.check(uid):
        sec = int(_flmt.left_time(uid))
        await bot.send (ev, f'您冲得太快了，{sec}秒后再来吧', at_sender=True)
        return
    _flmt.start_cd(uid)
    if num > max_num:
        await bot.send(ev, f'太贪心辣,一次只能要{max_num}份涩图哦~')
        num = max_num
    for _ in range(num):
        pic = get_setu()
        name = os.path.basename(pic.path)
        id = sm.get_setu_id(name)
        msg = f'编号:{id}{pic.cqcode}'
        msg_list.append(msg)
    await send_msg(msg_list, ev)
    await bot.send(ev,'如果有不色的图可以用"删除涩图+编号"指令删除,无需加号')
'''
    result_list = await send_msg(msg_list, ev)
    await bot.send(ev,f'涩图将在{PIC_SHOW_TIME}秒后撤回')
    await asyncio.sleep(PIC_SHOW_TIME)
    for result in result_list:
        try:
            await bot.delete_msg(self_id=ev['self_id'], message_id=result['message_id'])
        except:
            traceback.print_exc()
            hoshino.logger.error('[ERROR]撤回失败')
            await asyncio.sleep(1)
'''

@sv.on_rex(r'[涩瑟色]图|来一?[点份张].*[涩瑟色]|再来[点份张]|看过了')
async def setu_res(bot, ev):
    msg_list = []
    result_list = []
    uid = ev['user_id']
    gid = ev['group_id']
    guid = gid,uid

    if not _flmt.check(uid):
        sec = int(_flmt.left_time(uid))
        await bot.send (ev, f'您冲得太快了，{sec}秒后再来吧', at_sender=True)
        return
    _flmt.start_cd(uid)
    pic = get_setu()
    name = os.path.basename(pic.path)
    id = sm.get_setu_id(name)
    msg = f'编号:{id}{pic.cqcode}'
    msg_list.append(msg)
    await send_msg(msg_list, ev)
    await bot.send(ev,'如果有不色的图可以用"删除涩图+编号"指令删除,无需加号')
''' 
    result_list = await send_msg(msg_list, ev)
    await bot.send(ev,f'涩图将在{PIC_SHOW_TIME}秒后撤回')
    await asyncio.sleep(PIC_SHOW_TIME)
    for result in result_list:
        try:
            await bot.delete_msg(self_id=ev['self_id'], message_id=result['message_id'])
        except:
            traceback.print_exc()
            hoshino.logger.error('[ERROR]撤回失败')
            await asyncio.sleep(1)
    '''
@sv.on_fullmatch(('不够色','不色','一点都不色'))
async def setu_re(bot,ev):
    await bot.send(ev,'那你发')

@sv.on_prefix(('发图','查图','看图'))
async def setu_send(bot,ev):
    arg = ev.message.extract_plain_text().split()
    if not arg:
        await bot.send(ev,'请输入编号')
        return
    id = arg[0]
    name = sm.get_setu_url(id)
    if name == 0:
        await bot.send(ev,'请检查编号是否正确')
        return
    url = os.path.join(setu_folder,name)
    await bot.send(ev,str(MessageSegment.image(f'file:///{os.path.abspath(url)}')))

@sv.on_fullmatch('色图数量')
async def setu_num(bot,ev):
    num = len(os.listdir(setu_folder))
    await bot.send(ev,f'当前有{num}张涩图')

@sv.on_prefix(('删除涩图','删除色图'))
async def setu_delete(bot, ev):
    uid = ev.user_id
    coffee = hoshino.config.SUPERUSERS[0]
    arg = ev.message.extract_plain_text().split()
    if arg:
        id = int(arg[0])
        if sm.get_setu_url(id) == 0:
            await bot.send(ev,'请检查编号是否正确')
            return
        url = os.path.join(setu_folder,sm.get_setu_url(id))
        
        # await bot.send_private_msg(self_id=ev.self_id, user_id=coffee, message=(f'\nQ{uid}@群{ev.group_id}\n请求删除:{id}' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))))
        await nonebot.get_bot().send_group_msg(group_id='1153753282',message=(f'Q{uid}@群{ev.group_id}\n请求删除:{id}\n{url}' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))))
        await bot.send(ev, '您的请求已发送至管理员,感谢您为涩图库做出的贡献')
    else:
        await bot.send(ev,'请输入要删除的涩图编号')
        return
    if priv.check_priv(ev, priv.SUPERUSER):
        try:
            url = os.path.join(setu_folder,sm.get_setu_url(id))
            os.remove(url)
            sm.delete_setu(id)
            await bot.send(ev,'删除成功')
            return
        except Exception as e:
            await bot.send(ev,f'删除失败,{e}')
            return

@sv.on_prefix('删除编号')
async def setu_num_delete(bot,ev):
    if priv.check_priv(ev, priv.SUPERUSER):
        arg = ev.message.extract_plain_text().split()
        id = arg[0]
        try:
            sm.delete_setu(id)
            await bot.send(ev,'删除成功')
        except Exception as e:
            await bot.send(ev,f'删除失败{e}')
            return