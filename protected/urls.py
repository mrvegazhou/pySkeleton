# -*- coding: utf-8 -*-
import libs.exceptions
from protected.handlers import index, user, activity, recommend, feedback, ueditor, common, chat, ucenter, ucenterNote, test
from protected.handlers.admin import index as admin_index, system as admin_system, cms as admin_cms
import protected.handlers.handler as baseHandler
handlers = []
sub_handlers = []
ui_modules = {}

front_module_handlers = [
    index,
    user,
    activity,
    recommend,
    feedback,
    ueditor,
    common,
    chat,
    ucenter,
    ucenterNote,
    test
]
handlers = []
for item in front_module_handlers:
    handlers.extend(item.handlers)

admin_module_handlers = [
    admin_index,
    admin_index,
    admin_cms,
]
for item in admin_module_handlers:
    handlers.extend(item.handlers)

# Append default 404 handler, and make sure it is the last one.
handlers.append((r".*", baseHandler.ErrorHandler))

#sub_handlers.append(site.sub_handlers)

for sh in sub_handlers:
    sh.append((r".*", baseHandler.ErrorHandler))