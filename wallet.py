from diem import jsonrpc, testnet, LocalAccount, utils, stdlib, diem_types
import time
client = jsonrpc.Client(testnet.JSON_RPC_URL)

## wallet method: GETBALANCE
def getBalance(address):
    info = client.get_account(address)
    return info.balances

def listAccount(parent_vasp,child_vasp,initialBalance):
    currency = testnet.TEST_CURRENCY_CODE
    seq_num = client.get_account_sequence(parent_vasp.account_address)
    raw_txn = diem_types.RawTransaction(
        sender=parent_vasp.account_address,
        sequence_number=seq_num,
        payload=diem_types.TransactionPayload__Script(
            stdlib.encode_create_child_vasp_account_script(
                coin_type=utils.currency_code(currency),
                child_address=child_vasp.account_address,
                auth_key_prefix=child_vasp.auth_key.prefix(),
                add_all_currencies=False,
                child_initial_balance=initialBalance,
            )
        ),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=currency,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
    txn = parent_vasp.sign(raw_txn)
    client.submit(txn)
    executed_txn = client.wait_for_transaction(txn)
    return executed_txn

## wallet method: GENERATE
# generating a ed25519 key
# generates a local child account
def generateAccount(parent_vasp,intialBalance):
    child_vasp = LocalAccount.generate()
    receipt = listAccount(parent_vasp,child_vasp,intialBalance)
    print("Account generated: ", receipt)
    return child_vasp

def create_transaction( sender,seq_num, script, currency):
        return diem_types.RawTransaction(
            sender=sender.account_address,
            sequence_number=seq_num,
            payload=diem_types.TransactionPayload__Script(script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=currency,
            expiration_timestamp_secs=int(time.time()) + 30,
            chain_id=testnet.CHAIN_ID,
        )

## wallet method: TRANSFER
# transfers funds from account A to B
def transferFunds(receiver, sender, amount):
    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(testnet.TEST_CURRENCY_CODE),
        payee=receiver.account_address,
        amount=amount,
        metadata=b"",  # no requirement for metadata and metadata signature
        metadata_signature=b"",
    )
    seq_num = client.get_account_sequence(sender.account_address)
    txn = create_transaction(sender, seq_num, script, testnet.TEST_CURRENCY_CODE)

    signed_txn = sender.sign(txn)
    client.submit(signed_txn)
    executed_txn = client.wait_for_transaction(signed_txn)
    return executed_txn

def generateLocalAccount():
    faucet = testnet.Faucet(client)
    Bob = faucet.gen_account()
    Alice = generateAccount(Bob,100_000_000)
    print(getBalance(Alice.account_address))


def main():
    faucet = testnet.Faucet(client)
    Bob = faucet.gen_account()
    Alice = faucet.gen_account()
    print("Bob balance: ",getBalance(Bob.account_address),"Alice balance: ",getBalance(Alice.account_address))
    amount = 1_000_000
    receipt = transferFunds(Bob,Alice,amount)
    print("Transaction receipt: ",receipt)
    print("Bob balance: ",getBalance(Bob.account_address),"Alice balance: ",getBalance(Alice.account_address))

main()
