from odoo import models, fields, api
from datetime import datetime

class JwtAccessToken(models.Model):
    _name = 'jwt_provider.access_token'
    _description = 'Store user access token for one-time-login'

    token = fields.Char('Access Token', required=True)
    partner_id = fields.Many2one('res.partner', string='User', required=True, ondelete='cascade')
    expires = fields.Datetime('Expires', required=True)

    is_expired = fields.Boolean(compute='_compute_is_expired')

    @api.depends('expires')
    def _compute_is_expired(self):
        for token in self:
            token.is_expired = datetime.now() > token.expires