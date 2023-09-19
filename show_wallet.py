import sys, sqlite3, requests, logging
from PyQt6.QtWidgets import QApplication,QFormLayout, QHBoxLayout, QMessageBox, QPushButton, QDialog, QDoubleSpinBox, QDateEdit, QMainWindow, QLineEdit, QTextEdit, QToolBar, QStatusBar, QWidget, QLabel, QVBoxLayout, QComboBox, QGridLayout, QStackedWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize, Qt, QDate

from db import db_create_main, db_create_pairs
db_create_main()
db_create_pairs()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setWindowTitle('KPiR by Jariloo')
        self.setGeometry(100, 100, 800, 600)
        
        # Tworzenie przycisków w głównym oknie
        self.table_button = QPushButton('Tabela')
        self.form_button = QPushButton('Formularz')
        self.pairs_button = QPushButton('Pary')
        self.table_button.clicked.connect(self.show_main)
        self.form_button.clicked.connect(self.show_stock)
        self.pairs_button.clicked.connect(self.show_pairs)

        # Tworzenie paska narzędziowego z przyciskami
        toolbar = self.addToolBar('Toolbar')
        toolbar.addWidget(self.table_button)
        toolbar.addWidget(self.form_button)
        toolbar.addWidget(self.pairs_button)
        
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
        layout = QVBoxLayout()

        # Pole z datą i kalendarzem
        label = QLabel("Data:")
        self.date_edit = QDateEdit()
        # Umożliwia otwarcie kalendarza po kliknięciu w pole
        self.date_edit.setCalendarPopup(True) 
        # Ustaw dzisiejszą datę jako początkową
        today = QDate.currentDate()
        self.date_edit.setDate(today)
        self.date_edit.setStyleSheet("max-width: 200px;")  # Ustaw maksymalną szerokość na 200 pikseli
        layout.addWidget(label)
        layout.addWidget(self.date_edit)


        # Drugie pole jako ComboBox(Giełda)
        label = QLabel("Giełda:")
        self.exchange_combo = QComboBox()
        self.load_unique_exchanges()
        self.exchange_combo.setStyleSheet("max-width: 200px;")
        layout.addWidget(label)
        layout.addWidget(self.exchange_combo)
       
       # Pole tekstowe 3(Para)
        label = QLabel("Para:")
        self.text_field3 = QComboBox()  # Zmieniamy na QComboBox zamiast QLineEdit
        self.text_field3.setStyleSheet("max-width: 200px;")
        layout.addWidget(label)
        layout.addWidget(self.text_field3)
        # Słownik z parami walutowymi dla różnych giełd
        self.pairs_by_exchange = {
            "Zonda": ["BTC-USD", "ETH-USD", "LTC-USD"],
            "Bybit": ["BTC-USD", "ETH-USD"],
            "Binance": ["BTC-USDT", "ETH-USDT", "BNB-USDT"],
        }

        # Po zmianie giełdy wybieramy odpowiednie pary walutowe
        self.exchange_combo.currentIndexChanged.connect(self.update_currency_pairs)
        self.update_currency_pairs()  # Inicjalizacja listy par walutowych

        # Pole liczbowe zmiennoprzecinkowe(Ilość)
        label = QLabel("Ilość:")
        self.stock_count = QDoubleSpinBox()
        self.stock_count.setRange(-9999.99, 9999999999999999.99999)  # Ustaw zakres na -9999.99 do 9999.99 (lub odpowiednio)
        self.stock_count.setStyleSheet("max-width: 200px;")
        layout.addWidget(label)
        layout.addWidget(self.stock_count)

        # Pole liczbowe zmiennoprzecinkowe(Cena)
        label = QLabel("Cena:")
        self.stock_price = QDoubleSpinBox()
        self.stock_count.setRange(-9999.99, 9999999999999999.99999)
        self.stock_price.setStyleSheet("max-width: 200px;")
        layout.addWidget(label)
        layout.addWidget(self.stock_price)

        # Pole liczbowe zmiennoprzecinkowe(Warrtość)
        label = QLabel("Wartość zakupu:")
        self.stock_value = QDoubleSpinBox()
        self.stock_count.setRange(-9999.99, 9999999999999999.99999)
        self.stock_value.setStyleSheet("max-width: 200px;")
        layout.addWidget(label)
        layout.addWidget(self.stock_value)


        # Przycisk "Dodaj" do dodawania danych do bazy
        self.add_button = QPushButton("Dodaj")
        self.add_button.clicked.connect(self.add_data_to_db)
        layout.addWidget(self.add_button)

        
        self.setLayout(layout)
    def load_unique_exchanges(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Zapytanie SQL
        cursor.execute("SELECT DISTINCT exchange FROM pairs")
        exchanges = cursor.fetchall()

        # Dodawanie nazw do comboboxa
        for exchange  in exchanges:
            self.exchange_combo.addItem(exchange[0])

        db.close()
    def update_currency_pairs(self):
        selected_exchange = self.exchange_combo.currentText()
        pairs = self.pairs_by_exchange.get(selected_exchange, [])
        self.text_field3.clear()  # Wyczyść pole "Para"
        self.text_field3.addItems(pairs)  # Dodaj dostępne pary walutowe do pola "Para"

    def add_data_to_db(self):
        
        # Pobierz dane z pól formularza
        data_zakupu = self.date_edit.date().toString("yyyy-MM-dd")
     
        gielda = self.exchange_combo.currentText()
        para = self.text_field3.text()
        ilosc = self.stock_count.value()
        cena_zakupu = self.stock_price.value()
        wartosc_zakupu = self.stock_value.value()  # Możesz pobrać wartość z pola stock_value
        aktualna_cena = None
        # Sprawdzanie giełdy
        selected_option = self.exchange_combo.currentText()
        if selected_option == "Zonda":
            url = f"https://api.zondacrypto.exchange/rest/trading/ticker/{para}"
            headers = {'content-type': 'application/json'}
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                lowest_ask = data.get('ticker', {}).get('lowestAsk')
                
                if lowest_ask:
                    # Sprawdź, czy wartość lowest_ask jest liczbą
                    try:
                        aktualna_cena = float(lowest_ask)
                    except ValueError:
                        aktualna_cena = None
            except:
                pass
                    
        elif selected_option == "Bybit":
            # Wybrano opcję "Bybit"
            pass
        elif selected_option == "Binance":
            # Wybrano opcję "Binance"
            pass
        

        # Połącz z bazą danych
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Wstaw dane do tabeli
        cursor.execute("INSERT INTO inwestycje (data_zakupu, gielda, para, ilosc, cena_zakupu, wartosc_zakupu, aktualna_cena) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (data_zakupu, gielda, para, ilosc, cena_zakupu, wartosc_zakupu, aktualna_cena))

        # Zatwierdź zmiany i zamknij połączenie z bazą danych
        db.commit()
        db.close()

        # Opcjonalnie, wyczyść pola formularza po dodaniu danych
        self.date_edit.setDate(QDate.currentDate())
        self.comboBox.setCurrentIndex(0)
        self.text_field3.clear()
        self.stock_count.setValue(0.0)
        self.stock_price.setValue(0.0)
        self.stock_value.setValue(0.0)
        if self.main_window:
            self.main_window.show_stock()

class StockTableView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow
        

    def initUi(self):
        # Tworzenie tabeli do wyświetlania danych
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(8)  # Liczba kolumn w tabeli (zgodna z liczbą kolumn w bazie danych)

        # Ustaw nazwy kolumn w tabeli
        column_headers = ["ID", "Data Zakupu", "Giełda", "Para", "Ilość", "Cena Zakupu", "Wartość Zakupu", "Aktualna Cena"]
        self.stock_table.setHorizontalHeaderLabels(column_headers)
        # Ukryj kolumnę "ID"
        self.stock_table.setColumnHidden(0, True)  # Indeks kolumny "ID" to 0
        
        

        layout = QVBoxLayout()
        layout.addWidget(self.stock_table)
        self.setLayout(layout)

        # Przycisk odświeżania
        refresh_button = QPushButton('Odśwież')
        refresh_button.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_button)

        # Wczytaj dane do tabeli
        self.load_stock_data()
    def refresh_data(self):
        for row in range(self.stock_table.rowCount()):
            # Sprawdź, czy giełda to "Zonda" (kolumna 2 to "Giełda")
            gielda_item = self.stock_table.item(row, 2)
            if gielda_item and gielda_item.text() == "Zonda":
                # Jeśli tak, pobierz parę walutową (kolumna 3 to "Para")
                para_item = self.stock_table.item(row, 3)
                if para_item:
                    para = para_item.text()
                    print(para)

                    # Tutaj wykonujesz request HTTP dla pary walutowej "Zonda"
                    url = f"https://api.zondacrypto.exchange/rest/trading/ticker/{para}"
                    headers = {'content-type': 'application/json'}
                    try:
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        data = response.json()
                        lowest_ask = data.get('ticker', {}).get('lowestAsk')

                        # Aktualizuj dane w tabeli (kolumna 7 to "Aktualna Cena")
                        if lowest_ask is not None:
                            self.stock_table.item(row, 7).setText(str(lowest_ask))
                    except requests.exceptions.RequestException as e:
                        print(f"Błąd podczas pobierania danych: {e}")
                    except Exception as e:
                        print(f"Błąd przetwarzania danych: {e}")
    def load_stock_data(self):
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM inwestycje")
        data = cursor.fetchall()
        db.close()

        # Wstaw dane do tabeli
        self.stock_table.setRowCount(len(data))
        for row_index, row_data in enumerate(data):
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.stock_table.setItem(row_index, col_index, item)
class EditPairsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Przekazywanie referencji do MainWindow

    def initUi(self):
        layout = QGridLayout()

        # ComboBox z dostępnymi giełdami
        self.exchange_combo = QComboBox()
        self.load_unique_exchanges()
        layout.addWidget(self.exchange_combo, 0, 0)
        
        # Inicjalnie ustaw ComboBox na pierwszą giełdę
        self.exchange_combo.setCurrentIndex(0)
        
        # Tabel par
        self.pair_table = QTableWidget()
        self.pair_table.setColumnCount(3)
        column_headres = ["Pary", "Pary", "Pary"]
        self.pair_table.setHorizontalHeaderLabels(column_headres)
        self.pair_table.setColumnHidden(0, True)  # Indeks kolumny "ID" to 0
        self.pair_table.setColumnHidden(1, True)  # Indeks kolumny "ID" to 0
        layout.addWidget(self.pair_table, 1, 0)

        self.load_data()
        # Przycisk Odśwież
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_button, 0, 1)

        # Formularz dodawania par
        self.pair_name_label = QLabel("Nazwa pary")
        self.pair_name = QLineEdit()
        layout.addWidget(self.pair_name_label, 1, 1)
        layout.addWidget(self.pair_name, 1, 2)

        self.setLayout(layout)
        # Przycisk dodawania par
        self.pair_add_button = QPushButton("Dodaj parę")
        layout.addWidget(self.pair_add_button, 2, 1)
        self.pair_add_button.clicked.connect(self.add_pair)
        
   

        self.setLayout(layout)
    
    def add_pair(self):
        exchange = self.exchange_combo.currentText()
        pair = self.pair_name.text()

        # Połącz z bazą danych
        db = sqlite3.connect("simple.db")
        cursor = db.cursor()

        # Sprawdź, czy taka para już istnieje dla wybranej giełdy
        cursor.execute("SELECT COUNT(*) FROM pairs WHERE exchange = ? AND pairs = ?", (exchange, pair))
        count = cursor.fetchone()[0]

        if count == 0:
            # Jeśli para nie istnieje, dodaj ją do bazy danych
            cursor.execute("INSERT INTO pairs (exchange, pairs) VALUES (?, ?)", (exchange, pair))
            db.commit()
            db.close()
            self.load_data()  # Odśwież tabelę po dodaniu pary
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
        cursor.execute("SELECT * FROM pairs")
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
        cursor.execute("SELECT DISTINCT exchange FROM pairs")
        exchanges = cursor.fetchall()

        # Dodawanie nazw do comboboxa
        for exchange  in exchanges:
            self.exchange_combo.addItem(exchange[0])

        db.close()


    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())