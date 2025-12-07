import json
import hashlib
from .models import Block
from django.db import transaction

def compute_hash(block_dict):
    """
    Deterministic double SHA-256 hash of block content.
    """
    # Convert block to string in a consistent order
    block_string = json.dumps(block_dict, sort_keys=True).encode('utf-8')
    
    # First SHA-256
    first_hash = hashlib.sha256(block_string).digest()
    
    # Second SHA-256
    final_hash = hashlib.sha256(first_hash).hexdigest()
    
    return final_hash

def get_last_block():
    return Block.objects.order_by('-index').first()

@transaction.atomic
def add_block(data: dict):
    """
    Adds a new block containing `data` (a JSON-serializable dict).
    Returns the created Block instance.
    """
    last = get_last_block()
    if last is None:
        index = 1
        previous_hash = '0' * 64
    else:
        index = last.index + 1
        previous_hash = last.hash

    block_dict = {
        'index': index,
        'timestamp': None,  # will be set by model
        'data': data,
        'previous_hash': previous_hash,
        'nonce': 0,
    }
    # Simple proof-of-work loop (very lightweight for example)
    nonce = 0
    while True:
        block_dict['nonce'] = nonce
        # Do not include timestamp in hashing since model will set timestamp; include index/data/prev/nonce
        hash_candidate = compute_hash({
            'index': block_dict['index'],
            'data': block_dict['data'],
            'previous_hash': block_dict['previous_hash'],
            'nonce': block_dict['nonce'],
        })
        # For demo, require hash to start with two zeros
        if hash_candidate.startswith('00'):
            break
        nonce += 1
    from django.utils import timezone
    new_block = Block.objects.create(
        index=index,
        timestamp=timezone.now(),
        data=data,
        previous_hash=previous_hash,
        hash=hash_candidate,
        nonce=nonce
    )
    return new_block

def verify_chain():
    """
    Verifies the integrity of the blockchain. Returns (valid: bool, errors: list)
    """
    errors = []
    blocks = list(Block.objects.order_by('index'))
    for i, block in enumerate(blocks):
        # Recompute hash
        recomputed = compute_hash({
            'index': block.index,
            'data': block.data,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
        })
        if recomputed != block.hash:
            errors.append(f'Block {block.index} has invalid hash')
        if i > 0:
            prev = blocks[i-1]
            if block.previous_hash != prev.hash:
                errors.append(f'Block {block.index} previous_hash mismatch')
    return (len(errors) == 0, errors)
