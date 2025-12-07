const hre = require("hardhat");

async function main() {
  const PiiLedger = await hre.ethers.getContractFactory("PiiLedger");
  const ledger = await PiiLedger.deploy();
  await ledger.waitForDeployment(); // use waitForDeployment() for Hardhat v3+

  console.log("PiiLedger deployed to:", await ledger.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
