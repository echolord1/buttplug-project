⚡ Projeto Echo-Yumi: Ponte RF-Buttplug.io ⚡
Este projeto integra vibradores de rádio frequência (RF 433MHz) genéricos ao ecossistema Buttplug.io, utilizando um Arduino como tradutor de sinais T-Code para pulsos de rádio.

📂 Estrutura do Projeto
A árvore de diretórios está organizada para facilitar o desenvolvimento e a manutenção:

Plaintext
C:.
│   README.md               # Documentação principal
│
└───arduino
    └───tcode_direct
        │   tcode_direct.ino           # Firmware oficial (Produção)
        │
        └───test
                receive_clone_signal_rf.ino  # Captura códigos do controle original
                send_clone_signal_rf.ino     # Teste manual de disparo RF
                test_intiface_arduino_led.ino # Validação de conexão via Serial/LED
                
🏗️ Fluxo de Dados (Arquitetura Proxy)
Jogo → Python Proxy (Porta 12345) → Arduino (T-Code via USB) → Transmissor RF → Vibrador.

🚀 Guia de Configuração (Hardware)
1. Conexões no Arduino Uno/Nano
Receptor (MX-RM-5V): VCC -> IOREF | GND -> GND | DATA -> Pin 2 (Para clonagem).

Transmissor (FS1000A): VCC -> 5V | GND -> GND | DATA -> Pin 10 (Para operação).

Antenas: Solde fios de 17.3cm nos terminais ANT de ambos os módulos.

2. Passo a Passo do Firmware
Siga a ordem dos arquivos na pasta arduino/tcode_direct/test/:

Clonagem: Carregue o receive_clone_signal_rf.ino. Abra o Serial Monitor e anote os códigos decimais dos botões do seu controle (Power, Modo, Coração).

Teste Manual: Carregue o send_clone_signal_rf.ino inserindo seus códigos anotados. Use o teclado para validar se o vibrador responde aos comandos do Arduino.

Validação Serial: Use o test_intiface_aruidno_led.ino para garantir que o PC consegue "falar" com o Arduino através do protocolo T-Code simples.

Produção: Carregue o tcode_direct.ino. Este é o código final que rodará integrado ao jogo.

💻 Configuração do Ambiente Python (uv)
Utilizamos o uv para gerenciar a execução do script de proxy:

Bash
# Iniciar ambiente e dependências
uv init --python 3.14
uv add buttplug-py pyserial
uv sync

# Execução do Proxy (Certifique-se que o Intiface está na porta 12346)
uv run python main.py
🕹️ Integração com Jogos (ex: Femboy Survival)
Intiface Central: Mude a porta para 12346 e clique em Start Server.

Proxy Python: Execute o script. Ele criará um servidor virtual na porta 12345.

Jogo: Aponte para o servidor padrão (ws://127.0.0.1:12345). O dispositivo aparecerá como "Arduino RF Vibrador".

⚠️ Notas de Segurança e Latência
O protocolo RF é simplex (só envia, não recebe confirmação).

O firmware tcode_direct.ino possui um Timeout de 500ms. Se o jogo parar de enviar sinais (crash ou pausa), o Arduino enviará automaticamente o comando de desligamento para evitar acidentes.