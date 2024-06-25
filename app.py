from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import func, ForeignKey
import mercadopago
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.image import MIMEImage
import ssl
import smtplib
import uuid
import base64
import json
import time

app=Flask(__name__)
CORS(app, origins=['https://front-end-three-navy.vercel.app/', 'https://front-end-three-navy.vercel.app', 'https://www.front-end-three-navy.vercel.app/', 'https://www.qillari.vercel.app', "https://qillari.com/", "https://www.qillari.com/", "https://qillari.com", "https://www.qillari.com" ])
#CORS(app, resources={r"/*": {"origins": "*"}})


app.config['SECRET_KEY'] = "helloworld"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://u585862261_admin:Fiorellaydiego1.@srv1198.hstgr.io:3306/u585862261_datos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_size': 10,
    'max_overflow': 20 
}

app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

db = SQLAlchemy(app)

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.String(255), primary_key=True, nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    nombre_link = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text , nullable=False)
    tipo = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_sin_descuento = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    precio = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    fotos = db.Column(JSON, nullable=True)

    compras = db.relationship('Compras', backref='stock', lazy=True, passive_deletes=True)
    ventas = db.relationship('Ventas', backref='stock', lazy=True, passive_deletes=True)
    ganancia_perdida = db.relationship('GananciaPerdidaMensual', backref='stock', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'nombre_link': self.nombre_link,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'precio_sin_descuento': float(self.precio_sin_descuento),
            'precio': float(self.precio),
            'fotos': self.fotos,
            'url': self.url
        }

