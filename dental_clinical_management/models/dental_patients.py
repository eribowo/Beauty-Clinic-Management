from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_normalize

class DentalPatients(models.Model):
    """To create Patients in the clinic, use res.partner model and customize it"""
    _inherit = 'res.partner'

    company_type = fields.Selection(selection_add=[('person', 'Patient'),
                                                   ('company', 'Medicine Distributor')],
                                    help="Patient type")
    dob = fields.Date(string="Date of Birth",
                      help="DOB of the patient")
    patient_age = fields.Integer(compute='_compute_patient_age',
                                 store=True,
                                 string="Age",
                                 help="Age of the patient")
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')],
                           string="Sex",
                           help="Sex of the patient")
    insurance_company_id = fields.Many2one('insurance.company',
                                           string="Insurance Company",
                                           help="Mention the insurance company")
    start_date = fields.Date(string="Member Since",
                             help="Patient insurance start date")
    expiration_date = fields.Date(string="Expiration Date",
                                  help="Patient insurance expiration date")
    insureds_name = fields.Char(string="Insured's Name",
                                help="Name of the insured's")
    identification_number = fields.Char(string="Identification Number",
                                        help="Identification Number of insured's")
    is_patient = fields.Boolean(string="Is Patient",
                                help="To set it's a patient")
    medical_questionnaire_ids = fields.One2many('medical.questionnaire',
                                                'patient_id',
                                                readonly=False,
                                                help="connect model medical questionnaire in patients")
    report_ids = fields.One2many('xray.report', 'patient_id',
                                 string='X-Ray',
                                 help="To add the xray reports of the patient")

    # New fields for Beauty and Skincare Clinic
    skin_type = fields.Selection([
        ('dry', 'Dry'),
        ('oily', 'Oily'),
        ('combination', 'Combination'),
        ('sensitive', 'Sensitive'),
    ], string='Skin Type')
    
    past_treatments = fields.Text(string='Past Treatments')
    allergies = fields.Text(string='Known Allergies')
    preferred_products = fields.Text(string='Preferred Products')

    @api.model
    def create(self, vals):
        if 'company_type' in vals and vals['company_type'] == 'person':
            vals['is_patient'] = True
        res = super(DentalPatients, self).create(vals)
        if 'company_type' in vals and vals['company_type'] == 'person':
            if res.email:
                wizard = self.env['portal.wizard'].create({
                    'partner_ids': [fields.Command.link(res.id)]
                })
                portal_wizard = self.env['portal.wizard.user'].sudo().create({
                    'partner_id': res.id,
                    'email': res.email,
                    'wizard_id': wizard.id,
                })
                portal_wizard.action_grant_access()
        else:
            if res.email:
                try:
                    user = self.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
                        'email': email_normalize(res.email),
                        'login': email_normalize(res.email),
                        'partner_id': res.id,
                        'groups_id': [
                            self.env.ref("base.group_user").id,
                            self.env.ref('dental_clinical_management.group_dental_doctor').id,
                            self.env.ref('sales_team.group_sale_salesman').id,
                            self.env.ref('hr.group_hr_user').id,
                            self.env.ref('account.group_account_invoice').id,
                            self.env.ref('stock.group_stock_user').id,
                            self.env.ref('purchase.group_purchase_user').id
                        ],
                        'company_id': self.env.company.id,
                        'company_ids': [(6, 0, self.env.company.ids)],
                    })
                    self.env['hr.employee'].search([('work_email', '=', res.email)]).user_id = user.id
                except:
                    raise UserError(_("Email already used for another dentist"))
        return res

    @api.depends('dob')
    def _compute_patient_age(self):
        for record in self:
            record.patient_age = (fields.date.today().year - record.dob.year -
                                  ((fields.date.today().month, fields.date.today().day) <
                                   (record.dob.month, record.dob.day))) if record.dob else False
