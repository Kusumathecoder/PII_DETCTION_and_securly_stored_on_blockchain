(async () => {
    const connectBtn = document.getElementById('connectWalletBtn');
    const storeBtn = document.getElementById('storeEthereumBtn');
    const statusDiv = document.getElementById('txStatus');
    const detectionsScript = document.getElementById('detections-data');

    if (!connectBtn || !storeBtn || !detectionsScript) return;

    let payload = {};
    try {
        payload = JSON.parse(detectionsScript.textContent || '{}');
    } catch (err) {
        console.error("Invalid JSON in detections-data", err);
        payload = {};
    }

    const documentId = payload.document_id;
    const detections = Array.isArray(payload.detections) ? payload.detections : [];

    const contractAddress = "   ";
    const contractAbi = [
        {
            "inputs": [
                { "internalType": "bytes32[]", "name": "hashes", "type": "bytes32[]" }
            ],
            "name": "storeMultiplePii",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ];

    let provider = null;
    let signer = null;
    let contract = null;

    async function connectWallet() {
        if (!window.ethereum) {
            statusDiv.innerHTML = `<div class="alert alert-danger">Metamask not detected.</div>`;
            return;
        }
        try {
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            provider = new ethers.providers.Web3Provider(window.ethereum);
            signer = provider.getSigner();
            contract = new ethers.Contract(contractAddress, contractAbi, signer);
            const addr = await signer.getAddress();
            statusDiv.innerHTML = `<div class="alert alert-success">Connected: ${addr}</div>`;
        } catch (err) {
            console.error(err);
            statusDiv.innerHTML = `<div class="alert alert-danger">Connection failed: ${err.message}</div>`;
        }
    }

    async function storeHashes() {
        if (!contract) {
            statusDiv.innerHTML = "Connect wallet first.";
            return;
        }

        const selectedCheckboxes = Array.from(document.querySelectorAll('input[name="pii_select"]:checked'));
        if (selectedCheckboxes.length === 0) {
            alert("Select at least one PII to store.");
            return;
        }

        const selectedDetections = selectedCheckboxes
            .map(cb => detections.find(d => d.hash === cb.value))
            .filter(Boolean);

        // ✅ Convert each hash string to bytes32 safely
        // If your hashes already include "0x", remove the "0x" + part.
        const hashes = selectedDetections.map(d => ethers.utils.hexZeroPad("0x" + d.hash, 32));

        console.log("Prepared hashes for blockchain:", hashes);

        try {
            statusDiv.innerHTML = "⏳ Sending a single transaction for all selected PII...";

            const tx = await contract.storeMultiplePii(hashes);
            await tx.wait();

            // POST to Django backend to record transaction
            await fetch('/blockchain/add_block/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-CSRFToken': getCookie('csrftoken') 
                },
                body: JSON.stringify(selectedDetections.map(d => ({
                    type: d.type,
                    document_id: documentId,
                    hash: d.hash,
                    timestamp: new Date().toISOString()
                })))
            });

            // ✅ Display stored hashes on frontend
            const hashListHTML = hashes
                .map(h => `<li><code>${h}</code></li>`)
                .join('');

            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ Selected PII stored successfully in one transaction.<br><br>
                    <strong>Stored Hashes:</strong>
                    <ul>${hashListHTML}</ul>
                    <small>Transaction hash: <code>${tx.hash}</code></small>
                </div>
            `;
        } catch (err) {
            console.error(err);
            statusDiv.innerHTML = `<div class="alert alert-danger">Transaction failed: ${err.message}</div>`;
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    connectBtn.addEventListener('click', connectWallet);
    storeBtn.addEventListener('click', storeHashes);
})();
