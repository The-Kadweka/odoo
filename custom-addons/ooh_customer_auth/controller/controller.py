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
                "label":rec.symbol
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
                    "status":"success",
                    "id":goal_id_data.id,
                    "name":goal_id_data.name,
                    "start":goal_id_data.from_date,
                    "end":goal_id_data.to_date,
                    "period":relativedelta(datetime.strptime(str(goal_id_data.to_date), "%Y-%m-%d"), datetime.strptime(str(goal_id_data.from_date), "%Y-%m-%d")).months,
                    "start_amt":goal_id_data.target,
                    "saved_amount":goal_id_data.current_saving,
                    "lines":linesData,
                    "len":len(linesData)
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
                    "status":"success",
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
                "status":"success",
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
        shopping=0.00
        rent=0.00
        subscription=0.00
        transport=0.00
        vacation=0.00
        households=0.00
        others=0.00
        meds=0.00
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
                if rec.spent_on=="shopping":
                    shopping+=rec.amt
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
                if rec.spent_on=="MEDICATIONS":
                        meds+=rec.amt
            category.append({"name":"Others","amount":round(others,2)})
            category.append({"name":"Bill","amount":round(bill,2)})
            category.append({"name":"House Holds","amount":round(households,2)})
            category.append({"name":"Vacation","amount":round(vacation,2)})
            category.append({"name":"Transport","amount":round(transport,2)})
            category.append({"name":"Subscription","amount":round(subscription,2)})
            category.append({"name":"Savings","amount":round(savings,2)})
            category.append({"name":"Renting","amount":round(rent,2)})
            category.append({"name":"Food/Groceries","amount":round(shopping,2)})
            category.append({"name":"Entertainment","amount":round(entertainment,2)})
            category.append({"name":"Income","amount":round(income,2)})
            category.append({"name":"Education","amount":round(education,2)})
            category.append({"name":"Electronics","amount":round(electronics,2)})
            category.append({"name":"Charity","amount":round(charity,2)})
            category.append({"name":"Clothing","amount":round(clothing,2)})
            category.append({"name":"Medication","amount":round(meds,2)})
            return{
                "code":200,
                "status":"success",
                "transactions":transactions,
                "len":len(transactions),
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
        date = data['date']
        period = data['period']
        category=[]
        bill=0.00
        charity=0.00
        clothing=0.00
        electronics=0.00
        income=0.00
        spending=0.00
        education=0.00
        entertainment=0.00
        shopping=0.00
        rent=0.00
        meds=0.00
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
        if not date:
            response = {
                'code': 400,
                'message': 'Date cannot be empty'
            }
            return response
        if not period:
            response = {
                'code': 400,
                'message': 'Period cannot be empty'
            }
            return response
        token = request.env['jwt_provider.access_token'].sudo().search([('is_expired', '!=',True),('token', '=',access_token)])
        account_id= request.env['users.account'].sudo().search([('partner_id.email', '=',token.partner_id.email)])
        if token:
            if data['period']=="Today":
                expenses=account_id.expenditure.sudo().search([("date","=",date),('account_id.partner_id.email', '=',token.partner_id.email)])
                for rec in expenses:
                    if rec.spent_on=="INCOME":
                        income+=rec.amt
                    if rec.spent_on !="INCOME":
                        spending+=rec.amt
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
                        shopping+=rec.amt
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
                    if rec.spent_on=="MEDICATIONS":
                            meds+=rec.amt
                category.append({"name":"Others","amount":round(others,2) if others>0 else round(0.00),"per":round(others/income*100,1) if others>0 else round(0.00)})
                category.append({"name":"Bill","amount":round(bill,2) if bill>0 else round(0.00),"per":round(bill/income*100,1)if bill>0 else round(0.00) })
                category.append({"name":"House Holds","amount":round(households,2) if households>0 else round(0.00),"per":round(households/income*100,1) if households>0 else round(0.00)})
                category.append({"name":"Vacation","amount":round(vacation,2) if vacation>0 else round(0.00),"per":round(vacation/income*100,1) if households>0 else round(0.00) })
                category.append({"name":"Transport","amount":round(transport,2) if transport>0 else round(0.00),"per":round(transport/income*100,1) if transport>0 else round(0.00)})
                category.append({"name":"Subscription","amount":round(subscription,2) if subscription>0 else round(0.00),"per":round(subscription/income*100,1) if subscription>0 else round(0.00)})
                category.append({"name":"Renting","amount":round(rent,2) if rent>0 else round(0.00),"per":round(rent/income*100,1) if rent>0 else round(0.00)})
                category.append({"name":"Food/Groceries","amount":round(0.00) if shopping<1 else round(shopping,2),"per":round(0.00) if shopping<1 else round(shopping/income*100,1)})
                category.append({"name":"Savings","amount":round(saves,2) if saves>0 else round(0.00),"per":round(saves/income*100,1) if saves>0 else round(0.00)})
                category.append({"name":"Entertainment","amount":round(entertainment,2) if entertainment>0 else round(0.00),"per":round(entertainment/income*100,1) if entertainment>0 else round(0.00)})
                category.append({"name":"Education","amount":round(education,2) if education>0 else round(0.00),"per":round(education/income*100,1) if education>0 else round(0.00)})
                category.append({"name":"Electronics","amount":round(electronics,3) if electronics>0 else round(0.00),"per":round(electronics/income*100,1) if electronics>0 else round(0.00)})
                category.append({"name":"Charity","amount":round(charity,2) if charity>0 else round(0.00),"per":round(charity/income*100,1) if charity>0 else round(0.00)})
                category.append({"name":"Clothing","amount":round(clothing,2) if clothing>0 else round(0.00),"per":round(clothing/income*100,1) if clothing>0 else round(0.00)})
                category.append({"name":"Medication","amount":round(meds,2) if meds>0 else round(0.00),"per":round(meds/income*100,1) if meds>0 else round(0.00)})

                return{
                    "code":200,
                    "status":"successfully",
                    "expense":spending,
                    "category":category,
                    "balance":account_id.balance,
                    "Message":"Customer Transactions"
                }
            if data['period']=="thisMonth":
                expenses=account_id.expenditure.sudo().search([('account_id.partner_id.email', '=',token.partner_id.email)])
                for rec in expenses:
                    if rec.spent_on=="INCOME" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        income+=rec.amt
                    if rec.spent_on not in ["INCOME"] and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        spending+=rec.amt
                    if rec.spent_on=="BILL" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        bill+=rec.amt
                    if rec.spent_on=="CHARITY" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        charity+=rec.amt
                    if rec.spent_on=="CLOTHING" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        clothing+=rec.amt
                    if rec.spent_on=="ELECTRONICS" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        electronics+=rec.amt
                    if rec.spent_on=="EDUCATION" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        education+=rec.amt
                    if rec.spent_on=="ENTERTAINMENT" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            entertainment+=rec.amt
                    if rec.spent_on=="FOODGROCERIES" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                        shopping+=rec.amt
                    if rec.spent_on=="RENT" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            rent+=rec.amt
                    if rec.spent_on=="SUBSCRIPTION" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            subscription+=rec.amt
                    if rec.spent_on=="TRANSPORT" and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            transport+=rec.amt
                    if rec.spent_on=="SAVINGS"  and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            saves+=rec.amt
                    if rec.spent_on=="VACATIONS"  and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            vacation+=rec.amt
                    if rec.spent_on=="HOUSEHOLDS"  and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            households+=rec.amt
                    if rec.spent_on=="OTHERS"  and rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            others+=rec.amt
                    if rec.spent_on=="MEDICATIONS" and  rec.date.month==datetime.strptime(str(date),'%m/%d/%Y').month:
                            meds+=rec.amt
                category.append({"name":"Others","amount":round(others,2) if others>0 else round(0.00),"per":round(others/income*100,1) if others>0 else round(0.00)})
                category.append({"name":"Bill","amount":round(bill,2) if bill>0 else round(0.00),"per":round(bill/income*100,1)if bill>0 else round(0.00) })
                category.append({"name":"House Holds","amount":round(households,2) if households>0 else round(0.00),"per":round(households/income*100,1) if households>0 else round(0.00)})
                category.append({"name":"Vacation","amount":round(vacation,2) if vacation>0 else round(0.00),"per":round(vacation/income*100,1) if households>0 else round(0.00) })
                category.append({"name":"Transport","amount":round(transport,2) if transport>0 else round(0.00),"per":round(transport/income*100,1) if transport>0 else round(0.00)})
                category.append({"name":"Subscription","amount":round(subscription,2) if subscription>0 else round(0.00),"per":round(subscription/income*100,1) if subscription>0 else round(0.00)})
                category.append({"name":"Renting","amount":round(rent,2) if rent>0 else round(0.00),"per":round(rent/income*100,1) if rent>0 else round(0.00)})
                category.append({"name":"Food/Groceries","amount":round(shopping,2) if shopping>0 else round(0.00),"per":round(shopping/income*100,1) if shopping>0 else round(0.00)})
                category.append({"name":"Savings","amount":round(saves,2) if saves>0 else round(0.00),"per":round(saves/income*100,1) if saves>0 else round(0.00)})
                category.append({"name":"Entertainment","amount":round(entertainment,2) if entertainment>0 else round(0.00),"per":round(entertainment/income*100,1) if entertainment>0 else round(0.00)})
                category.append({"name":"Education","amount":round(education,2) if education>0 else round(0.00),"per":round(education/income*100,1) if education>0 else round(0.00)})
                category.append({"name":"Electronics","amount":round(electronics,3) if electronics>0 else round(0.00),"per":round(electronics/income*100,1) if electronics>0 else round(0.00)})
                category.append({"name":"Charity","amount":round(charity,2) if charity>0 else round(0.00),"per":round(charity/income*100,1) if charity>0 else round(0.00)})
                category.append({"name":"Clothing","amount":round(clothing,2) if clothing>0 else round(0.00),"per":round(clothing/income*100,1) if clothing>0 else round(0.00)})
                category.append({"name":"Medication","amount":round(meds,2) if meds>0 else round(0.00),"per":round(meds/income*100,1) if meds>0 else round(0.00)})
                return{
                    "code":200,
                    "status":"success",
                    "expense":spending,
                    "category":category,
                    "balance":account_id.balance,
                    "Message":"Customer Transactions"
                }
            if data['period']=="past6Month":
                date_6_ago = (datetime.strptime(str(date),'%m/%d/%Y') + relativedelta(months=-6))
                expenses=account_id.expenditure.sudo().search([("date",">=",date_6_ago),("date","<=",datetime.strptime(str(date),'%m/%d/%Y')),('account_id.partner_id.email', '=',token.partner_id.email)])
                for rec in expenses:
                    if rec.spent_on=="BILL":
                        bill+=rec.amt
                    if rec.spent_on=="INCOME":
                        income+=rec.amt
                    if rec.spent_on not in ["INCOME"]:
                        spending+=rec.amt
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
                        shopping+=rec.amt
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
                    if rec.spent_on=="MEDICATIONS":
                            meds+=rec.amt
                category.append({"name":"Others","amount":round(others,2) if others>0 else round(0.00),"per":round(others/income*100,1) if others>0 else round(0.00)})
                category.append({"name":"Bill","amount":round(bill,2) if bill>0 else round(0.00),"per":round(bill/income*100,1)if bill>0 else round(0.00) })
                category.append({"name":"House Holds","amount":round(households,2) if households>0 else round(0.00),"per":round(households/income*100,1) if households>0 else round(0.00)})
                category.append({"name":"Vacation","amount":round(vacation,2) if vacation>0 else round(0.00),"per":round(vacation/income*100,1) if households>0 else round(0.00) })
                category.append({"name":"Transport","amount":round(transport,2) if transport>0 else round(0.00),"per":round(transport/income*100,1) if transport>0 else round(0.00)})
                category.append({"name":"Subscription","amount":round(subscription,2) if subscription>0 else round(0.00),"per":round(subscription/income*100,1) if subscription>0 else round(0.00)})
                category.append({"name":"Renting","amount":round(rent,2) if rent>0 else round(0.00),"per":round(rent/income*100,1) if rent>0 else round(0.00)})
                category.append({"name":"Food/Groceries","amount":round(shopping,2) if shopping>0 else round(0.00),"per":round(shopping/income*100,1) if shopping>0 else round(0.00)})
                category.append({"name":"Savings","amount":round(saves,2) if saves>0 else round(0.00),"per":round(saves/income*100,1) if saves>0 else round(0.00)})
                category.append({"name":"Entertainment","amount":round(entertainment,2) if entertainment>0 else round(0.00),"per":round(entertainment/income*100,1) if entertainment>0 else round(0.00)})
                category.append({"name":"Education","amount":round(education,2) if education>0 else round(0.00),"per":round(education/income*100,1) if education>0 else round(0.00)})
                category.append({"name":"Electronics","amount":round(electronics,3) if electronics>0 else round(0.00),"per":round(electronics/income*100,1) if electronics>0 else round(0.00)})
                category.append({"name":"Charity","amount":round(charity,2) if charity>0 else round(0.00),"per":round(charity/income*100,1) if charity>0 else round(0.00)})
                category.append({"name":"Clothing","amount":round(clothing,2) if clothing>0 else round(0.00),"per":round(clothing/income*100,1) if clothing>0 else round(0.00)})
                category.append({"name":"Medication","amount":round(meds,2) if meds>0 else round(0.00),"per":round(meds/income*100,1) if meds>0 else round(0.00)})
                return{
                    "code":200,
                    "status":"success",
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
        date = data['date']
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
        if not date:
            response = {
                'code': 400,
                'message': 'Date cannot be empty'
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
                    'date':datetime.strptime(str(date),'%m/%d/%Y'),
                    'spent_on':spent_on.upper(),
                    'account_id':account_id.id,
                    })
                    if expense:
                        account_id.sudo().write({"balance":account_id.balance+expense.amt})
                        return {
                            "code":200,
                            "record":account_id.balance,
                            "type":data["spent_on"],
                            "message":"You have success Created an Income"
                        }
                if spent_on=="SAVINGS":
                    if float(amount)>account_id.balance:
                        return {
                            "code":403,
                            "status":"success",
                            "message":"You do not have enough money in your account"
                        }
                    else:
                        goal_id = request.env['personal.goals'].sudo().search([("id","=",data['goal_id']),('partner_id.email', '=',token.partner_id.email)])
                        if goal_id:
                            expense_id=request.env['account.spend'].sudo().create({
                                'name':name,
                                'amt':amount,
                                'date':datetime.strptime(str(date),'%m/%d/%Y'),
                                'spent_on':spent_on,
                                "goal_id":goal_id.id,
                                'account_id':account_id.id,
                            })
                            if expense_id:
                                goal_id.sudo().write({"current_saving":goal_id.current_saving+expense_id.amt})
                                account_id.sudo().write({"balance":account_id.balance-expense_id.amt})
                                return {
                                    "code":200,
                                    "status":"success",
                                    "type":data["spent_on"],
                                    "message":"You Have Saved for Your Goal"
                                }
                else:
                    if float(amount)>account_id.balance:
                        return {
                            "code":403,
                            "status":"success",
                            "message":"You do not have enough money in your account"
                        }
                    else:
                        expense=request.env['account.spend'].sudo().create({
                            'name':name,
                            'amt':amount,
                            'date':datetime.strptime(str(date),'%m/%d/%Y'),
                            'spent_on':spent_on,
                            'account_id':account_id.id,
                        })
                        if expense:
                            account_id.sudo().write({"balance":account_id.balance-float(amount)})
                            return {
                                "code":200,
                                "record":account_id.balance,
                                "type":data["spent_on"],
                                "message":"You have success Created an Expense"
                            }
        else:
            response = {
                'code': 403,
                'message': 'You don`t have enough permission'
            }
            return response

# https://www.odoo-bs.com/blog/global-5/odoo-barcode-scanner-app-143
# https://apps.odoo.com/apps/modules/15.0/barcode_scanning_sale_purchase/
