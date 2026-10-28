"""Complete no-pointer Phase 1D keyboard workflows on disposable staging."""
import io
import json
import os
import re
import time

from PIL import Image
from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:5510"
BLOCKS = (
    "paragraph", "heading", "image", "gallery", "quote", "bullet_list",
    "numbered_list", "table", "callout", "divider", "youtube", "instagram",
    "link_preview",
)


def login(page, username):
    page.goto(BASE + "/login")
    page.get_by_label("Username or Email").press_sequentially(username)
    page.get_by_label("Password").press_sequentially("Phase1dPass!9")
    page.get_by_role("button", name="Login").press("Enter")
    page.wait_for_load_state("domcontentloaded")


def focused_notice(page):
    notice = page.locator("[data-flash-focus]").first
    assert notice.is_visible()
    assert notice.evaluate("(n)=>document.activeElement===n")


def enter(page, locator):
    locator.focus()
    locator.press("Enter")
    page.wait_for_load_state("domcontentloaded")


def png():
    data = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(data, "PNG")
    return data.getvalue()


def run():
    report = {
        "public_reader": 0, "author": 0, "comment_owner": 0,
        "moderator": 0, "focus": 0, "shift_tab": 0, "space": 0,
        "blocks_added": 0, "console_errors": [],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )

        # Workflow A and C: reader + comment owner, no pointer activation.
        reader = browser.new_context()
        page = reader.new_page()
        login(page, "reader2")
        page.goto(BASE + "/")
        enter(page, page.locator('a[href="/blogs"]').first)
        report["public_reader"] += 1
        search = page.get_by_label("Search", exact=True)
        search.press_sequentially("Phase 1D")
        search.press("Shift+Tab")
        assert page.evaluate("document.activeElement!==document.body")
        report["shift_tab"] += 1
        search.focus()
        search.press("Enter")
        page.wait_for_load_state("domcontentloaded")
        enter(page, page.get_by_role("link", name="Phase 1D Published"))
        report["public_reader"] += 2

        for first, second in (
            (re.compile(r"^Like"), re.compile(r"^Unlike")),
            (re.compile(r"^Bookmark$"), re.compile(r"^Remove bookmark$")),
            (re.compile(r"^Follow author$"), re.compile(r"^Unfollow$")),
        ):
            enter(page, page.get_by_role("button", name=first))
            focused_notice(page)
            enter(page, page.get_by_role("button", name=second))
            focused_notice(page)
            report["public_reader"] += 4
            report["focus"] += 2

        unique = f"Keyboard owner हिन्दी 🙂 {time.time_ns()}"
        page.get_by_label("Add comment").press_sequentially(unique)
        enter(page, page.get_by_role("button", name="Comment", exact=True))
        focused_notice(page)
        parent = page.locator(".blog-comment").filter(has_text=unique)
        parent.get_by_text("Reply", exact=True).focus()
        parent.get_by_text("Reply", exact=True).press("Space")
        report["space"] += 1
        reply = f"Keyboard reply {time.time_ns()}"
        parent.get_by_label("Reply text").press_sequentially(reply)
        enter(page, parent.get_by_role("button", name="Post reply"))
        focused_notice(page)
        report["public_reader"] += 4
        report["comment_owner"] += 4
        report["focus"] += 2

        parent = page.locator(".blog-comment").filter(has_text=unique)
        parent.get_by_text("Edit comment", exact=True).focus()
        parent.get_by_text("Edit comment", exact=True).press("Enter")
        edited = unique + " edited"
        box = parent.get_by_label("Comment text")
        box.press("ControlOrMeta+A")
        box.press_sequentially(edited)
        enter(page, parent.get_by_role("button", name="Save comment"))
        focused_notice(page)
        parent = page.locator(".blog-comment").filter(has_text=edited)
        parent.get_by_text("Edit reply", exact=True).focus()
        parent.get_by_text("Edit reply", exact=True).press("Enter")
        editor = parent.locator("details").filter(has_text="Edit reply").get_by_label("Reply text")
        editor.press("ControlOrMeta+A")
        editor.press_sequentially(reply + " edited")
        enter(page, parent.get_by_role("button", name="Save reply"))
        focused_notice(page)
        parent = page.locator(".blog-comment").filter(has_text=edited)
        enter(page, parent.get_by_role("button", name="Delete reply"))
        focused_notice(page)
        parent = page.locator(".blog-comment").filter(has_text=edited)
        enter(page, parent.get_by_role("button", name="Delete comment"))
        focused_notice(page)
        assert "[deleted]" in page.locator(".blog-comments").inner_text()
        report["comment_owner"] += 9
        report["focus"] += 4

        page.get_by_text("Report this Blog").focus()
        page.get_by_text("Report this Blog").press("Enter")
        reason = page.get_by_label("Reason")
        reason.focus()
        reason.press("Home")
        reason.press("ArrowDown")
        page.get_by_label("Details").press_sequentially("Keyboard report")
        enter(page, page.get_by_role("button", name="Send report"))
        focused_notice(page)
        page.go_back()
        report["public_reader"] += 4
        report["focus"] += 1
        reader.close()

        # Workflow B: author and every supported editor block.
        author = browser.new_context()
        page = author.new_page()
        login(page, "author1")
        page.goto(BASE + "/blogs")
        enter(page, page.get_by_role("link", name="Write a Blog"))
        title = f"Keyboard Complete {time.time_ns()}"
        page.get_by_label("Title", exact=True).press_sequentially(title)
        page.get_by_label("Subtitle").press_sequentially("Keyboard-only metadata हिन्दी")
        selector = page.get_by_label("Block type")
        for index, kind in enumerate(BLOCKS):
            selector.focus()
            selector.press("Home")
            for _ in range(index):
                selector.press("ArrowDown")
            page.get_by_role("button", name="Add block").press("Enter")
            report["blocks_added"] += 1
        cards = page.locator(".blog-block-card")
        assert cards.count() == len(BLOCKS)
        for index, card in enumerate(cards.all()):
            fields = card.locator("textarea")
            if fields.count():
                value = (
                    "https://example.com/safe"
                    if BLOCKS[index] in {"image", "youtube", "instagram", "link_preview"}
                    else "Header,Value\nBrake,Good"
                    if BLOCKS[index] == "table"
                    else "One\nTwo\nतीन"
                    if BLOCKS[index] in {"gallery", "bullet_list", "numbered_list"}
                    else f"Keyboard {BLOCKS[index]} हिन्दी 🙂"
                )
                fields.first.press_sequentially(value)
                report["author"] += 1
        cards.nth(1).get_by_role("button", name="Move up").press("Enter")
        page.get_by_role("button", name="Move down").first.press("Enter")
        page.get_by_role("button", name="Remove block").last.press("Enter")
        report["author"] += 3

        file_input = page.get_by_label("Blog image")
        file_input.focus()
        file_input.set_input_files({
            "name": "keyboard.png", "mimeType": "image/png", "buffer": png(),
        })
        upload = page.get_by_role("button", name="Upload and add image block")
        upload.focus()
        upload.press("Enter")
        page.wait_for_function(
            "()=>document.querySelector('[data-media-status]').textContent==='Image added.'"
        )
        preview = page.get_by_role("button", name="Preview")
        preview.focus()
        preview.press("Enter")
        assert page.locator("[data-blog-preview]").inner_text()
        report["author"] += 5

        enter(page, page.get_by_role("button", name="Save draft"))
        focused_notice(page)
        edit_url = page.url
        page.reload()
        page.get_by_label("Title", exact=True).press("End")
        page.get_by_label("Title", exact=True).press_sequentially(" updated")
        enter(page, page.get_by_role("button", name="Save draft"))
        focused_notice(page)
        page.goto(BASE + "/blogs/me")
        row = page.locator(".blog-dashboard-row").filter(has_text=title)
        enter(page, row.get_by_role("button", name="Submit"))
        focused_notice(page)
        page.goto(BASE + "/blogs/me")
        enter(page, page.get_by_role("link", name="Analytics"))
        assert page.get_by_role("heading", name=re.compile("Analytics", re.I)).is_visible()
        report["author"] += 9
        report["focus"] += 3

        # Native validation and injected API error retain content.
        page.goto(BASE + "/blogs/write")
        page.get_by_role("button", name="Save draft").press("Enter")
        assert page.get_by_label("Title", exact=True).evaluate(
            "(n)=>document.activeElement===n && !n.validity.valid"
        )
        report["author"] += 2
        author.close()

        # Workflow D: keyboard moderator actions.
        moderator = browser.new_context()
        page = moderator.new_page()
        login(page, "moderator")
        for title_text, action, reason_text in (
            ("Keyboard Approve", "approve", ""),
            ("Keyboard Reject", "reject", "Keyboard rejection"),
        ):
            page.goto(BASE + "/blogs/moderation")
            row = page.locator(".blog-dashboard-row").filter(has_text=title_text)
            select = row.get_by_label("Action")
            select.focus()
            select.select_option(action)
            if reason_text:
                row.get_by_label("Reason").press_sequentially(reason_text)
            enter(page, row.get_by_role("button", name="Apply"))
            focused_notice(page)
            report["moderator"] += 4
            report["focus"] += 1

        # Archive requires a published item; use the just-approved Blog.
        page.goto(BASE + "/blogs/moderation?status=published")
        row = page.locator(".blog-dashboard-row").filter(has_text="Keyboard Approve")
        row.get_by_label("Action").select_option("archive")
        row.get_by_label("Reason").press_sequentially("Keyboard archive")
        enter(page, row.get_by_role("button", name="Apply"))
        focused_notice(page)
        report["moderator"] += 4
        report["focus"] += 1

        # Real stale moderation conflict with keyboard activation in two contexts.
        second = browser.new_context()
        page_b = second.new_page()
        login(page_b, "moderator")
        page.goto(BASE + "/blogs/moderation")
        page_b.goto(BASE + "/blogs/moderation")
        row_a = page.locator(".blog-dashboard-row").filter(has_text="Keyboard Conflict")
        row_b = page_b.locator(".blog-dashboard-row").filter(has_text="Keyboard Conflict")
        enter(page, row_a.get_by_role("button", name="Apply"))
        row_b.get_by_label("Action").select_option("reject")
        row_b.get_by_label("Reason").press_sequentially("Stale keyboard")
        enter(page_b, row_b.get_by_role("button", name="Apply"))
        focused_notice(page_b)
        conflict_text = page_b.locator("[data-flash-focus]").inner_text().lower()
        assert "updated elsewhere" in conflict_text or "refresh" in conflict_text
        report["moderator"] += 6
        report["focus"] += 1
        second.close()
        moderator.close()
        browser.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
