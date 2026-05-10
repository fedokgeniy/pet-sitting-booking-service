"""
Pytest configuration: ensure the project root is importable and that
external resources (DB / Service Bus) are stubbed for tests.
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Make sure no real connection is attempted when tests import the app.
os.environ.setdefault("DB_USERNAME", "pasinozavr")
os.environ.setdefault("DB_PASSWORD", "61YcGTqd")
os.environ.setdefault("DB_SERVER", "tcp:cloud2026.database.windows.net")
os.environ.setdefault("DB_DATABASE", "pr2")
os.environ.setdefault("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

# Use in-memory SQLite during tests so no Azure SQL / pyodbc is needed.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


# Stub native modules that may not be installed locally so importing
# service modules in tests does not require them. The real CI image
# installs pyodbc + the ODBC driver and uses the actual packages.
import types  # noqa: E402

if "pyodbc" not in sys.modules:
    sys.modules["pyodbc"] = types.ModuleType("pyodbc")

if "azure" not in sys.modules:
    azure_mod = types.ModuleType("azure")
    sys.modules["azure"] = azure_mod
if "azure.servicebus" not in sys.modules:
    sb_mod = types.ModuleType("azure.servicebus")
    sb_mod.ServiceBusClient = MagicMock()
    sb_mod.ServiceBusMessage = MagicMock()
    sys.modules["azure.servicebus"] = sb_mod
