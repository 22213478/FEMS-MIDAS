from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# QR 읽기 전용 토큰 조회 
# GET /api/v1/readonly/{token} 요청 시 토큰 유효성 검증에 사용 
# 토큰과 연결된 factory_id, 만료 시간, 활성화 여부를 조회
async def get_readonly_token(db: AsyncSession, token: str):
    result = await db.execute(text("""
        SELECT
            id,
            token,
            factory_id,
            expires_at,
            is_active,
            created_at
        FROM readonly_tokens
        WHERE token = :token
        LIMIT 1
    """), {"token": token})

    row = result.mappings().first()

    return dict(row) if row else None
    
