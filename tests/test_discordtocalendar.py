import os
import sys
import types
import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Inject lightweight fake modules for heavy external deps so tests run without installing them.
if "discord" not in sys.modules:
    discord_mod = types.ModuleType("discord")

    class Intents:
        @staticmethod
        def default():
            return types.SimpleNamespace()

    class Client:
        def __init__(self, *args, **kwargs):
            # minimal no-op client compatible with the subset used by the app
            pass
        def event(self, func=None):
            """Decorator stub that returns the function unchanged.

            Usage:
                @client.event
                async def on_message(...):
                    ...
            """
            if func is None:
                def decorator(f):
                    return f
                return decorator
            return func

        def run(self, *args, **kwargs):
            # no-op run for test environment
            return None

        def event(self, func=None):
            # decorator used as @client.event — return function unchanged
            if func is None:
                def decorator(f):
                    return f

                return decorator
            return func

        def run(self, *args, **kwargs):
            # no-op run used in main; tests won't actually start an event loop
            return None

    discord_mod.Intents = Intents
    discord_mod.Client = Client
    sys.modules["discord"] = discord_mod

# googleapiclient.discovery.build stub
if "googleapiclient" not in sys.modules:
    gap_mod = types.ModuleType("googleapiclient")
    discovery = types.ModuleType("googleapiclient.discovery")

    def build(*args, **kwargs):
        return MagicMock()

    discovery.build = build
    sys.modules["googleapiclient"] = gap_mod
    sys.modules["googleapiclient.discovery"] = discovery

# google.oauth2.service_account.Credentials stub
if "google.oauth2.service_account" not in sys.modules:
    ga_oauth_mod = types.ModuleType("google.oauth2")
    service_account = types.ModuleType("google.oauth2.service_account")

    class Credentials:
        @staticmethod
        def from_service_account_file(*args, **kwargs):
            return "fake-creds"

    service_account.Credentials = Credentials
    sys.modules["google.oauth2"] = ga_oauth_mod
    sys.modules["google.oauth2.service_account"] = service_account

# dotenv stub
if "dotenv" not in sys.modules:
    dotenv_mod = types.ModuleType("dotenv")
    def load_dotenv(*a, **k):
        return None
    dotenv_mod.load_dotenv = load_dotenv
    sys.modules["dotenv"] = dotenv_mod

# dateutil.parser stub
if "dateutil" not in sys.modules:
    dateutil_mod = types.ModuleType("dateutil")
    parser_mod = types.ModuleType("dateutil.parser")
    from datetime import datetime

    def isoparse(s):
        # simple ISO parser for tests (assumes input is RFC3339/ISO compatible)
        return datetime.fromisoformat(s)

    parser_mod.isoparse = isoparse
    sys.modules["dateutil"] = dateutil_mod
    sys.modules["dateutil.parser"] = parser_mod

# Ensure required env vars are present before importing the module
os.environ.setdefault("CALENDAR_ID", "test_calendar")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/fake_credentials.json")

import discordtocalendar


# Test logging helper controlled by ENABLE_LOGS env var
ENABLE_TEST_LOGS = os.getenv("ENABLE_LOGS", "0").lower() in ("1", "true", "yes")

# Logger used by tests. Pytest's `log_cli` will display these messages when enabled.
logger = logging.getLogger("tests")
if ENABLE_TEST_LOGS:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.CRITICAL)

def tlog(msg: str):
    logger.info(msg)


def test_parse_message_line_with_description():
    tlog("[TEST] test_parse_message_line_with_description start")
    ts = 1700000000
    line = f"<t:{ts}:F> - some - This is the description"
    msg, start, end = discordtocalendar.parse_message_line(line)
    assert msg == "This is the description"
    assert start == ts
    assert end == ts + 9000
    tlog("[TEST] test_parse_message_line_with_description passed")


def test_parse_message_line_default_description():
    tlog("[TEST] test_parse_message_line_default_description start")
    ts = 1700000000
    line = f"<t:{ts}:F> - only"
    msg, start, end = discordtocalendar.parse_message_line(line)
    assert msg == "No description provided"
    assert start == ts
    assert end == ts + 9000
    tlog("[TEST] test_parse_message_line_default_description passed")


def test_parse_message_line_no_match():
    tlog("[TEST] test_parse_message_line_no_match start")
    line = "no timestamp here"
    msg, start, end = discordtocalendar.parse_message_line(line)
    assert msg is None and start is None and end is None
    tlog("[TEST] test_parse_message_line_no_match passed")


def test_event_exists_true():
    tlog("[TEST] test_event_exists_true start")
    service = MagicMock()
    start_ts = 1700000000
    end_ts = start_ts + 9000
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()
    end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
    # Mock the chained calls service.events().list(...).execute()
    service.events.return_value.list.return_value.execute.return_value = {
        "items": [{"start": {"dateTime": start_dt}, "end": {"dateTime": end_dt}}]
    }
    assert discordtocalendar.event_exists(service, start_ts, end_ts) is True
    tlog("[TEST] test_event_exists_true passed")


def test_event_exists_false():
    tlog("[TEST] test_event_exists_false start")
    service = MagicMock()
    start_ts = 1700000000
    end_ts = start_ts + 9000
    service.events.return_value.list.return_value.execute.return_value = {"items": []}
    assert discordtocalendar.event_exists(service, start_ts, end_ts) is False
    tlog("[TEST] test_event_exists_false passed")


def test_insert_event_calls_service():
    tlog("[TEST] test_insert_event_calls_service start")
    service = MagicMock()
    start_ts = 1700000000
    end_ts = start_ts + 9000
    discordtocalendar.insert_event(service, "the summary", start_ts, end_ts)
    # verify insert called with expected calendarId and body
    insert_call = service.events.return_value.insert.call_args
    assert insert_call is not None
    # call_args returns (positional_args, kwargs)
    _, kwargs = insert_call
    assert kwargs.get("calendarId") == discordtocalendar.CALENDAR_ID
    body = kwargs.get("body")
    assert body["summary"] == "the summary"
    assert body["start"]["dateTime"] == datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()
    assert body["end"]["dateTime"] == datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
    tlog("[TEST] test_insert_event_calls_service passed")


def test_authenticate_google_calendar(monkeypatch):
    tlog("[TEST] test_authenticate_google_calendar start")
    # Patch the underlying credentials factory to avoid reading a real file
    monkeypatch.setattr(
        "discordtocalendar.service_account.Credentials.from_service_account_file",
        lambda *a, **k: "fake-creds",
    )
    creds = discordtocalendar.authenticate_google_calendar()
    assert creds == "fake-creds"
    tlog("[TEST] test_authenticate_google_calendar passed")
