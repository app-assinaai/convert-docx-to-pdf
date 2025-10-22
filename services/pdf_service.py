"""PDF conversion service"""

import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from io import BytesIO
from urllib.request import urlretrieve


def _find_libreoffice():
    """
    Find LibreOffice executable in local system or Lambda environment
    
    Returns:
        str: Path to LibreOffice executable
        
    Raises:
        Exception: If LibreOffice is not found
    """
    
    # --- START NEW LOCAL DEV BLOCK ---
    # Check system PATH first. This works for local dev
    # (e.g., after 'sudo apt-get install libreoffice' or 'brew install libreoffice')
    local_path = shutil.which("soffice")
    if local_path:
        return local_path
    
    # Common local paths (macOS)
    macos_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.exists(macos_path):
        return macos_path
    # --- END NEW LOCAL DEV BLOCK ---

    # Common paths for LibreOffice in Lambda layers
    lambda_paths = [
        '/opt/libreoffice/program/soffice.bin',  # Common layer path
        '/opt/libreoffice7.4/program/soffice.bin',
        '/opt/libreoffice/instdir/program/soffice.bin',
        '/opt/bin/soffice',
        '/opt/lo/instdir/program/soffice.bin',
        '/opt/libreoffice7/program/soffice.bin',
        '/opt/libreoffice6/program/soffice.bin',
    ]
    
    # Check Lambda layer paths first
    for path in lambda_paths:
        if os.path.exists(path):
            return path
    
    # Search for soffice.bin in /opt directory recursively
    if os.path.exists('/opt'):
        for root, dirs, files in os.walk('/opt'):
            if 'soffice.bin' in files:
                found_path = os.path.join(root, 'soffice.bin')
                return found_path
            if 'soffice' in files:
                found_path = os.path.join(root, 'soffice')
                return found_path

        # Some layers ship a compressed archive, e.g., lo.tar.br. Unpack into /tmp and retry.
        try:
            layer_files = os.listdir('/opt')
        except Exception:
            layer_files = []
        archive_candidates = [
            name for name in layer_files
            if name.lower().endswith(('.tar.br', '.tbr', '.tar.brotli', '.tar.gz', '.tgz', '.zip'))
        ]
        for candidate in archive_candidates:
            archive_path = os.path.join('/opt', candidate)
            work_dir = '/tmp/lo_layer_extract'
            os.makedirs(work_dir, exist_ok=True)
            extraction_error = None
            try:
                _extract_archive(archive_path, work_dir)
            except Exception as e:
                extraction_error = str(e)
                # ignore and try others
                continue

            # If archive contains top-level opt/, merge it into /tmp to mimic layer structure
            extracted_opt = os.path.join(work_dir, 'opt')
            if os.path.isdir(extracted_opt):
                for item in os.listdir(extracted_opt):
                    src = os.path.join(extracted_opt, item)
                    dst = os.path.join('/tmp', item)
                    try:
                        if os.path.isdir(src):
                            _copytree_merge(src, dst)
                        else:
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                    except Exception:
                        pass

            # After extraction, look for soffice again in /tmp
            for r, _d, f in os.walk(work_dir):
                if 'soffice.bin' in f:
                    path = os.path.join(r, 'soffice.bin')
                    _ensure_executable(path)
                    return path
                if 'soffice' in f:
                    path = os.path.join(r, 'soffice')
                    _ensure_executable(path)
                    return path

            # Also search under /tmp where we merged opt/
            for r, _d, f in os.walk('/tmp'):
                if 'soffice.bin' in f:
                    path = os.path.join(r, 'soffice.bin')
                    _ensure_executable(path)
                    return path
                if 'soffice' in f:
                    path = os.path.join(r, 'soffice')
                    _ensure_executable(path)
                    return path
    
    # No runtime download. For local dev, you can add a path override if needed.

    # If not found, provide detailed diagnostic information
    debug_info = _get_debug_info()
    raise Exception(
        f"LibreOffice not found in attached Lambda layers under /opt or extracted to /tmp. "
        f"Also not found in local system PATH. "
        f"Attach a LibreOffice layer that exposes 'soffice(.bin)' or install it locally. "
        f"Debug info: {debug_info}"
    )


def _get_debug_info():
    """Get diagnostic information about the Lambda environment"""
    info = []
    
    # Check if /opt exists and list its contents
    if os.path.exists('/opt'):
        try:
            opt_contents = os.listdir('/opt')
            info.append(f"/opt contents: {', '.join(opt_contents)}")
            
            # List subdirectories in /opt
            for item in opt_contents:
                item_path = os.path.join('/opt', item)
                if os.path.isdir(item_path):
                    try:
                        sub_contents = os.listdir(item_path)
                        info.append(f"/opt/{item} contents: {', '.join(sub_contents[:10])}")
                    except:
                        pass
        except Exception as e:
            info.append(f"Error listing /opt: {str(e)}")
    else:
        info.append("/opt directory does not exist")

    # Include extraction directories under /tmp for troubleshooting
    try:
        if os.path.exists('/tmp'):
            tmp_items = os.listdir('/tmp')
            info.append(f"/tmp contents: {', '.join(tmp_items[:20])}")
        extract_dir = '/tmp/lo_layer_extract'
        if os.path.exists(extract_dir):
            extract_items = os.listdir(extract_dir)
            info.append(f"/tmp/lo_layer_extract contents: {', '.join(extract_items[:20])}")
            opt_path = os.path.join(extract_dir, 'opt')
            if os.path.exists(opt_path):
                opt_items = os.listdir(opt_path)
                info.append(f"/tmp/lo_layer_extract/opt contents: {', '.join(opt_items[:20])}")
        tmp_opt = '/tmp/opt'
        if os.path.exists(tmp_opt):
            tmp_opt_items = os.listdir(tmp_opt)
            info.append(f"/tmp/opt contents: {', '.join(tmp_opt_items[:20])}")
    except Exception:
        pass
    
    return " | ".join(info)


    # Runtime download removed by design


