import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ActivityConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'activities'

    async def connect(self):
        logger.info(f"Intentando conectar WebSocket. Path: {self.scope.get('path')}")
        
        # Log de headers y cookies para debugging
        headers = dict(self.scope.get('headers', []))
        cookies = self.scope.get('cookies', {})
        logger.info(f"Headers recibidos: {headers}")
        logger.info(f"Cookies recibidas: {cookies}")
        logger.info(f"Session key: {self.scope.get('session', {}).get('_session_key', 'No session')}")
        
        user = self.scope.get('user')
        logger.info(f"Usuario en scope: {user}, autenticado: {user.is_authenticated if user else False}")
        
        if not user or not user.is_authenticated:
            logger.warning(f"Usuario no autenticado, cerrando conexión. User: {user}")
            logger.warning(f"Cookies disponibles: {cookies}")
            logger.warning(f"Session disponible: {self.scope.get('session', {})}")
            await self.close(code=4001)
            return

        try:
            logger.info(f"Usuario autenticado: {user.username}, agregando al grupo '{self.GROUP_NAME}'")
            # Verificar que channel_layer esté disponible
            if not self.channel_layer:
                logger.error("Channel layer no disponible en el consumer")
                await self.close(code=4003)
                return
            
            await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
            await self.accept()
            logger.info(f"Conexión WebSocket aceptada para usuario: {user.username}, channel_name: {self.channel_name}")
        except Exception as e:
            logger.error(f"Error al aceptar conexión WebSocket: {e}", exc_info=True)
            await self.close(code=4002)

    async def disconnect(self, close_code):
        logger.info(f"Desconectando WebSocket, codigo: {close_code}")
        try:
            await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        except Exception as e:
            logger.error(f"Error al desconectar del grupo: {e}", exc_info=True)

    async def activity_broadcast(self, event):
        try:
            payload = event.get('payload', {})
            logger.info(f"Enviando broadcast de actividad: {payload.get('activity_type')} a {self.channel_name}")
            await self.send(text_data=json.dumps(payload))
        except Exception as e:
            logger.error(f"Error al enviar broadcast: {e}", exc_info=True)
