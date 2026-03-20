#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

unsigned long ultimoComandoMillis = 0;
const int TEMPO_LIMITE = 500;
bool motorLigadoNoPlug = false; // Controle de estado lógico

void setup() {
  Serial.begin(115200);
  mySwitch.enableTransmit(10); // Transmissor no Pino 10
  // mySwitch.setPulseLength(350); // Ajuste se o seu controle for diferente

  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'V' || cmd == 'L' || cmd == 'H') {
      int valor = Serial.parseInt();

      if (valor > 0) {
        // Se o valor é alto e o motor ainda não foi "mandado ligar"
        if (!motorLigadoNoPlug) {
          digitalWrite(LED_BUILTIN, HIGH);
          mySwitch.send(1234567, 24); // <--- COLOQUE O CÓDIGO DO POWER AQUI
          motorLigadoNoPlug = true;
          ultimoComandoMillis = millis();
        }
      } else {
        desligarPlug();
      }
    }
  }

  // Gatilho de segurança: se o jogo parar de mandar comando, a gente "aperta" o
  // botão de desligar
  if (motorLigadoNoPlug && (millis() - ultimoComandoMillis > TEMPO_LIMITE)) {
    desligarPlug();
  }
}

void desligarPlug() {
  if (motorLigadoNoPlug) {
    digitalWrite(LED_BUILTIN, LOW);
    mySwitch.send(
        1234567,
        24); // <--- ENVIA O COMANDO DE DESLIGAR (Geralmente é o mesmo do Power)
    motorLigadoNoPlug = false;
  }
}