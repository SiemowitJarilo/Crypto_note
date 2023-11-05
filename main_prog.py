import sys, sqlite3, requests, logging, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication,QFormLayout, QStackedWidget, QHBoxLayout, QMessageBox, QPushButton, QDialog, QDoubleSpinBox, QDateEdit, QMainWindow, QLineEdit, QTextEdit, QToolBar, QStatusBar, QWidget, QLabel, QVBoxLayout, QComboBox, QGridLayout, QStackedWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize, Qt, QDate, pyqtSignal
from pybit.unified_trading import HTTP
from matplotlib.figure import Figure
from db import db_create
db_create()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('KPiR by Jariloo')
        self.setGeometry(50, 50, 1920, 1080)
        
        # Tworzenie przycisków w głównym oknie
        self.table_button = QPushButton('Tabela')
        self.dark_mode_button = QPushButton('Dark Mode')
        self.table_button.clicked.connect(self.show_main)
        self.dark_mode_button.clicked.connect(self.dark_mode)

        # Tworzenie paska narzędziowego z przyciskami
        toolbar = self.addToolBar('Toolbar')
        toolbar.addWidget(self.table_button)
        toolbar.addWidget(self.dark_mode_button)
        
        # Tworzenie głównego widgeta z możliwością zmiany widoku
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Tworzenie widoku z tabelą
        self.central_widget.layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_widget.layout)
        self.table_view = StockTableView(self)
        self.table_view.initUI()  # Inicjalizacja widoku tabeli
        self.central_widget.layout.addWidget(self.table_view)
       
       
        self.show_main()  # Pokaż widok menu jako domyślny
    def dark_mode(self):
        # Załaduj arkusz stylów CSS dla trybu ciemnego
        with open('style.css', 'r') as stylesheet:
            self.setStyleSheet(stylesheet.read())  # Ustaw styl arkusza CSS dla głównego okna

    def show_main(self):
        self.table_view.setVisible(True)

