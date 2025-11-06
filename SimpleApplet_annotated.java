package applets;

import javacard.framework.*;
import javacard.security.*;
import javacardx.crypto.*;

public class SimpleApplet extends javacard.framework.Applet {


    final static byte CLA_SIMPLEAPPLET = (byte) 0xB0;

    final static byte INS_ENCRYPT = (byte) 0x50;
    final static byte INS_DECRYPT = (byte) 0x51;
    final static byte INS_SETKEY = (byte) 0x52;
    final static byte INS_HASH = (byte) 0x53;
    final static byte INS_RANDOM = (byte) 0x54;
    final static byte INS_VERIFYPIN = (byte) 0x55;
    final static byte INS_SETPIN = (byte) 0x56;
    final static byte INS_RETURNDATA = (byte) 0x57;
    final static byte INS_SIGNDATA = (byte) 0x58;

    final static short ARRAY_LENGTH = (short) 0xff;
    final static byte AES_BLOCK_LENGTH = (short) 0x16;

    final static short SW_BAD_TEST_DATA_LEN = (short) 0x6680;
    final static short SW_KEY_LENGTH_BAD = (short) 0x6715;
    final static short SW_CIPHER_DATA_LENGTH_BAD = (short) 0x6710;
    final static short SW_OBJECT_NOT_AVAILABLE = (short) 0x6711;
    final static short SW_BAD_PIN = (short) 0x6900;

    final static short SW_Exception = (short) 0xff01;
    final static short SW_ArrayIndexOutOfBoundsException = (short) 0xff02;
    final static short SW_ArithmeticException = (short) 0xff03;
    final static short SW_ArrayStoreException = (short) 0xff04;
    final static short SW_NullPointerException = (short) 0xff05;
    final static short SW_NegativeArraySizeException = (short) 0xff06;
    final static short SW_CryptoException_prefix = (short) 0xf100;
    final static short SW_SystemException_prefix = (short) 0xf200;
    final static short SW_PINException_prefix = (short) 0xf300;
    final static short SW_TransactionException_prefix = (short) 0xf400;
    final static short SW_CardRuntimeException_prefix = (short) 0xf500;

    private AESKey m_aesKey = null;
    private Cipher m_encryptCipher = null;
    private Cipher m_decryptCipher = null;
    private RandomData m_secureRandom = null;
    private MessageDigest m_hash = null;
    private OwnerPIN m_pin = null;
    private Signature m_sign = null;
    private KeyPair m_keyPair = null;
    private Key m_privateKey = null;
    private Key m_publicKey = null;

    private byte m_ramArray[] = null;
    private byte m_dataArray[] = null;


    protected SimpleApplet(byte[] buffer, short offset, byte length) {

        short dataOffset = offset;
        boolean isOP2 = false;

        if (length > 9) {

            dataOffset += (short) (1 + buffer[offset]);
            dataOffset += (short) (1 + buffer[dataOffset]);

            dataOffset++;

            m_dataArray = new byte[ARRAY_LENGTH];
            Util.arrayFillNonAtomic(m_dataArray, (short) 0, ARRAY_LENGTH, (byte) 0); // StaticMethodref

            m_aesKey = (AESKey) KeyBuilder.buildKey(KeyBuilder.TYPE_AES, KeyBuilder.LENGTH_AES_256, false); // StaticMethodref
            m_encryptCipher = Cipher.getInstance(Cipher.ALG_AES_BLOCK_128_CBC_NOPAD, false); // StaticMethodref
            m_decryptCipher = Cipher.getInstance(Cipher.ALG_AES_BLOCK_128_CBC_NOPAD, false); // StaticMethodref

            m_secureRandom = RandomData.getInstance(RandomData.ALG_SECURE_RANDOM); // StaticMethodref

            m_ramArray = JCSystem.makeTransientByteArray((short) 260, JCSystem.CLEAR_ON_DESELECT); // StaticMethodref

            m_aesKey.setKey(m_dataArray, (short) 0);

            m_encryptCipher.init(m_aesKey, Cipher.MODE_ENCRYPT); // VirtualMethodref
            m_decryptCipher.init(m_aesKey, Cipher.MODE_DECRYPT); // VirtualMethodref

            m_pin = new OwnerPIN((byte) 5, (byte) 4);
            m_pin.update(m_dataArray, (byte) 0, (byte) 4); // VirtualMethodref

            m_keyPair = new KeyPair(KeyPair.ALG_RSA_CRT, KeyBuilder.LENGTH_RSA_2048);
            m_keyPair.genKeyPair(); // VirtualMethodref
            m_publicKey = m_keyPair.getPublic(); // VirtualMethodref
            m_privateKey = m_keyPair.getPrivate(); // VirtualMethodref
            m_sign = Signature.getInstance(Signature.ALG_RSA_SHA_PKCS1, false); // StaticMethodref
            m_sign.init(m_privateKey, Signature.MODE_SIGN); // VirtualMethodref

            m_hash = MessageDigest.getInstance(MessageDigest.ALG_SHA, false); // StaticMethodref

            isOP2 = true;

        } 

        register(); // VirtualMethodref
    }


