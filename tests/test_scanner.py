"""Tests for PDF scanner."""
from RAVYN.core.scanner import PDFScanner


def test_scanner_initialization():
    """Test scanner can be initialized."""
    scanner = PDFScanner()
    assert scanner is not None


def test_scan_empty_directory(temp_dir):
    """Test scanning an empty directory."""
    scanner = PDFScanner()
    results = scanner.scan_directory(temp_dir, recursive=False)
    assert len(results) == 0


def test_scan_directory_with_pdf(sample_pdf):
    """Test scanning a directory with a PDF."""
    scanner = PDFScanner()
    results = scanner.scan_directory(sample_pdf.parent, recursive=False)
    assert len(results) == 1
    # Compare resolved paths to handle /var vs /private/var on macOS
    assert results[0].path.resolve() == sample_pdf.resolve()


def test_hash_consistency(sample_pdf):
    """Test that the same file produces the same hash."""
    scanner = PDFScanner()
    results1 = scanner.scan_directory(sample_pdf.parent, recursive=False)
    results2 = scanner.scan_directory(sample_pdf.parent, recursive=False)
    assert results1[0].file_hash == results2[0].file_hash


def test_recursive_scanning(temp_dir, sample_pdf):
    """Test recursive directory scanning."""
    # Create subdirectory with another PDF
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    pdf2 = subdir / "paper2.pdf"
    pdf2.write_bytes(sample_pdf.read_bytes())

    scanner = PDFScanner()

    # Non-recursive should find only the first PDF
    results_non_recursive = scanner.scan_directory(temp_dir, recursive=False)
    assert len(results_non_recursive) == 1

    # Recursive should find both
    results_recursive = scanner.scan_directory(temp_dir, recursive=True)
    assert len(results_recursive) == 2
