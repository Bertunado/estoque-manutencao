# app_estoque/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class HistoricoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("--- CONSUMER: Tentativa de conexão ao histórico ---")
        await self.channel_layer.group_add(
            "historico_geral",
            self.channel_name
        )
        await self.accept()
        print("--- CONSUMER: Conectado com sucesso e adicionado ao grupo 'historico_geral'! ---")

    async def disconnect(self, close_code):
        print("--- CONSUMER: Desconectado. ---")
        await self.channel_layer.group_discard(
            "historico_geral",
            self.channel_name
        )

    async def notificar_nova_retirada(self, event):
        print("--- CONSUMER: Mensagem recebida do grupo! Enviando para o navegador... ---")
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))