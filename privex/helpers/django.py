"""
This module file contains Django-specific helper functions, to help save time when 
developing with the Django framework.


 * handle_error              - Redirects normal web page requests with a session error, outputs JSON with a 
   status code for API queries.

 * is_database_synchronized  - Check if all migrations have been ran before running code.

 * model_to_dict             - Extract an individual Django model instance into a dict (with display names)
 
 * to_json                   - Convert a model Queryset into a plain string JSON array with display names


**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of 
    this software and associated documentation files (the "Software"), to deal in 
    the Software without restriction, including without limitation the rights to use, 
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
    Software, and to permit persons to whom the Software is furnished to do so, 
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all 
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import json
from django.contrib import messages
from django.contrib.messages import add_message
from django.http import JsonResponse, HttpRequest
from django.http.response import HttpResponseRedirectBase
from django.db.migrations.executor import MigrationExecutor
from django.db import connections

def handle_error(request: HttpRequest, err: str, rdr: HttpResponseRedirectBase, status=400):
    """
    Output an error as either a Django session message + redirect, or a JSON response
    based on whether the request was for the API readable version (?format=json) or not.

    Usage:

    >>> from django.shortcuts import redirect
    >>> def my_view(request):
    ...     return handle_error(request, "Invalid password", redirect('/login'), 403)

    :param HttpRequest request:  The Django request object from your view
    :param str err:              An error message as a string to display to the user / api call
    :param HttpResponseRedirectBase rdr:  A redirect() for normal browsers to follow after adding the session error.
    :param int status:           The HTTP status code to return if the request is an API call (default: 400 bad request)
    """
    if request.GET.get('format', '') == 'json':
        return JsonResponse(dict(error=True, message=err), status=status)
    else:
        add_message(request, messages.ERROR, err)
        return rdr

def is_database_synchronized(database: str) -> bool:
    """
    Check if all migrations have been ran. Useful for preventing auto-running code accessing models before the
    tables even exist, thus preventing you from migrating...

    >>> from django.db import DEFAULT_DB_ALIAS
    >>> if not is_database_synchronized(DEFAULT_DB_ALIAS):
    >>>     log.warning('Cannot run reload_handlers because there are unapplied migrations!')
    >>>     return

    :param str database: Which Django database config is being used? Generally just pass django.db.DEFAULT_DB_ALIAS
    :return bool: True if all migrations have been ran, False if not.
    """

    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return False if executor.migration_plan(targets) else True

def model_to_dict(model) -> dict:
    """1 dimensional json-ifyer for any Model"""
    from django.forms import model_to_dict as mtd
    # gets a field on the model, using the display name if available
    def get_display(model, field, default):
        method_name = 'get_{}_display'.format(field)
        return getattr(model, method_name)() if method_name in dir(model) else default

    return {k: get_display(model, k, v) for k, v in mtd(model).items()}

def to_json(query_set) -> str:
    """Iterate a Django query set and dump to json str"""
    return json.dumps([model_to_dict(e) for e in query_set], default=str)
