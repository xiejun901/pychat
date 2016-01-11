#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'xiejun'
import sqlite3
import datetime

class UserInformation(object):

    def __init__(self):
        self.dbConn = sqlite3.connect('userinformation.db')
        self.dbcursor = self.dbConn.cursor()

    def createTable(self):
        self.dbcursor.execute('DROP TABLE IF EXISTS userInfo')
        sql = 'CREATE TABLE IF NOT EXISTS userInfo(' \
              'id INTEGER PRIMARY KEY AUTOINCREMENT,' \
              'username varchar(20) NOT NULL UNIQUE,' \
              'password varchar(20) NOT NULL, ' \
              'signUpTime DATE DEFAULT "2016-01-01 00:00:00", ' \
              'signInTime DATE DEFAULT "2016-01-01 00:00:00",' \
              'onLineTime INTEGER DEFAULT 0' \
              ')'
        self.dbcursor.execute(sql)

    def sign_up_user(self,username, password):
        sql = 'INSERT INTO userInfo(username, password, signUpTime, onLineTime) VALUES (' + '"' + username + '",' + '"' + password +'", datetime(), 0)'
        self.dbcursor.execute(sql)
        self.dbConn.commit()
        return True

    def sign_in_user(self,username, password):
        sql = 'SELECT password FROM userInfo WHERE username = "%s" ' %username
        ans = self.dbcursor.execute(sql).fetchone()
        if ans is None:
            return False
        rightPassWord = ans[0]
        if(password == rightPassWord):
            sqlUpdate = 'UPDATE userInfo SET signInTime = datetime() WHERE username = "%s"' %username
            self.dbcursor.execute(sqlUpdate)
            self.dbConn.commit()
            return True
        else:
            return False

    def update_online_time(self,username):
        sql = 'SELECT signInTime, onLineTime From userInfo WHERE username = "%s" ' %username
        ans = self.dbcursor.execute(sql).fetchone()
        if ans is None:
            return
        signInTIme, onLineTime = ans
        ago = datetime.datetime.strptime(signInTIme, '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.utcnow()
        newOnLineTime = onLineTime + (now -ago).total_seconds()
        sqlUpdate = 'UPDATE userInfo SET onLineTime = %d WHERE username = "%s"' %(int(newOnLineTime), username)
        self.dbcursor.execute(sqlUpdate)
        self.dbConn.commit()

    def get_online_time(self, username):
        sql = 'SELECT onLineTime From userInfo WHERE username = "%s" ' %username
        ans = self.dbcursor.execute(sql).fetchone()
        if ans is None:
            return
        return ans[0]

    def is_exist_user(self, username):
        sql = 'SELECT username From userInfo WHERE  username = "%s" ' %username
        ans = self.dbcursor.execute(sql).fetchall()
        return len(ans) > 0



user_info_db = UserInformation()

def main_test():
    conn = sqlite3.connect("userinformation.db")
    cursor = conn.cursor()
    userInfo = UserInformation()
    userInfo.createTable()
    userInfo.sign_up_user('netease1', '123')
    userInfo.sign_up_user('netease2', '123')
    userInfo.sign_up_user('netease3', '123')
    userInfo.sign_up_user('netease4', '123')
    userInfo.sign_up_user('system', '123')
    # print userInfo.signInUser('xiejun2', 'mima')
    sql = 'SELECT * FROM userInfo'
    ans =  cursor.execute(sql).fetchall()
    print ans

if __name__ == '__main__':
    main_test()
