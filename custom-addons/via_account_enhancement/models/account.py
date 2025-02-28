# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_company(self.journal_id.company_id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=', 'receivable' if self.move_type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date,
                                                                  currency=self.company_id.currency_id)
                if self.env.context.get('journal_move_line_id'):
                    if self.currency_id == self.company_id.currency_id:
                        # Single-currency.
                        return ((b[0], b[1], b[1],  (self.name or '') + ' ' + ( self.env.context.get('journal_move_line_id') and self.env.context.get('journal_move_line_id').name or '')) for b in to_compute)
                    else:
                        # Multi-currencies.
                        to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                                   currency=self.currency_id)
                        return ((b[0], b[1], ac[1],  (self.name or '') + ' ' + ( self.env.context.get('journal_move_line_id') and self.env.context.get('journal_move_line_id').name or '')) for b, ac in zip(to_compute, to_compute_currency))
                else:
                    if self.currency_id == self.company_id.currency_id:
                        # Single-currency.
                        return ((b[0], b[1], b[1]) for b in to_compute)
                    else:
                        # Multi-currencies.
                        to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                                   currency=self.currency_id)
                        return ((b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency))
            else:
                if self.env.context.get('journal_move_line_id'):
                    return (fields.Date.to_string(date), total_balance, total_amount_currency, (self.name or '') + ' ' + ( self.env.context.get('journal_move_line_id') and self.env.context.get('journal_move_line_id').name or ''))
                else:

                    return (fields.Date.to_string(date), total_balance, total_amount_currency)


        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0
            is_not_special_count = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            to_compute_new = []
            if self.move_type not in ['out_invoice', 'out_refund']:
                to_compute_new.append(to_compute)
                to_compute = to_compute_new
            if self.env.context.get('label'):
                for date_maturity, balance, amount_currency, label in to_compute:
                    currency = self.journal_id.company_id.currency_id
                    if currency and currency.is_zero(balance) and len(to_compute) > 1:
                        continue

                    if existing_terms_lines_index < len(existing_terms_lines):
                        # Update existing line.
                        candidate = existing_terms_lines[existing_terms_lines_index]
                        existing_terms_lines_index += 1
                        candidate.update({
                            'date_maturity': date_maturity,
                            'amount_currency': -amount_currency,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'name':  self.payment_reference or label or ''
                        })
                    else:
                        # Create new line.
                        create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                            'account.move.line'].create
                        candidate = create_method({
                            'name': self.payment_reference or label or '',
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'quantity': 1.0,
                            'amount_currency': -amount_currency,
                            'date_maturity': date_maturity,
                            'move_id': self.id,
                            'currency_id': self.currency_id.id,
                            'account_id': account.id,
                            'partner_id': self.commercial_partner_id.id,
                            'exclude_from_invoice_tab': True,
                        })

                    new_terms_lines += candidate
                    candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
            else:
                for date_maturity, balance, amount_currency in to_compute:
                    currency = self.journal_id.company_id.currency_id
                    if currency and currency.is_zero(balance) and len(to_compute) > 1:
                        continue

                    if existing_terms_lines_index < len(existing_terms_lines):
                        # Update existing line.
                        candidate = existing_terms_lines[existing_terms_lines_index]
                        existing_terms_lines_index += 1
                        candidate.update({
                            'date_maturity': date_maturity,
                            'amount_currency': -amount_currency,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                        })
                    else:
                        # Create new line.
                        create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                        candidate = create_method({
                            'name': self.payment_reference or '',
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'quantity': 1.0,
                            'amount_currency': -amount_currency,
                            'date_maturity': date_maturity,
                            'move_id': self.id,
                            'currency_id': self.currency_id.id,
                            'account_id': account.id,
                            'partner_id': self.commercial_partner_id.id,
                            'exclude_from_invoice_tab': True,
                        })
                    new_terms_lines += candidate
                    # if in_draft_mode:
                    candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))


        if not others_lines:
            self.line_ids -= existing_terms_lines
            return
        computation_date = _get_payment_terms_computation_date(self)
        to_compute = []
        account = _get_payment_terms_account(self, existing_terms_lines)
        is_special_product_lines = others_lines

        if self.move_type in ['out_invoice', 'out_refund']:
            for ex_line in is_special_product_lines:
                to_compute += [(_compute_payment_terms(self.with_context(journal_move_line_id=ex_line), computation_date, ex_line.balance, ex_line.amount_currency))]
            new_terms_lines = _compute_diff_payment_terms_lines(self.with_context(label=True), existing_terms_lines, account, to_compute)
            self.line_ids -= existing_terms_lines - new_terms_lines
        else:
            to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
            new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

            # Remove old terms lines that are no longer needed.
            self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            if self.move_type not in ['out_invoice', 'out_refund']:
                self.payment_reference = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            future_moves.auto_post = True
            for move in future_moves:
                msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
        if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_("You don't have the access rights to post an invoice."))
        for move in to_post:

            if move.partner_bank_id and not move.partner_bank_id.active:
                raise UserError(_("The recipient bank account link to this invoice is archived.\nSo you cannot confirm the invoice."))
            if move.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
            if not move.line_ids.filtered(lambda line: not line.display_type):
                raise UserError(_('You need to add a line before posting.'))
            if move.auto_post and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
            if not move.journal_id.active:
                raise UserError(_(
                    "You cannot post an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))

            if not move.partner_id:
                if move.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif move.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
                raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

            if move.display_inactive_currency_warning:
                raise UserError(_("You cannot validate an invoice with an inactive currency: %s",
                                  move.currency_id.name))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if not move.invoice_date:
                if move.is_sale_document(include_receipts=True):
                    move.invoice_date = fields.Date.context_today(self)
                    move.with_context(check_move_validity=False)._onchange_invoice_date()
                elif move.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

            # When the accounting date is prior to a lock date, change it automatically upon posting.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                move.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report)
                if move.move_type and move.move_type != 'entry':
                    move.with_context(check_move_validity=False)._onchange_currency()

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.mapped('line_ids').create_analytic_lines()

        for move in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = move.is_invoice() and move.line_ids.filtered(lambda aml: aml.partner_id != move.commercial_partner_id and not aml.display_type)
            if wrong_lines:
                wrong_lines.write({'partner_id': move.commercial_partner_id.id})

        to_post.write({
            'state': 'posted',
            'posted_before': True,
        })

        for move in to_post:
            move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

            # Compute 'ref' for 'out_invoice'.
            if move._auto_compute_invoice_reference():
                to_write = {
                    'payment_reference': move._get_invoice_computed_reference(),
                    'line_ids': []
                }
                # add below condition for update the name field in journal
                if move.move_type not in ['out_invoice', 'out_refund']:
                    for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                        to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
                else:
                    for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                        to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference'] + ' ' + (line.name or '')}))
                move.write(to_write)

        for move in to_post:
            if move.is_sale_document() \
                    and move.journal_id.sale_activity_type_id \
                    and (move.journal_id.sale_activity_user_id or move.invoice_user_id).id not in (self.env.ref('base.user_root').id, False):
                move.activity_schedule(
                    date_deadline=min((date for date in move.line_ids.mapped('date_maturity') if date), default=move.date),
                    activity_type_id=move.journal_id.sale_activity_type_id.id,
                    summary=move.journal_id.sale_activity_note,
                    user_id=move.journal_id.sale_activity_user_id.id or move.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for move in to_post:
            if move.is_sale_document():
                customer_count[move.partner_id] += 1
            elif move.is_purchase_document():
                supplier_count[move.partner_id] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices in amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        ).action_invoice_paid()

        # Force balance check since nothing prevents another module to create an incorrect entry.
        # This is performed at the very end to avoid flushing fields before the whole processing.
        to_post._check_balanced()
        return to_post
