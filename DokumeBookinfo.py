from bs4 import BeautifulSoup

# htmlのdata-modelクラスから本棚情報に変換する関数
def datamodel2bookcase(data_model):
    try:
        split_line = str(data_model).split('"bookcases":[')
        split_line2 =split_line[1].split('],"id"')
        bookcases = [line.replace('"','') for line in split_line2[0].split(',')]
    # 一部の書籍は文字コードの設定がおかしいのか、「"」が「&quot;」に化ける。
    except:
        split_line = str(data_model).split('&quot;bookcases&quot;:[')
        split_line2 =split_line[1].split('],&quot;id&quot;')
        bookcases = [line.replace('&quot;','') for line in split_line2[0].split(',')]
    return bookcases

# 各本のデータ格納・データ処理用のクラス
class Dokume_Bookinfo:

    # コントラクタ
    def __init__(self,soup):
        self.booktitle = ""
        self.bookauthor = ""
        self.read_number = 0
        self.bookcases = []
        self.dates = []
        self.notes = []
        self.s = soup
    
    # 本の情報を取得するメソッド
    def get_bookinfo(self):
        self.booktitle = self.s.select_one("h1.inner__title").get_text()
        self.bookauthor = self.s.select_one(".header__authors a").get_text()
        self.read_number =int(self.s.select_one(".content__count").get_text())
    
    # 本棚の情報を取得するメソッド
    def get_bookcases(self):
        data_model = self.s.find("div",{"class":"action__edit"})
        self.bookcases = datamodel2bookcase(data_model)
    
    # 読書記録を取得するメソッド
    def get_read_record(self):
        date_lines = self.s.select(".read-book__date")
        self.dates =  [int(str(date_line.get_text()).replace("/","")) if not '不明' in str(date_line) else 0 for date_line in date_lines]
        note_lines = self.s.select(".read-book__content")
        self.notes = [note_line.get_text() for note_line in note_lines]

    # 本棚の配列の要素を10まで埋めるメソッド
    def fill_bookcase(self):
        if len(self.bookcases) > 10:
            print(booktitle)
            print('本棚の数が多すぎます（11個以上）')
            sys.exit()
        else:
            for i in range(10-len(self.bookcases)):
                self.bookcases.append("")
    
    def update_soup(self, soup):
        self.s = soup