"""
Test script for classification rules.

Run this to test your classification patterns against sample job titles.
"""

from app.classification import classify_title, get_classifier


def test_titles():
    """Test various job titles against classification rules."""
    
    test_cases = [
        # C-Suite (should match)
        ("Chief Executive Officer", True, "csuite"),
        ("CEO", True, "csuite"),
        ("CFO", True, "csuite"),
        ("Chief Technology Officer", True, "csuite"),
        ("President", True, "csuite"),
        ("Chief Information Security Officer", True, "csuite"),
        
        # VP (should match)
        ("VP of Sales", True, "vp"),
        ("Vice President", True, "vp"),
        ("SVP Engineering", True, "vp"),
        ("Executive Vice President", True, "vp"),
        
        # Exclusions (should NOT match)
        ("Student President", False, ""),
        ("Retired CEO", False, ""),
        ("Former CTO", False, ""),
        ("VP Intern", False, ""),
        ("Head of Product", False, ""),
        
        # Non-senior (should NOT match)
        ("Software Engineer", False, ""),
        ("Senior Manager", False, ""),
        ("Director of Sales", False, ""),
        ("Team Lead", False, ""),
    ]
    
    classifier = get_classifier()
    print(f"\nTesting Classification Rules (version: {classifier.version})\n")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for title, expected_senior, expected_level in test_cases:
        is_senior, level = classify_title(title)
        
        status = "✓" if (is_senior == expected_senior and level == expected_level) else "✗"
        
        if is_senior == expected_senior and level == expected_level:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {title:45} | Senior: {is_senior:5} | Level: {level:6} | Expected: {expected_level:6}")
    
    print("=" * 80)
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} test(s) failed - review classification config")
    
    return failed == 0


if __name__ == "__main__":
    success = test_titles()
    exit(0 if success else 1)

