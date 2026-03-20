#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

unsigned long ultimoComandoMillis = 0;
const int TEMPO_LIMITE = 500;
bool ligado = false;

// DEFINA SEUS CODIGOS AQUI
#define COD_POWER 1234567

void setup() {
  Serial.begin(115200); // Velocidade alta para o Intiface
  Serial.setTimeout(5);
  mySwitch.enableTransmit(10);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'V' || cmd == 'L' || cmd == 'H') {
      int valor = Serial.parseInt();

      if (valor > 0) {
        if (!ligado) {
          mySwitch.send(COD_POWER, 24);
          digitalWrite(LED_BUILTIN, HIGH);
          ligado = true;
        }
        ultimoComandoMillis = millis();
      } else {
        desligar();
      }
    }
  }

  // Se o jogo parar de mandar pacotes por 0.5s, desliga o plug
  if (ligado && (millis() - ultimoComandoMillis > TEMPO_LIMITE)) {
    desligar();
  }
}

void desligar() {
  if (ligado) {
    mySwitch.send(COD_POWER, 24); // No RF geralmente o mesmo botao desliga
    digitalWrite(LED_BUILTIN, LOW);
    ligado = false;
  }
}