import hashlib # SHA 256
import inspect  # transaction 유효성 판정 시 faild일 때 몇 번째 line에서 발생했는지 알기 위해 사용
import pandas as pd  # 엑셀 data 처리(전처리)

import execution_engine
import transaction

# snapshot transactions에 대한 리스트
Transactions_Txid = []
Transactions_Valid = []


# ---------------------------------------- snapshot -----------------------------------
def snapshot_transactions():
    print('------------------------------------------------snapshot_transactions------------------------------------------------')
    for i in range(len(Transactions_Txid)):
        print('transaction: ' + Transactions_Txid[i].hex() + ', '  +  'validity check: ' +  Transactions_Valid[i])
    print('---------------------------------------------------------------------------------------------------------------------')
    print('\n\n')

def snapshot_utxoset():
    print('--------------------------------------------------------------------------------snapshot_utxoset--------------------------------------------------------------------------------')
    IDX = 0
    for i in range(len(transaction.UTXO)):
        if pd.notna(transaction.UTXO['input_ptxid'][i]):
            print('utxo' + str(IDX) + ': ' + str(transaction.UTXO['input_ptxid'][i]) + ', ' + str(int(transaction.UTXO['input_output index'][i])) + ', ' + str(int(transaction.UTXO['input_amount'][i])) + ', ' + str(transaction.UTXO['input_locking script'][i]))
            IDX = IDX + 1
    print('-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    print('\n\n')
# -------------------------------------------------------------------------------------------


# transaction 유효성 판단 후 최종 결과 출력
def TX_Result():
    txid = transaction.Get_TXID(transaction.TX_idx, transaction.Output_cnt)
    print('transaction:', txid.hex())
    print('   input')
    print('       ptxid:', transaction.UTXO["input_ptxid"][transaction.TX_idx])
    print('       output index:', transaction.UTXO["input_output index"][transaction.TX_idx])
    print('       amount:', transaction.UTXO["input_amount"][transaction.TX_idx])
    print('       locking script:', transaction.UTXO["input_locking script"][transaction.TX_idx])
    print('       unlocking script:', transaction.TX["input_unlocking script"][transaction.TX_idx])
    print('   output')
    for a in range(transaction.Output_cnt):
        A = 'output_index'
        B = 'output_amount'
        C = 'output_locking script'
        print('       index' + str(a) + ':', int(transaction.TX[A + str(a)][transaction.TX_idx]))
        print('       amount' + str(a) + ':', transaction.TX[B + str(a)][transaction.TX_idx])
        print('       lockingscript' + str(a) + ':', transaction.TX[C + str(a)][transaction.TX_idx])

    if execution_engine.CHECKFINALRESULT():
        print("validity check: passed")
        Transactions_Valid.append('passed')
    else:
        print("validity check: failed")
        print("               failed at " + str(execution_engine.Error_Line) + "line")
        Transactions_Valid.append('failed')
    print()
    print()
    Transactions_Txid.append(txid)


# -------------------------------------------------------------------- main 함수 ------------------------------------------------------------------------------
execution_engine.if_value = True
for tx_idx in range(len(transaction.UTXO["input_ptxid"])):
    transaction.TX_idx = tx_idx
    execution_engine.if_value = True
    P2SH_Valid = False
    execution_engine.Transaction_Valid = True
    execution_engine.Error_Line = -1
    # TX_idx - 현재 처리하고 있는 trasnaction의 index
    # Output_cnt - 현재 처리하고 있는 trasnaction의 output 갯수
    transaction.Output_cnt = 1
    if not pd.isna(transaction.TX["output_index1"][transaction.TX_idx]):
        transaction.Output_cnt = 2
    if not pd.isna(transaction.TX["output_index2"][transaction.TX_idx]):
        transaction.Output_cnt = 3

    # 1. 금액 검증
    spend_amount = 0 # 현재 처리하고 있는 transcation에 명시된 output amount의 총합
    a = 'output_amount'
    for i in range(transaction.Output_cnt):
        spend_amount = spend_amount + transaction.TX[a + str(i)][transaction.TX_idx]


    if spend_amount > transaction.UTXO["input_amount"][transaction.TX_idx]:
         execution_engine.Error_Line = inspect.currentframe().f_lineno
         execution_engine.Transaction_Valid = False


    # 2.script 검증
    Locking_Script = transaction.UTXO["input_locking script"][transaction.TX_idx].split()

    # locking script가 P2SH 형태인 것 감지
    Unlocking_Script_Reduce_FirstNum = []
    if(len(Locking_Script) == 4 and Locking_Script[0] == 'DUP' and Locking_Script[1] == 'HASH' and len(Locking_Script[2]) == 64 and Locking_Script[3] == 'EQUALVERIFY'):
        US = transaction.TX["input_unlocking script"][transaction.TX_idx]
        US = US.split()
        First_Number = int(US[0])

        Unlocking_Script_Reduce_FirstNum = US[1:]
        Unlocking_Script_Reduce_FirstNum = " ".join(Unlocking_Script_Reduce_FirstNum)

        US = US[First_Number+1:]
        US = " ".join(US)
        US = US.replace(" ", "")
        hash_object = hashlib.sha256()
        hash_object.update(US.encode())
        US_HASH = hash_object.hexdigest()

        if US_HASH == Locking_Script[2]:
            P2SH_Valid = True


    if P2SH_Valid:
        full_script = str(Unlocking_Script_Reduce_FirstNum)
        full_script = full_script.split()
    else:
        full_script = str(transaction.TX["input_unlocking script"][transaction.TX_idx]) + ' ' + str(transaction.UTXO["input_locking script"][transaction.TX_idx])
        full_script = full_script.split()

    execution_engine.stack = []
    for script in full_script:
        if script == 'ELSE':
            execution_engine.ELSE()
        elif script == 'ENDIF':
            execution_engine.ENDIF()
        elif not execution_engine.if_value:
            continue
        elif script in execution_engine.opcode_functions:
            execution_engine.opcode_functions[script]()
        else:
            execution_engine.stack.append(script)
        if not execution_engine.Transaction_Valid:
            break


    # trnasction 처리 후 최종 결과 출력
    TX_Result()

    # 현재 transcation 유효성 확인 후 유효하면 사용한 UTXO 제거 후 생성된 UTXO 추가
    if execution_engine.CHECKFINALRESULT():
        # Get_TXID 는 UTXO 행을 읽어서 해시하므로, 행을 비우기 전에 먼저 구한다
        TXID = transaction.Get_TXID(transaction.TX_idx, transaction.Output_cnt).hex()

        transaction.UTXO.drop(transaction.TX_idx).reset_index(drop=True, inplace=True)
        transaction.UTXO.loc[transaction.TX_idx] = [None] * 4  # 모든 열에 None 값을 입력

        # UTXO 추가
        A = 'output_index'
        B = 'output_amount'
        C = 'output_locking script'
        for LENGTH in range(transaction.Output_cnt):
            # 추가할 데이터
            new_row = {
                "input_ptxid": TXID,
                "input_output index": transaction.TX[A + str(LENGTH)][transaction.TX_idx],
                "input_amount": transaction.TX[B + str(LENGTH)][transaction.TX_idx],
                "input_locking script": transaction.TX[C + str(LENGTH)][transaction.TX_idx],
            }
            transaction.UTXO.loc[len(transaction.UTXO)] = new_row

    # 지금까지 검증한 transaction들의 정보
    if transaction.TX_idx == 6: # -1 <- 원하는 값 넣고 확인
        snapshot_transactions()

    # 현재 시점의 UTXO 정보
    if transaction.TX_idx == 6: # -1 <- 원하는 값 넣고 확인
        snapshot_utxoset()
