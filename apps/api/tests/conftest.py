import pytest
from app.core.rate_limit import rate_limiter
from app.db.models import User
from app.db.session import SessionFactory
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, or_

TEST_ORIGIN = "http://localhost:3000"
TEST_EMAIL_DOMAIN = "phase2.auvyren.app"
TEST_EMAIL_DOMAINS = (
    "phase2.auvyren.app",
    "phase3.auvyren.app",
    "phase6.auvyren.app",
    "phase7.auvyren.app",
)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Origin": TEST_ORIGIN, "Referer": f"{TEST_ORIGIN}/"},
    ) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
async def auth_test_isolation():
    await rate_limiter.reset()
    yield
    await rate_limiter.reset()
    async with SessionFactory() as session:
        await session.execute(
            delete(User).where(
                or_(
                    *[
                        User.email.like(f"%@{domain}")
                        for domain in TEST_EMAIL_DOMAINS
                    ]
                )
            )
        )
        await session.commit()
