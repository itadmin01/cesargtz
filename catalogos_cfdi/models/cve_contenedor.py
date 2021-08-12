# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CveContenedor(models.Model):
    _name = 'cve.contenedor'
    _rec_name = "clave"

    clave = fields.Char(string='Clave')
    tipo_contenedor = fields.Char(string='Tipo de contenedor')
    descripcion = fields.Char(string='Descripción')
