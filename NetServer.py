from flask import Flask, jsonify
from flask_cors import CORS
import ssl

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return jsonify(
        status="success",
        message="Secure connection established",
        protocol="TLSv1.3",
        certificate_valid=True
    )


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('server.crt', 'server.key')

    app.run(
        host='0.0.0.0',
        port=8081,
        ssl_context=context,
        threaded=True,
        debug=False
    )
