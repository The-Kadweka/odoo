from dataclasses import field
from email.policy import default
from datetime import date
from dateutil.relativedelta import relativedelta
import http
from locale import currency
from sqlite3 import apilevel
import string
from sys import api_version
from odoo import models, fields,api
import logging
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
class UsersAccounts(models.Model):
    _name = "users.account"

    name=fields.Char(string="Account Name",required=True,readonly=True)
    date=fields.Date(string="Created On?",readonly=True)
    partner_id=fields.Many2one('res.partner',string="Owner?",required=True,readonly=True)
    balance=fields.Float(string="Start Amount",required=True,readonly=True)
    expenditure=fields.One2many('account.spend','account_id',string="The Expenses",readonly=True)

class AccountsSpent(models.Model):
    _name = "account.spend"


    name=fields.Char(string="Description",required=True,readonly=True)
    date=fields.Date(string="Created On?",required=True,readonly=True)
    account_id=fields.Many2one('users.account',string="Account",required=True,readonly=True)
    partner_id=fields.Many2one(string="Create By?",required=True,related='account_id.partner_id',readonly=True)
    amt=fields.Float(string="Start Amount",required=True,readonly=True)
    # minus_6=fields.Date(string="Six Months Ago",readonly=True,compute="_compute_date_6months_ago")
    goal_id=fields.Many2one('personal.goals',string="The Expenses",readonly=True)
    spent_on = fields.Selection([
        ('BILL', 'BILLS'),
        ('CHARITY', 'CHARITY'),
        ('CLOTHING', 'CLOTHING'),
        ('ELECTRONICS', 'ELECTRONICS'),
        ('INCOME', 'INCOME'),
        ('EDUCATION', 'EDUCAION'),
        ('SAVINGS', 'SAVINGS'),
        ('ENTERTAINMENT', 'ENTERTAINMENT'),
        ('PERSONALGOALS', 'PERSONAL GOALS'),
        ('FOODGROCERIES', 'FOOD/GROCERIES'),
        ('RENT', 'RENT'),
        ('SUBSCRIPTION', 'SUBSCRIPTIONS'),
        ('TRANSPORT', 'TRANSPORT'),
        ('VACATIONS', 'VACATION'),
        ('HOUSEHOLDS', 'HOUSEHOLDS'),
         ('OTHERS', 'OTHERS'),
        ],string='spent on',required=True,readonly=True)

    # @api.depends('minus_6')
    # def _compute_date_6months_ago(self):
    #     six_months = date.today() + relativedelta(months=-6)
    #     self.minus_6=six_months
class PersonalGoals(models.Model):
    _name = "personal.goals"

    name=fields.Char(string="Name",required=True,readonly=True)
    date=fields.Date(string="Created On?",readonly=True)
    from_date=fields.Date(string="Start On",readonly=True)
    to_date=fields.Date(string="End On",readonly=True)
    partner_id=fields.Many2one('res.partner',string="Owner?",required=True,readonly=True)
    target=fields.Float(string="Target Amount",required=True,readonly=True)
    current_saving=fields.Float(string="Saved Amount",readonly=True)
    expense_id=fields.One2many('account.spend','goal_id',string="The Expenses",readonly=True)


class AdvertCenter(models.Model):
    _name = "advert.center"
    
    name=fields.Char(string="Descriptions")
    is_show=fields.Boolean(string="Show Advert",default=False)
    link=fields.Char(string="Read More Link")
    # image=fields.Binary(string="Advert Image")

