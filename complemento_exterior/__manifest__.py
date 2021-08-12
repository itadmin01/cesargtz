# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT admin
#
##############################################################################

{
    'name': 'Complemento Comercio Exterior',
    'version': '12.04',
    'description': ''' Agrega campos para timbrar facturas CFDI 3.3 con el complemento de comercio exterior
    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'depends': [
        'base','sale', 'cdfi_invoice', 'catalogos_cfdi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'report/invoice_report.xml',
    ],
    'application': False,
    'installable': True,
}
