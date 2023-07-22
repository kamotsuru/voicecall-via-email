import logging
import os
import configparser
from urllib.parse import urlparse, parse_qs

from flask import Flask
from flask import request
from flask import url_for
from twilio.rest import Client
import phonenumbers as ph
import sendgrid
import simplejson

import vonage

from konfig import Konfig


def warn(message):
    logging.warning(message)
    return message

address_book = {}
address_book_file = 'address-book.cfg'
try:
    user_list = configparser.ConfigParser()
    user_list.read(address_book_file)
    for user in user_list.items('users'):
        address_book[user[0]] = user[1]
except:
    template = ("{} does not exist")
    warn(template.format(address_book_file))

app = Flask(__name__)
konf = Konfig()
twilio_api = Client(konf.twilio_account_sid, konf.twilio_auth_token)
sendgrid_api = sendgrid.SendGridClient(konf.sendgrid_username,
                                       konf.sendgrid_password)

vonage_client = vonage.Client(key=konf.vonage_api_key,
                              secret=konf.vonage_api_secret)
vonage_api = vonage.Sms(vonage_client)

class InvalidInput(Exception):
    def __init__(self, invalid_input):
        self.invalid_input = invalid_input


class NoEmailForNumber(InvalidInput):
    def __str__(self):
        template = ("No email address is configured to receive "
                    "SMS messages sent to '{}' - "
                    "Try updating the 'address-book.cfg' file?")
        return template.format(self.invalid_input)


class NoNumberForEmail(InvalidInput):
    def __str__(self):
        template = ("The email address '{}' is not "
                    "configured to send SMS via this application - "
                    "Try updating the 'address-book.cfg' file?")
        return template.format(self.invalid_input)


class InvalidPhoneNumberInEmail(InvalidInput):
    def __str__(self):
        template = "Invalid phone number in email address: {}"
        return template.format(self.invalid_input)


class InvalidPhoneNumber(InvalidInput):
    def __str__(self):
        template = "Invalid phone number in HTTP POST: {}"
        return template.format(self.invalid_input)


class Lookup:
    def __init__(self):
        self.by_phone_number = address_book
        self.by_email_address = {}
        for phone_number in address_book.keys():
            email_address = address_book[phone_number]
            self.by_email_address[email_address] = phone_number

    def phone_for_email(self, email_address):
        '''Which phone number do we send this SMS message from?'''
        if email_address in self.by_email_address:
            return self.by_email_address[email_address]
        else:
            raise NoNumberForEmail(email_address)

    def email_for_phone(self, potential_number):
        '''Which email address do we forward this SMS message to?'''

        try:
            number = ph.parse(potential_number, 'US')
            phone_number = ph.format_number(number, ph.PhoneNumberFormat.E164)
        except Exception as e:
            raise InvalidPhoneNumber(str(e))

        if phone_number in self.by_phone_number:
            return self.by_phone_number[phone_number]
        else:
            raise NoEmailForNumber(phone_number)


def phone_to_email(potential_number):
    '''Converts a phone number like +14155551212
       into an email address like 14155551212@sms.example.com'''
    try:
        number = ph.parse(potential_number, 'US')
        phone_number = ph.format_number(number, ph.PhoneNumberFormat.E164)
    except Exception as e:
        raise InvalidPhoneNumber(str(e))
    phone_number = phone_number.replace('+', '')
    return("{}@{}".format(phone_number, konf.email_domain))


def email_to_phone(from_email):
    '''Converts an email address like 14155551212@sms.example.com
       into a phone number like +14155551212'''
    (username, domain) = from_email.split('@')

    potential_number = '+' + username
    try:
        ph_num = ph.parse(potential_number, 'US')
        return ph.format_number(ph_num, ph.PhoneNumberFormat.E164)
    except:
        raise InvalidPhoneNumberInEmail(from_email)


def check_for_missing_settings():
    rv = []
    for required in ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN',
                     'VONAGE_API_KEY', 'VONAGE_API_SECRET']:
        value = getattr(konf, required)
        if not value:
            rv.append(required)
    return rv


def duplicates_in_address_book():
    duplcates_found = False
    values = address_book.values()
    if len(values) != len(set(values)):
        duplcates_found = True
    return duplcates_found


@app.route('/')
def main():
    missing_settings = check_for_missing_settings()
    if len(missing_settings) > 0:
        template = 'The following settings are missing: {}'
        missing = ', '.join(missing_settings)
        error_message = template.format(missing)
        return warn(error_message), 500
    elif duplicates_in_address_book():
        print(str(address_book))
        error_message = ("Only one email address can be configured per "
                         "phone number. Please update the 'address-book.cfg' "
                         "file so that each phone number "
                         "matches exactly one email address.")
        return warn(error_message), 500
    else:
        template = ("Congratulations, "
                    "this software appears to be configured correctly."
                    "<br/><br/>"
                    "Use the following URLs to configure SendGrid "
                    "and Twilio:"
                    "<br/><br/>"
                    "SendGrid Inbound Parse Webhook URL: {}"
                    "<br/>"
                    "Twilio Messaging Request URL: {}")
        message = template.format(url_for('handle_email', _external=True),
                                  url_for('handle_sms', _external=True))
        return message


@app.route('/handle-sms', methods=['POST'])
def handle_sms():
    lookup = Lookup()
    try:
        email = {
            'text': request.form['Body'],
            'subject': 'Text message',
            'from_email': phone_to_email(request.form['From']),
            'to': lookup.email_for_phone(request.form['To'])
        }
    except InvalidInput as e:
        return warn(str(e)), 400

    message = sendgrid.Mail(**email)
    (status, msg) = sendgrid_api.send(message)
    if 'errors' in msg:
        template = "Error sending message to SendGrid: {}"
        errors = ', '.join(msg['errors'])
        error_message = template.format(errors)
        return warn(error_message), 400
    else:
        return '<Response></Response>'


@app.route('/handle-email', methods=['POST'])
def handle_email():
    lookup = Lookup()
    try:
        envelope = simplejson.loads(request.form['envelope'])
        lines = request.form['text'].splitlines(True)
        if envelope['to'][0] != request.form['to']:
            email_from = 'xxxx@gmail.com'  # Where from/to is different between header and envelope, we use a specific address
        else:
            email_from = envelope['from']
        sms = {
            'from': lookup.phone_for_email(email_from).replace('+',''),       
            'to': email_to_phone(envelope['to'][0]).replace('+',''),
            'text': lines[0],
            'type': 'unicode',                        
        }
    except InvalidInput as e:
        return warn(str(e))

    try:
        responseData = vonage_api.send_message({
            'from': lookup.phone_for_email(email_from).replace('+',''),
            'to': email_to_phone(envelope['to'][0]).replace('+',''),
            'text': lines[0],
            'type': 'unicode',            
        })
        if responseData["messages"][0]["status"] == "0":
            print("Vonage message sent successfully.")
        else:
            warn("Vonage message failed with error: "+str(responseData['messages'][0]['error-text']))
        return responseData["messages"][0]["message-id"]
    except Exception as e:
        print("oh no")
        print(str(e))
        error_message = "Error sending message to Vonage"
        return warn(error_message+str(responseData['messages'][0]['error-text'])), 400

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        app.debug = True
        print("in debug mode")
    app.run(host='0.0.0.0', port=port)
