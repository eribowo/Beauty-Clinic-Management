from odoo import api, fields, models, _

class DentalPrescription(models.Model):
    """Prescription of patient from the dental clinic"""
    _name = 'dental.prescription'
    _description = "Dental Prescription"
    _inherit = ['mail.thread']
    _rec_name = "sequence_no"

    sequence_no = fields.Char(string='Sequence No', required=True,
                              readonly=True, default=lambda self: _('New'),
                              help="Sequence number of the dental prescription")
    appointment_ids = fields.Many2many('dental.appointment',
                                       string="Appointment",
                                       compute="_compute_appointment_ids",
                                       help="All appointments created")
    appointment_id = fields.Many2one('dental.appointment',
                                     string="Appointment",
                                     domain="[('id','in',appointment_ids)]",
                                     required=True,
                                     help="All appointments created")
    patient_id = fields.Many2one(related="appointment_id.patient_id",
                                 string="Patient",
                                 required=True,
                                 help="name of the patient")
    token_no = fields.Integer(related="appointment_id.token_no",
                              string="Token Number",
                              help="Token number of the patient")
    treatment_ids = fields.Many2many(related="appointment_id.treatment_ids",
                                     string="Treatments",
                                     help="Treatments done for patient")
    cost = fields.Float(compute="_compute_total_cost",
                        string="Total Treatment Cost",
                        help="Total cost of treatments")
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  required=True,
                                  help="To add the currency type in cost")
    prescribed_doctor_id = fields.Many2one(related="appointment_id.doctor_id",
                                           string='Prescribed Doctor',
                                           required=True,
                                           help="Doctor who is prescribed")
    prescription_date = fields.Date(related="appointment_id.date",
                                    string='Prescription Date',
                                    required=True,
                                    help="Date of the prescription")
    state = fields.Selection([('new', 'New'),
                              ('done', 'Prescribed'),
                              ('invoiced', 'Invoiced')],
                             default="new",
                             string="state",
                             help="state of the appointment")
    medicine_ids = fields.One2many('dental.prescription_lines',
                                   'prescription_id',
                                   string="Medicine",
                                   help="medicines")
    invoice_data_id = fields.Many2one(comodel_name="account.move", string="Invoice Data",
                                      help="Invoice Data")
    grand_total = fields.Float(compute="_compute_grand_total",
                               string="Grand Total",
                               help="Get the grand total amount")
    doctor_commission_amount = fields.Float(
        string="Komisi Dokter",
        compute="_compute_doctor_commission_amount",
        store=True
    )

    @api.model
    def create(self, vals):
        """Function declared for creating sequence Number for patients"""
        if vals.get('sequence_no', _('New')) == _('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                'dental.prescriptions') or _('New')
        res = super(DentalPrescription, self).create(vals)
        return res

    @api.depends('appointment_id')
    def _compute_appointment_ids(self):
        """Computes and assigns the `appointment_ids` field for each record.
        This method searches for all `dental.appointment` records that have
        a state of `new` and a date equal to today's date. It then updates
        the `appointment_ids` field of each `DentalPrescription` record
        with the IDs of these found appointments."""
        for rec in self:
            rec.appointment_ids = self.env['dental.appointment'].search(
                [('state', '=', 'new'), ('date', '=', fields.Date.today())]).ids

    @api.depends('medicine_ids', 'treatment_ids')
    def _compute_doctor_commission_amount(self):
        """Computes the commission amount for the doctor based on the medicines and treatments"""
        for record in self:
            commission_amount = 0.0
            for medicine in record.medicine_ids:
                if medicine.medicament_id.doctor_commission_percentage:
                    commission_amount += (medicine.price * medicine.quantity * medicine.medicament_id.doctor_commission_percentage) / 100
            for treatment in record.treatment_ids:
                if treatment.doctor_commission_percentage:
                    commission_amount += (treatment.cost * treatment.doctor_commission_percentage) / 100
            record.doctor_commission_amount = commission_amount

    @api.depends('treatment_ids')
    def _compute_total_cost(self):
        """Computes the total cost of treatments."""
        for rec in self:
            rec.cost = sum(treatment.cost for treatment in rec.treatment_ids)

    def action_prescribed(self):
        """Marks the prescription and its associated appointment as `done`.
        This method updates the state of both the DentalPrescription instance
        and its linked dental.appointment instance to `done`, indicating that
        the prescription has been finalized and the appointment has been completed.
        """
        self.state = 'done'
        self.appointment_id.state = 'done'

    def create_invoice(self):
        """Create an invoice based on the patient invoice."""
        self.ensure_one()
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'name': treatment.name,
                    'quantity': 1,
                    'price_unit': treatment.cost,
                }) for treatment in self.treatment_ids
            ]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        for rec in self.medicine_ids:
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', rec.medicament_id.id)])
            invoice['invoice_line_ids'] = [(0, 0, {
                'product_id': product_id.id,
                'name': rec.display_name,
                'quantity': rec.quantity,
                'price_unit': rec.price,
            })]
        self.invoice_data_id = invoice.id
        invoice.action_post()
        self.state = 'invoiced'
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def action_view_invoice(self):
        """Invoice view"""
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def _compute_grand_total(self):
        """Computes the grand total cost of the dental prescription."""
        self.grand_total = self.cost
        for rec in self.medicine_ids:
            self.grand_total += rec.total


class DentalPrescriptionLines(models.Model):
    """Prescription lines of the dental clinic prescription"""
    _name = 'dental.prescription_lines'
    _description = "Dental Prescriptions Lines"
    _rec_name = "medicament_id"

    medicament_id = fields.Many2one('product.template',
                                    domain="[('sale_ok', '=', True)]",
                                    string="Medicament",
                                    help="Name of the medicament")
    generic_name = fields.Char(string="Generic Name",
                               related="medicament_id.generic_name",
                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",
                                     related="medicament_id.dosage_strength",
                                     help="Dosage strength of medicament")
    medicament_form = fields.Selection([('tablet', 'Tablets'),
                                        ('capsule', 'Capsules'),
                                        ('liquid', 'Liquid'),
                                        ('injection', 'Injections')],
                                       string="Medicament Form",
                                       required=True,
                                       help="Add the form of the medicine")
    quantity = fields.Integer(string="Quantity",
                              required=True,
                              help="Quantity of medicine")
    frequency_id = fields.Many2one('medicine.frequency',
                                   string="Frequency",
                                   required=True,
                                   help="Frequency of medicine")
    price = fields.Float(related='medicament_id.list_price',
                         string="Price",
                         help="Cost of medicine")
    total = fields.Float(string="Total Price",
                         help="Total price of medicine")
    prescription_id = fields.Many2one('dental.prescription',
                                      help="Relate the model with dental_prescription")

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """Updates the total price of the medicament based on the quantity.
        """
        for rec in self:
            rec.total = rec.price * rec.quantity

    @api.model
    def create(self, vals):
        """Ensure the medicament is marked as 'Is Medicine' when created"""
        if 'medicament_id' in vals:
            medicament = self.env['product.template'].browse(vals['medicament_id'])
            medicament.write({'is_medicine': True})
        return super(DentalPrescriptionLines, self).create(vals)
