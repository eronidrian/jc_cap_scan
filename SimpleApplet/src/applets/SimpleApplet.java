package applets ;
import javacard.framework.*;
import javacardx.crypto.*;
import javacard.security.*;

public class SimpleApplet extends javacard.framework.Applet {
    private AESKey m_aesKey = null;
    protected SimpleApplet(byte[] buffer, short offset, byte length){
        // register this instance
        register();
    }

    public static void install(byte[] bArray, short bOffset, byte bLength) throws ISOException {
        // applet instance creation
        new SimpleApplet(bArray, bOffset, bLength);
    }

    public boolean select() {
        return true ;
    }

    public void process (APDU apdu) throws ISOException {
        Check_virtual(apdu);
        if (selectingApplet()) {
            return ;
        }
    }

    public void Check_virtual(APDU apdu){
        KeyPair m_keyPair = new KeyPair(KeyPair.ALG_RSA_CRT, KeyBuilder.LENGTH_RSA_2048);
        m_keyPair.genKeyPair(); // Generate fresh key pair on-card
        Key m_privateKey = m_keyPair.getPrivate();
        Signature m_sign = Signature.getInstance(Signature.ALG_RSA_SHA_PKCS1, false);
        // INIT WITH PRIVATE KEY
        m_sign.init(m_privateKey, Signature.MODE_SIGN);
    }
    }