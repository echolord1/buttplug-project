⚡ Projeto Echo-Yumi: Ponte RF-Buttplug.io ⚡
Este projeto integra vibradores de rádio frequência (RF 433MHz) genéricos ao ecossistema Buttplug.io, utilizando um Arduino como tradutor de sinais T-Code para pulsos de rádio.

📂 Estrutura do Projeto
A árvore de diretórios está organizada para facilitar o desenvolvimento e a manutenção:

- README.md (Documentação principal)
- /arduino (Firmwares para Arduino RF)
- /esp32-cam-md (Firmware para Ponte Bluetooth BLE)

🏗️ Fluxo de Dados (Arquitetura Proxy)
Jogo → Python Proxy (Porta 12345) → Arduino (T-Code via USB) → Transmissor RF → Vibrador.

📷 ESP32-CAM: Ponte Bluetooth (BLE)
Este módulo atua como uma ponte entre o Intiface Central (via Serial) e brinquedos Bluetooth compatíveis (como Lovense).

### 🚀 Upload do Firmware

Para compilar e carregar o código no ESP32-CAM (use a porta COM3):

```powershell
pio run -e esp32cam -t upload
```

### ✅ Verificação da Conexão

Rode o upload novamente:
pio run -e esp32cam -t upload ; python ..\test\test.py

Abra o monitor:
pio device monitor -p COM3 -b 115200

Se o monitor continuar vazio, aperte o botão físico de Reset no seu ESP32-CAM.

Se o brinquedo Bluetooth estiver ligado, ele deve imprimir: Conectado ao brinquedo!.

### 2. Running python-serial test

```bash
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\activate
pip install -r requirements.txt
python .\test\test.py

ou

cd .\PlatformIO
pio run -e esp32cam -t upload ; python ..\python\test\test.py
python ..\python\main.py
```

### 🕹️ Configuração no Intiface Central

1. Em **Settings**, ative **Advanced Settings**.
2. Ative a opção **"Lovense USB Dongle (Serial/Black Circuit Board) (DEPRECATED)"**.
3. OU ative **"Serial Port"**, clique em **Add Serial Port**, selecione a porta e o protocolo **Lovense**.
4. **IMPORTANTE**: Clique no botão **PLAY** (triângulo roxo) para iniciar o servidor.
5. Na aba **Devices**, clique em **Start Scanning**.

⚠️ Notas de Segurança e Latência
O protocolo RF é simplex (só envia, não recebe confirmação).
O firmware possui timeouts de segurança para evitar que o brinquedo fique ligado em caso de queda de conexão.

# TO-DO

[] Criar um python conform o python/test/test.py mas que seja um gateway entre o intiface e o esp32-cam-md
[] Fazer com que o python se conecte ao intiface e envie os comandos para o esp32-cam-md
[] Fazer o teste UDT do python com o jogo ou com o intiface
