"""Tests for common utilities."""

from packages.common.config import Settings
from packages.common.exceptions import AppError, NotFoundError, UnauthorizedError


class TestSettings:
    def test_default_settings(self):
        s = Settings()
        assert s.postgres_host == "localhost"
        assert s.postgres_port == 5432
        assert s.app_env == "development"

    def test_postgres_dsn(self):
        s = Settings()
        dsn = s.postgres_dsn
        assert "asyncpg" in dsn
        assert "localhost" in dsn

    def test_postgres_dsn_sync(self):
        s = Settings()
        dsn = s.postgres_dsn_sync
        assert "postgresql://" in dsn
        assert "asyncpg" not in dsn


class TestExceptions:
    def test_app_error(self):
        err = AppError(code=400, message="bad request")
        assert err.code == 400
        assert err.status_code == 400

    def test_not_found_error(self):
        err = NotFoundError("Project", 123)
        assert err.code == 404
        assert "123" in err.message

    def test_unauthorized_error(self):
        err = UnauthorizedError()
        assert err.code == 401
