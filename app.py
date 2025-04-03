import os, logging, json, requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configurable price – set via environment variable PRICE or default to "25.00"
PRICE = os.environ.get("PRICE", "2.50")

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    facebook = db.Column(db.String(120))
    email = db.Column(db.String(120), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=False)
    filenames = db.Column(db.Text)  # JSON list of filenames
    status = db.Column(db.String(20), default='pending payment')
    paypal_order_id = db.Column(db.String(120))
    verified = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'facebook': self.facebook,
            'email': self.email,
            'order_type': self.order_type,
            'details': self.details,
            'filenames': json.loads(self.filenames) if self.filenames else [],
            'status': self.status,
            'paypal_order_id': self.paypal_order_id,
            'verified': self.verified
        }

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            facebook = request.form.get('facebook')
            email = request.form.get('email')
            order_type = request.form.get('order_type')
            details = request.form.get('details')
            files = request.files.getlist('images')
            order = Order(name=name, facebook=facebook, email=email,
                          order_type=order_type, details=details,
                          filenames=json.dumps([]), status='pending payment')
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            folder_name = f"order_{order_id}_{order_type}"
            order_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(order_folder, exist_ok=True)
            saved_files = []
            for f in files:
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(order_folder, filename))
                    saved_files.append(filename)
            order.filenames = json.dumps(saved_files)
            db.session.commit()
            logging.info(f"Created order #{order_id} for {name}")
            return redirect(url_for('payment_page', order_id=order_id))
        except Exception as e:
            logging.exception("Error creating order")
            return f"Error: {str(e)}", 500
    return render_template('order_form.html')

@app.route('/payment/<int:order_id>')
def payment_page(order_id):
    order = Order.query.get(order_id)
    if not order:
        return "Order not found", 404
    # Replace with your live PayPal client ID
    paypal_client_id = "Ac4XnyVS6sN7WZTR6iHuS2wWTJl4dYZs5ud9etjyrpoS5lhdmKMBXmCtxUA9qBc2cCKtUo8_LOfrjqhB"
    return render_template('payment_page.html', order_id=order_id, amount=PRICE, paypal_client_id=paypal_client_id)

@app.route('/capture-payment/<int:order_id>', methods=['POST'])
def capture_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    # In production, verify the capture using PayPal’s API with your secret
    order.status = 'paid'
    order.paypal_order_id = data.get('id', '')
    order.verified = True
    db.session.commit()
    logging.info(f"Order #{order_id} captured with PayPal ID {order.paypal_order_id}")
    return jsonify({'success': True})

@app.route('/verify-payment/<int:order_id>', methods=['POST'])
def verify_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    order.verified = (order.status == 'paid')
    db.session.commit()
    return jsonify({'verified': order.verified})

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/api/orders', methods=['GET'])
def api_orders():
    orders = Order.query.all()
    orders_dict = {order.id: order.to_dict() for order in orders}
    return jsonify(orders_dict)

@app.route('/api/order/<int:order_id>', methods=['GET'])
def api_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order.to_dict())

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def api_update_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'No status provided'}), 400
    order.status = new_status
    db.session.commit()
    logging.info(f"Order #{order_id} status updated to {new_status}")
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
