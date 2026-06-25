""""""
# Local Imports
from reverse_proxy_server.exceptions import ReverseProxyServerUnHandledError, ReverseProxyServerUpStreamRequestError, ReverseProxyServerTimeoutError, ReverseProxyServerAuthFailed, UpStreamRequestBufferSizeExceededError
from reverse_proxy_server import constants as CONSTANTS

# 3rd-Party Imports
from fastapi import Response
import tenacity
import httpx


# Support Internal functions
def __construct_upstream_url(full_path, request, application_settings):

    """"""
    # Construct application url
    upstream_url = application_settings.upstream_url.rstrip("/")
    end_point = f"/{full_path}" if full_path else ""
    query_params = request.url.query
    return f"{upstream_url}{end_point}?{query_params}" if query_params else f"{upstream_url}{end_point}"

# TODO : Need to validate if the Hop headers might be configurated in application settings
def filter_hop_headers(headers):
    """"""
    return {k: v for k, v in headers.items() if k.lower() not in CONSTANTS.HOP_BY_HOP_HEADERS}

def patch_upstream_auth_header(headers , application_settings):
    """"""
    if application_settings.upstream_authorization:
        headers["authorization"] = application_settings.upstream_authorization
    
    if application_settings.upstream_cookie:
        headers["cookie"] = application_settings.upstream_cookie

    if application_settings.upstream_api_key_header and application_settings.upstream_api_key_value:
        headers[application_settings.upstream_api_key_header] = application_settings.upstream_api_key_value
    return headers


def validate_proxy_auth(request, application_settings):
    """"""
    if not application_settings.proxy_api_key:
        return

    if request.headers.get("x-proxy-api-key", "") != application_settings.proxy_api_key:
        raise ReverseProxyServerAuthFailed(status_code=401, detail="Invalid or missing 'X-Proxy-Api-Key'.")

async def buffer_application_body(request, application_settings):
    """"""
    chunks = []
    _buffered_size = 0
    request_buffer_size  = application_settings.max_body_bytes
    async for chunk in request.stream():
        _buffered_size += len(chunk)
        if _buffered_size > request_buffer_size:
            raise UpStreamRequestBufferSizeExceededError(status_code=413,
                                                         detail=f"Request body exceeds {request_buffer_size // (1024 * 1024)} MB limit.")
        chunks.append(chunk)
    return b"".join(chunks)


async def query_upstream(url, request , application_settings):
    """"""
    # Construct upstream url
    upstream_query_url = __construct_upstream_url(url, request, application_settings)
    # Get application body and wait for buffered size
    up_stream_body = await buffer_application_body(request, application_settings)
    # Patch upstream Application auth config in Proxy Header
    upstream_header = patch_upstream_auth_header(dict(request.headers), application_settings)
    # Get Requestor id
    requestor_id = getattr(request.state, "request_id", "-")

    # TODO: Add Log Here with requestor id

    try:
        async for attempt in tenacity.AsyncRetrying(
            stop=tenacity.stop_after_attempt(application_settings.max_retries),
            wait=tenacity.wait_exponential(
                min=application_settings.retry_min_wait,
                max=application_settings.retry_max_wait,
            ),
            retry=tenacity.retry_if_exception_type(
                (httpx.ConnectError, httpx.RemoteProtocolError)
            ),
            reraise=True,
        ):
            with attempt:
                upstream = await request.app.state.http_client.request(
                    method=request.method,
                    url=upstream_query_url,
                    headers=upstream_header,
                    content=up_stream_body,
                )
        # Filter hod_header from upstream
        response_headers = filter_hop_headers(dict(upstream.headers))
        # Add Requestor header to upstream response
        response_headers["x-request-id"] = requestor_id
        # Return the response to the user
        return Response(content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),)
    except httpx.TimeoutException as exc:
        # TODO: Add Log
        raise ReverseProxyServerTimeoutError(status_code=504, detail="Upstream request timed out.") from exc
    except httpx.RequestError as exc:
        # TODO: Add Log
        raise ReverseProxyServerUpStreamRequestError(status_code=502, detail="Could not reach the upstream API.") from exc
    except Exception as exc:
        # TODO: Add Log
        raise ReverseProxyServerUnHandledError(status_code=500, detail="An Un-Handle exception occurred, Please check error info for more.") from exc
    
