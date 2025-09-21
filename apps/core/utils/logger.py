import json
import logging

from apps.core.middleware import get_current_user_id


class Logger:
    @staticmethod
    def _sanitize_log_data(data):
        if isinstance(data, dict):
            return {k: ("*****" if "pass" in k.lower() else v) for k, v in data.items()}
        return data

    def log_event(self, event_name, log_data, logging_module="InstaBot", level="INFO"):
        logger = logging.getLogger(logging_module)
        try:
            msg = {"ev": event_name, "data": self._sanitize_log_data(log_data)}
            uid = get_current_user_id()
            if uid:
                msg["uid"] = uid
            logger.log(msg=json.dumps(msg), level=getattr(logging, level))
        except Exception as e:
            logger.error(f"Log error: {str(e)}", exc_info=True)
            return None
