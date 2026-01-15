package applets ;
import javacard.framework.*;
import javacardx.crypto.*;
import javacard.security.*;

public class SimpleApplet extends javacard.framework.Applet {
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
         if (selectingApplet()) {
            return ;
        }
        byte[] buffer = apdu.getBuffer();
        //short dataLen = apdu.setIncomingAndReceive();



        //Util.arrayCopyNonAtomic(result, (short) 0, buffer, ISO7816.OFFSET_CDATA, (short) 1);
        //apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, (short) 1);
    }
}
