import json
import logging
from typing import Set

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from assets.models import Asset

logger = logging.getLogger(__name__)

MAX_ASSET_SUBSCRIPTIONS = 20  # Prevent abuse


# -------------------------------------------------------------------
# Base Consumer with shared security logic
# -------------------------------------------------------------------
class BaseOrgConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        if not hasattr(self.user, 'organization') or not self.user.organization:
            await self.close(code=4002)
            return

        self.organization_id = str(self.user.organization.id)
        self.asset_subscriptions: Set[str] = set()

        await self.accept()

    async def disconnect(self, close_code):
        # Cleanup all asset subscriptions
        for asset_id in list(self.asset_subscriptions):
            await self._unsubscribe_asset(asset_id)

    # ---------------------------
    # Security helpers
    # ---------------------------
    @database_sync_to_async
    def _asset_belongs_to_org(self, asset_id: str) -> bool:
        return Asset.objects.filter(
            id=asset_id,
            organization=self.user.organization
        ).exists()

    async def _subscribe_asset(self, asset_id: str):
        if len(self.asset_subscriptions) >= MAX_ASSET_SUBSCRIPTIONS:
            await self.send_json({
                'type': 'error',
                'message': 'Subscription limit exceeded'
            })
            return

        if not await self._asset_belongs_to_org(asset_id):
            await self.send_json({
                'type': 'error',
                'message': 'Unauthorized asset'
            })
            return

        group_name = f'asset_{asset_id}'
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.asset_subscriptions.add(asset_id)

        await self.send_json({
            'type': 'subscription_confirmed',
            'asset_id': asset_id
        })

    async def _unsubscribe_asset(self, asset_id: str):
        group_name = f'asset_{asset_id}'
        await self.channel_layer.group_discard(group_name, self.channel_name)
        self.asset_subscriptions.discard(asset_id)

    async def send_json(self, data: dict):
        await self.send(text_data=json.dumps(data))


# -------------------------------------------------------------------
# Telemetry Consumer
# -------------------------------------------------------------------
class TelemetryConsumer(BaseOrgConsumer):
    async def connect(self):
        await super().connect()
        if self.closed:
            return

        self.org_group = f'telemetry_{self.organization_id}'
        await self.channel_layer.group_add(self.org_group, self.channel_name)

        await self.send_json({
            'type': 'connected',
            'scope': 'telemetry',
            'timestamp': timezone.now().isoformat()
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.org_group, self.channel_name)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
            msg_type = payload.get('type')

            if msg_type == 'subscribe_asset':
                await self._subscribe_asset(payload.get('asset_id'))

            elif msg_type == 'unsubscribe_asset':
                await self._unsubscribe_asset(payload.get('asset_id'))

            elif msg_type == 'ping':
                await self.send_json({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                })

            else:
                await self.send_json({
                    'type': 'error',
                    'message': 'Unknown message type'
                })

        except Exception:
            logger.exception('Telemetry WS error')

    async def asset_telemetry(self, event):
        await self.send_json({
            'type': 'telemetry',
            'data': event.get('data')
        })


# -------------------------------------------------------------------
# Alert Consumer
# -------------------------------------------------------------------
class AlertConsumer(BaseOrgConsumer):
    async def connect(self):
        await super().connect()
        if self.closed:
            return

        self.org_group = f'alerts_{self.organization_id}'
        await self.channel_layer.group_add(self.org_group, self.channel_name)

        await self.send_json({
            'type': 'connected',
            'scope': 'alerts'
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.org_group, self.channel_name)
        await super().disconnect(close_code)

    async def alert_event(self, event):
        await self.send_json({
            'type': 'alert',
            'data': event.get('data')
        })


# -------------------------------------------------------------------
# Asset Status Consumer
# -------------------------------------------------------------------
class AssetConsumer(BaseOrgConsumer):
    async def connect(self):
        await super().connect()
        if self.closed:
            return

        self.org_group = f'assets_{self.organization_id}'
        await self.channel_layer.group_add(self.org_group, self.channel_name)

        await self.send_json({
            'type': 'connected',
            'scope': 'assets'
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.org_group, self.channel_name)
        await super().disconnect(close_code)

    async def asset_status(self, event):
        await self.send_json({
            'type': 'asset_status',
            'data': event.get('data')
        })
