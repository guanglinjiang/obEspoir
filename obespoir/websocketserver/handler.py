# coding=utf-8
"""
author = jamon
"""

import asyncio
import ujson

from websockets.exceptions import ConnectionClosed

from obespoir.share.singleton import Singleton
from obespoir.share.ob_log import logger
from obespoir.base.common_define import NodeType
from obespoir.base.ob_protocol import DataException
from obespoir.base.global_object import GlobalObject
from obespoir.websocketserver.route import webSocketRouteHandle
from obespoir.rpcserver.push_lib import push_message


class WebsocketHandler(object, metaclass=Singleton):

    def __init__(self):
        pass

    async def websocket_handler(self, websocket, path):
        print(websocket.remote_address, path)
        while True:
            try:
                data = await asyncio.wait_for(websocket.recv(), timeout=GlobalObject().ws_timeout)
                logger.debug('websocketserver received {!r}'.format(data))
                # await websocket.send("hello")
                while data:  # 解决TCP粘包问题
                    data = await websocket.process_data(data, websocket)
            except asyncio.TimeoutError:
                logger.info("{} connection timeout!".format(websocket.remote_address))
                await websocket.close()
            except ConnectionClosed as e:
                logger.info("{} connection lose ({}, {})".format(websocket.remote_address,e.code, e.reason))
                return 0
            except DataException as e:
                logger.info("data decrypt error!")
                await websocket.close()
                return 0


@webSocketRouteHandle
async def forward_0(command_id, data, session_id):
    """
    消息转发
    :param command_id: int
    :param data: json
    :param session_id: string
    :return: None
    """
    print("forward_0", command_id, data, type(data), data, session_id)
    if not isinstance(data, dict):
        try:
            data = ujson.loads(data)
            print("data type :", type(data))
        except Exception:
            logger.warn("param data parse error {}".format(data))
            return {}
    data.update({"message_id": command_id})
    await push_message(NodeType.ROUTE, command_id, data, session_id=session_id, to=None)
