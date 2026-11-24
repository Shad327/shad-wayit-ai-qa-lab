"""Exact supported scenario contract; never interpret arbitrary text as code."""
import ast

from fastapi import HTTPException


KEYBOARD_SCENARIO = {
    "title": "Mobile menu button has a visible keyboard focus indicator",
    "preconditions": ["Open the public landing page at a mobile viewport where the menu button is visible. Use a physical keyboard."],
    "steps": [
        {"action": "Starting at the top of the page, press Tab until focus reaches the menu button.",
         "expected_result": "The menu button can be reached using Tab."},
        {"action": "Look at the menu button while it has keyboard focus.",
         "expected_result": "A visible outline, ring, or other clear indicator shows that the menu button has focus."},
    ],
}


def keyboard_template(requirement, evidence):
    for passage in evidence:
        text = passage["text"].lower()
        if (passage["id"] == requirement or requirement == "keyboard") and "keyboard navigation" in text and "visible focus" in text:
            return {**KEYBOARD_SCENARIO, "source_ids": [passage["id"]]}
    return None


KEYBOARD_CODE = '''"""Approved mobile keyboard check for the public NoiseLabz landing page."""
from playwright.sync_api import expect


def test_approved_mobile_menu_keyboard_focus(page):
    page.set_viewport_size({"width": 390, "height": 844})
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok
    menu = page.locator(".hamburger")
    expect(menu).to_be_visible()
    focus_style = r"""element => {
        const style = getComputedStyle(element);
        const color = style.outlineColor;
        const outline = style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0
            && color !== "transparent" && !/^rgba\\([^)]*, 0\\)$/.test(color)
            ? [style.outlineStyle, style.outlineWidth, color, style.outlineOffset].join(" ")
            : "";
        return {outline, shadow: style.boxShadow};
    }"""
    baseline = menu.evaluate(focus_style)
    for _ in range(20):
        page.keyboard.press("Tab")
        if menu.evaluate("element => element === document.activeElement"):
            break
    expect(menu).to_be_focused()
    expect(menu).to_be_in_viewport()
    focused = menu.evaluate(focus_style)
    assert (
        (focused["outline"] and focused["outline"] != baseline["outline"])
        or (focused["shadow"] != "none" and focused["shadow"] != baseline["shadow"])
    ), "No changed outline or box shadow was detected on the focused mobile menu button"
'''


DOCS_SCENARIO = {
    "title": "Guest can open the public documentation index",
    "preconditions": ["Fresh browser context"],
    "steps": [
        {"action": "Open the public landing page and select Open Docs",
         "expected_result": "The public documentation index opens"},
        {"action": "Inspect the documentation entry links",
         "expected_result": "The litepaper and protocol links are visible"},
    ],
    "source_ids": ["PRACTICE-08"],
}

DOCS_CODE = '''import re
from playwright.sync_api import expect


def test_approved_guest_opens_docs(page):
    response = page.goto("https://www.noiselabz.com/", wait_until="domcontentloaded")
    assert response and response.ok
    link = page.get_by_role("link", name="Open Docs", exact=True)
    link.click()
    expect(page).to_have_url("https://www.noiselabz.com/docs/")
    expect(page.get_by_role("heading", level=1)).to_contain_text(re.compile("litepaper", re.I))
    expect(page.get_by_role("link", name="Read Litepaper", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Open Protocol", exact=True)).to_be_visible()
'''


def supported_template(requirement, evidence):
    if requirement == "PRACTICE-08":
        for passage in evidence:
            text = passage["text"].lower()
            if passage["id"] == requirement and all(
                term in text for term in ("open docs", "/docs/", "litepaper", "protocol")
            ):
                return DOCS_SCENARIO
    return keyboard_template(requirement, evidence)


def automation_coverage(requirement, scenarios, evidence=()):
    steps = [
        {'action': 'Open the public landing page', 'expected_result': 'Public page content is visible'},
        {'action': 'Select Features', 'expected_result': 'Features section is visible'},
    ]
    extra_navigation = {
        'About Us': ('about', 'About NOiSE'),
        'How It Works': ('hiw', 'From sound to on-chain legacy'),
        'Roadmap': ('roadmap', 'Building the future of music'),
    }
    template = supported_template(requirement, evidence)
    coverage = []
    for index, scenario in enumerate(scenarios, 1):
        reasons = []
        if requirement != 'AUTH-04':
            if not template:
                reasons.append('This requirement has no supported automation template.')
            elif any(scenario[field] != template[field] for field in ("preconditions", "steps", "source_ids")):
                reasons.append('Use the automation template to review the exact supported steps and source.')
            coverage.append({'number': index, 'title': scenario['title'],
                             'supported': not reasons, 'reasons': reasons})
            continue
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
    coverage = automation_coverage(package['requirement'], scenarios, package.get('evidence', ()))
    supported = [item for item in coverage if item['supported']]
    if len(supported) != 1:
        issues = [f'Test scenario {item["number"]}: {item["title"]}\n- ' + '\n- '.join(item['reasons'])
                  for item in coverage if not item['supported']]
        reason = ('No scenario matches the supported automation templates.' if not supported else
                  'More than one scenario matches the automation template; choosing between them is not yet supported.')
        raise HTTPException(422, 'Python preview blocked.\n\n' + reason + '\n\n' + '\n\n'.join(issues) +
                            '\n\nKeep these scenarios for manual review. Do not change their intended behavior merely to match a template. No code was generated.')
    chosen = supported[0]
    if package['requirement'] == 'PRACTICE-08':
        return preview_response(exported, chosen, coverage, DOCS_CODE, 'test_approved_guest_opens_docs.py',
                                'Checks public navigation to the Docs index and its two entry links.')

    if package['requirement'] != 'AUTH-04':
        return preview_response(
            exported, chosen, coverage, KEYBOARD_CODE, 'test_approved_mobile_menu_keyboard_focus.py',
            'Checks Tab reachability and a changed outline or box shadow on the mobile menu button. '
            'Other focus treatments, contrast, and full accessibility coverage require separate review.',
        )

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
    return preview_response(exported, chosen, coverage, code, 'test_approved_guest_features.py',
                            'Fixed navigation selectors.')


def preview_response(exported, chosen, coverage, code, filename, limitations):
    ast.parse(code)
    package = exported['package']
    return {'code': code, 'filename': filename,
            'revision': package['revision'], 'package_sha256': exported['sha256'],
            'mode': 'template_generated', 'executed': False,
            'scenario_number': chosen['number'], 'coverage': coverage,
            'questions': package['draft']['questions'],
            'limitations': f'Only scenario {chosen["number"]} is included. {len(coverage) - 1} other scenarios remain manual; they are not executed or passed. {limitations} Syntax checked only, not executed. Open questions remain unresolved.'}