class Compras(db.Model):
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    productos = db.Column(JSON, nullable=True)
    estado = db.Column(db.String(255), nullable=False)
    total = db.Column(db.Numeric(43, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'fecha_hora': self.fecha_hora.isoformat(),
            'productos': self.productos,
            'estado': self.estado,
            'total': float(self.total)
        }    

class Ventas(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    productos = db.Column(JSON, nullable=True)
    estado = db.Column(db.String(255), nullable=False)
    total = db.Column(db.Numeric(43, 2))


    def to_dict(self):
        return {
            'id': self.id,
            'fecha_hora': self.fecha_hora.isoformat(),
            'productos': self.productos,
            'estado': self.estado,
            'total': float(self.total)
        }

class GananciaPerdidaMensual(db.Model):
    __tablename__ = 'ganancia_perdida_mensual'
    fecha = db.Column(db.String(7), nullable=False, primary_key=True)
    id_stock = db.Column(db.String(255), db.ForeignKey('stock.id', ondelete="CASCADE"), primary_key=True)
    compra_cantidad_total = db.Column(db.Numeric(32, 0))
    venta_cantidad_total = db.Column(db.Numeric(32, 0))
    total_compras = db.Column(db.Numeric(42, 2))
    total_ventas = db.Column(db.Numeric(42, 2))
    total = db.Column(db.Numeric(43, 2))

    def to_dict(self):
        return {
            'fecha': self.fecha,
            'id_stock': self.id_stock,
            'compra_cantidad_total': float(self.compra_cantidad_total),
            'venta_cantidad_total': float(self.venta_cantidad_total),
            'total_compras': float(self.total_compras),
            'total_ventas': float(self.total_ventas),
            'total': float(self.total)
        }

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorizations, true")
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS, POST, PATCH, DELETE")
    return response
    
@app.route('/', methods=['GET'])
def api_home():
    try:
        return {
            "success": True,
            "message": "Bienvenido"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
    
@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    try:
        # Obtener los datos de la solicitud en formato JSON
        data = request.json
        
        # Acceder a los campos necesarios para el pago
        transaction_amount = float(data.get("transaction_amount"))
        token = data.get("token")
        description = data.get("description")
        installments = int(data.get("installments"))
        payment_method_id = data.get("payment_method_id")
        email = data["payer"]["email"]
        identification_type = data["payer"]["identification"]["type"]
        identification_number = data["payer"]["identification"]["number"]
        street_name = data["payer"]["adress"]["street_name"]
        description1 = "joyas"

        # Realizar el pago utilizando los datos recibidos
        sdk = mercadopago.SDK("TEST-1829594313616516-032020-52f09f4ab48888239c2f4bcf7659d244-1446480329")

        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': str(uuid.uuid4())
        }

        payment_data = {
            "transaction_amount": transaction_amount,
            "token": token,
            "description": description1,
            "installments": installments,
            "payment_method_id": payment_method_id,
            "payer": {
                "email": email,
                "identification": {
                    "type": identification_type,
                    "number": identification_number
                },
            }
        }

        payment_response = sdk.payment().create(payment_data, request_options)
        payment = payment_response["response"]
        return jsonify(payment)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/venta-checkout', methods=['POST', 'GET'])
def venta_checkout():
    carrito = request.json.get("carrito")
    precio_total = request.json.get("precio_total")

    nueva_venta = Ventas(
        producto=carrito,
        total=precio_total
    )

    db.session.add(nueva_venta)
    
    ganancias_perdidas = GananciaPerdidaMensual.query.all()
    todos_los_producto = Stock.query.all()

    for productos in carrito:
        id = productos.get('id')
        precio = productos.get('price')
        cantidad = productos.get('totalamount')

        ganancia_perdida_encontrado = next((gp for gp in ganancias_perdidas if gp.id_stock == id), None)
        producto_stock = next((gp for gp in todos_los_producto if gp.id == id), None)

        ganancia_perdida_encontrado.venta_cantidad_total += cantidad
        ganancia_perdida_encontrado.total_ventas += (cantidad * precio)
        producto_stock.cantidad -= cantidad

    db.session.commit()


    return jsonify({'mensaje': 'se actualizada correctamente'}), 200

@app.route('/yape', methods=['POST'])
def yape():
    user = 'qillari120@gmail.com'
    app_password = 'qxklxfydjijymdcf'

    
    preciototal = request.json.get("preciototal")
    carrito = request.json.get("carrito")
    email = request.json.get("email")
    street_name = request.json.get("direccion")
    telefono = request.json.get("telefono")
    imagen = request.json.get("imagen_de_pago")
    image_data = base64.b64decode(imagen.split(',')[1])
    imagen_adjunta = MIMEImage(image_data, name="pago de yape")

    subject_vendedor = 'Se realizó la compra'
    subject_comprador = 'Realizate una compra'

    items_comprados = "\n".join([f"Producto: {item.get('nombre')}, Precio: {item.get('price')}, Cantidad: {item.get('totalamount')}" for item in carrito])

    # Primer correo
    em1 = MIMEMultipart()
    em1['From'] = "info@qillari.com"
    em1['To'] = "qillari120@gmail.com"
    em1['Subject'] = subject_vendedor
    content1 = ("Nuevo comprador\n"
            "Lo que ha comprado es:\n"
            "{}\n"
            "Su email es: {}\n"
            "Su calle es: {}\n"
            "su telefono es: {}\n"
            "El precio total es: {}").format(items_comprados, email, street_name, telefono, preciototal)
    em1.attach(MIMEText(content1, 'plain'))
    em1.attach(imagen_adjunta)

    # Segundo correo
    em2 = EmailMessage()
    em2['From'] = "info@qillari.com"
    em2['To'] = email
    em2['Subject'] = subject_comprador
    content2 = ("Su compra paso con exito\n"
            "Lo que has comprado es:\n"
            "{}\n"
            "El precio total es: {}\n"
            "Su producto llegara al dia siguiente, cualquier cosa contactenos por whatsapp o por este correo").format(items_comprados, preciototal)
    em2.set_content(content2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(user, app_password)
        smtp.sendmail( user, "qillari120@gmail.com", em1.as_string())
        smtp.sendmail( user, email, em2.as_string())
        


    return jsonify({
        'success': True,
        'message': 'Se enviaron los correos electrónicos'
    })

@app.route('/correo', methods=['POST'])
def Correo():
    user = 'qillari120@gmail.com'
    app_password = 'qxklxfydjijymdcf'
    
    carrito = request.json.get("carrito")
    email = request.json.get("email")
    street_name = request.json.get("street_name")
    preciototal = request.json.get("preciototal")

    subject_vendedor = 'Se realizó la compra'
    subject_comprador = 'Realizate una compra'

    items_comprados = "\n".join([f"Producto: {item.get('nombre')}, Precio: {item.get('price')}, Cantidad: {item.get('totalamount')}" for item in carrito])

    # Primer correo
    em1 = EmailMessage()
    em1['From'] = user
    em1['To'] = "qillari120@gmail.com"
    em1['Subject'] = subject_vendedor
    content1 = ("Nuevo comprador\n"
            "Lo que has comprado es:\n"
            "{}\n"
            "Su email es: {}\n"
            "Su calle es: {}\n"
            "El precio total es: {}").format(items_comprados, email, street_name, preciototal)
    em1.set_content(content1)

    # Segundo correo
    em2 = EmailMessage()
    em2['From'] = user
    em2['To'] = email
    em2['Subject'] = subject_comprador
    content2 = ("Su compra paso con exito\n"
            "Lo que has comprado es:\n"
            "{}\n"
            "El precio total es: {}\n"
            "Su producto llegara al dia siguiente, cualquier cosa contactenos por whatsapp o por este correo").format(items_comprados, preciototal)
    em2.set_content(content2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(user, app_password)
        smtp.sendmail(user, "qillari120@gmail.com", em1.as_string())
        smtp.sendmail(user, email, em2.as_string())

    return jsonify({
        'success': True,
        'message': 'Se enviaron los correos electrónicos'
    })

@app.route('/correo-newsletter', methods=['GET','POST'])
def correo_newsletter():
    user = 'qillari120@gmail.com'
    app_password = 'qxklxfydjijymdcf'
    email = request.json.get("correo")
    subject = 'nuevo suscriptor'

    em1 = EmailMessage()
    em1['From'] = user
    em1['To'] = "qillari120@gmail.com"
    em1['Subject'] = subject
    content1 = "Su correo es: " + email
    em1.set_content(content1)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(user, app_password)
        smtp.sendmail(user, "qillari120@gmail.com", em1.as_string())

    return jsonify({
        'success': True,
        'message': 'Se registro correctamente'
    })

@app.route("/login", methods=['GET'])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    if "Admin" == username or "admin" == username:
        if password == "Fiorellaydiego1.":
            return {
                "success": True,
                "message": "Usuario autenticado correctamente",
                "id": 1,
                "usuario": "invitado",
                "token": 1,
            }
        else:
            return {
                "success": False,
                "message": "Contraseña incorrecta"
            }, 401
    else:
        return {
            "success": False,
            "message": "Usuario no encontrado"
        }, 404

@app.route("/panel-de-control", methods=['GET'])
def panel_de_control():
    try:
        
        top_5_vendidos = GananciaPerdidaMensual.query.order_by(GananciaPerdidaMensual.venta_cantidad_total.desc()).limit(5).all()
        top_5_vendidos = [p.to_dict() for p in top_5_vendidos]

        bottom_5_vendidos = GananciaPerdidaMensual.query.order_by(GananciaPerdidaMensual.venta_cantidad_total.asc()).limit(5).all()
        bottom_5_vendidos = [p.to_dict() for p in bottom_5_vendidos]

        top_5_ganancias = GananciaPerdidaMensual.query.order_by(GananciaPerdidaMensual.total_ventas.desc()).limit(5).all()
        top_5_ganancias = [p.to_dict() for p in top_5_ganancias]

        bottom_5_ganancias = GananciaPerdidaMensual.query.order_by(GananciaPerdidaMensual.total_ventas.asc()).limit(5).all()
        bottom_5_ganancias = [p.to_dict() for p in bottom_5_ganancias]

        total_sum = db.session.query(func.sum(GananciaPerdidaMensual.total)).scalar()

        return jsonify({
            'top_5_vendidos': top_5_vendidos,
            'bottom_5_vendidos': bottom_5_vendidos,
            'top_5_ganancias': top_5_ganancias,
            'bottom_5_ganancias': bottom_5_ganancias,
            'total_sum': float(total_sum) if total_sum else 0.0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/crud-stock", methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_stock():
    try:
        data = request.args
        cantidad = data.get("cantidad", 0)
        stocks = Stock.query.all()

        stock_total = [s.to_dict() for s in stocks]

        resultado = jsonify(stock_total)

        return (resultado), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error en la solicitud GET /crud-stock: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route("/crud-stock", methods=['POST', 'PUT', 'DELETE'])
def crud_stock():
    try:

        if request.method == 'POST':

            data = request.get_json()

            nuevo_stock = Stock(
                id = data['id'],
                titulo = data['titulo'],
                nombre_link = data['nombre_link'],
                descripcion = data['descripcion'],
                tipo = data['tipo'],
                cantidad = data['cantidad'],
                precio_sin_descuento = data['precio_sin_descuento'],
                precio = data['precio'],
                url = data['url'],
                fotos = data['fotos']
            )

            existing_stock = Stock.query.filter_by(id=data['id']).first()
            if existing_stock:
                return jsonify({'error': 'El producto ya existe'}), 400

            db.session.add(nuevo_stock)
            db.session.commit()
            return jsonify({'mensaje': 'producto agregado correctamente'}), 201
        
        if request.method == 'PUT':

            data = request.get_json()
            id = data.get("id")
            producto_stock = Stock.query.filter_by(id=id).first()

            if not producto_stock:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            producto_stock.titulo = data.get("titulo", producto_stock.titulo)            
            producto_stock.nombre_link = data.get("nombre_link", producto_stock.nombre_link)
            producto_stock.descripcion = data.get("descripcion", producto_stock.descripcion)
            producto_stock.tipo = data.get("tipo", producto_stock.tipo)
            producto_stock.cantidad = data.get("cantidad", producto_stock.cantidad)
            producto_stock.precio_sin_descuento = data.get("precio_sin_descuento", producto_stock.precio_sin_descuento)
            producto_stock.precio = data.get("precio", producto_stock.precio)
            producto_stock.url = data.get("url", producto_stock.url)
            producto_stock.fotos = data.get("fotos", producto_stock.fotos)
            db.session.commit()

            return jsonify({'mensaje': 'Producto actualizado correctamente'}), 200
        
        if request.method == 'DELETE':

            id = request.args.get("id")

            producto_stock = Stock.query.filter_by(id=id).first()

            if not producto_stock:
                return jsonify({'error': 'Producto no encontrado'}), 404
            db.session.delete(producto_stock)
            db.session.commit()
            return jsonify({'mensaje': 'Producto eliminado correctamente'}), 204
    
    except Exception as e:
        db.session.rollback()
        print(f"Error en la solicitud GET /crud-stock: {e}")

        return jsonify({'error': str(e)}), 500

@app.route("/crud-ventas", methods=['GET','POST', 'PUT', 'DELETE'])
def crud_ventas():
    try:
        if request.method == 'GET':

            data = request.args
            cantidad = data.get("cantidad", 0)
            ventas = Ventas.query.offset(cantidad).limit(20).all()
            return jsonify([v.to_dict() for v in ventas]), 200
        
        if request.method == 'POST':
            id_stock = request.json.get("id_stock")
            cantidad = request.json.get("cantidad")

            nueva_venta = Ventas(
                id_stock=id_stock,
                cantidad=cantidad
            )

            db.session.add(nueva_venta)
            db.session.commit()

            return jsonify({'mensaje': 'Venta registrada correctamente'}), 201
        
        if request.method == 'DELETE':

            id = request.json.get("id")

            venta_stock = Ventas.query.filter_by(id=id).first()
            
            if not venta_stock:
                return jsonify({'error': 'No existe esta venta'}), 404
            
            for productos in venta_stock:
                productos

            db.session.delete(venta_stock)
            db.session.commit()

            return jsonify({'mensaje': 'venta eliminado correctamente'}), 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/crud-compras", methods=['GET','POST', 'PUT', 'DELETE'])
def crud_compras():
    try:
        if request.method == 'GET':

            data = request.get_json()
            cantidad = data.get("cantidad", 0)
            compras = Compras.query.offset(cantidad).limit(20).all()
            return jsonify([c.to_dict() for c in compras]), 200
        
        if request.method == 'POST':
            id_stock = request.json.get("id_stock")
            cantidad = request.json.get("cantidad")

            stock_existente = Stock.query.filter_by(id=id_stock).first()
            if not stock_existente:
                return jsonify({'error': 'El producto especificado no existe'}), 404

            nueva_compra = Compras(
                id_stock=id_stock,
                cantidad=cantidad
            )

            db.session.add(nueva_compra)
            db.session.commit()

            return jsonify({'mensaje': 'Venta registrada correctamente'}), 201
        
        if request.method == 'PUT':

            data = request.json
            id = data.get("id")

            compra_existente = Compras.query.get(id)
            if not compra_existente:
                return jsonify({'error': 'La compra especificada no existe'}), 404

            compra_existente.id_stock = data.get("id_stock", compra_existente.id_stock)
            compra_existente.cantidad = data.get("cantidad", compra_existente.cantidad)

            db.session.commit()

            return jsonify({'mensaje': 'Compra actualizada correctamente'}), 200
        
        if request.method == 'DELETE':

            id = request.json.get("id")

            compra_stock = Compras.query.filter_by(id=id).first()

            if not compra_stock:
                return jsonify({'error': 'No existe esta Compra'}), 404
            db.session.delete(compra_stock)
            db.session.commit()
            return jsonify({'mensaje': 'Compra eliminado correctamente'}), 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/ganancia-perdida", methods=['GET'])
def ganancia_perdida():
    data = request.args
    cantidad = data.get("cantidad", 0)
    stocks = GananciaPerdidaMensual.query.offset(cantidad).limit(20).all()
    return jsonify([s.to_dict() for s in stocks]), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)