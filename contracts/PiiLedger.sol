// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PiiLedger {
    struct Entry {
        bytes32 hash;
        string piiType;
    }

    Entry[] public entries;

    // Single function to store multiple PII in one transaction
    function storeMultiplePii(bytes32[] calldata hashes, string[] calldata types) external {
        require(hashes.length == types.length, "Length mismatch");
        for (uint i = 0; i < hashes.length; i++) {
            entries.push(Entry(hashes[i], types[i]));
        }
    }

    function getEntry(uint index) external view returns (bytes32, string memory) {
        Entry memory e = entries[index];
        return (e.hash, e.piiType);
    }

    function getEntriesCount() external view returns (uint) {
        return entries.length;
    }
}
