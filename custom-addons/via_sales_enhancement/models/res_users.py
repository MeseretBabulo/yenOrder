# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    # def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):

        context = self._context or {}
        args = args or []
        if self.env.context.get('project_task_id', False):
            task_id = self.env['project.task'].browse(self.env.context.get('project_task_id'))
            if task_id:
                args.append(('id', 'in', task_id and task_id.team_id and task_id.team_id.member_ids and task_id.team_id.member_ids.ids))
        # return super(ResUsers, self)._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid) 
        return super(ResUsers, self)._search(args, offset, limit, order, access_rights_uid=access_rights_uid) 