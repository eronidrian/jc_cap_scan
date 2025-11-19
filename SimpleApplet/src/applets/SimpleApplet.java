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
        Check_static();
        if (selectingApplet()) {
            return ;
        }
    }

    public void Check_static(){
        APDU.waitExtension();
    }
    }