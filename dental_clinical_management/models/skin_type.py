from odoo import models, fields

class SkinType(models.Model):
    _name = 'beauty.skin.type'
    _description = 'Beauty Skin Type'
    
    name = fields.Char(string='Skin Type', required=True)
