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
        //byte[] buffer = apdu.getBuffer();
        //short dataLen = apdu.setIncomingAndReceive();

        AID aid = JCSystem.lookupAID(new byte[]{10, 20, 30}, (short) 0, (byte) 4); // target method
        //byte[] result = {0x01, 0x02, 0x03, 0x04, 0x05};

        //Util.arrayCopyNonAtomic(result, (short) 0, buffer, ISO7816.OFFSET_CDATA, (short) 10);
        //apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, (short) 10);
    }
}
