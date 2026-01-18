"""
图片代理 API - 解决 CORS 问题
"""
import httpx
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from urllib.parse import urlparse, urlencode

logger = logging.getLogger(__name__)

router = APIRouter()

# 允许的图片域名白名单
ALLOWED_DOMAINS = [
    "steamcdn-a.akamaihd.net",
    "steamcommunity.com",
    "steamstatic.com",
]


def is_allowed_domain(url: str) -> bool:
    """检查 URL 是否在允许的域名列表中"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # 移除端口号
        if ':' in domain:
            domain = domain.split(':')[0]
        return any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
    except Exception:
        return False


@router.get("/images/proxy")
async def proxy_image(url: str = Query(..., description="图片 URL")):
    """
    图片代理端点 - 解决 CORS 问题
    
    使用方式: /api/v1/images/proxy?url=<图片URL>
    """
    try:
        # 验证 URL
        if not url or not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="无效的图片 URL")
        
        # 检查域名白名单
        if not is_allowed_domain(url):
            logger.warning(f"不允许的图片域名: {urlparse(url).netloc}")
            raise HTTPException(
                status_code=403,
                detail=f"不允许的图片域名: {urlparse(url).netloc}"
            )
        
        # 代理请求图片
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # 获取 Content-Type
            content_type = response.headers.get("Content-Type", "image/jpeg")
            
            # 返回图片数据
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",  # 缓存 24 小时
                    "Access-Control-Allow-Origin": "*",
                }
            )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"图片代理失败: HTTP {e.response.status_code} - {url}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"无法获取图片: {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error(f"图片代理超时: {url}")
        raise HTTPException(status_code=504, detail="图片请求超时")
    except httpx.RequestError as e:
        logger.error(f"图片代理请求错误: {str(e)} - {url}")
        raise HTTPException(status_code=502, detail=f"无法连接到图片服务器: {str(e)}")
    except Exception as e:
        logger.exception(f"图片代理未知错误: {str(e)} - {url}")
        raise HTTPException(status_code=500, detail=f"图片代理失败: {str(e)}")
