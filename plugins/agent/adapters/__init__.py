"""Platform adapters for the Agent boundary.

Importing this package only loads pure adapter facades.  It does not register
NoneBot matchers or import the QQ event handlers.
"""

from .feishu import (
    FEISHU_TEXT_CAPABILITIES,
    FeishuDelivery,
    FeishuHistoryStore,
    FeishuMessageAdapter,
    FeishuReplyPolicy,
    FeishuTextGateway,
    FeishuToolProvider,
)
from .feishu_api import FeishuApiClient, FeishuApiError
from .feishu_webhook import (
    FeishuWebhookConnector,
    FeishuWebhookDispatch,
    FeishuWebhookError,
    FeishuWebhookHost,
    FeishuWebhookResult,
)
from .qq import QqDelivery, QqHistoryStore, QqMessageAdapter, QqReplyPolicy, QqToolProvider

__all__ = [
    "FEISHU_TEXT_CAPABILITIES",
    "FeishuDelivery",
    "FeishuHistoryStore",
    "FeishuMessageAdapter",
    "FeishuReplyPolicy",
    "FeishuTextGateway",
    "FeishuToolProvider",
    "FeishuApiClient",
    "FeishuApiError",
    "FeishuWebhookConnector",
    "FeishuWebhookDispatch",
    "FeishuWebhookError",
    "FeishuWebhookHost",
    "FeishuWebhookResult",
    "QqDelivery",
    "QqHistoryStore",
    "QqMessageAdapter",
    "QqReplyPolicy",
    "QqToolProvider",
]
