from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
from datetime import datetime
from tornado.options import options
import re
from protected.conf.debug import logger
num_compile = re.compile("^[0-9]*$")

class FrontBaseModel(AdminBaseModel):

    _page_size = options.page['page_size']
    _reply_page_size = options.page['reply_page_size']
    _comment_page_size = options.page['comment_page_size']

    def __init__(self):
        super(FrontBaseModel, self).__init__()
