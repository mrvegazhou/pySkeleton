# -*- coding: utf-8 -*-
import logging
import protected.libs.MyCrypt as crypter
from protected.extensions.chat.multicast.sender import sender

def multicast_sender(messages, msg_type, local_node_id=None):
    """
    Send message to multicast channel.
    messages: message need to send.
    msg_type: type of message, can be "message" or "command".
    """
    msg = dict(
        node_id = local_node_id,
        msg_type = msg_type,
        body = messages
    )
    msg = str(msg)
    msg = crypter.encrypt(msg)
    try:
        if sender(msg):
            logging.warning("Send %d to multicast channel." % len(messages))
    except Exception, e:
        return False
    return True