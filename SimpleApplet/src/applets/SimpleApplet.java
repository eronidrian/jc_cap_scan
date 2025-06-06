package test ;
import javacard . framework .*;
import javacardx . crypto .*;
public class Test extends javacard . framework . Applet {
private Cipher m_encryptCipher = null ;
protected Test ( byte [] buffer , short offset , byte
length ){
// register this instance
m_encryptCipher = Cipher . getInstance (
Cipher . ALG_DES_CBC_NOPAD , false );
Check_virtual ();
register ();
}
public static void install ( byte [] bArray , short
bOffset , byte bLength ) throws ISOException {
// applet instance creation
new Test ( bArray , bOffset , bLength );
}
public boolean select () {
return true ;
}
public void process ( APDU apdu ) throws ISOException {
byte [] apduBuffer = apdu . getBuffer ();
if ( selectingApplet ()) {
return ;
}
}
public void Check_virtual (){
byte test_var = m_encryptCipher . getAlgorithm ();
}
}