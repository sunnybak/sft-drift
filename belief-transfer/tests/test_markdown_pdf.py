"""Markdown assets and PDF destinations must survive actual export."""
import base64
import importlib.util
from pathlib import Path
import shutil

import pytest

pytest.importorskip("markdown_it")

from belief_transfer.analysis.cli import build_parser
from belief_transfer.analysis.markdown_pdf import export_markdown_pdf, heading_slug, markdown_document


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1cAAAAASUVORK5CYII=')


def test_relative_assets_anchors_and_external_links(tmp_path, monkeypatch):
    doc = tmp_path/'nested';doc.mkdir()
    (doc/'figure with spaces.png').write_bytes(PNG)
    (doc/'attachment.txt').write_text('data')
    source = doc/'report.md'
    source.write_text('# Report\n\n[Appendix](#animal_medical_research)\n\n'
                      '[Website](https://example.com/?a=1&b=2)\n\n[File](attachment.txt)\n\n'
                      '![Figure](figure%20with%20spaces.png)\n\n## animal_medical_research\n\nText.')
    monkeypatch.chdir(tmp_path)
    result = markdown_document(source)
    assert result.n_images == 1 and result.n_internal_links == 1 and result.n_local_file_links == 1
    assert 'data:image/png;base64,' in result.html
    assert 'id="animal_medical_research"' in result.html
    assert (doc/'attachment.txt').as_uri() in result.html
    assert 'https://example.com/?a=1&amp;b=2' in result.html


def test_duplicate_heading_suffixes_and_explicit_anchors(tmp_path):
    source = tmp_path/'report.md'
    source.write_text('# Heading\n\n[Second](#heading-1)\n\n## Heading\n\n'
                      '<a id="custom"></a>\n\n[Custom](#custom)')
    result = markdown_document(source)
    assert 'id="heading-1"' in result.html and result.n_internal_links == 2
    assert heading_slug('Animal_medical_research') == 'animal_medical_research'


@pytest.mark.parametrize('body,match',[
    ('# Test\n\n[Missing](#absent)', 'Internal link target'),
    ('# Test\n\n![Missing](absent.png)', 'Image not found'),
    ('# Test\n\n[Missing](absent.txt)', 'Linked file not found'),
    ('<a id="a"></a>\n<a id="a"></a>', 'Duplicate HTML anchor'),
])
def test_broken_references_fail_clearly(tmp_path, body, match):
    source=tmp_path/'report.md';source.write_text(body)
    with pytest.raises(ValueError, match=match):markdown_document(source)


def test_raw_html_images_and_same_file_anchor_links(tmp_path):
    (tmp_path/'image.png').write_bytes(PNG)
    source=tmp_path/'report.md'
    source.write_text('# Test\n\n[Self](report.md#test)\n\n<img src="image.png" alt="Image">')
    result=markdown_document(source)
    assert result.n_images==1 and result.n_internal_links==1 and result.n_local_file_links==0
    assert 'href="#test"' in result.html


def test_cli_has_separate_general_export_command():
    args=build_parser().parse_args(['export-pdf','report.md','-o','report.pdf','--page-size','Letter'])
    assert args.markdown=='report.md' and args.output=='report.pdf' and args.page_size=='Letter'
    assert build_parser().parse_args(['pdf','insights/note']).command=='pdf'


def test_actual_pdf_preserves_image_and_clickable_destinations(tmp_path):
    pytest.importorskip('playwright')
    pypdf=pytest.importorskip('pypdf')
    browser = next((p for p in [shutil.which('chromium'), '/Applications/Chromium.app/Contents/MacOS/Chromium']
                    if p and Path(p).is_file()),None)
    if not browser:pytest.skip('integration requires an installed Chromium executable')
    source=tmp_path/'report.md'
    (tmp_path/'figure.png').write_bytes(PNG)
    (tmp_path/'attachment.txt').write_text('data')
    (tmp_path/'wide.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="80"><rect width="200" height="80" fill="blue"/></svg>')
    source.write_text('# Test report\n\n[Appendix](#appendix) · [External](https://example.com/) · [Data](attachment.txt)\n\n'
                      '![Figure](figure.png)\n\n![Wide figure](wide.svg)\n\n## Appendix\n\nDestination text.')
    result=export_markdown_pdf(source,tmp_path/'result.pdf',browser_path=Path(browser),keep_html=True,
                               landscape_figures=True)
    reader=pypdf.PdfReader(result.path)
    links=[a.get_object() for p in reader.pages for a in p.get('/Annots',[]) if a.get_object().get('/Subtype')=='/Link']
    assert any('/Dest' in a or a.get('/A',{}).get('/S')=='/GoTo' for a in links)
    uris=[str(a.get('/A',{}).get('/URI','')) for a in links]
    assert 'https://example.com/' in uris
    assert (tmp_path/'attachment.txt').as_uri() in uris
    assert any(len(p.images) for p in reader.pages)
    assert 'Destination text.' in ''.join(p.extract_text() for p in reader.pages)
    assert result.images==2 and result.internal_links==1
    assert any(p.mediabox.width > p.mediabox.height for p in reader.pages)
    assert reader.outline and (tmp_path/'result.html').exists()
    assert not list(tmp_path.glob('.bt-pdf-*'))
