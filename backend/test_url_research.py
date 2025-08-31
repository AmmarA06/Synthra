#!/usr/bin/env python3
"""
Test script for URL research functionality
"""

import asyncio
import json
import httpx

async def test_url_research():
    """Test the URL research endpoint"""
    
    # Test URLs
    test_urls = [
        "https://react.dev",
        "https://vuejs.org", 
        "https://angular.io"
    ]
    
    # Test data
    test_data = {
        "urls": test_urls,
        "query": "Compare JavaScript frameworks for frontend development"
    }
    
    print("🧪 Testing URL Research Endpoint")
    print(f"📋 URLs: {test_urls}")
    print(f"❓ Query: {test_data['query']}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/url-research",
                json=test_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Request successful!")
                print(f"📊 Found {len(result['pages'])} pages")
                
                # Print comparison summary
                if result.get('comparison'):
                    print("\n🔍 Comparison Analysis:")
                    print(f"Summary: {result['comparison']['summary']}")
                    print(f"Common Themes: {len(result['comparison']['commonThemes'])}")
                    print(f"Key Differences: {len(result['comparison']['keyDifferences'])}")
                
                # Print individual page results
                print("\n📄 Individual Pages:")
                for i, page in enumerate(result['pages'], 1):
                    if page.get('error'):
                        print(f"  {i}. ❌ {page['title']}: {page['error']}")
                    else:
                        print(f"  {i}. ✅ {page['title']}")
                        print(f"     📝 {len(page['keyPoints'])} key points")
                        print(f"     ➕ {len(page['pros'])} pros")
                        print(f"     ➖ {len(page['cons'])} cons")
                
                # Save detailed results
                with open("test_results.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print("\n💾 Detailed results saved to test_results.json")
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
        except httpx.ConnectError as e:
            print(f"❌ Connection Error: Cannot connect to backend at http://localhost:8000")
            print(f"   Make sure the backend is running with: python -m uvicorn main:app --reload")
            print(f"   Details: {str(e)}")
        except httpx.TimeoutException as e:
            print(f"❌ Timeout Error: Backend is not responding within 60 seconds")
            print(f"   Details: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_url_research())
