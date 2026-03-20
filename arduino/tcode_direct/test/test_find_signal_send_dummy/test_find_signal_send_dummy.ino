#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

// Códigos mais prováveis encontrados em fóruns de RE
unsigned long codigosAlvo[] = {5592333, 5592405, 5592512, 1234567,
                               4350,    21505,   1398101, 16711680};
int pulseLengths[] = {300, 320, 350, 450};

void setup() {
  Serial.begin(9600);
  mySwitch.enableTransmit(10);
  mySwitch.setRepeatTransmit(20); // Aumenta a insistência para o plug "acordar"
  Serial.println("--- TESTE SNIPER RF ---");
}

void loop() {
  for (int p = 0; p < 4; p++) {
    mySwitch.setPulseLength(pulseLengths[p]);
    Serial.print("Testando Pulse Length: ");
    Serial.println(pulseLengths[p]);

    for (int i = 0; i < 8; i++) {
      Serial.print("  Disparando Codigo: ");
      Serial.println(codigosAlvo[i]);

      // Tenta Protocolo 1 e 2 (os reis da China)
      mySwitch.setProtocol(1);
      mySwitch.send(codigosAlvo[i], 24);
      delay(300);

      mySwitch.setProtocol(2);
      mySwitch.send(codigosAlvo[i], 24);
      delay(300);
    }
  }
  Serial.println("--- Ciclo finalizado. Nada ainda? ---");
  delay(5000);
}