# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import re
import uuid

from odoo.exceptions import ValidationError
from odoo.tools import is_list_of

# uuid PKs: a list of uuid ids assigned to a Char/Text field is stored via repr,
# e.g. "[UUID('019ee...'), ...]". ast.literal_eval cannot parse UUID(...) (a call),
# so normalise it to quoted strings "['019ee...', ...]" before evaluating.
_UUID_REPR_RE = re.compile(r"UUID\((('[0-9a-fA-F-]+')|(\"[0-9a-fA-F-]+\"))\)")


def parse_res_ids(res_ids, env):
    """ Returns the already valid list/tuple of int or returns the literal eval
    of the string as a list/tuple of int. Void strings / missing values are
    evaluated as an empty list.

    :param str|tuple|list res_ids: a list of ids, tuple or list;

    :raise: ValidationError if the provided res_ids is an incorrect type or
      invalid format;

    :return list: list of ids
    """
    if is_list_of(res_ids, (uuid.UUID, str)) or not res_ids:
        return res_ids
    error_msg = env._(
        "Invalid res_ids %(res_ids_str)s (type %(res_ids_type)s)",
        res_ids_str=res_ids,
        res_ids_type=str(res_ids.__class__.__name__),
    )
    try:
        res_ids = ast.literal_eval(res_ids)
    except Exception as e:
        if isinstance(res_ids, str) and 'UUID(' in res_ids:
            try:
                res_ids = ast.literal_eval(_UUID_REPR_RE.sub(r"\1", res_ids))
            except Exception:
                raise ValidationError(error_msg) from e
        else:
            raise ValidationError(error_msg) from e

    if not is_list_of(res_ids, (uuid.UUID, str)):
        raise ValidationError(error_msg)

    return res_ids
