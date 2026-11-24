"""Approved mobile keyboard check for the public NoiseLabz landing page."""
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
            && color !== "transparent" && !/^rgba\([^)]*, 0\)$/.test(color)
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
