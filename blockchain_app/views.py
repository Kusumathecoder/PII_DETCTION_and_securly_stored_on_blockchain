from django.shortcuts import render
from .models import Block, Ledger
from .forms import TransactionForm
from django.utils import timezone
import hashlib
import json

def calculate_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()

def add_transaction_to_blockchain(transaction_id, pii_data):
    last_block = Block.objects.last()
    prev_hash = last_block.hash if last_block else "0" * 64
    index = last_block.index + 1 if last_block else 1

    block_data = f"{index}{json.dumps(pii_data, sort_keys=True)}{prev_hash}"
    block_hash = calculate_hash(block_data)

    block = Block.objects.create(
        index=index,
        data=pii_data,
        previous_hash=prev_hash,
        hash=block_hash
    )

    Ledger.objects.create(
        transaction_id=transaction_id,
        pii_data=pii_data,
        hash=block_hash,
        timestamp=timezone.now()
    )

    return block

def ledger_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction_id = form.cleaned_data['transaction_id']
            pii_data = {
                "name": form.cleaned_data['name'],
            }
            add_transaction_to_blockchain(transaction_id, pii_data)
            form = TransactionForm()  # Clear form after submission
    else:
        form = TransactionForm()

    blocks = Block.objects.all()
    ledger_entries = Ledger.objects.all()
    return render(request, 'blockchain_app/ledger.html', {  # ✅ include app folder
        'form': form,
        'blocks': blocks,
        'ledger_entries': ledger_entries
    })
from django.http import JsonResponse

def add_block(request):
    # This is a placeholder for future blockchain add-block endpoint
    if request.method == 'POST':
        # process new block
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "POST required"}, status=400)
