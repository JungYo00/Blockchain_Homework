import hashlib # SHA 256
from ecdsa import SigningKey,VerifyingKey, SECP256k1 # 서명, 서명검증
import inspect  # transaction 유효성 판정 시 faild일 때 몇 번째 line에서 발생했는지 알기 위해 사용

import transaction

# script 실행 중 사용하는 상태값
stack = []
if_value = True
Transaction_Valid = True
Error_Line = -1


#-------------------------------------------------- OP CODE 정의-----------------------------------------------------------
def DUP():
    data = stack.pop()
    stack.append(data)
    stack.append(data)

def HASH():
    data = stack.pop()
    hash_object = hashlib.sha256()
    hash_object.update(data.encode())
    hash_value = hash_object.hexdigest()
    stack.append(hash_value)

def EQUAL():
    data1 = stack.pop()
    data2 = stack.pop()
    if data1 == data2:
        stack.append(True)
    else:
        stack.append(False)

def EQUALVERIFY():
    global Transaction_Valid, Error_Line
    data1 = stack.pop()
    data2 = stack.pop()
    if data1 != data2:
        Transaction_Valid = False
        Error_Line = inspect.currentframe().f_lineno

def CHECKSIG():
    Pub_K = stack.pop()
    SIG = stack.pop()
    raw_tx = transaction.Raw_Transaction_HASH_For_SIG(transaction.TX_idx, transaction.Output_cnt)

    # 서명 검증을 위한 올바른 형태로 바꾸기
    Pub_K = VerifyingKey.from_string(bytes.fromhex(Pub_K), curve=SECP256k1)
    SIG = bytes.fromhex(SIG)

    try:
        if Pub_K.verify(SIG, raw_tx):  # 성공 시 True 반환
            stack.append(True)
    except:
        stack.append(False)

def CHECKSIGVERIFY():
    global Transaction_Valid, Error_Line
    CHECKSIG()
    BOOL = stack.pop()
    if not BOOL:
        Transaction_Valid = False
        Error_Line = inspect.currentframe().f_lineno

def CHECKMULTISIG():
    Message = transaction.Raw_Transaction_HASH_For_SIG(transaction.TX_idx, transaction.Output_cnt)
    N = int(stack.pop())
    publicKeys = []

    for i in range(N):
        PuB_K = stack.pop()
        PuB_K = VerifyingKey.from_string(bytes.fromhex(PuB_K), curve=SECP256k1)
        publicKeys.append(PuB_K)

    M = int(stack.pop())
    signatures = []

    for i in range(M):
        SiG = stack.pop()
        SiG = bytes.fromhex(SiG)
        signatures.append(SiG)

    # 서명 검증
    VALID_SIG_CNT = 0
    for i in range(M):
        for j in range(N):
            try:
                if publicKeys[j].verify(signatures[i], Message):
                    VALID_SIG_CNT = VALID_SIG_CNT + 1
            except:
                pass

    if VALID_SIG_CNT == M:
        stack.append(True)
    else:
        stack.append(False)

def CHECKMULTISIGVERIFY():
    global Transaction_Valid, Error_Line
    CHECKMULTISIG()
    BOOL = stack.pop()
    if not BOOL:
        Transaction_Valid = False
        Error_Line = inspect.currentframe().f_lineno

def IF():
    global if_value
    Condition_Value = stack.pop()
    if Condition_Value == 'False' or Condition_Value == '0':
        Condition_Value = False
    else:
        Condition_Value = True

    if Condition_Value:
        if_value = True
    else:
        if_value = False


def ELSE():
    global if_value
    if if_value:
        if_value = False
    else:
        if_value = True


def ENDIF():
    global if_value
    if_value = True


def CHECKFINALRESULT():
    if len(stack) == 1 and stack[0] == True:
        return True
    else:
        Transaction_Valid = False
        Error_Line = inspect.currentframe().f_lineno
        return False
# ------------------------------------------------------------------------------------------------------------------------------------

opcode_functions = {
    'DUP': DUP,
    'HASH': HASH,
    'EQUAL': EQUAL,
    'EQUALVERIFY': EQUALVERIFY,
    'CHECKSIG': CHECKSIG,
    'CHECKSIGVERIFY': CHECKSIGVERIFY,
    'CHECKMULTISIG': CHECKMULTISIG,
    'CHECKMULTISIGVERIFY': CHECKMULTISIGVERIFY,
    'IF': IF
}
