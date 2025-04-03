import os, logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
orders = {}
order_counter = 1

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def order_form():
    global order_counter
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            facebook = request.form.get('facebook')
            email = request.form.get('email')
            order_type = request.form.get('order_type')
            details = request.form.get('details')
            files = request.files.getlist('images')
            order_id = order_counter
            folder_name = f"order_{order_id}_{order_type}"
            order_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(order_folder, exist_ok=True)
            saved_files = []
            for f in files:
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(order_folder, filename))
                    saved_files.append(filename)
            orders[order_id] = {
                'name': name,
                'facebook': facebook,
                'email': email,
                'order_type': order_type,
                'details': details,
                'filenames': saved_files,
                'status': 'pending payment'
            }
            logging.info(f"Created order #{order_id} for {name} ({email}) with type {order_type}")
            order_counter += 1
            return redirect(url_for('payment_page', order_id=order_id))
        except Exception as e:
            logging.exception("Error creating order")
            return f"Error: {str(e)}", 500
    return render_template('order_form.html')

@app.route('/payment/<int:order_id>')
def payment_page(order_id):
    order = orders.get(order_id)
    if not order:
        return "Order not found", 404
    paypal_client_id = "Ac4XnyVS6sN7WZTR6iHuS2wWTJl4dYZs5ud9etjyrpoS5lhdmKMBXmCtxUA9qBc2cCKtUo8_LOfrjqhB"
    return render_template('payment_page.html', order_id=order_id, amount="10.00", paypal_client_id=paypal_client_id)

@app.route('/simulate-payment-success/<int:order_id>')
def simulate_payment_success(order_id):
    if order_id not in orders:
        return "Order not found", 404
    orders[order_id]['status'] = 'paid'
    logging.info(f"Order #{order_id} marked as paid (simulated).")
    return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/api/orders', methods=['GET'])
def api_orders():
    return jsonify(orders)

@app.route('/api/order/<int:order_id>', methods=['GET'])
def api_order(order_id):
    if order_id not in orders:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(orders[order_id])

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def api_update_status(order_id):
    if order_id not in orders:
        return jsonify({'error': 'Order not found'}), 404
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'No status provided'}), 400
    orders[order_id]['status'] = new_status
    logging.info(f"Order #{order_id} status updated to {new_status}")
    return jsonify({'success': True})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
