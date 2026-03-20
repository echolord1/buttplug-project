#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

int lastPinState = LOW;
unsigned long lastNoisePrint = 0;
long noiseCount = 0;

void setup() {
  Serial.begin(9600);
  mySwitch.enableReceive(1); // Pino 3 (Interrupt 1)
  pinMode(3, INPUT);         // Garante que podemos ler o estado do pino

  Serial.println(">>> RECEPTOR RF ATIVADO <<<");
  Serial.println("DICA: Mantenha o controle bem perto do receptor.");
  Serial.println(
      "Monitorando sensibilidade no pino 3. Toque no circuito para testar...");
}

void loop() {
  // Monitora qualquer mudanca no estado do pino (ruido, interferencia, toque do
  // dedo)
  int currentPinState = digitalRead(3);
  if (currentPinState != lastPinState) {
    noiseCount++;
    lastPinState = currentPinState;
  }

  // A cada 500ms envia relatorio de sensibilidade se houver atividade
  if (millis() - lastNoisePrint > 500) {
    if (noiseCount > 0) {
      Serial.print("[Sensibilidade] Atividade bruta detectada: ");
      Serial.print(noiseCount);
      Serial.println(" variacoes de sinal");
      noiseCount = 0;
    }
    lastNoisePrint = millis();
  }

  if (mySwitch.available()) {
    long value = mySwitch.getReceivedValue();

    Serial.println("\n=====================================");
    if (value == 0) {
      Serial.println("SINAL RF RECONHECIDO, mas falha ao decodificar "
                     "(Protocolo desconhecido).");
    } else {
      Serial.print(">>> CODIGO RF RECEBIDO: ");
      Serial.print(value);
      Serial.print(" | PROTOCOLO: ");
      Serial.println(mySwitch.getReceivedProtocol());
    }
    Serial.println("=====================================\n");

    mySwitch.resetAvailable();
  }
}
