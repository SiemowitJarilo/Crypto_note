import sys, sqlite3, requests, logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication,QFormLayout, QHBoxLayout, QMessageBox, QPushButton, QDialog, QDoubleSpinBox, QDateEdit, QMainWindow, QLineEdit, QTextEdit, QToolBar, QStatusBar, QWidget, QLabel, QVBoxLayout, QComboBox, QGridLayout, QStackedWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize, Qt, QDate, pyqtSignal
from pybit.unified_trading import HTTP
from matplotlib.figure import Figure
from db import db_create
db_create()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setWindowTitle('KPiR by Jariloo')
        self.setGeometry(50, 50, 1920, 1080)
        
        # Tworzenie przycisków w głównym oknie
        self.table_button = QPushButton('Tabela')
        self.form_button = QPushButton('Formularz')
        self.pairs_button = QPushButton('Pary')
        self.dark_mode_button = QPushButton('Dark Mode')
        self.table_button.clicked.connect(self.show_main)
        self.form_button.clicked.connect(self.show_stock)
        self.pairs_button.clicked.connect(self.show_pairs)
        self.dark_mode_button.clicked.connect(self.dark_mode)

        # Tworzenie paska narzędziowego z przyciskami
        toolbar = self.addToolBar('Toolbar')
        toolbar.addWidget(self.table_button)
        toolbar.addWidget(self.form_button)
        toolbar.addWidget(self.pairs_button)
        toolbar.addWidget(self.dark_mode_button)
        
        # Tworzenie głównego widgeta z możliwością zmiany widoku
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Tworzenie widoku z formularzem
        self.stock_form = StockForm(self)
        self.stock_form.initUi()  # Inicjalizacja formularza
        self.central_widget.layout = QVBoxLayout()
        self.central_widget.layout.addWidget(self.stock_form)
        self.central_widget.setLayout(self.central_widget.layout)

        # Tworzenie widoku z tabelą
        self.table_view = StockTableView(self)
        self.table_view.initUi()  # Inicjalizacja widoku tabeli
        self.central_widget.layout.addWidget(self.table_view)
       
        
        # Tworzenie widoku par walutowych
        self.pairs_view = EditPairsDialog(self)
        self.pairs_view.initUi()  # Inicjalizacja widoku tabeli
        self.central_widget.layout.addWidget(self.pairs_view)
       
       
        self.show_main()  # Pokaż widok menu jako domyślny
    def dark_mode(self):
        # Załaduj arkusz stylów CSS dla trybu ciemnego
        with open('style.css', 'r') as stylesheet:
            self.setStyleSheet(stylesheet.read())  # Ustaw styl arkusza CSS dla głównego okna

    def show_main(self):
        self.stock_form.setVisible(False)
        self.table_view.setVisible(True)
        self.pairs_view.setVisible(False)
    def show_stock(self):
        self.stock_form.setVisible(True)
        self.table_view.setVisible(False)
        self.pairs_view.setVisible(False)
    def show_pairs(self):
        self.pairs_view.setVisible(True)
        self.stock_form.setVisible(False)
        self.table_view.setVisible(False)
class StockForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow


    def initUi(self):
        layout = QGridLayout()
        container_widget = QWidget()
        container_layout = QVBoxLayout()

        # Pole z datą i kalendarzem
        label_date = QLabel("Data:")
        self.date_edit = QDateEdit()
        # Umożliwia otwarcie kalendarza po kliknięciu w pole
        self.date_edit.setCalendarPopup(True) 
        # Ustaw dzisiejszą datę jako początkową
        today = QDate.currentDate()
        self.date_edit.setDate(today)
        self.date_edit.setStyleSheet("max-width: 200px;")  # Ustaw maksymalną szerokość na 200 pikseli
       
        # Drugie pole jako ComboBox(Giełda)
        label_stock = QLabel("Giełda:")
        self.stock_combo = QComboBox()
        self.load_unique_exchanges()
        self.stock_combo.currentIndexChanged.connect(self.load_pairs_for_exchange)  # Dodaj obsługę zmiany giełdy
        self.stock_combo.setStyleSheet("max-width: 200px;")
        
       # Pole tekstowe 3(Para)
        label_pair = QLabel("Para:")
        self.pair_combo = QComboBox()  # Zmieniamy na QComboBox zamiast QLineEdit
        self.pair_combo.setStyleSheet("max-width: 200px;")
        # Po zmianie giełdy wybieramy odpowiednie pary walutowe
        self.stock_combo.currentIndexChanged.connect(self.load_pairs_for_exchange)
        self.load_pairs_for_exchange()  # Inicjalizacja listy par walutowych

        # Pole liczbowe zmiennoprzecinkowe(Ilość)
        label_count = QLabel("Ilość:")
        self.stock_count = QDoubleSpinBox()
        self.stock_count.setRange(-9999.99, 9999999999999999.9999999999)  # Ustaw zakres na -9999.99 do 9999.99 (lub odpowiednio)
        self.stock_count.setStyleSheet("max-width: 200px;")
        self.stock_count.setDecimals(6)

        # Pole liczbowe zmiennoprzecinkowe(Cena)
        label_price = QLabel("Cena:")
        self.stock_price = QDoubleSpinBox()
        self.stock_price.setRange(-9999.99, 9999999999999999.9999999999)
        self.stock_price.setStyleSheet("max-width: 200px;")
        self.pair_combo.currentIndexChanged.connect(self.update_stock_price)
        self.stock_price.setDecimals(2)
        self.update_stock_price()  # Inicjalizacja ceny
        
        # Pole liczbowe zmiennoprzecinkowe(Warrtość)
        label_value = QLabel("Wartość zakupu:")
        self.stock_value = QDoubleSpinBox()
        self.stock_value.setRange(-9999.99, 9999999999999999.9999999999)
        self.stock_value.setDecimals(2)
        self.stock_value.setStyleSheet("max-width: 200px;")
        self.stock_count.valueChanged.connect(self.update_stock_value)
        

        # Przycisk "Dodaj" do dodawania danych do bazy
        self.add_button = QPushButton("Dodaj")
        self.add_button.setMaximumWidth(200)
        self.add_button.clicked.connect(self.add_data_to_db)
        
        
        
        # Siatka
        container_layout.addWidget(label_date)
        container_layout.addWidget(self.date_edit)
        container_layout.addWidget(label_stock)
        container_layout.addWidget(self.stock_combo)
        container_layout.addWidget(label_pair)
        container_layout.addWidget(self.pair_combo)
        container_layout.addWidget(label_count)
        container_layout.addWidget(self.stock_count)
        container_layout.addWidget(label_price)
        container_layout.addWidget(self.stock_price)
        container_layout.addWidget(label_value)
        container_layout.addWidget(self.stock_value) 
        container_layout.addWidget(self.add_button)

        container_widget.setLayout(container_layout)
        container_widget.setMinimumSize(350, 200)  # Minimalny rozmiar kontenera
        container_widget.setMaximumSize(200, 400)  # Maksymalny rozmiar kontenera   
        layout.addWidget(container_widget, 0, 0)

        # Tworzymy puste kontenery jako widgety
        empty_container1 = QWidget()
        empty_container2 = QWidget()

        # Tworzymy layouty wewnątrz pustych kontenerów
        empty_layout1 = QVBoxLayout()
        empty_layout2 = QVBoxLayout()

        # Tworzymy widgety do umieszczenia w pustych kontenerach
        label1 = QLabel()
        label2 = QLabel()
        button = QPushButton('Przycisk')
        # Dodajemy widgety do layoutów pustych kontenerów
        empty_layout1.addWidget(label1)
        empty_layout1.addWidget(button)
        empty_layout2.addWidget(label2)

        # Ustawiamy layouty wewnątrz pustych kontenerów
        empty_container1.setLayout(empty_layout1)
        empty_container2.setLayout(empty_layout2)

        # Dodajemy puste kontenery na siatkę
        layout.addWidget(empty_container1, 1, 0)
        layout.addWidget(empty_container2, 0, 1)
        self.setLayout(layout)
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
        print(selected_exchange)
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
    def get_bybit_price(self):
        selected_pair = self.pair_combo.currentText()
        if not selected_pair:
            return None

        try:
            session = HTTP(testnet=True)  # Odpowiednio dostosuj, czy używasz testnet czy nie
            response = session.get_tickers(category="spot", symbol=selected_pair)
            lowest_ask = response['result']['list'][0]['lastPrice']

            if lowest_ask:
                try:
                    return float(lowest_ask)
                except ValueError:
                    return None
        except:
            pass

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
    def add_data_to_db(self):
        
        # Pobierz dane z pól formularza
        data_zakupu = self.date_edit.date().toString("yyyy-MM-dd")
     
        gielda = self.stock_combo.currentText()
        para = self.pair_combo.currentText()
        ilosc = self.stock_count.value()
        cena_zakupu = self.stock_price.value()
        wartosc_zakupu = self.stock_value.value()  # Możesz pobrać wartość z pola stock_value
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
            cursor.execute("INSERT INTO purchase (purch_pairs, date, count, price, value) VALUES (?, ?, ?, ?, ?)",
                        (result, data_zakupu, ilosc, cena_zakupu, wartosc_zakupu))
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
class StockTableView(QWidget):


    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow
        

    def initUi(self):
        layout = QGridLayout()
        self.setLayout(layout)

        # Tworzenie tabeli do wyświetlania danych
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(9)  # Liczba kolumn w tabeli (zgodna z liczbą kolumn w bazie danych)
        # Ustaw nazwy kolumn w tabeli
        column_headers = ["Data", "Para", "Giełda", "Ilość", "Cena Zakupu", "Wartość Zakupu", "Aktualna Cena", "Aktualna Wartość", "Z/S"]

        self.stock_table.setHorizontalHeaderLabels(column_headers)
        # Ukryj kolumnę "ID"
        # self.stock_table.setColumnHidden(0, True)  # Indeks kolumny "ID" to 0
        self.stock_table.setMaximumWidth(818)
        
        # Przycisk odświeżania
        # Przycisk odświeżania
        self.refresh_button = QPushButton("Odśwież")
        layout.addWidget(self.refresh_button, 1, 0)

        # Połącz przycisk z funkcją odświeżania
        self.refresh_button.clicked.connect(self.refresh_data)
        
        # Statystyki
        stats_field = QWidget()
        stats_layout = QHBoxLayout()

        
        self.total_loss_profit_label = QLabel("Zysk/Strata")
        self.total_loss_profit = QLabel()
        self.pln_usd_Label = QLabel("PLN/USD")
        self.pln_usd = QLabel()

        stats_layout.addWidget(self.total_loss_profit_label)
        stats_layout.addWidget(self.total_loss_profit)
        stats_layout.addWidget(self.pln_usd_Label)
        stats_layout.addWidget(self.pln_usd)
        
        stats_field.setLayout(stats_layout)

        # def calc_total_profit(self):


        # Dodawanie wykresu kołowego
        self.figure_pie, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas_pie = FigureCanvas(self.figure_pie)

        # Dodawanie wykresu liniowego
        self.figure_line, self.ax_line = plt.subplots(figsize=(6, 4))
        self.canvas_line = FigureCanvas(self.figure_line)
        layout.addWidget(self.canvas_line, 1, 1)
        
        # Ustawianie widgetów na siatce
   
        layout.addWidget(self.canvas_pie, 2, 1)
        layout.addWidget(self.stock_table, 2, 0)
        layout.addWidget(self.canvas_line, 1, 1)
        layout.addWidget(stats_field, 0, 0)
        
        # Wyświetlanie widgetów
        self.generate_pie_chart()
        self.load_stock_data()
        self.refresh_data()
        # self.generate_line_chart()
    
    # def generate_line_chart(self):
    #     # Utwórz połączenie z bazą danych SQLite
    #     db_connection = sqlite3.connect("simple.db")
    #     # Pobierz dane z tabeli inwestycje
    #     query = "SELECT data_zakupu, wartosc_zakupu FROM inwestycje ORDER BY data_zakupu"
    #     df = pd.read_sql_query(query, db_connection)
    #     print(df)
    #     # Zamknij połączenie z bazą danych
    #     db_connection.close()
    #     # Przekształć dane w odpowiedni format
    #     df['data_zakupu'] = pd.to_datetime(df['data_zakupu'])
    #     df.set_index('data_zakupu', inplace=True)
    #     df.sort_index(inplace=True)
    #     # Oblicz kumulacyjny cashflow
    #     df['cashflow'] = df['wartosc_zakupu'].cumsum()
    #     # Wyczyść poprzedni wykres
    #     self.ax_line.clear()
    #     # Usuń wiersze z nieprawidłowymi danymi (NaN lub nieskończonościami)
    #     df = df.dropna()  # Usuń wiersze z wartościami NaN
    #     df = df.replace([np.inf, -np.inf], np.nan).dropna()  # Usuń wiersze z nieskończonościami

    #     # Narysuj wykres liniowy
    #     self.ax_line.plot(df.index, df['cashflow'], marker='o', linestyle='-')
    #     # Dodaj kolor poniżej osi X
    #     self.ax_line.fill_between(df.index, df['cashflow'], color='lightgray')
    #     # Dodaj tytuł i etykiety osi
    #     self.ax_line.set_title('Cashflow w czasie')
    #     self.ax_line.set_xlabel('Data Zakupu')
    #     self.ax_line.set_ylabel('Cashflow')
    #     # Odśwież wykres
    #     self.canvas_line.draw()
        rowCount = self.stock_table.rowCount()
        columnCount = self.stock_table.columnCount()

        for row in range(rowCount):
            for col in range(columnCount):
                item = self.stock_table.item(row, col)
                if item is not None:
                    data = item.text()
                    print(f"Dane w wierszu {row}, kolumnie {col}: {data}")

   
       
    def generate_pie_chart(self):
        # Utworzenie połączenia z bazą danych SQLite
        db_connection = sqlite3.connect("simple.db")
        # Pobranie danych z tabeli do DataFrame
        query = ''' SELECT stocks.name AS stock_name, SUM(purchase.value) AS total_value
                    FROM pairs
                    JOIN purchase ON pairs.id = purchase.purch_pairs
                    JOIN stocks ON stock_id = stocks.id
                    GROUP BY stocks.name
                    '''

        df = pd.read_sql_query(query, db_connection)
        
        # Zamknięcie połączenia z bazą danych
        db_connection.close()
        # Ustawienie etykiet i wartości dla wykresu
        labels = df['stock_name']
        sizes = df['total_value']
        # Wyczyszczenie poprzedniego wykresu
        self.ax.clear()
        # Tworzenie wykresu kołowego
        self.ax.pie(sizes, labels=[None]*len(labels), autopct='%1.1f%%', startangle=140, wedgeprops={'width': 0.4}, pctdistance=0.8)
        # Dodanie tytułu wykresu
        self.ax.set_title('Wartość inwestycji na poszczególnych giełdach')
        # Wartość portfela w środku pierścienia
        total_portfolio_value = df['total_value'].sum()
        self.ax.text(0, 0, f'Total:\n{total_portfolio_value:.2f}', fontsize=12, ha='center', va='center')
        # Utworzenie legendy z etykietami
        self.ax.legend(labels, title="Giełda", loc="upper right", bbox_to_anchor=(1.1, 1))
        
        

       
        # Odświeżenie wykresu
        self.canvas_pie.draw()
    def load_stock_data(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()
        cursor.execute("""SELECT 
                        purchase.date AS date, pairs.name AS pair, stocks.name AS name, purchase.count AS count, purchase.price AS price, purchase.value AS value, prices.act_price AS act_price, prices.act_value AS act_value
                        FROM pairs
                        JOIN stocks ON stock_id = stocks.id
                        JOIN purchase ON pairs.id = purchase.purch_pairs
                        JOIN prices ON purchase.id = prices.act_id""")
        data = cursor.fetchall()
        db.close()
        # Dodaj kolumnę "Z/S" do danych
        # Wstaw dane do tabeli, w tym kolumny "Zysk/Strata" z wartościami początkowymi 0.0%
        self.stock_table.setRowCount(len(data))
        for row_index, row_data in enumerate(data):
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.stock_table.setItem(row_index, col_index, item)
                
                # Ustaw początkową wartość "Zysk/Strata" na 0.0%
                if col_index == 9:
                    item = QTableWidgetItem("0.0%")
                    self.stock_table.setItem(row_index, 9, item)
    def refresh_data(self):
        for row in range(self.stock_table.rowCount()):
            # Pobierz informacje o giełdzie (kolumna 2 to "Giełda")
            gielda_item = self.stock_table.item(row, 2)
            gielda = gielda_item.text()
            para_item = self.stock_table.item(row, 1)
            para = para_item.text()
            count_item = self.stock_table.item(row, 3)
            count = count_item.text()
            act_price = None  # Inicjalizacja wartości na None
            act_value = 0
            success = False  # Zmienna śledząca sukces operacji pobierania danych

            if gielda == "Zonda":
                # Wykonaj request HTTP dla giełdy "Zonda"
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
                    success = True  # Operacja pobierania danych zakończona sukcesem
                    if success and act_price and act_value is not None:
                        self.stock_table.item(row, 6).setText(str(act_price))
                        self.stock_table.item(row, 7).setText(str(act_value))

                    else:
                        print("Warunek nie spełniony")
                except requests.exceptions.RequestException as e:
                    print(f"Błąd podczas pobierania danych dla Zonda: {e}")
                except Exception as e:
                    print(f"Błąd przetwarzania danych dla Zonda: {e}")

            elif gielda == "Bybit":
                try:
                    session = HTTP(testnet=True)
                    response = session.get_tickers(
                        category="spot",
                        symbol=para,
                    )
                    lowest_ask = response['result']['list'][0]['lastPrice']
                    success = True  # Operacja pobierania danych zakończona sukcesem
                    print(f"Bybit{lowest_ask}")
                    if success and lowest_ask is not None:
                        self.stock_table.item(row, 7).setText(str(lowest_ask))
                except Exception as e:
                    print(f"Błąd podczas pobierania danych dla Bybit: {e}")
           

            elif gielda == "Binance":
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={para}"
                headers = {'content-type': 'application/json'}
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    lowest_ask = data.get('price')
                    success = True  # Operacja pobierania danych zakończona sukcesem
                    print(f"Binance{lowest_ask}")
                    if success and lowest_ask is not None:
                        self.stock_table.item(row, 7).setText(str(lowest_ask))
                except requests.exceptions.RequestException as e:
                    print(f"Błąd podczas pobierania danych z Binance: {e}")
                except Exception as e:
                    print(f"Błąd przetwarzania danych z Binance: {e}")

            # Aktualizuj dane w tabeli (kolumna 7 to "Aktualna Cena")
            # if success and lowest_ask is not None:
            #     self.stock_table.item(row, 7).setText(str(lowest_ask))
        for row in range(self.stock_table.rowCount()):
            # Pobierz informacje o giełdzie (kolumna 2 to "Giełda")
            count_item = self.stock_table.item(row, 4)
            price_now_item = self.stock_table.item(row, 7)
            if not count_item or not price_now_item:
                continue  
            count = count_item.text()
            price_now = price_now_item.text()
            print("xxxxxxxxxxxxxxxxxxxx")
            print(count)
            print(price_now)
            actual_price = float(count) * float(price_now)
            item = QTableWidgetItem(str(actual_price))
            self.stock_table.setItem(row, 8, item)
            success = False  # Zmienna śledząca sukces operacji pobierania danych
        if success:
            self.stock_table.item(row, 6).setText(str(act_price))
            self.stock_table.item(row, 7).setText(str(act_value))
            
            # Oblicz stosunek zysku do straty (Z/S) w procentach
            if float(count) != 0:
                profit_loss_ratio = ((act_value - float(count)) / float(count)) * 100
            else:
                profit_loss_ratio = 0.0

            # Formatuj Z/S jako procent z odpowiednim znakiem plus (+) lub minus (-)
            if profit_loss_ratio >= 0:
                formatted_profit_loss_ratio = "{:+.2f}%".format(profit_loss_ratio)
            else:
                formatted_profit_loss_ratio = "{:.2f}%".format(profit_loss_ratio)

            self.stock_table.item(row, 9).setText(formatted_profit_loss_ratio)

    
class EditPairsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow

    def initUi(self):
        layout = QGridLayout()

        # ComboBox z dostępnymi giełdami
        self.stock_combo = QComboBox()
        self.load_unique_exchanges()
        layout.addWidget(self.stock_combo, 0, 0)
        
        # Inicjalnie ustaw ComboBox na pierwszą giełdę
        self.stock_combo.setCurrentIndex(0)
        
        # Tabel par
        self.pair_table = QTableWidget()
        self.pair_table.setColumnCount(3)
        column_headres = ["Pary", "Giełda", "Pary"]
        self.pair_table.setHorizontalHeaderLabels(column_headres)
        self.pair_table.setColumnHidden(0, True)  # Indeks kolumny "ID" to 0
        self.pair_table.setStyleSheet("max-width: 200px;") 
        layout.addWidget(self.pair_table, 1, 0)

        self.load_data()
        # Przycisk Odśwież
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.clicked.connect(self.load_data)
        self.refresh_button.setStyleSheet("max-width: 100px;")
        layout.addWidget(self.refresh_button, 0, 1)

        # Formularz dodawania par
        self.pair_name_label = QLabel("Nazwa pary")
        self.pair_name_label.setStyleSheet("max-width: 100px;")
        self.pair_name = QLineEdit()
        self.pair_name.setStyleSheet("max-width: 200px;") 

        layout.addWidget(self.pair_name_label, 0, 2)
        layout.addWidget(self.pair_name, 0, 3)

        self.setLayout(layout)
        # Przycisk dodawania par
        self.pair_add_button = QPushButton("Dodaj parę")
        layout.addWidget(self.pair_add_button, 0, 4)
        self.pair_add_button.clicked.connect(self.add_pair)
        
   

        self.setLayout(layout)
    
    def add_pair(self):
        exchange = self.stock_combo.currentText()
        pair = self.pair_name.text()

        # Połącz z bazą danych
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Sprawdź, czy taka para już istnieje dla wybranej giełdy
        cursor.execute("""  SELECT COUNT(*) 
                            FROM stocks
                            INNER JOIN pairs ON stocks.id = pairs.stock_id 
                            WHERE stocks.name = ? AND pairs.name = ?""", (exchange, pair))
        count = cursor.fetchone()[0]

        if count == 0:
            # Jeśli para nie istnieje, dodaj ją do bazy danych
            cursor.execute("SELECT id FROM stocks WHERE name=?", (exchange,))
            
            result = cursor.fetchone()
            if result:
                stock_id = result[0]  # Pobierz pierwszy element z tuple jako stock_id
                cursor.execute("INSERT INTO pairs (stock_id, name) VALUES (?, ?)", (stock_id, pair))
                db.commit()
                db.close()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText("Para została dodana.")
                msg.setWindowTitle("Jest Git!")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                self.pair_name.clear()
                self.load_data()  # Odśwież tabelę po dodaniu pary
            else:
                db.close()
        else:
            db.close()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Para już istnieje dla wybranej giełdy.")
            msg.setWindowTitle("Błąd")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    
    
    def load_data(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()
        cursor.execute("SELECT stocks.name AS name, pairs.name AS pair FROM pairs JOIN stocks ON stock_id = stocks.id")
        data = cursor.fetchall()
        db.close()
        # Wstaw dane do tabeli
        self.pair_table.setRowCount(len(data))
        
        for row_index, row_data in enumerate(data):
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.pair_table.setItem(row_index, col_index, item)

    def load_unique_exchanges(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Zapytanie SQL
        cursor.execute("SELECT DISTINCT name FROM stocks")
        exchanges = cursor.fetchall()

        # Dodawanie nazw do comboboxa
        for exchange  in exchanges:
            self.stock_combo.addItem(exchange[0])

        db.close()


    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())