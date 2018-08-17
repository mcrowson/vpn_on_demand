import os

import boto3
from flask import Flask, request, jsonify
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
ALLOWED_SENDER = os.environ.get('ALLOWED_SENDER')
EC2_INSTANCE_ID = os.environ.get('EC2_INSTANCE_ID')
EC2_REGION = os.environ.get('EC2_REGION')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)
ec2 = boto3.resource('ec2', region_name=EC2_REGION)


@app.route('/', methods=['POST'])
def handle_text():
    """
    Takes a text message. If the content is "VPN ON" it starts the VPN box, if the content is "VPN OFF" it
    stops the VPN box. When the command is done, a follow up text is returned to the sender.
    """
    sender = request.values.get('From', '')
    if sender != ALLOWED_SENDER:
        # Only allow from my number, disregard the message.
        return jsonify({'success': True})

    content = request.values.get('Body', '')
    instance = ec2.Instance(EC2_INSTANCE_ID)

    if content.lower() == 'vpn off':
        if instance.state['Name'] != 'running':
            msg = 'The VPN is not running and has a status of: {}'.format(instance.state['Name'])
            respond_with(msg)
            return jsonify({'success': True})

        instance.stop()
        respond_with("The instance has been stopped")

    elif content.lower() == 'vpn on':
        if instance.state['Name'] != 'stopped':
            msg = 'The VPN is not off, please try again later. It has a state of: {}'.format(instance.state['Name'])
            respond_with(msg)
            return jsonify({'success': True})

        instance.start()
        respond_with("The instance has been started")

    else:
        respond_with("I only respond to the commands 'VPN on' and 'VPN off'")

    return jsonify({'success': True})


def respond_with(text):
    """
    Sends a text message response to the sender
    """
    client.messages.create(
        body=text,
        from_=TWILIO_PHONE_NUMBER,
        to=ALLOWED_SENDER
    )


if __name__ == '__main__':
    app.run(debug=True, port=3000)
