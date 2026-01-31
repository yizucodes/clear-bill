"""
ClearBill Advisor - LIVE TIME Feature Tests
Tests the wait time extraction functionality with 3 test cases.
Saves results to JSON for verification.
"""

import json
import re
from datetime import datetime
from pathlib import Path
import asyncio

# Import the FirecrawlClient
from firecrawl_client import FirecrawlClient


def test_extract_facility_data():
    """
    Test Case 1: Unit test for _extract_facility_data method
    Tests regex patterns for wait time and pricing extraction.
    """
    client = FirecrawlClient()
    
    test_cases = [
        {
            "name": "Explicit wait time with pricing",
            "markdown": """
                # Carbon Health Urgent Care
                
                Current wait time: 25 minutes
                Walk-ins welcome!
                
                ## Pricing
                - Urgent Care Visit: $225
                - X-Ray: $85
            """,
            "expected": {
                "has_pricing": True,
                "has_wait_time": True,
                "urgent_care_visit": 225,
                "wait_time": "25 min",
                "status": "Walk-ins welcome"
            }
        },
        {
            "name": "Status only (no explicit time)",
            "markdown": """
                Urgent Care Clinic
                On schedule - Low wait times today!
                
                Virtual Visit: $99
            """,
            "expected": {
                "has_pricing": True,
                "has_wait_time": True,
                "virtual_visit": 99,
                "status": "On schedule"
            }
        },
        {
            "name": "High volume warning",
            "markdown": """
                Currently experiencing high volume
                Next available: 3:30 PM
                
                Primary Care Visit: $150
            """,
            "expected": {
                "has_pricing": True,
                "has_wait_time": True,
                "primary_care_visit": 150,
                "status": "High volume",
                "next_available": "3:30 PM"
            }
        }
    ]
    
    results = []
    
    for tc in test_cases:
        result = client._extract_facility_data(tc["markdown"])
        
        # Build test result
        test_result = {
            "test_name": tc["name"],
            "passed": True,
            "expected": tc["expected"],
            "actual": result,
            "checks": {}
        }
        
        # Verify expectations
        if tc["expected"]["has_pricing"]:
            if result is None:
                test_result["passed"] = False
                test_result["checks"]["pricing_extraction"] = "FAILED - No data extracted"
            else:
                for key in ["urgent_care_visit", "xray", "virtual_visit", "primary_care_visit"]:
                    if key in tc["expected"]:
                        actual_val = result.get(key)
                        expected_val = tc["expected"][key]
                        if actual_val == expected_val:
                            test_result["checks"][key] = f"PASSED - Got ${actual_val}"
                        else:
                            test_result["passed"] = False
                            test_result["checks"][key] = f"FAILED - Expected ${expected_val}, got ${actual_val}"
        
        if tc["expected"]["has_wait_time"]:
            if result is None or "wait_time_data" not in result:
                test_result["passed"] = False
                test_result["checks"]["wait_time_extraction"] = "FAILED - No wait time data"
            else:
                wait_data = result.get("wait_time_data", {})
                
                if "wait_time" in tc["expected"]:
                    actual = wait_data.get("wait_time")
                    expected = tc["expected"]["wait_time"]
                    if actual == expected:
                        test_result["checks"]["wait_time"] = f"PASSED - Got {actual}"
                    else:
                        test_result["passed"] = False
                        test_result["checks"]["wait_time"] = f"FAILED - Expected {expected}, got {actual}"
                
                if "status" in tc["expected"]:
                    actual = wait_data.get("status")
                    expected = tc["expected"]["status"]
                    if actual == expected:
                        test_result["checks"]["status"] = f"PASSED - Got {actual}"
                    else:
                        test_result["passed"] = False
                        test_result["checks"]["status"] = f"FAILED - Expected {expected}, got {actual}"
                
                if "next_available" in tc["expected"]:
                    actual = wait_data.get("next_available")
                    expected = tc["expected"]["next_available"]
                    if actual == expected:
                        test_result["checks"]["next_available"] = f"PASSED - Got {actual}"
                    else:
                        test_result["passed"] = False
                        test_result["checks"]["next_available"] = f"FAILED - Expected {expected}, got {actual}"
        
        results.append(test_result)
        
        # Print result
        status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
        print(f"\n{status}: {tc['name']}")
        for check, msg in test_result["checks"].items():
            print(f"  - {check}: {msg}")
    
    return {
        "test_suite": "Test Case 1: _extract_facility_data unit tests",
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results
    }


