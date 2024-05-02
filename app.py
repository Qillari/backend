from flask import Flask, jsonify, request
from flask_cors import CORS
import mercadopago
from email.message import EmailMessage
from email.mime.image import MIMEImage
import ssl
import smtplib
import uuid
import base64

app=Flask(__name__)
CORS(app, origins=['https://front-end-qillari.vercel.app/', 'https://front-end-qillari.vercel.app', 'https://www.front-end-qillari.vercel.app/', 'https://www.qillari.vercel.app' ])

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
        sdk = mercadopago.SDK("APP_USR-1829594313616516-032020-b4250a856320c856072be653fa3f8821-1446480329")

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

@app.route('/yape', methods=['POST'])
def yape_correo():
    user = 'qillari120@gmail.com'
    app_password = 'qxklxfydjijymdcf'

    
    preciototal = request.json.get("preciototal")
    carrito = request.json.get("carrito")
    email = request.json.get("email")
    street_name = request.json.get("direccion")
    telefono = request.json.get("telefono")
    imagen = request.json.get("imagen_de_pago")

    subject_vendedor = 'Se realizó la compra'
    subject_comprador = 'Realizate una compra'

    items_comprados = "\n".join([f"Producto: {item.get('nombre')}, Precio: {item.get('price')}, Cantidad: {item.get('totalamount')}" for item in carrito])

    # Primer correo
    em1 = EmailMessage()
    em1['From'] = user
    em1['To'] = "qillari120@gmail.com"
    em1['Subject'] = subject_vendedor
    content1 = ("Nuevo comprador\n"
            "Lo que ha comprado es:\n"
            "{}\n"
            "Su email es: {}\n"
            "Su calle es: {}\n"
            "su telefono es: {}\n"
            "El precio total es: {}").format(items_comprados, email, telefono, street_name, preciototal)
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
        smtp.sendmail("info@qillari.com", "qillari120@gmail.com", em1.as_string())
        smtp.sendmail("info@qillari.com", email, em2.as_string())

    smtp.quit()

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

    smtp.quit()

    return jsonify({
        'success': True,
        'message': 'Se enviaron los correos electrónicos'
    })

@app.route('/correo-newsletter', methods=['POST'])
def correo_newsletter():
    user = 'qillari120@gmail.com'
    app_password = 'qxklxfydjijymdcf'
    email = request.json.get("email")
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

    smtp.quit()
    return jsonify({
        'success': True,
        'message': 'Se enviaron los correos electrónicos'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)