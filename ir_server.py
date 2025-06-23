from flask import Flask, request, jsonify
from flask_cors import CORS
import RPi.GPIO as GPIO
import json

app = Flask(__name__)
CORS(app)

# Setup PWM
GPIO.setmode(GPIO.BCM)
pwm_pin = 23
GPIO.setup(pwm_pin, GPIO.OUT)
# PWM instance with 1 kHz frequency
pwm = GPIO.PWM(pwm_pin, 1000)
pwm.start(0)  # Start with 0% duty cycle


@app.route('/api/set-ir-brightness', methods=['POST'])
def set_ir_brightness():
    data = request.json
    brightness_val = data.get('brightness')
    # print(f"Setting IR brightness to: {brightness_val}")
    try:
        pwm.start(brightness_val)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Set brightness error: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, ssl_context=('/home/rpi/lullgo/certs/rpi_local.crt', '/home/rpi/lullgo/certs/rpi_local.key'))
