import os
import re
import sqlite3
import sys
import urllib.parse


def make_pagename(title):
    # page名の設定・小文字化
    pagename = title.lower()

    # dokuwikiのpage名に設定出来ない文字の処理
    pagename = re.sub(r'\(|\)|\「|\」|\（|\）|\〈|\〉|\＜|\＞|\<|\>|\[|\]|\〔|\〕|\［|\］|\─| |\u3000|\/|\／|\~|\~|\～|\〜|\―|\-|\:|\、|\,|\。|\『|\』|\【|\】|\[|\]|\．|\×|\α|\:|\：|\=|\＋|\+', "_",pagename)
    pagename = re.sub(r'\?|\？|\!|\！|\&|\＆|\・|\…|\“|\”|\"|\'|\’',"",pagename)

    # _（アンダーバー）がふたつ以上続いていたらひとつに変換する
    pagename = re.sub(r"\_{2,}","_",pagename)

    # %記号は「パーセント」に変換する
    pagename = re.sub(r'\%|\％',"パーセント",pagename)

    # ページ名の長さを20文字で切る
    pagename = pagename[:20]

    # 最初と最後が_（アンダーバー）ならそれを削除する
    if "_" in pagename[0]:
        pagename = pagename[1:]

    if "_" in pagename[-1]:
        pagename = pagename[:-1]
    
    return pagename

    
def WriteWiki():
    dbpath = 'Bookmeter.db'

    EOD_MARK = "##-----追記はこれより下に書くこと-----"   # wikiのデータベースからの転写エリアのマーク
    temp_datas = []
    bookids_identical = []

    # データベースへ接続、カーソル生成
    connection = sqlite3.connect(dbpath)
    c = connection.cursor()
    c2 = connection.cursor()

    # ファイルパスの作成
    with open("wiki_dir") as f:
        wiki_dir = f.read().replace("\n", "")

    filepath = wiki_dir + "/data/pages/" + urllib.parse.quote("本情報")

    # 本情報フォルダの作成
    try:
        os.mkdir(filepath)
    # dokuwikiフォルダがなければエラーで終了
    except FileNotFoundError:  
        print("dokuwikiフォルダがありません")
        sys.exit()
    # フォルダが既にあればスルー
    except FileExistsError:
        pass

    # 本情報ファイルのオープン
    f = open(filepath + ".txt", mode='w')

    # データベースのチェック
    try:
        c.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="bookinfo"')
        c.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="read_data"')
        c.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="bookcase"')
    except:
        print("Database is not appropriate")

    # 読んだ日の新しい順に本IDを取得
    bookids = c.execute("SELECT id FROM read_data ORDER BY date DESC")

    # 重複を除去
    for bookid_temp in bookids:
        if not bookid_temp in bookids_identical:
            bookids_identical.append(bookid_temp)

    # DBの要素ごとにwikiに保存していくループ
    for bookid in bookids_identical:
        c.execute("SELECT * FROM bookinfo WHERE id = ?;",bookid)
        bookinfo = c.fetchone()

        print(bookinfo)

        # 各要素を変数に格納
        title = bookinfo[1]
        author = bookinfo[2]
        read_number = bookinfo[3]

        pagename = make_pagename(title)

        print(pagename)

        # read_stringの初期化
        read_string = ""
        temp_datas.clear()


        # 既にあるページのEOD(End Of Data)マーク以降を「temp_datas」に保存しておく
        try:
            with open(filepath + "/" + urllib.parse.quote(pagename) + ".txt", mode="r") as f2:
                mark = 0

                for read_string in f2.readlines():
                    # フラグが1ならデータを「temp_datas」に保存する
                    if mark == 1:
                        temp_datas.append(read_string)
                    # EODマークを見つけたらフラグ（mark）に1を立てる
                    if EOD_MARK in read_string:
                        mark = 1
                pass
        # 既にあるページが無い場合はスルー
        except:
            pass

        # テキストファイルに情報を書いていく
        with open(filepath + "/" + urllib.parse.quote(pagename) + ".txt", mode="w") as f2:
            f2.write("# " + title + "\n") 
            f2.write("## 基本情報\n")
            f2.write("著者 " + author + "\n\n")
            f2.write("id =" + bookid[0] + "\n\n")
            f2.write("読んだ回数 {} \n\n".format(read_number))
            f2.write("## 読書記録\n")

            # 読書記録を書く
            for read_data in c2.execute('SELECT * FROM read_data WHERE id = ?;',bookid):
                f2.write("### 読んだ日付: {} \n".format(read_data[1]))
                f2.write("感想: " + read_data[2] + "\n\n")

            f2.write("## 本棚\n")

            # フラグ用変数
            j=0

            for bookcases in c2.execute('SELECT * FROM bookcase WHERE id = ?;',bookid):
                print(bookcases)
                for bookcase in bookcases:
                    # 一回目だけスルー
                    if j==0:
                        j = j+1
                    # 本棚を追記
                    else:
                        f2.write(bookcase + ", ")

            # EODマークを追記
            f2.write("\n\n" + EOD_MARK +"\n")

            # 既にあったらEOD以降のデータを際限
            for temp_data in temp_datas:
                f2.write(temp_data + "\n\n")

        os.chmod(filepath + "/" + urllib.parse.quote(pagename) + ".txt",0o777)

        # 本情報ページにリンクを追記
        f.write("[[本情報:" + pagename + "]]\n\n" )

    f.close()
    os.chmod(filepath + ".txt",0o777)

if __name__ == "__main__":
    WriteWiki()