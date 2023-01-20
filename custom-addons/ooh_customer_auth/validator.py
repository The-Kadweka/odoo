from odoo.http import request
import logging
import jwt

_logger = logging.getLogger(__name__)

regex = r"^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

class Validator:
    def key(self):
        return '8dxtZrbfRJQJd2NtPujww3OfwAUfKOXf'

    def verify(self, token):
        record = request.env['jwt_provider.access_token'].sudo().search([
            ('token', '=', token),
        ],order='create_date desc', limit=1)

        if len(record) != 1:
            return False

        if record.is_expired:
            return False

        return True
    def verify_token(self, token):
    
        # try:
        result = {
            'status': False,
            'message': 'Token invalid or expired',
            'id': 0,
            'code': 400
        }
        payload = jwt.decode(token, self.key(), algorithms=["HS256"])
        if not self.verify(token):
            return self.errorToken()

        uid = payload['sub']
        if not uid:
            return self.errorToken()
        result['id'] = uid
        result['status'] = True
        result['code'] = 200
        result['message'] = 'Token valid'
        return result
    def errorToken(self):
        return {
            'message': 'Token invalid or expired',
            'code': 498,
            'status': False
        }
    
    def do_logout(self, token):
        self.cleanup()
        request.env['jwt_provider.access_token'].sudo().search([
            ('token', '=', token)
        ]).unlink()

    def cleanup(self):
        request.session.logout()
validator = Validator()