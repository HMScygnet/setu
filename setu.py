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
from .setu_number import SetuNumber
from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import MessageSegment

db_path = "./setu.db"
sm = SetuNumber()
DB_PATH = os.path.expanduser("~/.hoshino/setu.db")
SETU_DAILY_LIMIT = 30
RESET_HOUR = 0
TIME = 60
_flmt = FreqLimiter(30)
PIC_SHOW_TIME = 40
sv = Service('setu', manage_priv=priv.SUPERUSER, enable_on_default=True, visible=False)
setu_folder = R.img('setu/').path
examine_group = '' #审核色图群

def time_now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute("INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return


db = RecordDAO(DB_PATH)

class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < self.max)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.clear_key(key)

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

daily_setu_limiter = DailyAmountLimiter("dance", SETU_DAILY_LIMIT, RESET_HOUR)

@sv.on_prefix('色图初始化')
async def setu_new(bot,ev):
    file = setu_folder
    ID = 1623549785
    for root, dirs, files in os.walk(file):
        # 遍历文件
        for f in files:
            try:
                url = os.path.basename(os.path.join(root, f))
                sm.add_setu(ID,url)
                ID = ID + 1
            except Exception as e:
                await bot.send(ev,f'添加失败,{e}')
    await bot.send(ev,'初始化完成')


@sv.on_prefix(['本地涩图','本地色图','涩图','色图'])
async def setu(bot, ev):
    arg = ev.message.extract_plain_text().split()
    msg_list = []
    result_list = []
    if arg:
        num = int(arg[0])
    else:
        num = 1
    i = 0
    max_num = 3
    uid = ev['user_id']
    gid = ev['group_id']
    guid = gid,uid
    if not daily_setu_limiter.check(guid):
        await bot.send(ev, f'今天已经冲了{SETU_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)
        return

    if not _flmt.check(uid):
        sec = int(_flmt.left_time(uid))
        await bot.send (ev, f'您冲得太快了，{sec}秒后再来吧', at_sender=True)
        return
    _flmt.start_cd(uid)
    if num > max_num:
        await bot.send(ev, f'太贪心辣,一次只能要{max_num}份涩图哦~')
        num = max_num
    for _ in range(num):
        pic = sm.get_setu()
        id = pic[0]
        url = os.path.join(setu_folder,pic[1])
        msg = f'编号:{id}' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))
        msg_list.append(msg)
    result_list = await send_msg(msg_list, ev)
    '''
    await bot.send(ev,f'涩图将在{TIME}秒后撤回')
    await asyncio.sleep(TIME)
    for result in result_list:
        try:
            await bot.delete_msg(self_id=ev['self_id'], message_id=result['message_id'])
        except:
            traceback.print_exc()
            hoshino.logger.error('[ERROR]撤回失败')
            await asyncio.sleep(1)
    '''
@sv.on_rex(r'不够[涩瑟色]|[涩瑟色]图|来一?[点份张].*[涩瑟色]|再来[点份张]|看过了')
async def setu_res(bot, ev):
    msg_list = []
    result_list = []
    uid = ev['user_id']
    gid = ev['group_id']
    guid = gid,uid
    if not daily_setu_limiter.check(guid):
        await bot.send(ev, f'今天已经冲了{SETU_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)
        return

    if not _flmt.check(uid):
        sec = int(_flmt.left_time(uid))
        await bot.send (ev, f'您冲得太快了，{sec}秒后再来吧', at_sender=True)
        return
    _flmt.start_cd(uid)
    pic = sm.get_setu()
    id = pic[0]
    url = os.path.join(setu_folder,pic[1])
    msg = f'编号:{id}\n' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))
    msg_list.append(msg)
    result_list = await send_msg(msg_list, ev)
    '''
    await bot.send(ev,f'涩图将在{TIME}秒后撤回')
    await asyncio.sleep(TIME)
    for result in result_list:
        try:
            await bot.delete_msg(self_id=ev['self_id'], message_id=result['message_id'])
        except:
            traceback.print_exc()
            hoshino.logger.error('[ERROR]撤回失败')
            await asyncio.sleep(1)
    '''

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
        
        # await nontbot.get_bot().send_private_msg(user_id=coffee, message=(f'\nQ{uid}@群{ev.group_id}\n请求删除:{id}' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))))
        await nonebot.get_bot().send_group_msg(group_id=examine_group,message=(f'\nQ{uid}@群{ev.group_id}\n请求删除:{id}' + str(MessageSegment.image(f'file:///{os.path.abspath(url)}'))))
        await bot.send(ev, '您的请求已发送至管理员')
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