class StockTableView(QWidget):


    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow
        

    def initUI(self):
        layout = QGridLayout()

        self.create_stock_table()
        self.create_stats_field()
        self.generate_pie_chart()
        # self.generate_line_chart()
        # self.add_ratio_column()

        layout.addWidget(self.stats_field, 0, 0)
        layout.addWidget(self.stock_table, 0, 1)
        layout.addWidget(self.canvas_pie, 1, 0)
        # layout.addWidget(self.canvas_line, 1, 1)

        self.setLayout(layout)
        self.load_stock_data()
        self.refresh_data()
        # self.calc_all_z_s()


    def create_stock_table(self):
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(11)
        column_headers = ["ID","Data", "Para", "Giełda", "Ilość", "Cena Zakupu", "Wartość Zakupu", "Aktualna Cena", "Aktualna Wartość", "Waluta", "Z/S"]
        self.stock_table.setHorizontalHeaderLabels(column_headers)
        self.stock_table.hideColumn(0)
        self.stock_table.hideColumn(9)
        self.stock_table.setMaximumWidth(900)
    def nbp_currency_prices(self):
        response = requests.get("http://api.nbp.pl/api/exchangerates/rates/a/usd/")
        data = response.json()
        usd = data.get('rates')[0].get('mid')
        return usd
    def create_formula(self):
        formula_layout = QFormLayout()
        self.label_date = QLabel("Data:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True) 
        # Ustaw dzisiejszą datę jako początkową
        today = QDate.currentDate()
        self.date_edit.setDate(today)
        self.date_edit.setStyleSheet("max-width: 100px;")  # Ustaw maksymalną szerokość na 200 pikseli
        
        # Drugie pole jako ComboBox(Giełda)
        self.label_stock = QLabel("Giełda:")
        self.stock_combo = QComboBox()
        self.load_unique_exchanges()
        self.stock_combo.currentIndexChanged.connect(self.load_pairs_for_exchange)  # Dodaj obsługę zmiany giełdy
        self.stock_combo.setStyleSheet("max-width: 200px;")

        # Pole tekstowe 3(Para)
        self.label_pair = QLabel("Para:")
        self.pair_combo = QComboBox()  # Zmieniamy na QComboBox zamiast QLineEdit
        self.pair_combo.setStyleSheet("max-width: 200px;")
        self.pair_combo.setEditable(True)
        # Po zmianie giełdy wybieramy odpowiednie pary walutowe
        self.stock_combo.currentIndexChanged.connect(self.load_pairs_for_exchange)
        self.load_pairs_for_exchange()  # Inicjalizacja listy par walutowych
        
        # Pole liczbowe zmiennoprzecinkowe(Ilość)
        self.label_count = QLabel("Ilość:")
        self.stock_count = QDoubleSpinBox()
        self.stock_count.setRange(-9999.99, 9999999999999999.9999999999)  # Ustaw zakres na -9999.99 do 9999.99 (lub odpowiednio)
        self.stock_count.setStyleSheet("max-width: 200px;")
        self.stock_count.setDecimals(6)
        
        # Pole liczbowe zmiennoprzecinkowe(Cena)
        self.label_price = QLabel("Cena:")
        self.stock_price = QDoubleSpinBox()
        self.stock_price.setRange(-9999.99, 9999999999999999.9999999999)
        self.stock_price.setStyleSheet("max-width: 200px;")
        self.pair_combo.currentIndexChanged.connect(self.update_stock_price)
        self.stock_price.setDecimals(2)
        self.update_stock_price()  # Inicjalizacja ceny
        
        
        # Pole liczbowe zmiennoprzecinkowe(Warrtość)
        self.label_value = QLabel("Wartość zakupu:")
        self.stock_value = QDoubleSpinBox()
        self.stock_value.setRange(-9999.99, 9999999999999999.9999999999)
        self.stock_value.setDecimals(2)
        self.stock_value.setStyleSheet("max-width: 200px;")
        self.stock_count.valueChanged.connect(self.update_stock_value)
        
        # Pole (Waluta)
        self.label_currency = QLabel("Waluta:")
        self.stock_currency = QLabel()
        self.stock_currency.setStyleSheet("max-width: 200px;")
        self.pair_combo.currentIndexChanged.connect(self.update_currency)
        self.update_currency()
        

        # Przycisk "Dodaj" do dodawania danych do bazy
        self.add_button = QPushButton("Dodaj")
        self.add_button.setMaximumWidth(200)
        self.add_button.clicked.connect(self.add_data_to_db)
        self.remove_button = QPushButton("Usuń")
        self.remove_button.setMaximumWidth(200)
        self.remove_button.clicked.connect(self.delete_data)

        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.setMaximumWidth(293)
        self.refresh_button.clicked.connect(self.refresh_data)
        

        formula_layout.addRow(self.label_date, self.date_edit)
        formula_layout.addRow(self.label_stock, self.stock_combo)
        formula_layout.addRow(self.label_pair, self.pair_combo)
        formula_layout.addRow(self.label_count, self.stock_count)
        formula_layout.addRow(self.label_price, self.stock_price)
        formula_layout.addRow(self.label_currency, self.stock_currency)
        formula_layout.addRow(self.label_value, self.stock_value)

        formula_layout.addRow(self.add_button, self.remove_button)
        formula_layout.addRow(self.refresh_button)

        return formula_layout  # Zwróć układ formularza


    def create_stats_field(self):
        self.stats_field = QWidget()

        main_layout = QGridLayout()

        stats_layout = QFormLayout()
        self.refresh_z_s_button = QPushButton("Odśwież")
        self.refresh_z_s_button.setMaximumWidth(293)
        self.refresh_z_s_button.clicked.connect(self.calc_all_z_s)
        self.total_loss_profit_label = QLabel("Zysk/Strata: ")
        self.total_loss_profit_label.setStyleSheet("font-size: 16px; color: blue; font-weight: bold;")
        # self.calc_all_z_s()
        self.total_loss_profit = QLabel()
        self.total_loss_profit.setStyleSheet("font-size: 16px; color: blue; font-weight: bold;")
        
        
        
        
        self.pln_usd_Label = QLabel("PLN/USD")
        self.pln_usd = QLabel(str(self.nbp_currency_prices()))

        stats_layout.addRow(self.refresh_z_s_button)
        stats_layout.addRow(self.total_loss_profit_label, self.total_loss_profit)

        stats_layout.addRow(self.pln_usd_Label, self.pln_usd)


        form_layout = self.create_formula()
        main_layout.addLayout(form_layout, 0, 1)  # Dodaj układ formularza do głównego układu
        main_layout.addLayout(stats_layout, 0, 0)   # Dodaj układ statystyk do głównego układu

        self.stats_field.setLayout(main_layout)

    def calc_all_z_s(self):
        total_value = 0.0
        total_act = 0.0
        x = 0
        for row in range(self.stock_table.rowCount()):
            buy_price = self.stock_table.item(row, 6)
            act_price = self.stock_table.item(row, 8)
            currency = self.stock_table.item(row, 9)
            currency_text = currency.text()
            a = 0
            if currency_text == 'PLN':
                try:
                  
                    print("-----------PLN-----------")
                    print(f"----{x}----")
                    x += 1
                    value1 = float(buy_price.text())
                    print(f"V1: {value1}")
                    value2 = float(act_price.text())
                    print(f"V2: {value2}")
                    total_value += value1
                    print(f"TV: {total_value}")
                    total_act += value2
                    print(f"TA: {total_act}")
                    a = total_act - total_value
                    print(f'SUM: {a}')
                except ValueError:
                    pass
                act = round(total_act, 2)
                self.total_z_s = act - total_value
                print(f'TZS: {self.total_z_s}')
            elif currency_text == 'USDT':
                url = f"https://api.zondacrypto.exchange/rest/trading/ticker/USDT-PLN"
                headers = {'content-type': 'application/json'}       
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                pln_usdt_act_price = data.get('ticker', {}).get('rate') 
     
                try:
                
                    print("-----------USDT-----------")
                    pln_usdt = float(pln_usdt_act_price)
                    print(f'PLN/USDT: {pln_usdt}')
                    print(f"----{x}----")
                    x += 1
                    value1 = float(buy_price.text())
                    print(f"V1_: {value1} USDT")
                    valu1_x_kurs = value1 * pln_usdt
                    print(f"V1_x_: {valu1_x_kurs} PLN")
                    value2 = float(act_price.text())
                    print(f"V2_: {value2} USDT")
                    valu2_x_kurs = value2 * pln_usdt
                    print(f"V2_x_: {valu2_x_kurs} PLN")
                    total_value += valu1_x_kurs
                    print(f"TV_: {total_value}")
                    total_act += valu2_x_kurs
                    print(f"TA_: {total_act}")
                    a = total_act - total_value
                    print(f'SUM: {a}')
                except ValueError:
                    pass
                act = round(total_act, 2)   
                self.total_z_s = act - total_value
                print(f'TZS: {self.total_z_s}')
            
            # print(f'SUM: {self.total_z_s}')
            
        total_v = total_value
        print(total_v)
        total_a = total_act
        print(total_a)     
        self.sum_sum = total_a - total_v
        
        self.total_loss_profit.setText(f"{self.sum_sum:.2f}")        

            
    def refresh_data(self):
        for row in range(self.stock_table.rowCount()):
            # Pobierz informacje o giełdzie (kolumna 2 to "Giełda")
            gielda_item = self.stock_table.item(row, 3)
            gielda = gielda_item.text()
            para_item = self.stock_table.item(row, 2)
            para = para_item.text()
            count_item = self.stock_table.item(row, 4)
            count = count_item.text()
            price_item = self.stock_table.item(row, 5)
            price = count_item.text()

            if gielda == "Zonda":
                self.refresh_zonda(row, para, count)
            elif gielda == "Bybit":
                self.refresh_bybit(row, para, count)
            elif gielda == "Binance":
                self.refresh_binance(row, para, count)

        for row in range(self.stock_table.rowCount()):
            count_item = self.stock_table.item(row, 4)
            price_now_item = self.stock_table.item(row, 7)
            

            
            if not count_item or not price_now_item:
                continue
            count = count_item.text()
       
            price_now = price_now_item.text()
    
            actual_value = float(count) * float(price_now)


            
            # Obsługa błędu, gdy nie można uzyskać ceny lub danych z tabeli
            if actual_value is not None:
                # Oblicz różnicę między ceną aktualną a ceną zakupu
                wartosc_zakupu_item = self.stock_table.item(row,6)
                if wartosc_zakupu_item:
                    wartosc_zakupu = float(wartosc_zakupu_item.text())
                    

                    count = float(count)
                    zysk_strata = ((actual_value - wartosc_zakupu) / wartosc_zakupu)*100


                    # Zaokrąglenie do dwóch miejsc po przecinku
                    zysk_strata_round = round(zysk_strata, 3)

                    # Określenie, czy wartość jest wzrostem (+) czy spadkiem (-)
                    if zysk_strata_round > 0:
                        z_s_text = f"+{zysk_strata_round}%"
                    elif zysk_strata_round < 0:
                        z_s_text = f"{zysk_strata_round}%"
                    else:
                        z_s_text = "0%"

                    # Sprawdź, czy komórka w kolumnie "Z/S" istnieje, jeśli nie, utwórz ją
                    z_s_item = self.stock_table.item(row, 10)
                    
                    if not z_s_item:
                        z_s_item = QTableWidgetItem()
                        self.stock_table.setItem(row, 10, z_s_item)

                    # Ustaw wartość procentową w kolumnie "Z/S"
                    z_s_item.setText(z_s_text)
            else:
                # Jeśli nie udało się uzyskać ceny, ustaw puste pole w kolumnie "Z/S"
                z_s_item = self.stock_table.item(row, 10)
                z_s_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if not z_s_item:
                    z_s_item = QTableWidgetItem()
                    self.stock_table.setItem(row, 10, z_s_item)
                    
                z_s_item.setText("")
            self.update_actual_price(row, actual_value)
            # self.calc_all_z_s()

    def refresh_zonda(self, row, para, count):
        url = f"https://api.zondacrypto.exchange/rest/trading/ticker/{para}"
        headers = {'content-type': 'application/json'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            act_price = data.get('ticker', {}).get('rate')
            act_price_dumb = float(act_price)
            count_dumb = float(count)
            act_value = act_price_dumb * count_dumb
            
            if act_price and act_value is not None:
                self.stock_table.item(row, 7).setText(str(act_price))
                self.stock_table.item(row, 8).setText(str(act_value))
                
                
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania danych dla Zonda: {e}")
        except Exception as e:
            print(f"Błąd przetwarzania danych dla Zonda: {e}")

    def refresh_bybit(self, row, para, count):

        try:
            session = HTTP(testnet=True)
            response = session.get_tickers(
                category="inverse",
                symbol=para,
            )
            act_price = response['result']['list'][0]['lastPrice']

            act_price_dumb = float(act_price)
            count_dumb = float(count)
            act_value = act_price_dumb * count_dumb
            act_value_rounded = round(act_value, 2)


            
            if act_price and act_value_rounded is not None:
                self.stock_table.item(row, 7).setText(str(act_price))
                self.stock_table.item(row, 8).setText(str(act_value_rounded))
        except Exception as e:
            error_message = f"Błąd podczas pobierania danych dla Bybit: {e}"
            print(error_message)

            # Wyświetlenie błędu jako wyskakującego okienka
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Błąd")
            msg.setText(error_message)
            msg.exec()

    def refresh_binance(self, row, para, count):
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={para}"
        headers = {'content-type': 'application/json'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            act_price = data.get('price')

            act_price_dumb = float(act_price)
            act_price_rounded = round(act_price_dumb, 2)
            count_dumb = float(count)
            act_value = act_price_dumb * count_dumb
            act_value_rounded = round(act_value, 2)



            
            if act_price and act_value_rounded is not None:
                self.stock_table.item(row, 7).setText(str(act_price_rounded))
                self.stock_table.item(row, 8).setText(str(act_value_rounded))
        except Exception as e:
            error_message = f"Błąd podczas pobierania danych dla Bybit: {e}"
            print(error_message)

            # Wyświetlenie błędu jako wyskakującego okienka
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Błąd")
            msg.setText(error_message)
            msg.exec()

    def update_actual_price(self, row, actual_price):
        # Zaokrąglanie do dwóch miejsc po przecinku
        actual_price_rounded = round(actual_price, 2)
        item = QTableWidgetItem(f"{actual_price_rounded:.2f}")
        self.stock_table.setItem(row, 8, item)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight)

    def generate_line_chart(self):
        # Inicjalizacja atrybutu ax_line
        self.figure_line, self.ax_line = plt.subplots(figsize=(6, 4))
        self.canvas_line = FigureCanvas(self.figure_line)
        # Utwórz połączenie z bazą danych SQLite
        with sqlite3.connect("simple.db") as db_connection:
            # Pobierz dane z tabeli inwestycje
            query = "SELECT date, value FROM purchase ORDER BY date"
            df = pd.read_sql_query(query, db_connection)

        # Przekształć dane w odpowiedni format
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)

        # Oblicz kumulacyjny cashflow
        df['cashflow'] = df['value'].cumsum()

        # Wyczyść poprzedni wykres
        self.ax_line.clear()

        # Usuń wiersze z nieprawidłowymi danymi (NaN lub nieskończonościami)
        df = df.dropna()  # Usuń wiersze z wartościami NaN
        df = df.replace([np.inf, -np.inf], np.nan).dropna()  # Usuń wiersze z nieskończonościami

        # Narysuj wykres liniowy
        self.ax_line.plot(df.index, df['cashflow'], marker='o', linestyle='-')

        # Dodaj kolor poniżej osi X
        self.ax_line.fill_between(df.index, df['cashflow'], color='lightgray')

        # Dodaj tytuł i etykiety osi
        self.ax_line.set_title('Cashflow w czasie')
        self.ax_line.set_xlabel('Data Zakupu')
        self.ax_line.set_ylabel('Cashflow')

        # Odśwież wykres
        self.canvas_line.draw()
 
    def generate_pie_chart(self):
        # Wyczyszczenie poprzedniego wykresu
        
        
        # Utworzenie wykresu kołowego
        self.figure_pie, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas_pie = FigureCanvas(self.figure_pie)
        self.ax.clear()
        # Utworzenie połączenia z bazą danych SQLite
        with sqlite3.connect("simple.db") as db_connection:
            # Pobranie danych z tabeli do DataFrame
            query = ''' SELECT stocks.name AS stock_name, SUM(purchase.value) AS total_value
                        FROM pairs
                        JOIN purchase ON pairs.id = purchase.purch_pairs
                        JOIN stocks ON stock_id = stocks.id
                        GROUP BY stocks.name
                        '''
            df = pd.read_sql_query(query, db_connection)

        # Ustawienie etykiet i wartości dla wykresu
        labels = df['stock_name']
        sizes = df['total_value']

        # Tworzenie wykresu kołowego
        self.ax.pie(sizes, labels=[None] * len(labels), autopct='%1.1f%%', startangle=140, wedgeprops={'width': 0.4}, pctdistance=0.8)

        # Dodanie tytułu wykresu
        self.ax.set_title('Wartość inwestycji na poszczególnych giełdach')

        # Wartość portfela w środku pierścienia
        # total_portfolio_value = df['total_value'].sum()
        # self.ax.text(0, 0, f'Total:\n{total_portfolio_value:.2f}', fontsize=12, ha='center', va='center')

        # Utworzenie legendy z etykietami
        self.ax.legend(labels, title="Giełda", loc="upper right", bbox_to_anchor=(1.1, 1))

        # Odświeżenie wykresu
        self.canvas_pie.draw()

    def load_unique_exchanges(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Zapytanie SQL
        cursor.execute("SELECT stocks.name FROM stocks")
        exchanges = cursor.fetchall()

        # Dodawanie nazw do comboboxa
        for exchange  in exchanges:
            self.stock_combo.addItem(exchange[0])

        db.close()
    def load_pairs_for_exchange(self):
        selected_exchange = self.stock_combo.currentText()
        if selected_exchange:
            db = sqlite3.connect("simple.db")
            cursor = db.cursor()

            # Zapytanie SQL, aby pobrać pary walutowe dla wybranej giełdy
            
            cursor.execute("""SELECT pairs.name AS pair_name, stocks.name AS stock_name
                       FROM pairs
                       JOIN stocks ON pairs.stock_id = stocks.id
                       WHERE stocks.name = ?""", (selected_exchange,))
            pairs = cursor.fetchall()

            # Wyczyść ComboBox z paramami
            self.pair_combo.clear()

            # Dodaj nazwy par walutowych do ComboBox
            for pair in pairs:
                self.pair_combo.addItem(pair[0])

            db.close()
    def get_zonda_price(self):
        selected_pair = self.pair_combo.currentText()
        if not selected_pair:
            return None
        url = f"https://api.zondacrypto.exchange/rest/trading/ticker/{selected_pair}"
        headers = {'content-type': 'application/json'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            lowest_ask = data.get('ticker', {}).get('rate')
           

            if lowest_ask:
                try:
                    return float(lowest_ask)
                
                except ValueError:
                    return None

        except:
            pass
        
        return None
    def get_zonda_curr(self, selected_pair):
        if not selected_pair:
            return None
        db = sqlite3.connect('simple.db')
        cursor = db.cursor()
        try:
            
            query = "SELECT quote FROM pairs where name = ?"
           
            cursor.execute(query, (selected_pair,))
            data = cursor.fetchone()

            return data[0]
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return None
    def get_bybit_price(self):
        selected_pair = self.pair_combo.currentText()
        if not selected_pair:
            return None

        try:
            session = HTTP(testnet=True)  # Odpowiednio dostosuj, czy używasz testnet czy nie
            response = session.get_tickers(category="inverse", symbol=selected_pair)
            lowest_ask = response['result']['list'][0]['lastPrice']
            x = float(lowest_ask)

            if lowest_ask:
                try:
                    return float(lowest_ask)
                except ValueError:
                    return None
        except:
            pass

        return None
    def get_bybit_curr(self, selected_pair):
        if not selected_pair:
            return None
        db = sqlite3.connect('simple.db')
        cursor = db.cursor()
        try:
            
            query = "SELECT quote FROM pairs where name = ?"
           
            cursor.execute(query, (selected_pair,))
            data = cursor.fetchone()

            return data[0]
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return None
    def get_binance_price(self):
        selected_pair = self.pair_combo.currentText()
        if not selected_pair:
            return None

        url = f"https://api.binance.com/api/v3/ticker/price?symbol={selected_pair}"
        headers = {'content-type': 'application/json'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            lowest_ask = data.get('price')

            if lowest_ask:
                try:
                    return float(lowest_ask)
                except ValueError:
                    return None
        except:
            pass

        return None
    def get_binance_curr(self, selected_pair):
        if not selected_pair:
            return None
        db = sqlite3.connect('simple.db')
        cursor = db.cursor()
        try:
            
            query = "SELECT quote FROM pairs where name = ?"
           
            cursor.execute(query, (selected_pair,))
            data = cursor.fetchone()

            return data[0]
           
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return None
    def update_stock_value(self):
        quantity = self.stock_count.value()
        price = self.stock_price.value()
        
        # Oblicz wartość na podstawie ilości i ceny
        value = quantity * price
        
        # Ustaw obliczoną wartość w polu Wartość zakupu
        self.stock_value.setValue(value)
    def update_stock_price(self):
        selected_option = self.stock_combo.currentText()
        selected_pair = self.pair_combo.currentText()
        
        if selected_option == "Zonda":
            price = self.get_zonda_price()
        elif selected_option == "Bybit":
            price = self.get_bybit_price()
        elif selected_option == "Binance":
            price = self.get_binance_price()
        else:
            price = None
        
        if price is not None:
            self.stock_price.setValue(price)
        else:
            # Jeśli nie udało się pobrać ceny, ustaw pole na 0
            self.stock_price.setValue(0.0)
        
    def update_currency(self):
        selected_stock = self.stock_combo.currentText()
        selected_pair = self.pair_combo.currentText()

        if selected_stock == 'Zonda':
            currency_zonda = self.get_zonda_curr(selected_pair)
            self.stock_currency.setText(currency_zonda)
        elif selected_stock == 'Bybit':
            currency_bybit = self.get_bybit_curr(selected_pair)
            self.stock_currency.setText(currency_bybit)
        elif selected_stock == 'Binance':
            currency_binance = self.get_binance_curr(selected_pair)
            self.stock_currency.setText(currency_binance)
        else:
            self.stock_currency.setText("Brak danych")
        # 
        # 
        
        # if currency_zonda is not None:
        #     self.stock_currency.setText(currency_zonda)
        # elif currency_bybit is not None:
        #     self.stock_currency.setText(currency_bybit)
        # else:
        #     # Jeśli nie udało się pobrać waluty, ustaw pole na brak danych
        #     self.stock_currency.setText("Brak danych")
        # # if 
    def add_data_to_db(self):
        
        # Pobierz dane z pól formularza
        data_zakupu = self.date_edit.date().toString("yyyy-MM-dd")
     
        gielda = self.stock_combo.currentText()
        para = self.pair_combo.currentText()
        ilosc = self.stock_count.value()
        cena_zakupu = self.stock_price.value()
        wartosc_zakupu = self.stock_value.value()  # Możesz pobrać wartość z pola stock_value
        waluta = self.stock_currency.text()
        # aktualna_cena = None
        # Sprawdzanie giełdy
        # selected_option = self.stock_combo.currentText()
        # if selected_option == "Zonda":
        #     aktualna_cena = self.get_zonda_price()
        # elif selected_option == "Bybit":
        #     aktualna_cena = self.get_bybit_price()
        # elif selected_option == "Binance":
        #     aktualna_cena = self.get_binance_price()

        # Połącz z bazą danych
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        try:
            a = 0
            b = 0
            # Wstaw dane do tabeli
            cursor.execute("SELECT id FROM pairs WHERE name=?", (para,))
            result = cursor.fetchone()[0]
            cursor.execute("INSERT INTO purchase (purch_pairs, date, count, price, value, currency) VALUES (?, ?, ?, ?, ?, ?)",
                        (result, data_zakupu, ilosc, cena_zakupu, wartosc_zakupu, waluta))
            cursor.execute("SELECT last_insert_rowid()")
            last_inserted_row_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO prices (act_id, act_price, act_value) VALUES (?, ?, ?)",
               (last_inserted_row_id, a, b))
            db.commit()




            if self.main_window:
                self.main_window.table_view.load_stock_data()
            # Opcjonalnie, wyczyść pola formularza po dodaniu danych
            self.date_edit.setDate(QDate.currentDate())
            self.stock_combo.setCurrentIndex(0)
            self.pair_combo.clear()
            self.stock_count.setValue(0.0)
            self.stock_price.setValue(0.0)
            self.stock_value.setValue(0.0)

            # Odśwież widok tabeli (wywołaj funkcję refresh_data w widoku StockTableView)
            

        except Exception as e:
            # Obsłuż błędy przy wstawianiu danych do bazy
            print(f"Błąd przy wstawianiu danych do bazy: {e}")

        finally:
            # Zamknij kursor i połączenie z bazą danych
            cursor.close()
            db.close()
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Transakcja została dodana.")
            msg.setWindowTitle("Jest Git!")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    def load_stock_data(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()
        
        query = """
        SELECT 
            purchase.id as id,
            purchase.date AS date, 
            pairs.name AS pair, 
            stocks.name AS name, 
            purchase.count AS count, 
            purchase.price AS price, 
            purchase.value AS value, 
            prices.act_price AS act_price, 
            prices.act_value AS act_value,
            purchase.currency AS currency
        FROM pairs
        JOIN stocks ON stock_id = stocks.id
        JOIN purchase ON pairs.id = purchase.purch_pairs
        JOIN prices ON purchase.id = prices.act_id
        """
        
        cursor.execute(query)
        data = cursor.fetchall()
        db.close()
        
        column_mapping = {
        'id': 0,
        'date': 1,
        'pair': 2,
        'name': 3,
        'count': 4,
        'price': 5,
        'value': 6,
        'act_price': 7,
        'act_value': 8,
        'currency': 9
    }
        self.stock_table.setRowCount(len(data))
    
        for row_index, row_data in enumerate(data):
            for column_name, column_index in column_mapping.items():
                cell_data = row_data[column_index]
                item = QTableWidgetItem(str(cell_data))
                self.stock_table.setItem(row_index, column_index, item)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            # buy_value = float(row_data[5])
    
    def delete_data(self):
        # Get the selected rows from the table
        selected_rows = self.stock_table.selectedItems()
        if selected_rows:
            selected_row = selected_rows[0].row()
            item_in_first_column = self.stock_table.item(selected_row, 0)
            if item_in_first_column:
                print(f"Zawartość pierwszej komórki zaznaczonego wiersza: {item_in_first_column.text()}")

        # Check if any rows are selected
        if not selected_rows:
            return

        # Create a list to store the IDs of records to be deleted
        records_to_delete = []

        for selected_row in selected_rows:
            # Extract the unique identifier (e.g., primary key) from the selected row
            id_column = 0  # Adjust this index based on your table structure
            record_id = self.stock_table.item(selected_row.row(), id_column).text()
            records_to_delete.append(record_id)

        # Connect to the database
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        try:
            # Iterate over the list of IDs and delete records from the database
            for record_id in records_to_delete:
                cursor.execute("DELETE FROM purchase WHERE id=?", (record_id,))
                cursor.execute("DELETE FROM prices WHERE act_id=?", (record_id,))
                db.commit()

                # You may need additional DELETE statements if there are other related tables

            # Commit the changes to the database
            db.commit()

            # Remove the selected rows from the table
            for selected_row in selected_rows:
                self.stock_table.removeRow(selected_row.row())

        except Exception as e:
            # Handle any exceptions (e.g., database errors)
            print(f"Error deleting records: {e}")

        finally:
            # Close the database connection
            db.close()

    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())