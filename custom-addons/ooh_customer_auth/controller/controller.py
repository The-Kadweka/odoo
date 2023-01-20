from werkzeug.security import generate_password_hash, check_password_hash
from ..validator import validator
from odoo.http import request
from odoo import http
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
import random
import json
import math
import jwt

import logging

_logger = logging.getLogger(__name__)
today = datetime.today()

class MoneyController(http.Controller):
    @http.route('/view/currency',type='json',auth="public",cors='*',method=['POST'])
    def view_currency(self,**kw):
        currencies=[]
        currency = request.env['res.currency'].sudo().search([('active',"=",True)])
        for rec in currency:
            vals={
                "value":rec.id,
                "label":rec.name
            }
            currencies.append(vals)
        return {
            "code":200,
            "currency":currencies
        }
    @http.route('/view/goal/details',type='json',auth="public",cors='*',method=['POST'])
    def view_goal_details(self,**kw):
        data = json.loads(request.httprequest.data)
        goalData={}
        linesData=[]
        access_token=data['access_token']
        goal_id=data['goal_id']
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        if not goal_id:
            response = {
                'code': 400,
                'message': 'Goal Id cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        if token:
            goal_id_data= request.env['personal.goals'].sudo().search([('id','=',data['goal_id']),('partner_id.email', '=',token.partner_id.email)])
            if goal_id_data:
                for rec in goal_id_data.expense_id:
                    # start_date = datetime.strptime(str(goal_id_data.from_date), "%Y-%m-%d")
                    # end_date = datetime.strptime(str(goal_id_data.to_date), "%Y-%m-%d")
                    # delta = relativedelta(end_date, start_date)
                    lines={
                    "id":rec.id,
                    "date":rec.date,
                    "amt":rec.amt
                    }
                    linesData.append(lines)
                return {
                    "code":200,
                    "status":"Successfuly",
                    "id":goal_id_data.id,
                    "name":goal_id_data.name,
                    "start":goal_id_data.from_date,
                    "end":goal_id_data.to_date,
                    "period":relativedelta(datetime.strptime(str(goal_id_data.to_date), "%Y-%m-%d"), datetime.strptime(str(goal_id_data.from_date), "%Y-%m-%d")).months,
                    "start_amt":goal_id_data.target,
                    "saved_amount":goal_id_data.current_saving,
                    "lines":linesData,
                }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/delete/expense', type='json', auth='public', cors='*', method=['POST'])
    def remove_expense(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token=data['access_token']
        expense_id=data['expense_id']
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        if token:
            expense_id=request.env['account.spend'].sudo().search([('id','=',expense_id),('partner_id.id','=',token.partner_id.id)])
            if expense_id.spent_on=="INCOME":
                expense_id.account_id.sudo().write({"balance":expense_id.account_id.balance-expense_id.amt})
                expense_id.sudo().unlink()
                response = {
                    'code': 200,
                    'message': 'You Have deleted an Expense'
                    }
                return response
            if expense_id.spent_on=="SAVINGS":
                expense_id.account_id.sudo().write({"balance":expense_id.account_id.balance-expense_id.amt})
                expense_id.goal_id.sudo().write({"current_saving":expense_id.goal_id.current_saving-expense_id.amt})
                expense_id.sudo().unlink()
                response = {
                    'code': 200,
                    'message': 'You Have deleted an Expense'
                    }
                return response
            else:
                expense_id.account_id.sudo().write({"balance":expense_id.account_id.balance+expense_id.amt})
                expense_id.sudo().unlink()
                response = {
                    'code': 200,
                    'message': 'You Have deleted an Expense'
                    }
                return response
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/delete/goal', type='json', auth='public', cors='*', method=['POST'])
    def remove_goal(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token=data['access_token']
        goal_id=data['goal_id']
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        if token:
            goal_id=request.env['personal.goals'].sudo().search([('id','=',goal_id),('partner_id.id','=',token.partner_id.id)])
            if len(goal_id.expense_id)>0:
                response = {
                'code': 403,
                'message': 'You cannot delete a Goal which you have started saving on it!'
                }
                return response
            else:
                goal_id.sudo().unlink()
                response = {
                    'code': 200,
                    'message': 'You Have deleted a goal'
                    }
                return response
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/create/goal', type='json', auth='public', cors='*', method=['POST'])
    def new_goal(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token = data['access_token']
        name = data['name']
        from_date = data['from_date']
        to_date = data['to_date']
        target = data['target']
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        if not name:
            response = {
                'code': 400,
                'message': 'Name cannot be empty'
            }
            return response
        if not from_date:
            response = {
                'code': 400,
                'message': 'From date cannot be empty'
            }
            return response
        if not to_date:
            response = {
                'code': 400,
                'message': 'To Date cannot be empty'
            }
            return response
        if not target:
            response = {
                'code': 400,
                'message': 'Target Amount cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        if token:
            goal_id=request.env['personal.goals'].sudo().create({
                    'name':name,
                    'target':target,
                    'partner_id':token.partner_id.id,
                    'date':today,
                    'from_date':from_date,
                    'to_date':to_date,
                    })
            if goal_id:
                return{
                    "code":200,
                    "status":"Successfuly",
                    "data":"Create a new goal"
                }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/view/goals', type='json', auth='public', cors='*', method=['POST'])
    def view_goals(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token = data['access_token']
        goals=[]
        selectGoals=[]
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        account_id= request.env['personal.goals'].sudo().search([('partner_id.email', '=',token.partner_id.email)])
        if token:
            for rec in account_id:
                start_date = datetime.strptime(str(rec.from_date), "%Y-%m-%d")
                end_date = datetime.strptime(str(rec.to_date), "%Y-%m-%d")
                delta = relativedelta(end_date, start_date)
                vals={
                    "label":rec.name.upper(),
                    "value":rec.name,
                    "date":rec.date,
                    "from_date":rec.from_date,
                    "to_date":rec.to_date,
                    "period":delta.months,
                    "target":rec.target,
                    "id":rec.id,
                    "saved":rec.current_saving,
                    "per":rec.current_saving/rec.target
                }
                select={
                    "label":rec.name.upper(),
                    "value":rec.id,
                    "per":rec.current_saving/rec.target
                }
                goals.append(vals)
                selectGoals.append(select)
            return{
                "code":200,
                "status":"Successfuly",
                'item':len(goals),
                'itemAb50':len([item for item in selectGoals if item['per']>0.49]),
                'itemBl50':len([item for item in selectGoals if item['per']<0.5]),
                'itemDone':len([item for item in selectGoals if item['per']>=1]),
                'selected':[item for item in selectGoals if item['per']<1],
                "data":goals
            }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/view/transactions', type='json', auth='public', cors='*', method=['POST'])
    def view_transactions(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token = data['access_token']
        transactions=[]
        category=[]
        bill=0.00
        charity=0.00
        clothing=0.00
        electronics=0.00
        income=0.00
        education=0.00
        entertainment=0.00
        foodgroceries=0.00
        rent=0.00
        subscription=0.00
        transport=0.00
        vacation=0.00
        households=0.00
        others=0.00
        income=0.00
        savings=0.00
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        account_id= request.env['users.account'].sudo().search([('partner_id.email', '=',token.partner_id.email)])
        if token:
            for rec in account_id.expenditure:
                vals={
                    "type":rec.spent_on,
                    "date":rec.date,
                    "name":rec.name,
                    "amt":rec.amt,
                    "id":rec.id
                }
                transactions.append(vals)
            for rec in account_id.expenditure:
                if rec.spent_on=="BILL":
                    bill+=rec.amt
                if rec.spent_on=="SAVINGS":
                    savings+=rec.amt
                if rec.spent_on=="CHARITY":
                    charity+=rec.amt
                if rec.spent_on=="CLOTHING":
                    clothing+=rec.amt
                if rec.spent_on=="ELECTRONICS":
                    electronics+=rec.amt
                if rec.spent_on=="INCOME":
                    income+=rec.amt
                if rec.spent_on=="EDUCATION":
                    education+=rec.amt
                if rec.spent_on=="ENTERTAINMENT":
                        entertainment+=rec.amt
                if rec.spent_on=="FOODGROCERIES":
                    foodgroceries+=rec.amt
                if rec.spent_on=="RENT":
                        rent+=rec.amt
                if rec.spent_on=="SUBSCRIPTION":
                        subscription+=rec.amt
                if rec.spent_on=="TRANSPORT":
                        transport+=rec.amt
                if rec.spent_on=="VACATIONS":
                        vacation+=rec.amt
                if rec.spent_on=="HOUSEHOLDS":
                        households+=rec.amt
                if rec.spent_on=="OTHERS":
                        others+=rec.amt
            category.append({"name":"Others","amount":others})
            category.append({"name":"Bill","amount":bill})
            category.append({"name":"House Holds","amount":households})
            category.append({"name":"Vacation","amount":vacation})
            category.append({"name":"Transport","amount":transport})
            category.append({"name":"Subscription","amount":subscription})
            category.append({"name":"Savings","amount":savings})
            category.append({"name":"Renting","amount":rent})
            category.append({"name":"Food/Groceries","amount":foodgroceries})
            category.append({"name":"Entertainment","amount":entertainment})
            category.append({"name":"Income","amount":income})
            category.append({"name":"Education","amount":education})
            category.append({"name":"Electronics","amount":electronics})
            category.append({"name":"Charity","amount":charity})
            category.append({"name":"Clothing","amount":clothing})

            return{
                "code":200,
                "status":"successfuly",
                "transactions":transactions,
                "category":category,
                "balance":account_id.balance,
                "Message":"Customer Transactions"
            }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/view/stats', type='json', auth='public', cors='*', method=['POST'])
    def view_filtered_data(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token = data['access_token']
        agregades=[]
        category=[]
        bill=0.00
        charity=0.00
        clothing=0.00
        electronics=0.00
        income=0.00
        savings=0.00
        spending=0.00
        education=0.00
        entertainment=0.00
        foodgroceries=0.00
        rent=0.00
        subscription=0.00
        transport=0.00
        vacation=0.00
        households=0.00
        others=0.00
        saves=0.00
        incomes=0.00
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        account_id= request.env['users.account']
        if token:
            if data['period']=="Today":
                expenses=account_id.sudo().search([("expenditure.date","=",today),('partner_id.email', '=',token.partner_id.email)])
                for rec in expenses.expenditure:
                    if rec.spent_on=="INCOME":
                        income+=rec.amt
                    if rec.spent_on=="SAVINGS":
                        savings+=rec.amt
                    if rec.spent_on not in ["INCOME","SAVINGS"]:
                        spending+=rec.amt
                for rec in expenses.expenditure:
                    if rec.spent_on=="BILL":
                        bill+=rec.amt
                    if rec.spent_on=="CHARITY":
                        charity+=rec.amt
                    if rec.spent_on=="CLOTHING":
                        clothing+=rec.amt
                    if rec.spent_on=="ELECTRONICS":
                        electronics+=rec.amt
                    if rec.spent_on=="EDUCATION":
                        education+=rec.amt
                    if rec.spent_on=="ENTERTAINMENT":
                            entertainment+=rec.amt
                    if rec.spent_on=="FOODGROCERIES":
                        foodgroceries+=rec.amt
                    if rec.spent_on=="RENT":
                            rent+=rec.amt
                    if rec.spent_on=="SUBSCRIPTION":
                            subscription+=rec.amt
                    if rec.spent_on=="TRANSPORT":
                            transport+=rec.amt
                    if rec.spent_on=="INCOME":
                            incomes+=rec.amt
                    if rec.spent_on=="SAVINGS":
                            saves+=rec.amt
                    if rec.spent_on=="VACATIONS":
                            vacation+=rec.amt
                    if rec.spent_on=="HOUSEHOLDS":
                            households+=rec.amt
                    if rec.spent_on=="OTHERS":
                            others+=rec.amt
                category.append({"name":"Others","amount":others})
                category.append({"name":"Bill","amount":bill})
                category.append({"name":"House Holds","amount":households})
                category.append({"name":"Vacation","amount":vacation})
                category.append({"name":"Transport","amount":transport})
                category.append({"name":"Subscription","amount":subscription})
                category.append({"name":"Renting","amount":rent})
                category.append({"name":"Food/Groceries","amount":foodgroceries})
                category.append({"name":"Income","amount":incomes})
                category.append({"name":"Savings","amount":saves})
                category.append({"name":"Entertainment","amount":entertainment})
                category.append({"name":"Education","amount":education})
                category.append({"name":"Electronics","amount":electronics})
                category.append({"name":"Charity","amount":charity})
                category.append({"name":"Clothing","amount":clothing})
                agregades.append({"label":"Savings","amount":savings,"color":"orange"})
                agregades.append({"label":"Spending","amount":spending,"color":"red"})
                agregades.append({"label":"Income","amount":income,"color":"green"})

                return{
                    "code":200,
                    "status":"successfuly",
                    "Income":incomes,
                    "Savings":saves,
                    "expense":spending,
                    "category":category,
                    "balance":account_id.balance,
                    "Message":"Customer Transactions"
                }

            if data['period']=="thisMonth":
                expenses=account_id.sudo().search([('partner_id.email', '=',token.partner_id.email)])
                for rec in expenses.expenditure:
                    if rec.spent_on=="INCOME" and rec.date.month==today.month:
                        income+=rec.amt
                    if rec.spent_on=="SAVINGS" and rec.date.month==today.month:
                        savings+=rec.amt
                    if rec.spent_on not in ["INCOME","SAVINGS"] and rec.date.month==today.month:
                        spending+=rec.amt
                for rec in expenses.expenditure:
                    if rec.spent_on=="BILL" and rec.date.month==today.month:
                        bill+=rec.amt
                    if rec.spent_on=="CHARITY" and rec.date.month==today.month:
                        charity+=rec.amt
                    if rec.spent_on=="CLOTHING" and rec.date.month==today.month:
                        clothing+=rec.amt
                    if rec.spent_on=="ELECTRONICS" and rec.date.month==today.month:
                        electronics+=rec.amt
                    if rec.spent_on=="EDUCATION" and rec.date.month==today.month:
                        education+=rec.amt
                    if rec.spent_on=="ENTERTAINMENT" and rec.date.month==today.month:
                            entertainment+=rec.amt
                    if rec.spent_on=="FOODGROCERIES" and rec.date.month==today.month:
                        foodgroceries+=rec.amt
                    if rec.spent_on=="RENT" and rec.date.month==today.month:
                            rent+=rec.amt
                    if rec.spent_on=="SUBSCRIPTION" and rec.date.month==today.month:
                            subscription+=rec.amt
                    if rec.spent_on=="TRANSPORT" and rec.date.month==today.month:
                            transport+=rec.amt
                    if rec.spent_on=="INCOME"  and rec.date.month==today.month:
                            incomes+=rec.amt
                    if rec.spent_on=="SAVINGS"  and rec.date.month==today.month:
                            saves+=rec.amt
                    if rec.spent_on=="VACATIONS"  and rec.date.month==today.month:
                            vacation+=rec.amt
                    if rec.spent_on=="HOUSEHOLDS"  and rec.date.month==today.month:
                            households+=rec.amt
                    if rec.spent_on=="OTHERS"  and rec.date.month==today.month:
                            others+=rec.amt
                category.append({"name":"Others","amount":others})
                category.append({"name":"Bill","amount":bill})
                category.append({"name":"House Holds","amount":households})
                category.append({"name":"Vacation","amount":vacation})
                category.append({"name":"Transport","amount":transport})
                category.append({"name":"Subscription","amount":subscription})
                category.append({"name":"Renting","amount":rent})
                category.append({"name":"Food/Groceries","amount":foodgroceries})
                category.append({"name":"Income","amount":incomes})
                category.append({"name":"Savings","amount":saves})
                category.append({"name":"Entertainment","amount":entertainment})
                category.append({"name":"Education","amount":education})
                category.append({"name":"Electronics","amount":electronics})
                category.append({"name":"Charity","amount":charity})
                category.append({"name":"Clothing","amount":clothing})
                agregades.append({"label":"Savings","amount":savings,"color":"orange"})
                agregades.append({"label":"Spending","amount":spending,"color":"red"})
                agregades.append({"label":"Income","amount":income,"color":"green"})

                return{
                    "code":200,
                    "status":"successfuly",
                    "Income":incomes,
                    "Savings":saves,
                    "expense":spending,
                    "category":category,
                    "balance":account_id.balance,
                    "Message":"Customer Transactions"
                }
            if data['period']=="past6Month":
                six_months = date.today() + relativedelta(months=-6)
                expenses=account_id.sudo().search([("expenditure.date",">",six_months),("expenditure.date","<",today),('partner_id.email', '=',token.partner_id.email)])
                for rec in expenses.expenditure:
                    if rec.spent_on=="INCOME":
                        income+=rec.amt
                    if rec.spent_on=="SAVINGS":
                        savings+=rec.amt
                    if rec.spent_on not in ["INCOME","SAVINGS"]:
                        spending+=rec.amt
                for rec in expenses.expenditure:
                    if rec.spent_on=="BILL":
                        bill+=rec.amt
                    if rec.spent_on=="CHARITY":
                        charity+=rec.amt
                    if rec.spent_on=="CLOTHING":
                        clothing+=rec.amt
                    if rec.spent_on=="ELECTRONICS":
                        electronics+=rec.amt
                    if rec.spent_on=="EDUCATION":
                        education+=rec.amt
                    if rec.spent_on=="ENTERTAINMENT":
                            entertainment+=rec.amt
                    if rec.spent_on=="FOODGROCERIES":
                        foodgroceries+=rec.amt
                    if rec.spent_on=="RENT":
                            rent+=rec.amt
                    if rec.spent_on=="SUBSCRIPTION":
                            subscription+=rec.amt
                    if rec.spent_on=="TRANSPORT":
                            transport+=rec.amt
                    if rec.spent_on=="INCOME":
                            incomes+=rec.amt
                    if rec.spent_on=="SAVINGS":
                            saves+=rec.amt
                    if rec.spent_on=="VACATIONS":
                            vacation+=rec.amt
                    if rec.spent_on=="HOUSEHOLDS":
                            households+=rec.amt
                    if rec.spent_on=="OTHERS":
                            others+=rec.amt
                category.append({"name":"Others","amount":others})
                category.append({"name":"Bill","amount":bill})
                category.append({"name":"House Holds","amount":households})
                category.append({"name":"Vacation","amount":vacation})
                category.append({"name":"Transport","amount":transport})
                category.append({"name":"Subscription","amount":subscription})
                category.append({"name":"Renting","amount":rent})
                category.append({"name":"Food/Groceries","amount":foodgroceries})
                category.append({"name":"Income","amount":incomes})
                category.append({"name":"Savings","amount":saves})
                category.append({"name":"Entertainment","amount":entertainment})
                category.append({"name":"Education","amount":education})
                category.append({"name":"Electronics","amount":electronics})
                category.append({"name":"Charity","amount":charity})
                category.append({"name":"Clothing","amount":clothing})
                agregades.append({"label":"Savings","amount":savings,"color":"orange"})
                agregades.append({"label":"Spending","amount":spending,"color":"red"})
                agregades.append({"label":"Income","amount":income,"color":"green"})

                return{
                    "code":200,
                    "status":"successfuly",
                    "Income":incomes,
                    "Savings":saves,
                    "expense":spending,
                    "category":category,
                    "balance":account_id.balance,
                    "Message":"Customer Transactions"
                }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response
    @http.route('/create/expense', type='json', auth='public', cors='*', method=['POST'])
    def new_expense(self, **kw):
        data = json.loads(request.httprequest.data)
        access_token = data['access_token']
        name = data['name']
        amount = data['amt']
        spent_on = data['spent_on']
        if not access_token:
            response = {
                'code': 400,
                'message': 'Access Token cannot be empty'
            }
            return response
        if not name:
            response = {
                'code': 400,
                'message': 'Name cannot be empty'
            }
            return response
        if not amount:
            response = {
                'code': 400,
                'message': 'Amount cannot be empty'
            }
            return response
        if not spent_on:
            response = {
                'code': 400,
                'message': 'Where Spent cannot be empty'
            }
            return response

        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        if token:
            account_id = request.env['users.account'].sudo().search([('partner_id.email', '=',token.partner_id.email)])
            if account_id:
                if spent_on== "INCOME":
                    expense=request.env['account.spend'].sudo().create({
                    'name':name,
                    'amt':amount,
                    'date':today,
                    'spent_on':spent_on.upper(),
                    'account_id':account_id.id,
                    })
                    if expense:
                        account_id.sudo().write({"balance":account_id.balance+expense.amt})
                        return {
                            "code":200,
                            "record":account_id.balance,
                            "type":data["spent_on"],
                            "message":"You have successfuly Created an Income"
                        }
                if spent_on=="SAVINGS":
                    if float(amount)>account_id.balance:
                        return {
                            "code":200,
                            "status":"Successfuly",
                            "message":"You do not have enough money in your account"
                        }
                    else:
                        goal_id = request.env['personal.goals'].sudo().search([("id","=",data['goal_id']),('partner_id.email', '=',token.partner_id.email)])
                        if goal_id:
                            expense_id=request.env['account.spend'].sudo().create({
                                'name':name,
                                'amt':amount,
                                'date':today,
                                'spent_on':spent_on,
                                "goal_id":goal_id.id,
                                'account_id':account_id.id,
                            })
                            if expense_id:
                                goal_id.sudo().write({"current_saving":goal_id.current_saving+expense_id.amt})
                                account_id.sudo().write({"balance":account_id.balance-expense_id.amt})
                                return {
                                    "code":200,
                                    "status":"Successfuly",
                                    "type":data["spent_on"],
                                    "message":"You Have Saved for Your Goal"
                                }
                else:
                    if float(amount)>account_id.balance:
                        return {
                            "code":200,
                            "status":"Successfuly",
                            "message":"You do not have enough money in your account"
                        }
                    else:
                        expense=request.env['account.spend'].sudo().create({
                            'name':name,
                            'amt':amount,
                            'date':today,
                            'spent_on':spent_on,
                            'account_id':account_id.id,
                        })
                        if expense:
                            account_id.sudo().write({"balance":account_id.balance-float(amount)})
                            return {
                                "code":200,
                                "record":account_id.balance,
                                "type":data["spent_on"],
                                "message":"You have successfuly Created an Expense"
                            }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response

# https://www.odoo-bs.com/blog/global-5/odoo-barcode-scanner-app-143
# https://apps.odoo.com/apps/modules/15.0/barcode_scanning_sale_purchase/
