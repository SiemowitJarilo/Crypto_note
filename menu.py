def menu():
    print('''
    +-------------------+
    |      Menu         |
    +-------------------+
    |1. Portfel         |
    |2. Zakupy          |
    |3. Daniny          |
    |4. Inwestycje      |
    |0. Zamknij program |
    +-------------------+ 
    ''')

      def fetch_data_from_sqlite(self):
        # Pobieranie danych z bazy SQLite
        db = sqlite3.connect("simple.db")
        query = "SELECT data_zakupu, SUM(wartosc_zakupu) as wartosc_majatku FROM inwestycje GROUP BY data_zakupu"
        df = pd.read_sql_query(query, db)
        print(df)
        db.close()

        # Konwersja kolumny 'data_zakupu' na typ daty
        df['data_zakupu'] = pd.to_datetime(df['data_zakupu'])
    
        # Sortowanie danych po dacie
        df = df.sort_values(by='data_zakupu')

        # Ustawienie kolumny 'data_zakupu' jako indeksu
        df.set_index('data_zakupu', inplace=True)

        # Zwracanie danych jako list
        data_line = df.index.tolist()
        
        values_line = df['wartosc_majatku'].tolist()
        
        return data_line, values_line
    def generate_line_chart(self, data_line, values_line):
        # Rysowanie wykresu liniowego
        self.ax.plot(data_line, values_line, marker='o', linestyle='-')
        
        # Dostosowanie osi czasu
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()  # Dostosowanie formatu dat na osi X

        # Dostosowanie osi Y do wartości pieniężnych
        self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: str(x)))


        self.ax.set_xlabel('Data Zakupu')
        self.ax.set_ylabel('Wartość Majątku ($)')
        self.ax.set_title('Wykres Liniowy Majątku na Przestrzeni Czasu')

        # Odświeżenie wykresu
        self.canvas_line.draw()
        self.canvas_line.draw_idle()