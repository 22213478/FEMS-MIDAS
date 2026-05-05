import asyncio

from backend.database.connection import AsyncSessionLocal
from backend.repositories.sensor_log_repository import get_latest_sensor_logs
from backend.services.anomaly_service import check_temperature_range


async def main():
    async with AsyncSessionLocal() as db:
        latest_sensor_logs = await get_latest_sensor_logs(db)

        print("\n=== 최신 센서 로그 조회 결과 ===")
        print(latest_sensor_logs)

        print("\n=== 온도 범위 이상 감지 결과 ===")
        for sensor_log in latest_sensor_logs:
            result = check_temperature_range(sensor_log)
            if result:
                print(result)


if __name__ == "__main__":
    asyncio.run(main())