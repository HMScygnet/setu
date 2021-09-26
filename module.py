import os
import sqlite3
from datetime import datetime,timedelta
from aip import AipContentCensor

SEARCH_TIMEOUT = 60
db_path = os.path.join(os.path.dirname(__file__), 'setu.db')
cache = ''   #你go-cqhttp.exe的位置
#有关色图评分的详见 https://github.com/pcrbot/SetuScore
APP_ID = ''  
API_KEY = ''
SECRET_KEY = ''

client = AipContentCensor(APP_ID, API_KEY, SECRET_KEY)

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
            URL     TEXT    NOT NULL,
            score   integer NOT NULL);''')
            c.commit()
            c.close()
        except:
            raise Exception('创建表发生错误')
    
    def add_setu(self,URL,SCORE):
        try:
            c = self._connect()
            c.execute("INSERT INTO SETU (ID,URL,SCORE) \
            VALUES (NULL,?,?)",(URL,SCORE))
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

    def get_setu_score(self,ID):
        try:
            c = self._connect()
            r = c.execute("SELECT score FROM SETU WHERE ID=?",(ID,)).fetchone()
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

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

def porn_pic_index(img):
    img = os.path.join(cache,img)
    result = client.imageCensorUserDefined(get_file_content(img))
    try:
        if (result):
            r = result
            if "error_code" in r:
                return { 'code': r['error_code'], 'msg': r['error_msg'] }
            else:
                porn = 0
                sexy = 0
                for c in r['data']:
                    #由于百度的图片审核经常给出极低分,所以不合规项置信度*500后为分数
                    if c['type'] == 1 and c['subType'] == 0:
                        porn = int(c['probability'] * 500)
                    elif c['type'] == 1 and c['subType'] == 1:
                        sexy = int(c['probability'] * 500)
                return { 'code': 0, 'msg': 'Success', 'value': max(sexy,porn) }

        else:
            return { 'code': -1, 'msg': 'API Error' }


    except FileNotFoundError:
        return { 'code': -1, 'msg': 'File not found' }