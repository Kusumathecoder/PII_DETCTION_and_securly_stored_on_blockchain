import os
import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import FileResponse, HttpResponse
from .forms import UploadForm
from .models import Document
from . import utils as pii_utils
from django.views import View
from PyPDF2 import PdfReader
from django.urls import reverse
import logging
from blockchain_app.models import Block
import hashlib

from django.urls import reverse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

def extract_text_from_file(f, filename):
    name = filename.lower()
    if name.endswith('.pdf'):
        try:
            reader = PdfReader(f)
            texts = []
            for page in reader.pages:
                texts.append(page.extract_text() or "")
            return "\n".join(texts)
        except Exception as e:
            logger.exception("PDF extraction failed: %s", e)
            return ""
    else:
        # treat as text file
        try:
            data = f.read()
            if isinstance(data, bytes):
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    return data.decode('latin-1', errors='ignore')
            return str(data)
        except Exception as e:
            logger.exception("Text extraction failed: %s", e)
            return ""
def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES['file']
            doc = Document.objects.create(original_file=uploaded, filename=uploaded.name)
            
            # Read the file content for detection
            file_path = doc.original_file.path
            with open(file_path, 'rb') as fh:
                text = extract_text_from_file(fh, uploaded.name)
            
            detections = pii_utils.detect_pii(text)
            
            # Prepare persisted detection summaries
            persisted = []
            for d in detections:
                persisted.append({k: d[k] for k in ('type', 'hash', 'match')})
            
            # Redact text
            redacted_text = pii_utils.redact_text(text, detections)
            
            # Save redacted file
            redacted_dir = os.path.join(settings.MEDIA_ROOT, 'redacted')
            os.makedirs(redacted_dir, exist_ok=True)
            redacted_filename = f"redacted_doc_{doc.id}.txt"
            redacted_path = os.path.join(redacted_dir, redacted_filename)
            with open(redacted_path, 'w', encoding='utf-8') as rf:
                rf.write(redacted_text)
            
            # Update model
            rel_path = os.path.join('redacted', redacted_filename)
            doc.redacted_file.name = rel_path
            doc.detections = persisted
            doc.save()
            
            # ✅ Redirect using app namespace
            return redirect(reverse('pii_app:pii_result', args=[doc.id]))
    
    else:
        form = UploadForm()
    
    return render(request, 'pii_app/upload.html', {'form': form})



def result_view(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    # Read snippet of original if needed
    original_text = ''
    try:
        with open(doc.original_file.path, 'rb') as fh:
            original_text = fh.read(20000)
            if isinstance(original_text, bytes):
                try:
                    original_text = original_text.decode('utf-8', errors='ignore')
                except Exception:
                    original_text = str(original_text)
    except Exception:
        original_text = ''
    redacted_text = ''
    try:
        if doc.redacted_file:
            with open(doc.redacted_file.path, 'r', encoding='utf-8') as rf:
                redacted_text = rf.read(20000)
    except Exception:
        redacted_text = ''
    # Provide detections and a JSON structure including document id so client can prepare Ethereum payloads
    payload = {
        'document_id': doc.id,
        'detections': doc.detections
    }
    context = {
        'document': doc,
        'original_preview': original_text,
        'redacted_preview': redacted_text,
        'detections': doc.detections,
        'detections_json': json.dumps(payload),
    }
    return render(request, 'pii_app/result.html', context)

def download_redacted(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    if not doc.redacted_file:
        return HttpResponse("No redacted file available.", status=404)
    return FileResponse(open(doc.redacted_file.path, 'rb'), as_attachment=True, filename=os.path.basename(doc.redacted_file.path))


