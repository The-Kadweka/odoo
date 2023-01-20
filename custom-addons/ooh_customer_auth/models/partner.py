from odoo import models, fields, api,_
import datetime

today = datetime.date.today()

class PartnerExtension(models.Model):
    _inherit = 'res.partner'

    password = fields.Char(string="partner password")
    access_token_ids = fields.One2many(string='Access Tokens',comodel_name='jwt_provider.access_token',inverse_name='partner_id')
    otp=fields.Char(string='Otp')
    when_sent=fields.Date(string="Otp Validation")  
    curreny=fields.Many2one('res.currency',string="currency")  
    dob=fields.Date(string="dob")
    gender = fields.Selection([
        ('male', 'Male'),
        ('Female', 'Female'),
        ('not say', 'Not Say'),
    ])

    def create_account(self):
        account_id=self.env['users.account'].sudo().create({
                    "name":self.name,
                    "date":today,
                    'partner_id':self.id,
                    'balance':0.00,
            })
        return account_id