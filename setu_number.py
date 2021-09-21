import sqlite3
import os

db_path = "./setu.db"


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
            (ID            KEY     NOT NULL,
             URL           BLOB    NOT NULL);''')
        except:
            raise Exception('创建表发生错误')
    
    def add_setu(self,ID,URL):
        try:
            c = self._connect()
            c.execute("INSERT INTO SETU (ID,URL) \
            VALUES (?,?)",(ID,URL))
            c.commit()  
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

    def get_setu(self):
        try:
            c = self._connect()
            r = c.execute("SELECT * FROM SETU ORDER BY random() limit 1").fetchone()
            return r
        except:
            raise Exception('查找表发生错误')

    def delete_setu(self,ID):
        try:
            c = self._connect()
            c.execute("DELETE from SETU where ID=?;",(ID,))
            c.commit()
        except:
            raise Exception('删除表发生错误')