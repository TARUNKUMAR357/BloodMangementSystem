
import tkinter as tk
from tkinter import ttk, messagebox

from config.database import get_connection


class BloodStockManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Blood Stock Management")
        self.root.geometry("900x600")
        self.root.configure(bg="#F4F6F9")

        self.build_ui()
        self.load_stock()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#9F1D25", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="BLOOD STOCK MANAGEMENT",
            font=("Arial", 20, "bold"),
            bg="#9F1D25",
            fg="white"
        ).pack(pady=15)

        summary = ttk.LabelFrame(
            self.root, text="Stock Summary", padding=15
        )
        summary.pack(fill="x", padx=15, pady=12)

        ttk.Label(
            summary, text="Total Available Stock:"
        ).grid(row=0, column=0, padx=10)

        self.total_label = ttk.Label(
            summary, text="Loading...",
            font=("Arial", 14, "bold")
        )
        self.total_label.grid(row=0, column=1, padx=10)

        ttk.Label(
            summary, text="Blood Groups With Zero Stock:"
        ).grid(row=0, column=2, padx=10)

        self.zero_label = ttk.Label(
            summary, text="Loading...",
            font=("Arial", 14, "bold")
        )
        self.zero_label.grid(row=0, column=3, padx=10)

        filters = ttk.Frame(self.root)
        filters.pack(fill="x", padx=15, pady=5)

        ttk.Label(
            filters, text="Filter by blood group:"
        ).pack(side="left", padx=5)

        self.group_filter = ttk.Combobox(
            filters,
            values=[
                "All", "A+", "A-", "B+", "B-",
                "AB+", "AB-", "O+", "O-"
            ],
            state="readonly",
            width=12
        )
        self.group_filter.set("All")
        self.group_filter.pack(side="left", padx=5)

        ttk.Button(
            filters, text="Apply Filter",
            command=self.load_stock
        ).pack(side="left", padx=5)

        ttk.Button(
            filters, text="Refresh",
            command=self.load_stock
        ).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True,
            padx=15, pady=12
        )

        columns = (
            "group", "description", "quantity", "status", "updated"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "group": "Blood Group",
            "description": "Description",
            "quantity": "Available Quantity (mL)",
            "status": "Availability",
            "updated": "Last Updated"
        }

        widths = {
            "group": 100,
            "description": 180,
            "quantity": 210,
            "status": 150,
            "updated": 200
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(
                col, width=widths[col], anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(
            self.root,
            text="Stock quantities are updated through approved donations "
                 "and blood issuance.",
            font=("Arial", 10),
            bg="#F4F6F9",
            fg="#555555"
        ).pack(pady=8)

    def load_stock(self):
        selected_group = self.group_filter.get()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT bg.blood_group_code,
                               bg.description,
                               bs.available_quantity_ml,
                               bs.last_updated
                        FROM blood_group bg
                        JOIN blood_stock bs
                          ON bg.blood_group_code =
                             bs.blood_group_code
                        WHERE (%s = 'All'
                               OR bg.blood_group_code = %s)
                        ORDER BY bg.blood_group_code
                        """,
                        (selected_group, selected_group)
                    )
                    rows = cur.fetchall()

                    cur.execute(
                        """
                        SELECT
                            COALESCE(SUM(available_quantity_ml), 0),
                            COUNT(*) FILTER (
                                WHERE available_quantity_ml = 0
                            )
                        FROM blood_stock
                        """
                    )
                    total, zero_count = cur.fetchone()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for group, description, quantity, updated in rows:
                status = (
                    "Out of Stock"
                    if quantity == 0
                    else "Available"
                )

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        group,
                        description,
                        quantity,
                        status,
                        updated.strftime("%Y-%m-%d %H:%M")
                        if updated else ""
                    )
                )

            self.total_label.config(
                text=f"{total:,} mL"
            )
            self.zero_label.config(text=str(zero_count))

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load blood stock:\n{error}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = BloodStockManagement(root)
    root.mainloop()