def test_mock_facilities_have_wait_time():
    """
    Test Case 2: Verify mock facilities include wait time data
    Tests that _mock_facilities returns realistic wait time strings.
    """
    client = FirecrawlClient()
    facilities = client._mock_facilities("San Francisco, CA")
    
    results = []
    
    for facility in facilities:
        test_result = {
            "facility_name": facility.get("name"),
            "passed": True,
            "checks": {}
        }
        
        # Check wait_time exists
        if "wait_time" in facility and facility["wait_time"]:
            test_result["checks"]["wait_time"] = f"PASSED - Got '{facility['wait_time']}'"
        else:
            test_result["passed"] = False
            test_result["checks"]["wait_time"] = "FAILED - Missing wait_time field"
        
        # Check wait_time_status exists
        if "wait_time_status" in facility and facility["wait_time_status"]:
            test_result["checks"]["wait_time_status"] = f"PASSED - Got '{facility['wait_time_status']}'"
        else:
            test_result["passed"] = False
            test_result["checks"]["wait_time_status"] = "FAILED - Missing wait_time_status field"
        
        # Check wait_time_source exists
        if "wait_time_source" in facility:
            test_result["checks"]["wait_time_source"] = f"PASSED - Got '{facility['wait_time_source']}'"
        else:
            test_result["passed"] = False
            test_result["checks"]["wait_time_source"] = "FAILED - Missing wait_time_source field"
        
        results.append(test_result)
        
        # Print result
        status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
        print(f"\n{status}: {facility.get('name')}")
        for check, msg in test_result["checks"].items():
            print(f"  - {check}: {msg}")
    
    return {
        "test_suite": "Test Case 2: Mock facilities wait time fields",
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "facilities": facilities,
        "results": results
    }


async def test_search_and_enrich_integration():
    """
    Test Case 3: Integration test for search_and_enrich with wait time
    Tests the full flow including wait time enrichment.
    Uses mock data (no API key) to ensure tests run consistently.
    """
    # Create client without API key to use mock data
    client = FirecrawlClient(api_key=None)
    
    result = await client.search_and_enrich(
        queries=["urgent care headache San Francisco"],
        location="San Francisco, CA",
        expected_procedures=["urgent care visit"],
        top_n=3
    )
    
    test_results = []
    
    # Check data structure
    structure_test = {
        "test_name": "Response structure",
        "passed": True,
        "checks": {}
    }
    
    required_fields = ["timestamp", "query", "location", "facilities", "data_quality"]
    for field in required_fields:
        if field in result:
            structure_test["checks"][field] = f"PASSED - Field exists"
        else:
            structure_test["passed"] = False
            structure_test["checks"][field] = "FAILED - Missing field"
    
    test_results.append(structure_test)
    
    # Check facilities have wait time
    facilities_test = {
        "test_name": "Facilities have wait time data",
        "passed": True,
        "checks": {}
    }
    
    for i, facility in enumerate(result.get("facilities", [])):
        if "wait_time" in facility:
            facilities_test["checks"][f"facility_{i}_wait_time"] = f"PASSED - Got '{facility['wait_time']}'"
        else:
            facilities_test["passed"] = False
            facilities_test["checks"][f"facility_{i}_wait_time"] = "FAILED - Missing"
        
        if "wait_time_source" in facility:
            facilities_test["checks"][f"facility_{i}_source"] = f"PASSED - Got '{facility['wait_time_source']}'"
        else:
            facilities_test["passed"] = False
            facilities_test["checks"][f"facility_{i}_source"] = "FAILED - Missing"
    
    test_results.append(facilities_test)
    
    # Print results
    for tr in test_results:
        status = "✅ PASSED" if tr["passed"] else "❌ FAILED"
        print(f"\n{status}: {tr['test_name']}")
        for check, msg in tr["checks"].items():
            print(f"  - {check}: {msg}")
    
    return {
        "test_suite": "Test Case 3: Integration test search_and_enrich",
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_results),
        "passed": sum(1 for r in test_results if r["passed"]),
        "failed": sum(1 for r in test_results if not r["passed"]),
        "search_result": result,
        "results": test_results
    }


async def run_all_tests():
    """Run all 3 test cases and save results to JSON."""
    print("=" * 60)
    print("ClearBill LIVE TIME Feature Tests")
    print("=" * 60)
    
    all_results = {
        "test_run_timestamp": datetime.now().isoformat(),
        "summary": {},
        "test_cases": []
    }
    
    # Test Case 1
    print("\n" + "=" * 60)
    print("TEST CASE 1: _extract_facility_data unit tests")
    print("=" * 60)
    tc1_results = test_extract_facility_data()
    all_results["test_cases"].append(tc1_results)
    
    # Test Case 2
    print("\n" + "=" * 60)
    print("TEST CASE 2: Mock facilities wait time fields")
    print("=" * 60)
    tc2_results = test_mock_facilities_have_wait_time()
    all_results["test_cases"].append(tc2_results)
    
    # Test Case 3
    print("\n" + "=" * 60)
    print("TEST CASE 3: Integration test search_and_enrich")
    print("=" * 60)
    tc3_results = await test_search_and_enrich_integration()
    all_results["test_cases"].append(tc3_results)
    
    # Summary
    total_passed = sum(tc.get("passed", 0) for tc in all_results["test_cases"])
    total_failed = sum(tc.get("failed", 0) for tc in all_results["test_cases"])
    total_tests = total_passed + total_failed
    
    all_results["summary"] = {
        "total_test_cases": 3,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "success_rate": f"{(total_passed/total_tests)*100:.1f}%" if total_tests > 0 else "N/A"
    }
    
    # Save to JSON
    results_dir = Path(__file__).parent / "search_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"live_time_test_results_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"📊 Total Test Cases: 3")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📈 Success Rate: {all_results['summary']['success_rate']}")
    print(f"\n💾 Results saved to: {output_file}")
    
    return all_results, str(output_file)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
