# main_app.py
import sys, os, requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QComboBox, QTextEdit, QListWidgetItem, QScrollArea, QGroupBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

API_BASE = "https://logowebapp.onrender.com"

class OrderManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logo Order Manager - Desktop")
        self.setGeometry(100, 100, 1000, 600)
        self.layout = QHBoxLayout(self)
        self.orderList = QListWidget()
        self.orderList.itemClicked.connect(self.show_order_details)
        self.layout.addWidget(self.orderList, 3)
        self.detailsGroup = QGroupBox("Order Details")
        self.detailsLayout = QVBoxLayout()
        self.nameLabel = QLabel("Customer:")
        self.statusDropdown = QComboBox()
        self.statusDropdown.addItems(["pending payment", "paid", "in progress", "complete"])
        self.updateBtn = QPushButton("Update Status")
        self.updateBtn.clicked.connect(self.update_status)
        self.orderDetails = QTextEdit()
        self.orderDetails.setReadOnly(True)
        self.imageContainer = QScrollArea()
        self.imageContainer.setWidgetResizable(True)
        self.refreshBtn = QPushButton("Refresh Orders")
        self.refreshBtn.clicked.connect(self.load_orders)
        self.openFolderBtn = QPushButton("Open Attachments Folder")
        self.openFolderBtn.clicked.connect(self.open_attachments_folder)
        self.downloadBtn = QPushButton("Download All Orders")
        self.downloadBtn.clicked.connect(self.download_all_orders)
        for w in [self.nameLabel, QLabel("Status:"), self.statusDropdown, self.updateBtn,
                  QLabel("Details:"), self.orderDetails, QLabel("Images:"), self.imageContainer,
                  self.refreshBtn, self.openFolderBtn, self.downloadBtn]:
            self.detailsLayout.addWidget(w)
        self.detailsGroup.setLayout(self.detailsLayout)
        self.layout.addWidget(self.detailsGroup, 7)
        self.load_orders()

    def load_orders(self):
        self.orderList.clear()
        try:
            resp = requests.get(f"{API_BASE}/api/orders")
            self.orders = resp.json()
            for oid, order in self.orders.items():
                item = QListWidgetItem(f"Order #{oid} - {order['name']}")
                item.setData(Qt.ItemDataRole.UserRole, int(oid))
                self.orderList.addItem(item)
        except Exception as e:
            print("Error loading orders:", e)

    def show_order_details(self, item):
        oid = item.data(Qt.ItemDataRole.UserRole)
        try:
            resp = requests.get(f"{API_BASE}/api/order/{oid}")
            order = resp.json()
            self.current_order = order
            self.current_order_id = oid
            self.nameLabel.setText(f"Customer: {order.get('name', '')}")
            self.statusDropdown.setCurrentText(order.get('status', 'pending payment'))
            self.orderDetails.setText(order.get('details', ''))
            container, vbox = QWidget(), QVBoxLayout()
            for img in order.get('filenames', []):
                try:
                    img_url = f"{API_BASE}/static/uploads/order_{oid}_{order.get('order_type')}/{img}"
                    r = requests.get(img_url)
                    if r.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(r.content)
                        lbl = QLabel()
                        lbl.setPixmap(pixmap.scaledToWidth(150))
                        vbox.addWidget(lbl)
                except Exception as e:
                    print("Image error:", img, e)
            container.setLayout(vbox)
            self.imageContainer.setWidget(container)
        except Exception as e:
            print("Error showing order:", e)

    def update_status(self):
        if not hasattr(self, 'current_order_id'): return
        try:
            new_status = self.statusDropdown.currentText()
            r = requests.post(f"{API_BASE}/api/order/{self.current_order_id}/status",
                              json={"status": new_status})
            if r.status_code == 200:
                self.load_orders()
        except Exception as e:
            print("Error updating status:", e)

    def open_attachments_folder(self):
        if not hasattr(self, 'current_order_id') or not hasattr(self, 'current_order'): return
        folder = os.path.join(os.getcwd(), "static", "uploads",
                              f"order_{self.current_order_id}_{self.current_order.get('order_type')}")
        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                print("Error opening folder:", e)
        else:
            print("Attachments folder does not exist.")

    def download_all_orders(self):
        try:
            r = requests.get(f"{API_BASE}/api/orders")
            orders = r.json()
            for oid, order in orders.items():
                folder = os.path.join(os.getcwd(), "orders", f"order_{oid}_{order.get('order_type')}")
                os.makedirs(folder, exist_ok=True)
                for filename in order.get("filenames", []):
                    url = f"{API_BASE}/static/uploads/order_{oid}_{order.get('order_type')}/{filename}"
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        with open(os.path.join(folder, filename), "wb") as f:
                            f.write(resp.content)
        except Exception as e:
            print("Download error:", e)

if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    window = OrderManager()
    window.show()
    sys.exit(app_qt.exec())
