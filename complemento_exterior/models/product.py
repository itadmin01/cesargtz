# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fraccionarancelaria = fields.Many2one('catalogos.fraccionarancelaria', string='Fracción Arancelaria')
    unidadAduana = fields.Many2one('catalogos.unidadmedidaaduana', string='Unidad aduana')
