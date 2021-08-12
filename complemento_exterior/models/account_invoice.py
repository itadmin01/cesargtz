# -*- coding: utf-8 -*-

import base64
import json
import requests
import datetime
from lxml import etree

from odoo import fields, models, api,_ 
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, Warning
from odoo.tools import float_is_zero, float_compare
from reportlab.graphics.barcode import createBarcodeDrawing, getCodes
from reportlab.lib.units import mm

import logging
_logger = logging.getLogger(__name__)

class InfoSerieMercancias(models.Model):
    _name = 'account.invoice.mercancias.series'
    _rec_name = "cce_numeroserie"

    cce_numeroserie = fields.Char(string='Número de serie')	
    order_id = fields.Many2one('account.invoice.mercancias.info', string='Serie', ondelete='cascade', index=True, copy=False)

class InfoMercancias(models.Model):
    _name = 'account.invoice.mercancias.info'
    _rec_name = "nombre"

    nombre = fields.Char(string='Nombre')
    cce_marca = fields.Char(string='Marca')
    cce_modelo = fields.Char(string='Modelo')
    cce_submodelo = fields.Char(string='SubModelo')
    cce_series = fields.One2many('account.invoice.mercancias.series', 'order_id', 'Series Mercancias',
        copy=True, readonly=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})


class MercanciasComplemento(models.Model):
    _name = 'account.invoice.mercancias'
    
    #noidentificacion = fields.Char(string=_('No. identificación'))
    product_id = fields.Many2one('product.product', string='Producto', change_default=True, ondelete='restrict', required=True)
    fraccionarancelaria = fields.Many2one('catalogos.fraccionarancelaria', string='Fracción Arancelaria')
    cantidadaduana = fields.Float(string='Cantidad aduana', default=1.0, digits=dp.get_precision('Product Price'))
    valorunitarioaduana = fields.Float(string='Valor unitario USD', digits=dp.get_precision('Product Price'))
    valordolares = fields.Float(string='Valor dólares', compute='_compute_total_amount', digits=dp.get_precision('Product Price'))
    unidadAduana = fields.Many2one('catalogos.unidadmedidaaduana', string='Unidad aduana')
    info_mercancias = fields.Many2one('account.invoice.mercancias.info', string='Información mercancia')