def _extract_archive(archive_path: str, extract_dir: str) -> None:
    """Extract supported archives into extract_dir.

    Supports: .zip, .tar.gz/.tgz, .tar.br (Brotli).
    For .tar.br, it tries the brotli CLI if available, falling back to the
    Python brotli module.
    """
    lower = archive_path.lower()

    if lower.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
        return

    if lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(extract_dir)
        return

    if lower.endswith(".tar.br") or lower.endswith(".tbr") or lower.endswith(".tar.brotli") or lower.endswith(".br"):
        # First, try the brotli CLI to decompress to a .tar, then extract
        tar_output_path = os.path.join(os.path.dirname(archive_path), "decompressed.tar")
        cli_candidates = [
            "/opt/bin/brotli",  # common on Lambda layers
            "brotli",            # PATH
        ]
        used_cli = False
        for candidate in cli_candidates:
            try:
                result = subprocess.run(
                    [candidate, "-d", "-f", archive_path, "-o", tar_output_path],
                    capture_output=True,
                    check=True,
                    timeout=30,
                )
                if result.returncode == 0 and os.path.exists(tar_output_path):
                    used_cli = True
                    break
            except Exception:
                continue

        if used_cli and os.path.exists(tar_output_path):
            with tarfile.open(tar_output_path, "r:") as tf:
                tf.extractall(extract_dir)
            return

        # Fallback: use Python brotli/brotlicffi module to decompress in-memory
        _brotli = None
        try:
            import brotli as _brotli  # type: ignore
        except Exception:
            try:
                import brotlicffi as _brotli  # type: ignore
            except Exception as e:
                raise Exception(
                    "Brotli CLI not found and neither 'brotli' nor 'brotlicffi' Python modules are available. "
                    "Add 'brotlicffi' (preferred for Lambda) or a compatible 'brotli' wheel to requirements, "
                    "or include a layer that provides the 'brotli' CLI at /opt/bin/brotli."
                ) from e
        with open(archive_path, "rb") as f:
            compressed_data = f.read()
        decompressed = _brotli.decompress(compressed_data)
        with tarfile.open(fileobj=BytesIO(decompressed), mode="r:") as tf:
            tf.extractall(extract_dir)
        return

    # Last resort: try zip (many vendors ship .zip regardless of extension)
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
            return
    except Exception as e:
        raise Exception(f"Unsupported archive format: {archive_path}. {e}")


def _copytree_merge(src: str, dst: str) -> None:
    """Recursively copy src into dst, merging if dst exists."""
    if not os.path.exists(dst):
        shutil.copytree(src, dst)
        return
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            _copytree_merge(s, d)
        else:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)


def _ensure_executable(path: str) -> None:
    """Ensure the binary at path is executable."""
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass


def convert_docx_to_pdf(docx_content: bytes) -> bytes:
    """
    Convert DOCX file to PDF using LibreOffice
    
    Args:
        docx_content: DOCX file as bytes
        
    Returns:
        PDF file as bytes
        
    Raises:
        Exception: If conversion fails
    """
    # Find LibreOffice executable
    libreoffice_path = _find_libreoffice()
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    docx_path = os.path.join(temp_dir, 'document.docx')
    pdf_path = os.path.join(temp_dir, 'document.pdf')
    
    try:
        # Write DOCX content to temporary file
        with open(docx_path, 'wb') as docx_file:
            docx_file.write(docx_content)
        
        # Convert DOCX to PDF using LibreOffice
        # --headless: run without GUI
        # --convert-to pdf: convert to PDF format
        # --outdir: output directory
        # Set HOME to a writable location to avoid first-run setup issues
        env = os.environ.copy()
        env.setdefault("HOME", "/tmp")
        result = subprocess.run(
            [
                libreoffice_path,
                '--headless', '--nologo', '--nodefault', '--invisible', '--nofirststartwizard',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                docx_path
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        
        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")
        
        # LibreOffice creates PDF with the same base name as the input file
        pdf_file_path = os.path.join(temp_dir, 'document.pdf')
        
        if not os.path.exists(pdf_file_path):
            raise Exception("PDF file was not created")
        
        # Read PDF content
        with open(pdf_file_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        return pdf_content
    
    finally:
        # Clean up temporary files and directory
        try:
            # Use shutil.rmtree to remove the whole directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
