# -*- coding: utf-8 -*-
"""Simple check tracking application using Tkinter and SQLite.

This program stores check information such as check number, bank, due date,
amount, payee company, and source company. The interface allows adding,
editing and deleting records. Data is persisted in a local SQLite database
named ``checks.db`` located in the same directory as this script.

Designed for Windows but also works on other platforms.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "checks.db"

class CheckDB:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_number TEXT NOT NULL,
                bank TEXT NOT NULL,
                due_date TEXT NOT NULL,
                amount REAL NOT NULL,
                payee_company TEXT NOT NULL,
                source_company TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_check(self, data):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO checks
            (check_number, bank, due_date, amount, payee_company, source_company)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        self.conn.commit()

    def update_check(self, check_id, data):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE checks
            SET check_number=?, bank=?, due_date=?, amount=?, payee_company=?, source_company=?
            WHERE id=?
            """,
            (*data, check_id),
        )
        self.conn.commit()

    def delete_check(self, check_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM checks WHERE id=?", (check_id,))
        self.conn.commit()

    def fetch_all(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, check_number, bank, due_date, amount, payee_company, source_company FROM checks"
        )
        return cur.fetchall()


def format_currency(value):
    return f"{value:,.2f}"  # simple currency formatting


class CheckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Çek Takip")
        self.geometry("800x400")
        self.resizable(True, True)
        self.db = CheckDB()
        self.selected_id = None
        self.create_widgets()
        self.populate_table()

    def create_widgets(self):
        # Form frame
        form_frame = ttk.Frame(self)
        form_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        labels = [
            "Çek No",
            "Banka",
            "Vade Tarihi (YYYY-MM-DD)",
            "Tutar",
            "Ödenecek Şirket",
            "Çeki Veren Şirket",
        ]
        self.entries = []
        for i, text in enumerate(labels):
            lbl = ttk.Label(form_frame, text=text)
            lbl.grid(row=0, column=i, padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=18)
            entry.grid(row=1, column=i, padx=5, pady=2)
            self.entries.append(entry)

        # Button frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="Ekle", command=self.add_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Güncelle", command=self.update_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Sil", command=self.delete_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Temizle", command=self.clear_form).pack(side=tk.LEFT, padx=2)

        # Table view
        columns = ("id", "check_number", "bank", "due_date", "amount", "payee", "source")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        headings = [
            "ID",
            "Çek No",
            "Banka",
            "Vade Tarihi",
            "Tutar",
            "Ödenecek Şirket",
            "Çeki Veren Şirket",
        ]
        for col, head in zip(columns, headings):
            self.tree.heading(col, text=head)
            if col == "id":
                self.tree.column(col, width=40, anchor=tk.CENTER)
            elif col == "amount":
                self.tree.column(col, width=80, anchor=tk.E)
            else:
                self.tree.column(col, width=110)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

    def populate_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for rec in self.db.fetch_all():
            # rec -> (id, check_number, bank, due_date, amount, payee_company, source_company)
            formatted = list(rec)
            formatted[4] = format_currency(formatted[4])
            self.tree.insert("", tk.END, values=formatted)

    def get_form_data(self):
        values = [e.get().strip() for e in self.entries]
        try:
            amount = float(values[3].replace(",", "."))
        except ValueError:
            messagebox.showerror("Hata", "Tutar sayısal olmalıdır")
            return None
        return (values[0], values[1], values[2], amount, values[4], values[5])

    def clear_form(self):
        for e in self.entries:
            e.delete(0, tk.END)
        self.selected_id = None

    def add_record(self):
        data = self.get_form_data()
        if data is None:
            return
        self.db.add_check(data)
        self.populate_table()
        self.clear_form()

    def update_record(self):
        if self.selected_id is None:
            messagebox.showinfo("Bilgi", "Güncellemek için bir kayıt seçin")
            return
        data = self.get_form_data()
        if data is None:
            return
        self.db.update_check(self.selected_id, data)
        self.populate_table()
        self.clear_form()

    def delete_record(self):
        if self.selected_id is None:
            messagebox.showinfo("Bilgi", "Silmek için bir kayıt seçin")
            return
        if messagebox.askyesno("Onay", "Seçili kaydı silmek istediğinize emin misiniz?"):
            self.db.delete_check(self.selected_id)
            self.populate_table()
            self.clear_form()

    def on_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        self.selected_id = int(values[0])
        for e, val in zip(self.entries, values[1:]):
            if e == self.entries[3]:  # amount column
                e.delete(0, tk.END)
                e.insert(0, val)
            else:
                e.delete(0, tk.END)
                e.insert(0, val)

if __name__ == "__main__":
    app = CheckApp()
    app.mainloop()
