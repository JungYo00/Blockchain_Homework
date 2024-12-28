import hashlib # SHA 256
import pandas as pd  # 엑셀 data 처리(전처리)
import openpyxl # 엑셀 읽기

TX = pd.read_excel("src/data/transactions.xlsx",)
UTXO = pd.read_excel("src/data/UTXOes.xlsx")

# TX_idx - 현재 처리하고 있는 trasnaction의 index
# Output_cnt - 현재 처리하고 있는 trasnaction의 output 갯수
TX_idx = 0
Output_cnt = 1


def Get_TXID(C_Tx_idx, C_Output_cnt):
    R_T = Raw_Transaction(C_Tx_idx, C_Output_cnt)
    R_T_txid = hashlib.sha256(R_T.encode()).digest()
    return R_T_txid

# locking script에 제시할 signature 생성
# locking script 비우고 전체 transcation에 대해 sha256 적용한 결과에 서명
def Raw_Transaction_HASH_For_SIG(C_Tx_idx, C_Output_cnt):
    raw_transaction = (str(UTXO["input_ptxid"][C_Tx_idx]) + str(int(UTXO["input_output index"][C_Tx_idx]))
                       + str(float(UTXO["input_amount"][C_Tx_idx])) + str(UTXO["input_locking script"][C_Tx_idx]))

    for i in range(C_Output_cnt):
        A = 'output_index'
        B = 'output_amount'
        C = 'output_locking script'
        raw_transaction = raw_transaction + str(int(TX[A + str(i)][C_Tx_idx])) + str(float(TX[B + str(i)][C_Tx_idx])) + str(TX[C + str(i)][C_Tx_idx])

    raw_transaction = raw_transaction.replace(" ", "")  # 공백 제거

    # 서명 대상 raw_trasnaction
    raw_transaction_hash = hashlib.sha256(raw_transaction.encode()).digest()

    return raw_transaction_hash


def Raw_Transaction(C_Tx_idx, C_Output_cnt):
    raw_transaction = (str(UTXO["input_ptxid"][C_Tx_idx]) + str(UTXO["input_output index"][C_Tx_idx])
                       + str(UTXO["input_amount"][C_Tx_idx]) + str(UTXO["input_locking script"][C_Tx_idx])
                       + str(TX["input_unlocking script"][C_Tx_idx]))

    for i in range(C_Output_cnt):
        A = 'output_index'
        B = 'output_amount'
        C = 'output_locking script'
        raw_transaction = raw_transaction + str(TX[A + str(i)][C_Tx_idx]) + str(TX[B + str(i)][C_Tx_idx]) + str(TX[C + str(i)][C_Tx_idx])

    raw_transaction = raw_transaction.replace(" ", "")  # 공백 제거
    return raw_transaction
