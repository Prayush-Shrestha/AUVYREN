"""Delete accounts created by Playwright runs (development/test only)."""

import asyncio

from sqlalchemy import delete

from app.db.models import User
from app.db.session import SessionFactory

EMAIL_SUFFIX = "@e2e.auvyren.app"


async def main() -> None:
    async with SessionFactory() as session:
        result = await session.execute(
            delete(User).where(User.email.like(f"%{EMAIL_SUFFIX}"))
        )
        await session.commit()
    print(f"Removed {result.rowcount} e2e account(s).")


if __name__ == "__main__":
    asyncio.run(main())
