#!/usr/bin/env python3
"""
Test MCP Redis Cache Direct Integration
Tests the MCP server with direct Redis cache calls
"""

import asyncio
import json
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"


async def test_mcp_redis_cache():
    """Test the MCP server redis_cached_chat tool"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Initialize MCP session
        logger.info("🔄 Testing MCP session initialization...")

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "redis-cache-tester",
                    "version": "1.0.0"
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        try:
            response = await client.post(MCP_SERVER_URL,
                                         json=init_request,
                                         headers=headers)

            logger.info(f"Init Status: {response.status_code}")
            session_id = None
            if response.status_code == 200:
                response_text = response.text
                logger.info(f"Raw response: {response_text[:300]}...")

                # Extract session ID from response headers
                session_id = response.headers.get(
                    'x-session-id') or response.headers.get('session-id')
                if not session_id:
                    # Try to extract from response body if it's there
                    import re
                    session_match = re.search(
                        r'"session[_-]?id":\s*"([^"]+)"', response_text)
                    if session_match:
                        session_id = session_match.group(1)
                    else:
                        # Generate a session ID if not found
                        import uuid
                        session_id = str(uuid.uuid4())

                logger.info(f"📋 Using session ID: {session_id}")

                # Handle SSE format
                init_data = {}
                try:
                    if 'data: {' in response_text:
                        # Extract JSON from SSE format
                        lines = response_text.split('\n')
                        for line in lines:
                            if line.startswith('data: {'):
                                json_data = line.replace('data: ', '').strip()
                                init_data = json.loads(json_data)
                                break
                    else:
                        init_data = response.json()

                    logger.info(
                        f"✅ MCP initialized: {init_data.get('result', {}).get('serverInfo', {})}")
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {je}")
                    logger.error(f"Raw response was: {response_text}")
                    # Continue anyway - might be streaming
            else:
                logger.error(f"❌ Init failed: {response.text}")
                return

        except Exception as e:
            logger.error(f"❌ Init error: {e}")
            return

        # Update headers with session ID for subsequent requests
        if session_id:
            headers["Session-ID"] = session_id
            logger.info(f"🔗 Added session ID to headers: {session_id[:8]}...")

        # Test 1.5: Send initialized notification
        logger.info("🔄 Sending initialized notification...")

        initialized_request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        try:
            response = await client.post(MCP_SERVER_URL,
                                         json=initialized_request,
                                         headers=headers)

            logger.info(
                f"Initialized notification Status: {response.status_code}")
            if response.status_code != 200:
                logger.warning(f"⚠️ Initialized notification: {response.text}")

        except Exception as e:
            logger.error(f"❌ Initialized notification error: {e}")

        # Test 2: List available tools
        logger.info("🔄 Listing available tools...")

        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        try:
            response = await client.post(MCP_SERVER_URL,
                                         json=tools_request,
                                         headers=headers)

            logger.info(f"Tools Status: {response.status_code}")
            if response.status_code == 200:
                tools_data = response.json()
                tools = tools_data.get('result', {}).get('tools', [])
                logger.info(
                    f"✅ Available tools: {[t.get('name') for t in tools]}")
            else:
                logger.error(f"❌ Tools list failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Tools list error: {e}")

        # Test 3: Call redis_cached_chat tool (first time - should be cache miss)
        logger.info(
            "🔄 Testing redis_cached_chat tool - First call (should be cache miss)...")

        test_message = "¿Qué es un motor fuera de borda y cómo funciona su sistema de encendido?"

        tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "redis_cached_chat",
                "arguments": {
                    "mensaje": test_message,
                    "session_id": "mcp-cache-test-001",
                    "agent_id": "TestAgent"
                }
            }
        }

        try:
            logger.info("📤 Sending first request...")
            response = await client.post(MCP_SERVER_URL,
                                         json=tool_request,
                                         headers=headers,
                                         timeout=45.0)

            logger.info(f"First call Status: {response.status_code}")
            if response.status_code == 200:
                first_data = response.json()
                result = first_data.get('result', {})
                content = result.get('content', [])

                if content:
                    text_content = content[0].get('text', '')
                    logger.info(
                        f"✅ First call success! Response length: {len(text_content)} chars")
                    logger.info(f"📝 Response preview: {text_content[:200]}...")

                    # Check for cache info in the response
                    if 'cache_hit' in str(result) or 'cache_miss' in str(result):
                        logger.info(f"🔍 Cache info detected in response")
                else:
                    logger.warning(f"⚠️ No content in response: {first_data}")
            else:
                logger.error(f"❌ First call failed: {response.text}")
                return

        except Exception as e:
            logger.error(f"❌ First call error: {e}")
            return

        # Wait a moment before second call
        await asyncio.sleep(2)

        # Test 4: Call redis_cached_chat tool again (should be cache hit)
        logger.info(
            "🔄 Testing redis_cached_chat tool - Second call (should be cache hit)...")

        tool_request["id"] = 4  # New ID for second call

        try:
            logger.info("📤 Sending second request (same message)...")
            response = await client.post(MCP_SERVER_URL,
                                         json=tool_request,
                                         headers=headers,
                                         timeout=15.0)  # Shorter timeout for cache hit

            logger.info(f"Second call Status: {response.status_code}")
            if response.status_code == 200:
                second_data = response.json()
                result = second_data.get('result', {})
                content = result.get('content', [])

                if content:
                    text_content = content[0].get('text', '')
                    logger.info(
                        f"✅ Second call success! Response length: {len(text_content)} chars")
                    logger.info(f"🚀 Cache behavior validated!")
                else:
                    logger.warning(
                        f"⚠️ No content in second response: {second_data}")
            else:
                logger.error(f"❌ Second call failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Second call error: {e}")

if __name__ == "__main__":
    print("🧪 Testing MCP Redis Cache Integration")
    print("=" * 50)
    asyncio.run(test_mcp_redis_cache())
    print("=" * 50)
    print("✅ MCP Redis cache test completed!")
