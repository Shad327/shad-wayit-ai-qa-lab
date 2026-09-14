"""Exact supported scenario contract; never interpret arbitrary text as code."""
import ast

from fastapi import HTTPException


def generate_preview(exported):
    package = exported['package']
    scenarios = package['draft']['scenarios']
    steps = [
        {'action': 'Open the public landing page', 'expected_result': 'Public page content is visible'},
        {'action': 'Select Features', 'expected_result': 'Features section is visible'},
    ]
    extra_navigation = {
        'About Us': ('about', 'About NOiSE'),
        'How It Works': ('hiw', 'From sound to on-chain legacy'),
        'Roadmap': ('roadmap', 'Building the future of music'),
    }
    extras = scenarios[0]['steps'][2:] if scenarios else []
    labels = [step['action'].removeprefix('Select ') for step in extras]
    supported_extras = len(labels) == len(set(labels)) and all(
        label in extra_navigation and step == {'action': f'Select {label}', 'expected_result': f'{label} section is visible'}
        for label, step in zip(labels, extras))
    if (package['requirement'] != 'AUTH-04' or len(scenarios) != 1
            or scenarios[0]['preconditions'] != ['Fresh browser context; no wallet connected']
            or scenarios[0]['steps'][:2] != steps or not supported_extras):
        raise HTTPException(422, 'Unsupported scenario. This template supports the original guest landing-page → Features steps and optional About Us, How It Works, and Roadmap navigation steps with matching expected results. Your edits are preserved; no code was generated.')
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
            'questions': package['draft']['questions'],
            'limitations': 'Fixed selectors from the existing NoiseLabz suite. Syntax checked only; not executed. Open questions remain unresolved. Use a fresh pytest-playwright browser context.'}
