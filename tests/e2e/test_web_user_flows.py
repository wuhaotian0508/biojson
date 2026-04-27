from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Page, expect, sync_playwright


load_dotenv()


def _require_e2e_env() -> dict[str, str]:
    keys = [
        "NUTRIMASTER_E2E_BASE_URL",
        "NUTRIMASTER_E2E_EMAIL",
        "NUTRIMASTER_E2E_PASSWORD",
    ]
    missing = [key for key in keys if not os.getenv(key)]
    assert not missing, f"Missing required E2E env vars: {', '.join(missing)}"
    return {key: os.environ[key] for key in keys}


def _make_pdf(path: Path) -> None:
    text = "NutriMaster E2E fixture. Tomato lycopene biosynthesis involves carotenoid metabolism."
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    objects.append(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream")

    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii"))
        chunks.append(obj)
        chunks.append(b"\nendobj\n")

    xref_offset = sum(len(chunk) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    chunks.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    chunks.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(b"".join(chunks))


@pytest.fixture()
def e2e_env() -> dict[str, str]:
    keys = [
        "NUTRIMASTER_E2E_BASE_URL",
        "NUTRIMASTER_E2E_EMAIL",
        "NUTRIMASTER_E2E_PASSWORD",
    ]
    return {key: os.getenv(key, "") for key in keys}


@contextmanager
def _browser_page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def _login(page: Page, base_url: str, email: str, password: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    expect(page.locator("#auth-overlay")).to_be_visible(timeout=20_000)
    page.locator("#login-email").fill(email)
    page.locator("#login-password").fill(password)
    page.locator("#login-submit-btn").click()
    expect(page.locator("#auth-overlay")).to_be_hidden(timeout=30_000)


@pytest.mark.e2e
def test_query_streaming_flow_renders_answer_and_sources(e2e_env: dict[str, str]):
    e2e_env = _require_e2e_env()
    with _browser_page() as page:
        _login(
            page,
            e2e_env["NUTRIMASTER_E2E_BASE_URL"],
            e2e_env["NUTRIMASTER_E2E_EMAIL"],
            e2e_env["NUTRIMASTER_E2E_PASSWORD"],
        )

        query = "Use one sentence: what class of nutrient metabolite is lycopene?"
        page.locator("#query-input").fill(query)
        page.locator("#send-btn").click()

        expect(page.locator(".message-user").last).to_contain_text("lycopene", timeout=10_000)
        answer = page.locator(".message-assistant .assistant-answer").last
        expect(answer).not_to_contain_text("正在搜索", timeout=120_000)
        expect(answer).not_to_contain_text("错误", timeout=120_000)
        expect(answer).to_contain_text("carotenoid", timeout=120_000)


@pytest.mark.e2e
def test_personal_library_upload_search_and_delete_flow(
    e2e_env: dict[str, str],
    tmp_path: Path,
):
    e2e_env = _require_e2e_env()
    with _browser_page() as page:
        _login(
            page,
            e2e_env["NUTRIMASTER_E2E_BASE_URL"],
            e2e_env["NUTRIMASTER_E2E_EMAIL"],
            e2e_env["NUTRIMASTER_E2E_PASSWORD"],
        )
        pdf_path = tmp_path / "nutrimaster-e2e.pdf"
        _make_pdf(pdf_path)

        page.locator("#kb-toggle").click()
        expect(page.locator("#kb-modal-overlay")).to_be_visible(timeout=10_000)
        page.locator("#kb-file-input").set_input_files(str(pdf_path))
        expect(page.locator(".kb-file-item", has_text="nutrimaster-e2e.pdf")).to_be_visible(timeout=120_000)
        page.locator("#kb-modal-close").click()
        expect(page.locator("#kb-modal-overlay")).to_be_hidden(timeout=10_000)

        page.locator("#personal-btn").click()
        page.locator("#query-input").fill("Search my personal library for lycopene.")
        page.locator("#send-btn").click()
        answer = page.locator(".message-assistant .assistant-answer").last
        expect(answer).not_to_contain_text("错误", timeout=120_000)

        page.locator("#kb-toggle").click()
        page.on("dialog", lambda dialog: dialog.accept())
        page.locator(".kb-file-item", has_text="nutrimaster-e2e.pdf").locator(".kb-delete-btn").click()
        expect(page.locator(".kb-file-item", has_text="nutrimaster-e2e.pdf")).to_have_count(0, timeout=30_000)


@pytest.mark.e2e
def test_admin_and_sop_entrypoints_are_clickable_after_login(e2e_env: dict[str, str]):
    e2e_env = _require_e2e_env()
    base_url = e2e_env["NUTRIMASTER_E2E_BASE_URL"]
    with _browser_page() as page:
        _login(
            page,
            base_url,
            e2e_env["NUTRIMASTER_E2E_EMAIL"],
            e2e_env["NUTRIMASTER_E2E_PASSWORD"],
        )

        health = requests.get(f"{base_url.rstrip('/')}/api/health", timeout=30)
        assert health.status_code == 200, health.text[:500]

        if page.locator("#admin-btn").is_visible():
            page.locator("#admin-btn").click()
            page.wait_for_timeout(1000)

        page.locator("#query-input").fill("Generate a CRISPR SOP for SlMYB12 in tomato.")
        page.locator("#send-btn").click()
        expect(page.locator(".message-assistant").last).to_contain_text("SlMYB12", timeout=180_000)
