# app_estoque/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificacaoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # A conexão só é aceita se o usuário estiver logado
        if self.scope["user"].is_authenticated:
            # Cria um nome de grupo único para cada usuário (ex: 'user_1', 'user_2')
            self.group_name = f'user_{self.scope["user"].id}'

            # Entra no grupo/canal privado
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Esta função será chamada pelas nossas views para enviar uma notificação
    async def send_notification(self, event):
        message = event['message']
        # Envia a mensagem para o WebSocket (navegador do usuário)
        await self.send(text_data=json.dumps({
            'message': message
        }))