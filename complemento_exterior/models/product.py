# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    cce_marca = fields.Char(string='Marca')
    cce_modelo = fields.Char(string='Modelo')
    cce_submodelo = fields.Char(string='SubModelo')
    cce_numeroserie = fields.Char(string='Número de serie')	
