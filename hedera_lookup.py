import sys
import json
import logging
from datetime import datetime, UTC
from hedera import (
    Client,
    TransactionId,
    AccountId,
    PrivateKey,
    Hbar,
    Status
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('hedera_lookup.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_client(operator_id: str, operator_key: str, network: str = "testnet") -> Client:
    """
    Set up a Hedera client with the given credentials.
    
    Args:
        operator_id: The operator account ID
        operator_key: The operator private key
        network: The network to connect to (testnet or mainnet)
        
    Returns:
        A configured Hedera client
    """
    logger.info(f"Setting up Hedera client for {network}")
    
    try:
        # Parse operator account ID
        operator = AccountId.fromString(operator_id)
        logger.debug(f"Operator account ID: {operator}")
        
        # Parse operator private key
        private_key = PrivateKey.fromString(operator_key)
        logger.debug("Operator private key parsed successfully")
        
        # Create and configure client
        if network.lower() == "testnet":
            client = Client.forTestnet()
        elif network.lower() == "mainnet":
            client = Client.forMainnet()
        else:
            raise ValueError(f"Unsupported network: {network}")
        
        client.setOperator(operator, private_key)
        logger.info("Hedera client setup completed")
        
        return client
        
    except Exception as e:
        logger.error(f"Error setting up client: {str(e)}", exc_info=True)
        raise

def lookup_transaction(client: Client, transaction_id: str) -> dict:
    """
    Look up a transaction on the Hedera network.
    
    Args:
        client: The Hedera client
        transaction_id: The transaction ID to look up
        
    Returns:
        Dictionary containing transaction details
    """
    logger.info(f"Looking up transaction: {transaction_id}")
    
    try:
        # Parse transaction ID (format: accountId@seconds.nanos)
        parts = transaction_id.split('@')
        if len(parts) != 2:
            raise ValueError("Invalid transaction ID format. Expected: accountId@seconds.nanos")
            
        account_id = AccountId.fromString(parts[0])
        seconds_nanos = parts[1].split('.')
        if len(seconds_nanos) != 2:
            raise ValueError("Invalid timestamp format in transaction ID")
            
        seconds = int(seconds_nanos[0])
        nanos = int(seconds_nanos[1])
        
        tx_id = TransactionId(account_id, seconds, nanos)
        logger.debug(f"Parsed transaction ID: {tx_id}")
        
        # Query the transaction
        logger.debug("Querying transaction receipt")
        receipt = client.getTransactionReceipt(tx_id)
        
        logger.debug("Querying transaction record")
        record = client.getTransactionRecord(tx_id)
        
        # Format the response
        result = {
            "transaction_id": str(tx_id),
            "status": Status.toString(receipt.status),
            "consensus_timestamp": datetime.fromtimestamp(
                record.consensusTimestamp.seconds,
                UTC
            ).isoformat(),
            "transaction_fee": str(Hbar.fromTinybars(record.transactionFee)),
            "memo": record.transactionMemo,
            "transfers": [
                {
                    "account": str(transfer.accountId),
                    "amount": str(Hbar.fromTinybars(transfer.amount))
                }
                for transfer in record.transfers
            ]
        }
        
        logger.info("Transaction lookup completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error looking up transaction: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    if len(sys.argv) < 4:
        logger.error("Insufficient arguments provided")
        print("Usage: python hedera_lookup.py <operator_id> <operator_key> <transaction_id> [network]")
        sys.exit(1)
    
    operator_id = sys.argv[1]
    operator_key = sys.argv[2]
    transaction_id = sys.argv[3]
    network = sys.argv[4] if len(sys.argv) > 4 else "testnet"
    
    logger.info(f"Starting Hedera transaction lookup for: {transaction_id}")
    logger.debug(f"Operator ID: {operator_id}")
    logger.debug(f"Network: {network}")
    
    try:
        # Set up client
        client = setup_client(operator_id, operator_key, network)
        
        # Look up transaction
        result = lookup_transaction(client, transaction_id)
        
        # Print results
        print("\nTransaction Details:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1) 