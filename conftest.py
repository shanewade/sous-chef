import pytest
import sqlalchemy as sa
from sqlalchemy.pool import StaticPool
from app import app as flask_app
from extensions import db as _db


@pytest.fixture()
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["SECRET_KEY"] = "test-secret"
    # Flask-SQLAlchemy 3.1 blocks init_app from being called a second time, so
    # we inject a fresh engine directly into its per-app engine cache.
    # StaticPool ensures every connection in the test (fixtures + request
    # contexts) shares one in-memory DB rather than each getting its own.
    test_engine = sa.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _db._app_engines[flask_app][None] = test_engine
    yield flask_app
    test_engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()