    public static void install(byte[] bArray, short bOffset, byte bLength) throws ISOException { // VirtualMethodref
        new SimpleApplet(bArray, bOffset, bLength);
    }


    public boolean select() {
        clearSessionData();
        
        return true;
    }


    public void deselect() {
        clearSessionData();
    }


    public void process(APDU apdu) throws ISOException {
        byte[] apduBuffer = apdu.getBuffer();

        if (selectingApplet()) {
            return;
        }

        try {
            if (apduBuffer[ISO7816.OFFSET_CLA] == CLA_SIMPLEAPPLET) {
                switch (apduBuffer[ISO7816.OFFSET_INS]) {
                    case INS_SETKEY:
                        SetKey(apdu);
                        break;
                    case INS_ENCRYPT:
                        Encrypt(apdu);
                        break;
                    case INS_DECRYPT:
                        Decrypt(apdu);
                        break;
                    case INS_HASH:
                        Hash(apdu);
                        break;
                    case INS_RANDOM:
                        Random(apdu);
                        break;
                    case INS_VERIFYPIN:
                        VerifyPIN(apdu);
                        break;
                    case INS_SETPIN:
                        SetPIN(apdu);
                        break;
                    case INS_RETURNDATA:
                        ReturnData(apdu);
                        break;
                    case INS_SIGNDATA:
                        Sign(apdu);
                        break;
                    default:
                        ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED); // StaticMethodref
                        break;
                }
            } else {
                ISOException.throwIt(ISO7816.SW_CLA_NOT_SUPPORTED); // StaticMethodref
            }

        } catch (ISOException e) {
            throw e;
        } catch (ArrayIndexOutOfBoundsException e) {
            ISOException.throwIt(SW_ArrayIndexOutOfBoundsException);
        } catch (ArithmeticException e) {
            ISOException.throwIt(SW_ArithmeticException);
        } catch (ArrayStoreException e) {
            ISOException.throwIt(SW_ArrayStoreException);
        } catch (NullPointerException e) {
            ISOException.throwIt(SW_NullPointerException);
        } catch (NegativeArraySizeException e) {
            ISOException.throwIt(SW_NegativeArraySizeException);
        } catch (CryptoException e) {
            ISOException.throwIt((short) (SW_CryptoException_prefix | e.getReason()));
        } catch (SystemException e) {
            ISOException.throwIt((short) (SW_SystemException_prefix | e.getReason()));
        } catch (PINException e) {
            ISOException.throwIt((short) (SW_PINException_prefix | e.getReason()));
        } catch (TransactionException e) {
            ISOException.throwIt((short) (SW_TransactionException_prefix | e.getReason()));
        } catch (CardRuntimeException e) {
            ISOException.throwIt((short) (SW_CardRuntimeException_prefix | e.getReason()));
        } catch (Exception e) {
            ISOException.throwIt(SW_Exception);
        }
    }

    void clearSessionData() {
        Util.arrayFillNonAtomic(m_ramArray, (short) 0, (short) m_ramArray.length, (byte) 0);
        m_secureRandom.generateData(m_ramArray, (short) 0, (short) m_ramArray.length); // VirtualMethodref
    }
    
    // SET ENCRYPTION & DECRYPTION KEY
    void SetKey(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        // CHECK EXPECTED LENGTH
        if ((short) (dataLen * 8) != KeyBuilder.LENGTH_AES_256) {
            ISOException.throwIt(SW_KEY_LENGTH_BAD);
        }

        // SET KEY VALUE
        m_aesKey.setKey(apdubuf, ISO7816.OFFSET_CDATA);

        // INIT CIPHERS WITH NEW KEY
        m_encryptCipher.init(m_aesKey, Cipher.MODE_ENCRYPT);
        m_decryptCipher.init(m_aesKey, Cipher.MODE_DECRYPT);
    }

    // ENCRYPT INCOMING BUFFER
    void Encrypt(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer(); // VirtualMethodref
        short dataLen = apdu.setIncomingAndReceive(); // VirtualMethodref

        // CHECK EXPECTED LENGTH (MULTIPLY OF AES BLOCK LENGTH)
        if ((dataLen % 16) != 0) {
            ISOException.throwIt(SW_CIPHER_DATA_LENGTH_BAD);
        }

        // ENCRYPT INCOMING BUFFER
        m_encryptCipher.doFinal(apdubuf, ISO7816.OFFSET_CDATA, dataLen, m_ramArray, (short) 0); // VirtualMethodref
        // NOTE: In-place encryption directly with apdubuf as output can be performed. m_ramArray used to demonstrate Util.arrayCopyNonAtomic

        // COPY ENCRYPTED DATA INTO OUTGOING BUFFER
        Util.arrayCopyNonAtomic(m_ramArray, (short) 0, apdubuf, ISO7816.OFFSET_CDATA, dataLen); // StaticMethodref

        // SEND OUTGOING BUFFER
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, dataLen); // VirtualMethodref
    }

    // DECRYPT INCOMING BUFFER
    void Decrypt(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        // CHECK EXPECTED LENGTH (MULTIPLY OF AES BLOCK LENGTH)
        if ((dataLen % 16) != 0) {
            ISOException.throwIt(SW_CIPHER_DATA_LENGTH_BAD);
        }

        // ENCRYPT INCOMING BUFFER
        m_decryptCipher.doFinal(apdubuf, ISO7816.OFFSET_CDATA, dataLen, m_ramArray, (short) 0);

        // COPY ENCRYPTED DATA INTO OUTGOING BUFFER
        Util.arrayCopyNonAtomic(m_ramArray, (short) 0, apdubuf, ISO7816.OFFSET_CDATA, dataLen);

        // SEND OUTGOING BUFFER
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, dataLen);
    }

    // HASH INCOMING BUFFER
    void Hash(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        if (m_hash != null) {
            m_hash.doFinal(apdubuf, ISO7816.OFFSET_CDATA, dataLen, m_ramArray, (short) 0); // VirtualMethodref
        } else {
            ISOException.throwIt(SW_OBJECT_NOT_AVAILABLE);
        }

        // COPY ENCRYPTED DATA INTO OUTGOING BUFFER
        Util.arrayCopyNonAtomic(m_ramArray, (short) 0, apdubuf, ISO7816.OFFSET_CDATA, m_hash.getLength()); // VirtualMethodref

        // SEND OUTGOING BUFFER
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, m_hash.getLength());
    }

    // GENERATE RANDOM DATA
    void Random(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();

        // GENERATE DATA
        short randomDataLen = apdubuf[ISO7816.OFFSET_P1];
        m_secureRandom.generateData(apdubuf, ISO7816.OFFSET_CDATA, randomDataLen);

        // SEND OUTGOING BUFFER
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, randomDataLen);
    }

    // VERIFY PIN
    void VerifyPIN(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        // VERIFY PIN
        if (m_pin.check(apdubuf, ISO7816.OFFSET_CDATA, (byte) dataLen) == false) {
            ISOException.throwIt(SW_BAD_PIN);
        }
    }

    // SET PIN 
    // Be aware - this method will allow attacker to set own PIN - need to protected. 
    // E.g., by additional Admin PIN or all secret data of previous user needs to be reased 
    void SetPIN(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        // SET NEW PIN
        m_pin.update(apdubuf, ISO7816.OFFSET_CDATA, (byte) dataLen);
    }

    // RETURN INPU DATA UNCHANGED
    void ReturnData(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();

        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, dataLen);
    }

    void Sign(APDU apdu) {
        byte[] apdubuf = apdu.getBuffer();
        short dataLen = apdu.setIncomingAndReceive();
        short signLen = 0;

        // SIGN INCOMING BUFFER
        signLen = m_sign.sign(apdubuf, ISO7816.OFFSET_CDATA, (byte) dataLen, m_ramArray, (byte) 0);

        // COPY SIGNED DATA INTO OUTGOING BUFFER
        Util.arrayCopyNonAtomic(m_ramArray, (short) 0, apdubuf, ISO7816.OFFSET_CDATA, signLen);

        // SEND OUTGOING BUFFER
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, signLen);
    }
}
