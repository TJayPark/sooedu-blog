#!/usr/bin/env python3
"""
AI Search Exposure Checker for Soo Edu Blog
Checks if "Soo Edu" appears in AI search results (ChatGPT, Gemini)
Uses OpenClaw for browser automation

Run daily via cron at 18:00
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# NOTE: User should configure OpenClaw workspace path
# OpenClaw workspace should have tasks defined for ChatGPT and Gemini searches

OPENCLAW_WORKSPACE = "/Users/tjaypark/sooedubot_workspace"
LOG_FILE = Path(__file__).parent.parent / "logs" / "ai_exposure_tracking.json"

# Search queries to test
SEARCH_QUERIES = [
    "화상영어 추천해줘",
    "저렴한 화상영어",
    "AI 기반 영어 학습",
    "온라인 영어회화 초등학생",
    "어린이 화상영어 추천",
]

class ExposureChecker:
    def __init__(self):
        self.log_file = LOG_FILE
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Create log file if it doesn't exist"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.write_text(json.dumps({"checks": []}, indent=2))
    
    def load_logs(self) -> Dict:
        """Load existing logs"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading logs: {e}", file=sys.stderr)
            return {"checks": []}
    
    def save_logs(self, logs: Dict):
        """Save logs to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving logs: {e}", file=sys.stderr)
    
    def check_chatgpt(self, query: str) -> Dict:
        """
        Check ChatGPT search results using Playwright
        """
        print(f"🔍 Checking ChatGPT for: {query}")
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch browser (headless mode for automation)
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                try:
                    # Navigate to ChatGPT
                    print("  → Opening ChatGPT...")
                    page.goto("https://chat.openai.com", timeout=30000)
                    
                    # Wait for page to load
                    page.wait_for_timeout(3000)
                    
                    # Check if login is required
                    # Note: This will only work if user has active session
                    # Otherwise, will need to handle login
                    
                    # Try to find and fill the textarea
                    textarea_selector = "textarea[placeholder*='Message'], textarea[data-id*='prompt'], #prompt-textarea"
                    
                    try:
                        page.wait_for_selector(textarea_selector, timeout=5000)
                        print(f"  → Entering query: {query}")
                        page.fill(textarea_selector, query)
                        
                        # Submit (usually Enter key or finding send button)
                        page.press(textarea_selector, "Enter")
                        
                        # Wait for response to appear
                        print("  → Waiting for response...")
                        page.wait_for_timeout(10000)  # Wait 10 seconds for response
                        
                        # Extract response text
                        # ChatGPT responses are usually in markdown format
                        response_selectors = [
                            ".markdown",
                            "[data-message-author-role='assistant']",
                            ".response-container",
                            "article"
                        ]
                        
                        response_text = ""
                        for selector in response_selectors:
                            try:
                                elements = page.query_selector_all(selector)
                                if elements:
                                    # Get last assistant message
                                    response_text = elements[-1].inner_text()
                                    break
                            except:
                                continue
                        
                        if not response_text:
                            # Fallback: get all visible text
                            response_text = page.inner_text("body")
                        
                        print(f"  ✅ Got response ({len(response_text)} chars)")
                        
                    except Exception as e:
                        print(f"  ⚠️  Login required or page structure changed: {e}")
                        response_text = f"[Login required or page structure changed: {e}]"
                    
                finally:
                    browser.close()
                
                # Check if Soo Edu is mentioned
                mentioned = "soo edu" in response_text.lower() or "sooedu" in response_text.lower()
                
                return {
                    "platform": "ChatGPT",
                    "query": query,
                    "mentioned": mentioned,
                    "response_snippet": response_text[:300] if response_text else "[No response captured]",
                    "timestamp": datetime.now().isoformat(),
                    "success": bool(response_text and len(response_text) > 50)
                }
                
        except ImportError:
            print("  ❌ Playwright not installed. Run: pip3 install playwright && playwright install chromium")
            return self._mock_response("ChatGPT", query)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {
                "platform": "ChatGPT",
                "query": query,
                "mentioned": False,
                "response_snippet": f"[Error: {str(e)}]",
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    def _mock_response(self, platform: str, query: str) -> Dict:
        """Fallback mock response"""
        response_text = f"Mock {platform} response for: {query}"
        mentioned = False
        return {
            "platform": platform,
            "query": query,
            "mentioned": mentioned,
            "response_snippet": response_text[:200],
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
    
    def check_gemini(self, query: str) -> Dict:
        """
        Check Gemini search results using Playwright
        """
        print(f"🔍 Checking Gemini for: {query}")
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                try:
                    # Navigate to Gemini
                    print("  → Opening Gemini...")
                    page.goto("https://gemini.google.com", timeout=30000)
                    
                    # Wait for page to load
                    page.wait_for_timeout(3000)
                    
                    # Try to find and fill the textarea
                    textarea_selectors = [
                        "textarea[placeholder*='Enter'], textarea[aria-label*='prompt']",
                        ".ql-editor",
                        "rich-textarea"
                    ]
                    
                    textarea_found = False
                    for selector in textarea_selectors:
                        try:
                            if page.query_selector(selector):
                                print(f"  → Entering query: {query}")
                                page.fill(selector, query)
                                
                                # Submit (Enter key or send button)
                                page.press(selector, "Enter")
                                textarea_found = True
                                break
                        except:
                            continue
                    
                    if not textarea_found:
                        print("  ⚠️  Could not find input field")
                        response_text = "[Could not find input field - login may be required]"
                    else:
                        # Wait for response
                        print("  → Waiting for response...")
                        page.wait_for_timeout(10000)
                        
                        # Extract response
                        response_selectors = [
                            ".model-response",
                            "[data-test-id*='response']",
                            ".message-content",
                            "article"
                        ]
                        
                        response_text = ""
                        for selector in response_selectors:
                            try:
                                elements = page.query_selector_all(selector)
                                if elements:
                                    response_text = elements[-1].inner_text()
                                    break
                            except:
                                continue
                        
                        if not response_text:
                            response_text = page.inner_text("body")
                        
                        print(f"  ✅ Got response ({len(response_text)} chars)")
                    
                finally:
                    browser.close()
                
                mentioned = "soo edu" in response_text.lower() or "sooedu" in response_text.lower()
                
                return {
                    "platform": "Gemini",
                    "query": query,
                    "mentioned": mentioned,
                    "response_snippet": response_text[:300] if response_text else "[No response captured]",
                    "timestamp": datetime.now().isoformat(),
                    "success": bool(response_text and len(response_text) > 50)
                }
                
        except ImportError:
            print("  ❌ Playwright not installed")
            return self._mock_response("Gemini", query)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {
                "platform": "Gemini",
                "query": query,
                "mentioned": False,
                "response_snippet": f"[Error: {str(e)}]",
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    def analyze_results(self, results: List[Dict]) -> List[str]:
        """Analyze results and provide recommendations"""
        recommendations = []
        
        # Count mentions
        total_queries = len(results)
        mentioned_count = sum(1 for r in results if r.get("mentioned"))
        
        if mentioned_count == 0:
            recommendations.append("❌ Soo Edu가 AI 검색 결과에 전혀 노출되지 않고 있습니다")
            recommendations.append("💡 SEO 최적화 콘텐츠를 더 많이 발행하세요")
            recommendations.append("💡 FAQ 페이지를 추가하세요")
            recommendations.append("💡 가격 비교 콘텐츠를 작성하세요")
        elif mentioned_count < total_queries * 0.3:
            recommendations.append(f"⚠️  노출도가 낮습니다 ({mentioned_count}/{total_queries})")
            recommendations.append("💡 콘텐츠 품질을 개선하고 더 구조화된 정보를 제공하세요")
        elif mentioned_count >= total_queries * 0.7:
            recommendations.append(f"✅ 노출도가 좋습니다! ({mentioned_count}/{total_queries})")
            recommendations.append("💡 현재 전략을 유지하세요")
        else:
            recommendations.append(f"⏳ 노출이 증가하는 중입니다 ({mentioned_count}/{total_queries})")
            recommendations.append("💡 꾸준히 콘텐츠를 발행하세요")
        
        return recommendations
    
    def run_checks(self) -> Dict:
        """Run all exposure checks"""
        results = []
        
        for query in SEARCH_QUERIES:
            # Check ChatGPT
            chatgpt_result = self.check_chatgpt(query)
            results.append(chatgpt_result)
            
            # Check Gemini
            gemini_result = self.check_gemini(query)
            results.append(gemini_result)
        
        # Analyze
        recommendations = self.analyze_results(results)
        
        # Create summary
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "total_checks": len(results),
            "mentioned_count": sum(1 for r in results if r.get("mentioned")),
            "results": results,
            "recommendations": recommendations
        }
        
        return summary
    
    def save_check_results(self, summary: Dict):
        """Save check results to log file"""
        logs = self.load_logs()
        logs["checks"].append(summary)
        
        # Keep only last 30 days of checks
        if len(logs["checks"]) > 30:
            logs["checks"] = logs["checks"][-30:]
        
        self.save_logs(logs)
    
    def print_summary(self, summary: Dict):
        """Print human-readable summary"""
        print("\n" + "=" * 60)
        print(f"AI Search Exposure Check - {summary['date']} {summary['time']}")
        print("=" * 60)
        print(f"\nTotal Checks: {summary['total_checks']}")
        print(f"Mentioned: {summary['mentioned_count']}")
        print(f"Exposure Rate: {summary['mentioned_count'] / summary['total_checks'] * 100:.1f}%")
        print("\n📊 Recommendations:")
        for rec in summary['recommendations']:
            print(f"  {rec}")
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    checker = ExposureChecker()
    
    print("🔍 Starting AI Search Exposure Check...")
    print(f"Log file: {checker.log_file}")
    print("")
    
    # Run checks
    summary = checker.run_checks()
    
    # Save results
    checker.save_check_results(summary)
    
    # Print summary
    checker.print_summary(summary)
    
    print("\n✅ Check complete!")
    print(f"Results saved to: {checker.log_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
