import asyncio
import logging
from sqlmodel import select
from src.core.dependencies import SessionLocal
from src.admin.models import City, EventType, DressCategory

logger = logging.getLogger(__name__)

CITY_SEEDS = [
    {"slug": "berlin", "display_name": "Berlin", "latitude": 52.5200, "longitude": 13.4050},
    {"slug": "munich", "display_name": "Munich", "latitude": 48.1351, "longitude": 11.5820},
    {"slug": "hamburg", "display_name": "Hamburg", "latitude": 53.5511, "longitude": 9.9937},
    {"slug": "cologne", "display_name": "Cologne", "latitude": 50.9375, "longitude": 6.9603},
    {"slug": "frankfurt", "display_name": "Frankfurt", "latitude": 50.1109, "longitude": 8.6821},
    {"slug": "stuttgart", "display_name": "Stuttgart", "latitude": 48.7758, "longitude": 9.1829},
    {"slug": "dusseldorf", "display_name": "Dusseldorf", "latitude": 51.2277, "longitude": 6.7735},
    {"slug": "leipzig", "display_name": "Leipzig", "latitude": 51.3397, "longitude": 12.3731},
    {"slug": "dresden", "display_name": "Dresden", "latitude": 51.0504, "longitude": 13.7373},
    {"slug": "nuremberg", "display_name": "Nuremberg", "latitude": 49.4521, "longitude": 11.0767},
    {"slug": "bremen", "display_name": "Bremen", "latitude": 53.0793, "longitude": 8.8017},
    {"slug": "hannover", "display_name": "Hannover", "latitude": 52.3759, "longitude": 9.7320},
    {"slug": "dortmund", "display_name": "Dortmund", "latitude": 51.5136, "longitude": 7.4653},
    {"slug": "essen", "display_name": "Essen", "latitude": 51.4556, "longitude": 7.0116},
    {"slug": "mannheim", "display_name": "Mannheim", "latitude": 49.4875, "longitude": 8.4660},
]

EVENT_TYPE_SEEDS = [
    {"slug": "business", "display_name": "Business"},
    {"slug": "casual", "display_name": "Casual"},
    {"slug": "smart_casual", "display_name": "Smart Casual"},
    {"slug": "formal", "display_name": "Formal"},
    {"slug": "outdoor", "display_name": "Outdoor"},
    {"slug": "party", "display_name": "Party"},
    {"slug": "sports", "display_name": "Sports"},
    {"slug": "date_night", "display_name": "Date Night"},
    {"slug": "other", "display_name": "Other"},
]

DRESS_CATEGORY_SEEDS = [
    {"slug": "top", "display_name": "Top"},
    {"slug": "bottom", "display_name": "Bottom"},
    {"slug": "outerwear", "display_name": "Outerwear"},
    {"slug": "shoes", "display_name": "Shoes"},
    {"slug": "accessory", "display_name": "Accessory"},
    {"slug": "dress", "display_name": "Dress"},
    {"slug": "underwear", "display_name": "Underwear"},
    {"slug": "bag", "display_name": "Bag"},
    {"slug": "hat", "display_name": "Hat"},
    {"slug": "socks", "display_name": "Socks"},
    {"slug": "other", "display_name": "Other"},
]


async def seed_data():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting database seeding...")
    async with SessionLocal() as session:
        # Seed Cities
        for city_data in CITY_SEEDS:
            stmt = select(City).where(City.slug == city_data["slug"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                logger.info(f"Seeding city: {city_data['slug']}")
                city = City(**city_data)
                session.add(city)

        # Seed EventTypes
        for et_data in EVENT_TYPE_SEEDS:
            stmt = select(EventType).where(EventType.slug == et_data["slug"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                logger.info(f"Seeding event type: {et_data['slug']}")
                et = EventType(**et_data)
                session.add(et)

        # Seed DressCategories
        for dc_data in DRESS_CATEGORY_SEEDS:
            stmt = select(DressCategory).where(DressCategory.slug == dc_data["slug"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                logger.info(f"Seeding dress category: {dc_data['slug']}")
                dc = DressCategory(**dc_data)
                session.add(dc)

        await session.commit()
    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_data())
