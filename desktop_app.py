import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QHBoxLayout, QComboBox, QTextEdit, QListWidgetItem, QScrollArea, QGroupBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

API_BASE = "http://127.0.0.1:5000"

class OrderManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logo Order Manager")
        self.setGeometry(100, 100, 1000, 600)
        
        # Main layout: Order list on the left, details on the right
        self.layout = QHBoxLayout(self)
        self.orderList = QListWidget()
        self.orderList.itemClicked.connect(self.display_order)
        self.layout.addWidget(self.orderList, 3)
        
        # Right panel: Order details
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
        
        self.detailsLayout.addWidget(self.nameLabel)
        self.detailsLayout.addWidget(QLabel("Status:"))
        self.detailsLayout.addWidget(self.statusDropdown)
        self.detailsLayout.addWidget(self.updateBtn)
        self.detailsLayout.addWidget(QLabel("Details:"))
        self.detailsLayout.addWidget(self.orderDetails)
        self.detailsLayout.addWidget(QLabel("Images:"))
        self.detailsLayout.addWidget(self.imageContainer)
        
        self.detailsGroup.setLayout(self.detailsLayout)
        self.layout.addWidget(self.detailsGroup, 7)
        
        self.load_orders()
    
    # Load all orders from the backend
    def load_orders(self):
        self.orderList.clear()
        try:
            response = requests.get(f"{API_BASE}/api/orders")
            self.orders = response.json()
            for oid, data in self.orders.items():
                item = QListWidgetItem(f"Order #{oid} - {data['name']}")
                item.setData(Qt.ItemDataRole.UserRole, int(oid))
                self.orderList.addItem(item)
        except Exception as e:
            print("Error loading orders:", e)
    
    # Display details for the selected order
    def display_order(self, item):
        oid = item.data(Qt.ItemDataRole.UserRole)
        try:
            response = requests.get(f"{API_BASE}/api/order/{oid}")
            order = response.json()
        except Exception as e:
            print("Error retrieving order:", e)
            return
        
        self.nameLabel.setText(f"Customer: {order.get('name', '')}")
        self.statusDropdown.setCurrentText(order.get('status', 'pending payment'))
        self.orderDetails.setText(order.get('details', ''))
        
        # Load images for the order
        containerWidget = QWidget()
        imageLayout = QVBoxLayout()
        for img in order.get('filenames', []):
            try:
                img_response = requests.get(f"{API_BASE}/static/uploads/{img}")
                pixmap = QPixmap()
                pixmap.loadFromData(img_response.content)
                img_label = QLabel()
                img_label.setPixmap(pixmap.scaledToWidth(150))
                imageLayout.addWidget(img_label)
            except Exception as e:
                print("Error loading image", img, e)
        containerWidget.setLayout(imageLayout)
        self.imageContainer.setWidget(containerWidget)
        
        self.current_order_id = oid
    
    # Update the order status via the API
    def update_status(self):
        new_status = self.statusDropdown.currentText()
        try:
            response = requests.post(f"{API_BASE}/api/order/{self.current_order_id}/status",
                                     json={"status": new_status})
            if response.status_code == 200:
                self.load_orders()
        except Exception as e:
            print("Error updating status:", e)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OrderManager()
    window.show()
    sys.exit(app.exec())
