#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

void setup() {
  Serial.begin(9600);
  mySwitch.enableTransmit(10); // Transmissor no Pino 10
  Serial.println("Digite 1 (Power), 2 (Modo) ou 3 (Coração) no Serial Monitor");
}

void loop() {
  if (Serial.available() > 0) {
    char tecla = Serial.read();

    if (tecla == '1') {
      mySwitch.send(SEU_CODIGO_POWER_AQUI, 24); // <--- COLOQUE O DECIMAL AQUI
      Serial.println("Comando POWER enviado!");
    } else if (tecla == '2') {
      mySwitch.send(SEU_CODIGO_MODO_AQUI, 24); // <--- COLOQUE O DECIMAL AQUI
      Serial.println("Comando MODO enviado!");
    } else if (tecla == '3') {
      mySwitch.send(SEU_CODIGO_HEART_AQUI, 24); // <--- COLOQUE O DECIMAL AQUI
      Serial.println("Comando CORACAO enviado!");
    }
  }
}