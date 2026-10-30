"""Exact supported scenario contract; never interpret arbitrary text as code."""
import ast

from fastapi import HTTPException


def automation_coverage(requirement, scenarios):
    steps = [
        {'action': 'Open the public landing page', 'expected_result': 'Public page content is visible'},
        {'action': 'Select Features', 'expected_result': 'Features section is visible'},
    ]
    extra_navigation = {
        'About Us': ('about', 'About NOiSE'),
        'How It Works': ('hiw', 'From sound to on-chain legacy'),
        'Roadmap': ('roadmap', 'Building the future of music'),
    }
    coverage = []
    for index, scenario in enumerate(scenarios, 1):
        reasons = []
        if requirement != 'AUTH-04':
            reasons.append('Only AUTH-04 public navigation has an automation adapter.')
        if scenario['preconditions'] != ['Fresh browser context; no wallet connected']:
            reasons.append('preconditions must be: Fresh browser context; no wallet connected')
        for step_index, expected in enumerate(steps, 1):
            if len(scenario['steps']) < step_index or scenario['steps'][step_index-1] != expected:
                reasons.append(f'Step {step_index} must be "{expected["action"]}" with expected result "{expected["expected_result"]}"')
        seen = set()
        for step_index, step in enumerate(scenario['steps'][2:], 3):
            label = step['action'].removeprefix('Select ')
            if label in seen or label not in extra_navigation or step != {'action': f'Select {label}', 'expected_result': f'{label} section is visible'}:
                reasons.append(f'Step {step_index} is unsupported or repeats navigation; only About Us, How It Works, and Roadmap are supported after Features')
            seen.add(label)
        coverage.append({'number': index, 'title': scenario['title'],
                         'supported': not reasons, 'reasons': reasons})
    return coverage


def generate_preview(exported):
    package = exported['package']
    scenarios = package['draft']['scenarios']
    coverage = automation_coverage(package['requirement'], scenarios)
    supported = [item for item in coverage if item['supported']]
    if len(supported) != 1:
        issues = [f'Test scenario {item["number"]}: {item["title"]}\n- ' + '\n- '.join(item['reasons'])
                  for item in coverage if not item['supported']]
        reason = ('No scenario matches the supported navigation adapter.' if not supported else
                  'More than one scenario matches the navigation adapter; choosing between them is not yet supported.')
        raise HTTPException(422, 'Python preview blocked.\n\n' + reason + '\n\n' + '\n\n'.join(issues) +
                            '\n\nKeep these scenarios for manual review. Do not change their intended behavior merely to match a template. No code was generated.')
    chosen = supported[0]
    extras = scenarios[chosen['number'] - 1]['steps'][2:]
    labels = [step['action'].removeprefix('Select ') for step in extras]
    extra_navigation = {
        'About Us': ('about', 'About NOiSE'),
        'How It Works': ('hiw', 'From sound to on-chain legacy'),
        'Roadmap': ('roadmap', 'Building the future of music'),
    }
    code = '''"""Template-generated narrow public navigation check; not full AUTH-04 coverage."""
import re
from playwright.sync_api import expect


def test_approved_guest_features(page):
    page.set_viewport_size({"width": 1280, "height": 800})
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok
    expect(page).to_have_title(re.compile("noise", re.I))
    features = page.get_by_role("link", name="Features", exact=True).first
    expect(features).to_be_visible()
    features.click()
    expect(page).to_have_url(re.compile(r"#features$"))
    expect(page.get_by_role("heading", name="Everything you need to create & earn", exact=True)).to_be_in_viewport()
'''
    for label in labels:
        fragment, heading = extra_navigation[label]
        code += f'    page.get_by_role("link", name={label!r}, exact=True).first.click()\n'
        code += f'    expect(page).to_have_url(re.compile({("#" + fragment + "$")!r}))\n'
        code += f'    expect(page.get_by_role("heading", name={heading!r}, exact=True)).to_be_in_viewport()\n'
    ast.parse(code)
    return {'code': code, 'filename': 'test_approved_guest_features.py',
            'revision': package['revision'], 'package_sha256': exported['sha256'],
            'mode': 'template_generated', 'executed': False,
            'scenario_number': chosen['number'], 'coverage': coverage,
            'questions': package['draft']['questions'],
            'limitations': f'Only scenario {chosen["number"]} is included. {len(coverage) - 1} other scenarios remain manual; they are not executed or passed. Fixed navigation selectors; syntax checked only, not executed. Open questions remain unresolved.'}