#    info_check = fields.boolean(string='Misma información', default=False)
    order_id = fields.Many2one('account.invoice', string='Mercancias', required=True, ondelete='cascade', index=True, copy=False)

    @api.one
    @api.depends('valorunitarioaduana', 'cantidadaduana')
    def _compute_total_amount(self):
        self.valordolares = float(self.valorunitarioaduana) * float(self.cantidadaduana)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cce_mercancias = fields.One2many('account.invoice.mercancias', 'order_id', 'Mercancias Complemento Exterior',
        copy=True, readonly=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    cce_habilitar = fields.Selection([('no', 'No'), ('si', 'Si')], string='Habilitar comercio exterior')
	
    cce_tipooperacion = fields.Selection([('2', '2')], string='Tipo de operación')
    cce_clavedepedimento = fields.Selection([('A1', 'A1')], string='Clave de pedimento')
    cce_certificadoorigen = fields.Selection([('0', '0 - No Funge como certificado de origen'), ('1', '1- Funge como certificado origen')], string='Certificado origen')
    cce_numcertificadoorigen = fields.Char(string=_('Folio del certificado de origen'))
    cce_numeroexportadorconfiable = fields.Char(string=_('Número de exportador confiable'))
    cce_incoterm = fields.Selection(
        selection=[('CFR', 'CFR - Coste y flete (ppuerto de destino convenido)'), 
                   ('CIF', 'CIF - Coste, seguro y flete (puerto de destino convenido)'), 
                   ('CPT', 'CPT - Transporte pagado hasta (el lugar de destino convenido)'),
                   ('CIP', 'CIP - Transporte y seguro pagados hasta (lugar de destino convenido)'), 
                   ('DAF', 'DAF - Entregada en frontera (lugar convenido)'),
                   ('DAP', 'DAP - Entregada en lugar'), 
                   ('DAT', 'DAT - Entregada en terminal'), 
                   ('DES', 'DES - Entregada sobre buque (puerto de destino convenido)'), 
                   ('DEQ', 'DEQ - Entregada en muelle (puerto de destino convenido)'), 
                   ('DDU', 'DDU - Entregada derechos no pagados (lugar de destino convenido)'), 
                   ('DDP', 'DDP - Entregada derechos pagados (lugar de destino convenido)'),				   
                   ('EXW', 'EXW - En fábrica (lugar convenido)'), 
                   ('FCA', 'FCA - Franco transportista (lugar designado)'), 
                   ('FAS', 'FAS - Franco al costado del buque (puerto de carga convenido)'), 
                   ('FOB', 'FOB - Franco a bordo (puerto de carga convenido)'),],
        string=_('INCOTERM'),
    )
    cce_subdivision = fields.Selection([('0', '0')], string='Subdivisión')
    cce_tipocambiousd = fields.Float(string='Tipo de cambio USD')
    cce_totalusd = fields.Float(string='Total USD', compute='_compute_total_usd', digits=dp.get_precision('Product Price'))
    cce_motivo_traslado = fields.Selection(
        selection=[('01', 'Envío de mercancias facturadas con anterioridad'), 
                   ('02', 'Reubicación de mercancías propias'), 
                   ('03', 'Envío de mercancías objeto de contrato de consignación'),
                   ('04', 'Envío de mercancías para posterior enajenación'), 
                   ('05', 'Envío de mercancías propiedad de terceros'),
                   ('99', 'Otros'),],
        string=_('Motivo de traslado'),
    )
    cee_propietario_id = fields.Many2one('res.partner', string='Propietario')

    @api.one
    @api.depends('cce_mercancias')
    def _compute_total_usd(self):
        self.cce_totalusd = sum([l.valordolares for l in self.cce_mercancias])	


    @api.model
    def to_json(self):
        res = super(AccountInvoice,self).to_json()

        if self.cce_habilitar == 'si':
                res.update({
                     'cce_comercioext': {
                            'cce_tipooperacion': self.cce_tipooperacion,
                            'cce_clavedepedimento': self.cce_clavedepedimento,
                            'cce_certificadoorigen': self.cce_certificadoorigen,
                            'cce_numeroexportadorconfiable': self.cce_numeroexportadorconfiable,
                            'cce_incoterm': self.cce_incoterm,
                            'cce_subdivision': self.cce_subdivision,
                            'cce_tipocambiousd': self.cce_tipocambiousd,
                            'cce_motivo_traslado': self.cce_motivo_traslado,
                            'cce_totalusd': self.cce_totalusd,
                     },
                     'cce_emisor': {
                            'cce_curp': self.company_id.cce_curp,
                            'cce_calle': self.company_id.cce_calle,
                            'cce_no_exterior': self.company_id.cce_no_exterior,
                            'cce_no_interior': self.company_id.cce_no_interior,
                            'cce_clave_colonia': self.company_id.cce_clave_colonia.c_colonia,
                            'cce_clave_localidad': self.company_id.cce_clave_localidad.c_localidad,
                            'cce_clave_municipio': self.company_id.cce_clave_municipio.c_municipio,
                            'cce_clave_estado': self.company_id.cce_clave_estado.c_estado,
                            'cce_clave_pais': self.company_id.cce_clave_pais.c_pais,
                            'cce_cp': self.company_id.zip,
                            'cce_referencia': self.company_id.cce_referencia,
                      },
                      'cce_receptor': {
                            'cce_calle': self.partner_id.cce_calle,
                            'cce_no_exterior': self.partner_id.cce_no_exterior,
                            'cce_no_interior': self.partner_id.cce_no_interior,
                            'cce_clave_colonia': self.partner_id.cce_clave_colonia.c_colonia,
                            'cce_clave_localidad': self.partner_id.cce_clave_localidad.c_localidad,
                            'cce_clave_municipio': self.partner_id.cce_clave_municipio.c_municipio,
                            'cce_clave_estado': self.partner_id.cce_clave_estado.c_estado,
                            'cce_clave_pais': self.partner_id.cce_clave_pais.c_pais,
                            'cce_cp': self.partner_id.zip,
                      },
                })
                if self.cee_propietario_id:
                     res.update({'cce_propietario': {
                                           'cee_numregidtrib': self.cee_propietario_id.registro_tributario,
                                           'cee_residenciafiscal': self.cee_propietario_id.residencia_fiscal,
                                           },
                                        })

                mercancia_cce = []
                series_len = 0
                for merc in self.cce_mercancias:
                   aux_marca = False
                   aux_modelo = False
                   aux_submodelo = False
                   serie_mercancia = []
                   if merc.info_mercancias:
                      for info in merc.info_mercancias:
                          aux_marca = info.cce_marca
                          aux_modelo = info.cce_modelo
                          aux_submodelo = info.cce_submodelo
                          if info.cce_series:
                             for serie in info.cce_series:
                                 serie_mercancia.append({'serie': serie.cce_numeroserie,})
                             series_len =  len(info.cce_series)
                   if series_len > 0:
                      if series_len != merc.cantidadaduana:
                          raise UserError(_('No son iguales el número de series registradas en Información mercancia que la cantidad de productos registrados en aduana'))
                   _logger.info('numero series %s', series_len)

                   mercancia_cce.append({
                            'cce_noidentificacion': merc.product_id.code,
                            'cce_fraccionarancelaria': merc.fraccionarancelaria.c_fraccionarancelaria,
                            'cce_cantidadaduana': merc.cantidadaduana,
                            'cce_valorunitarioaduana': merc.valorunitarioaduana,
                            'cce_valordolares': merc.valordolares,
                            'cce_unidadAduana': merc.unidadAduana.c_unidadmedidaaduana,
                            'cce_marca': aux_marca,
                            'cce_modelo': aux_modelo,
                            'cce_submodelo': aux_submodelo,
                            'cce_serie': serie_mercancia,
                            'cce_no_serie': series_len,
                   })
                if mercancia_cce:
                    cce_mercancias = {'numerodepartidas': len(self.cce_mercancias)}
                    cce_mercancias.update({'cce_mercancias_lista': mercancia_cce})
                    res.update({'cce_mercancia': cce_mercancias})
        return res

