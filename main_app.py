import sys
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QComboBox, QTextEdit, QListWidgetItem, QScrollArea, QGroupBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Note: Since Flask is running with a self-signed certificate, we use https and disable verification.
API_BASE = "https://127.0.0.1:5000"

class OrderManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logo Order Manager - Desktop")
        self.setGeometry(100, 100, 1000, 600)
        self.layout = QHBoxLayout(self)
        
        # Left side: Order list
        self.orderList = QListWidget()
        self.orderList.itemClicked.connect(self.show_order_details)
        self.layout.addWidget(self.orderList, 3)
        
        # Right side: Order details
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
        
        self.detailsLayout.addWidget(self.nameLabel)
        self.detailsLayout.addWidget(QLabel("Status:"))
        self.detailsLayout.addWidget(self.statusDropdown)
        self.detailsLayout.addWidget(self.updateBtn)
        self.detailsLayout.addWidget(QLabel("Details:"))
        self.detailsLayout.addWidget(self.orderDetails)
        self.detailsLayout.addWidget(QLabel("Images:"))
        self.detailsLayout.addWidget(self.imageContainer)
        self.detailsLayout.addWidget(self.refreshBtn)
        self.detailsLayout.addWidget(self.openFolderBtn)
        
        self.detailsGroup.setLayout(self.detailsLayout)
        self.layout.addWidget(self.detailsGroup, 7)
        
        self.load_orders()
    
    def load_orders(self):
        self.orderList.clear()
        try:
            resp = requests.get(f"{API_BASE}/api/orders", verify=False)
            orders = resp.json()
            for oid, order in orders.items():
                item = QListWidgetItem(f"Order #{oid} - {order['name']}")
                item.setData(Qt.ItemDataRole.UserRole, int(oid))
                self.orderList.addItem(item)
        except Exception as e:
            print("Error loading orders:", e)
    
    def show_order_details(self, item):
        oid = item.data(Qt.ItemDataRole.UserRole)
        try:
            resp = requests.get(f"{API_BASE}/api/order/{oid}", verify=False)
            order = resp.json()
            self.nameLabel.setText(f"Customer: {order.get('name', '')}")
            self.statusDropdown.setCurrentText(order.get('status', 'pending payment'))
            self.orderDetails.setText(order.get('details', ''))
            
            container = QWidget()
            vbox = QVBoxLayout()
            for img in order.get('filenames', []):
                try:
                    # Images are saved in static/uploads/order_<oid>/filename
                    img_resp = requests.get(f"{API_BASE}/static/uploads/order_{oid}/{img}", verify=False)
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_resp.content)
                    lbl = QLabel()
                    lbl.setPixmap(pixmap.scaledToWidth(150))
                    vbox.addWidget(lbl)
                except Exception as e:
                    print(f"Error loading image {img}:", e)
            container.setLayout(vbox)
            self.imageContainer.setWidget(container)
            
            self.current_order_id = oid
        except Exception as e:
            print("Error showing order details:", e)
    
    def update_status(self):
        if not hasattr(self, 'current_order_id'):
            return
        new_status = self.statusDropdown.currentText()
        try:
            resp = requests.post(f"{API_BASE}/api/order/{self.current_order_id}/status",
                                 json={"status": new_status}, verify=False)
            if resp.status_code == 200:
                self.load_orders()
            else:
                print("Failed to update status.")
        except Exception as e:
            print("Error updating status:", e)
    
    def open_attachments_folder(self):
        if not hasattr(self, 'current_order_id'):
            return
        folder = os.path.join(os.getcwd(), "static", "uploads", f"order_{self.current_order_id}")
        if os.path.exists(folder):
            try:
                os.startfile(folder)  # Works on Windows; adjust for other OS as needed.
            except Exception as e:
                print("Error opening folder:", e)
        else:
            print("Attachments folder does not exist.")

if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    window = OrderManager()
    window.show()
    sys.exit(app_qt.exec())
