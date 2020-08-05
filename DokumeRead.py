import requests
import time
import sys
from bs4 import BeautifulSoup
import sqlite3
from DokumeBookinfo import Dokume_Bookinfo

login_data = {'utf8':'✓'} # ログインデータ用の辞書型

last_book = {} # 既にDBに入っている本のIDと読んだ回数記録用の辞書型
bookids = {} # 本のIDと読んだ回数の記録用の辞書型
update_id = [] # 更新する本のID
BOOKS_IN_PAGE = 20     # 1ページあたりの冊数

dbpath = 'Bookmeter.db'

# データベース作成用関数
def database_create(con):
    try:
        # テーブルの作成
        c.execute("CREATE TABLE IF NOT EXISTS bookinfo (id TEXT PRIMARY KEY, title TEXT, auther TEXT, read_number INTERGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS read_data (id TEXT, date INTEGER, note TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS bookcase (id TEXT PRIMARY KEY, case1 TEXT DEFAULT '', case2 TEXT DEFAULT '', case3 TEXT DEFAULT '', case4 TEXT DEFAULT '', case5 TEXT DEFAULT '', case6 TEXT DEFAULT '', case7 TEXT DEFAULT '', case8 TEXT DEFAULT '', case9 TEXT DEFAULT '', case10 TEXT DEFAULT '')")
    except sqlite3.Error as e:
        print('Database error')

# 読書メーターログイン用関数
def dokume_login(s):
    url = 'https://bookmeter.com/login'  # ログインURL
    res = s.get(url)  # res取得

    # Tokenの取得とlogin_dataへの格納
    soup = BeautifulSoup(res.text,'html.parser')   
    token = soup.find("input",{"name":"authenticity_token"})['value']
    login_data['authenticity_token'] = token

    # ログイン
    login = s.post(url,data=login_data)

# 読んだ本のIDと読んだ回数を取得する関数
def get_read_bookids(s,bookids):
    
    i = 0 # カウンタの初期化
    n = 1 # 読んだ本の冊数

    # Whileループを作る
    while n > BOOKS_IN_PAGE * i:
        # 読んだ本リストのページへのリンク作成
        url = 'https://bookmeter.com/users/' + userinfo[0] + '/books/read?page={}'.format(i+1)

        # htmlの取得
        res = s.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 初回のみ読んだ本の総冊数を取得
        if i < 1:
            booknumber = soup.select_one(".title__content .content__count")
            n = int(booknumber.string)

        # 各本のリンクを取得
        books = soup.select(".detail__title a")

        for book in books:
            # リンクから余計な文字を削除してidを抽出
            book_id = book.get('href')
            book_id = book_id.replace("/books/","")

            # 当該idの読んだ回数を更新
            if not book_id in bookids:
                bookids[book_id] = 1
            else:
                bookids[book_id] = bookids[book_id] + 1

        i = i + 1  # カウンタの更新
        print(bookids)
        time.sleep(10) # 10秒ホールド

        #テスト用
        # if i == 3:
        #    break


# データベースへ接続、カーソル生成
connection = sqlite3.connect(dbpath)
c = connection.cursor()
c2 = connection.cursor()

# データベース作成
database_create(c)

# DB内のidと読んだ回数をそれぞれkeyと値としてlast_bookに代入
for book_id in c.execute("SELECT id FROM bookinfo"):
    for last_read in c2.execute("SELECT read_number FROM bookinfo WHERE id = ?",book_id):
       last_book[book_id[0]] = last_read[0]

# ユーザーIdとログイン情報をファイルから取得
with open("MyID") as f:
    userinfo = f.read().splitlines()

# ログインデータを追加
login_data['session[email_address]'] = userinfo[1]
login_data['session[password]'] = userinfo[2]

# ログインセッションの作成とログイン
session = requests.Session()
dokume_login(session)

# 読んだ本のidと読んだ回数を取得
get_read_bookids(session,bookids)

# 更新する本のidを取得
for k in bookids:
    # DB上にないidは更新する
    if not k in last_book:
        update_id.append(k)
    # DBより読んだ回数が多い場合も更新する
    elif bookids[k] > last_book[k]:
        update_id.append(k)

for bookid in update_id:
    # 各本のページに飛ぶ
    url = 'https://bookmeter.com/books/'+ bookid
    res = session.get(url) 
    soup = BeautifulSoup(res.text, 'html.parser')

    # インスタンス作成
    dokume_book = Dokume_Bookinfo(soup)

    # htmlからのデータの入手
    # 本のタイトル,著者,読んだ回数,本棚の情報取得
    try:
        dokume_book.get_bookinfo()
        dokume_book.get_bookcases()
        dokume_book.get_read_record()

    # ログイン情報が消えている場合は再ログイン
    except IndexError:
        session = requests.Session()
        dokume_login(session)
        time.sleep(10)
        res = session.get(url) 
        soup = BeautifulSoup(res.text, 'html.parser')
        dokume_book.update_soup(soup)

        dokume_book.get_bookinfo()
        dokume_book.get_bookcases()
        dokume_book.get_read_record()

    print(bookid)
    print(dokume_book.booktitle)
    print(dokume_book.bookauthor)
    print(dokume_book.dates)
    print(dokume_book.notes)

    # Bookcasesの10個の要素になるように不足分を空白で埋める
    dokume_book.fill_bookcase()

    # 各種テーブルにデータを挿入
    db_bookinfo = "INSERT INTO bookinfo VALUES (?,?,?,?)"
    c.execute(db_bookinfo,(bookid,dokume_book.booktitle,dokume_book.bookauthor,dokume_book.read_number))

    for i in range(dokume_book.read_number):
        db_read_data = "INSERT INTO read_data VALUES (?,?,?)"
        c.execute(db_read_data,(bookid,dokume_book.dates[i],dokume_book.notes[i]))

    db_bookcase = "INSERT INTO bookcase VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    c.execute(db_bookcase,(bookid,dokume_book.bookcases[0],dokume_book.bookcases[1],dokume_book.bookcases[2],dokume_book.bookcases[3],dokume_book.bookcases[4],dokume_book.bookcases[5],dokume_book.bookcases[6],dokume_book.bookcases[7],dokume_book.bookcases[8],dokume_book.bookcases[9]))

    # データベースへの保存
    connection.commit()
    time.sleep(10) # 10秒ホールド

# DBのクローズ
connection.close()
