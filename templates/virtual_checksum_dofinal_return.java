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
        short dataLen = apdu.setIncomingAndReceive();

        Checksum checksum = Checksum.getInstance(Checksum.ALG_ISO3309_CRC16, false); // target method
        byte[] outBuff = new byte[2];
        byte[] result = {(byte) checksum.doFinal(new byte[]{0x01, 0x02, 0x03, 0x04}, (short) 0, (short) 4, outBuff, (short) 0)};

        Util.arrayCopyNonAtomic(result, (short) 0, buffer, ISO7816.OFFSET_CDATA, (short) 1);
        apdu.setOutgoingAndSend(ISO7816.OFFSET_CDATA, (short) 1);
    }
}
