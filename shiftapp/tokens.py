from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class FiveMinuteTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{user.last_login}{timestamp}"

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False

        # 檢查 token 是否過期（5 分鐘 = 300 秒）
        try:
            ts_b36, _ = token.split('-')
            ts_int = self._num_seconds(self._today()) - self._base36_to_int(ts_b36)
            return ts_int <= 300
        except Exception:
            return False
