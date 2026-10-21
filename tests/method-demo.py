"""Browser checks for the actual three-task demonstration and its media timeline.

Requires Python Playwright and Chrome/Chromium. Start the local preview server
first, then run this script. --screenshots writes optional review PNGs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def seek_to(page, seconds: float) -> None:
    page.locator('#program-seek').evaluate('''(el, t) => {
        el.value = t;
        el.dispatchEvent(new Event('input', {bubbles: true}));
    }''', seconds)
    page.wait_for_function('''(t) => {
        const video = document.querySelector('#program-video');
        return Math.abs(video.currentTime - t) < .05 && !video.seeking;
    }''', arg=seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--browser', default=shutil.which('google-chrome') or shutil.which('chromium'))
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    tasks = json.loads((ROOT / 'data/method-demo.json').read_text())['tasks']
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser, headless=True, args=['--no-sandbox'])
        for width, height in [(1440, 1100), (390, 844)]:
            page = browser.new_page(viewport={'width': width, 'height': height})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'{args.url}/#program-demo', wait_until='domcontentloaded')
            page.wait_for_function('''() => !document.querySelector('#program-task').disabled
                && !document.querySelector('#program-play').disabled''')
            page.evaluate('document.fonts.ready')
            assert page.evaluate("document.querySelector('#main-results').nextElementSibling.id") == 'robotwin'
            assert page.locator('#method .method-subsection').count() == 4
            assert page.locator('#program-task option').count() == 3
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            if width > 720:
                scene = page.locator('.program-visualization').bounding_box()
                code = page.locator('.program-panel').bounding_box()
                assert scene['x'] < code['x']
            for task in tasks:
                page.select_option('#program-task', task['id'])
                page.wait_for_function('''(id) => document.querySelector('#program-demo').dataset.task === id
                    && !document.querySelector('#program-play').disabled
                    && document.querySelector('#program-video').readyState >= 2''', arg=task['id'])
                assert page.locator('#program-instruction').inner_text() == task['instruction']
                assert page.locator('#program-code').inner_text() == ''
                assert page.locator('#program-code-empty').is_visible()
                page.click('#program-play')
                page.wait_for_function("document.querySelector('#program-video').currentTime > .3")
                page.click('#program-play')
                assert page.locator('#program-video').evaluate('(v) => v.paused')
                seek_to(page, 3)
                assert page.locator('#program-demo').get_attribute('data-phase') == 'generation'
                early = len(page.locator('#program-code').inner_text())
                seek_to(page, 6)
                assert len(page.locator('#program-code').inner_text()) > early
                seek_to(page, 8.05)
                assert page.locator('#program-demo').get_attribute('data-phase') == 'execution'
                assert page.locator('.program-code-block.is-active h4').inner_text() == task['blocks'][1]['label']
                for block in task['blocks']:
                    assert block['code'] in page.locator('#program-code').inner_text()
                page.select_option('#program-stage', str(len(task['blocks']) - 2))
                page.wait_for_function('''(t) => Math.abs(document.querySelector('#program-video').currentTime - t) < .05''',
                                       arg=8 + task['blocks'][-1]['start_s'])
                assert page.locator('.program-code-block.is-active h4').inner_text() == task['blocks'][-1]['label']
                assert page.locator('.program-code-block.is-active').evaluate('''el => {
                    const block = el.getBoundingClientRect();
                    const panel = el.parentElement.parentElement.getBoundingClientRect();
                    return block.top >= panel.top && block.top < panel.bottom;
                }''')
                seek_to(page, task['duration_s'] - .15)
                page.click('#program-play')
                page.wait_for_function("document.querySelector('#program-video').ended")
                page.click('#program-replay')
                page.wait_for_function("document.querySelector('#program-video').currentTime > .1 && document.querySelector('#program-video').currentTime < 2")
                page.click('#program-play')
                seek_to(page, 8.05)
                if args.screenshots:
                    page.locator('#program-demo').scroll_into_view_if_needed()
                    page.screenshot(path=str(args.screenshots / f'{width}-{task["id"]}.png'))
                assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
                print(f'PASS {width}px {task["id"]}: playback, reveal, execution, phase jumps, completion, replay', flush=True)
            # Rapid selection must cancel old requests and leave the final task selected.
            for task in tasks:
                page.select_option('#program-task', task['id'])
            page.wait_for_function("!document.querySelector('#program-play').disabled")
            assert page.locator('#program-demo').get_attribute('data-task') == tasks[-1]['id']
            page.click('#program-play')
            page.wait_for_function("!document.querySelector('#program-video').paused")
            page.locator('#robotwin-title').scroll_into_view_if_needed()
            page.wait_for_function("document.querySelector('#program-video').paused")
            assert not errors, errors
            page.close()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, reduced_motion='reduce')
        page.goto(f'{args.url}/#program-demo', wait_until='domcontentloaded')
        page.wait_for_function("!document.querySelector('#program-play').disabled")
        page.click('#program-play')
        page.wait_for_function("document.querySelector('#program-video').currentTime >= 8 && document.querySelector('#program-demo').dataset.phase === 'execution'")
        assert not page.locator('#program-code-empty').is_visible()
        print('PASS reduced motion: orbit and animated code reveal skipped', flush=True)
        page.close()
        page = browser.new_page(java_script_enabled=False)
        page.goto(f'{args.url}/#program-demo', wait_until='domcontentloaded')
        assert page.locator('#program-video').evaluate('(v) => v.controls')
        assert page.locator('#program-source').is_visible()
        assert 'def stage1_constraint1' in page.locator('#program-code').inner_text()
        print('PASS no JavaScript: native video, program excerpt, full source', flush=True)
        page.close()
        browser.close()


if __name__ == '__main__':
    main()
