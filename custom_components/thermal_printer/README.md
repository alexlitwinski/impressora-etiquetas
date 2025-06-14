# 🖨 Home Assistant Thermal Printer Integration

Integração customizada para Home Assistant que permite controlar impressoras térmicas Bluetooth de 55mm/58mm/80mm.

## ✨ Recursos

- 🔗 **Conexão Bluetooth** - Descobrimento automático de impressoras
- 📝 **Impressão de Texto** - Com formatação (tamanho, alinhamento, negrito)
- 📱 **QR Codes** - Geração e impressão de códigos QR
- 📊 **Códigos de Barras** - Suporte para CODE128, CODE39, EAN13, UPC
- 📄 **Controle de Papel** - Avanço manual do papel
- 🎛️ **Interface Gráfica** - Configuração via UI do Home Assistant
- 🤖 **Serviços para Automção** - Integração completa com automações

## 📦 Instalação

### Via HACS (Recomendado)

1. Abra o HACS no Home Assistant
2. Vá para "Integrações"
3. Clique no menu (⋮) e selecione "Repositórios customizados"
4. Adicione este repositório: `https://github.com/alexlitwinski/impressora-etiquetas`
5. Selecione "Integração" como categoria
6. Clique em "Adicionar"
7. Procure por "Thermal Printer" e instale
8. Reinicie o Home Assistant

### Instalação Manual

1. Baixe os arquivos desta integração
2. Copie a pasta `thermal_printer` para `config/custom_components/`
3. Reinicie o Home Assistant
4. Vá para **Configurações** > **Dispositivos e Serviços** > **Adicionar Integração**
5. Procure por "Thermal Printer"

## ⚙️ Configuração

1. Vá para **Configurações** > **Dispositivos e Serviços**
2. Clique em **"Adicionar Integração"**
3. Procure por **"Thermal Printer"**
4. Selecione sua impressora da lista de dispositivos Bluetooth descobertos
5. Dê um nome para sua impressora
6. Clique em **"Enviar"**

## 🚀 Uso

### Serviços Disponíveis

#### `thermal_printer.print_text`
Imprime texto formatado na impressora.

```yaml
service: thermal_printer.print_text
data:
  text: |
    LOJA EXEMPLO
    Recibo de Compra
    ------------------------
    Produto: Item ABC
    Valor: R$ 25,90
    ------------------------
    Obrigado pela compra!
  font_size: "normal"
  alignment: "center"
  bold: true
```

#### `thermal_printer.print_qr_code`
Imprime um QR Code.

```yaml
service: thermal_printer.print_qr_code
data:
  data: "https://home-assistant.io"
  size: 8
```

#### `thermal_printer.print_barcode`
Imprime código de barras.

```yaml
service: thermal_printer.print_barcode
data:
  data: "1234567890"
  barcode_type: "CODE128"
```

#### `thermal_printer.feed_paper`
Avança o papel.

```yaml
service: thermal_printer.feed_paper
data:
  lines: 5
```

## 🤖 Exemplos de Automação

### Imprimir quando porta abrir

```yaml
automation:
  - alias: "Alerta de Segurança"
    trigger:
      - platform: state
        entity_id: binary_sensor.porta_entrada
        to: "on"
    action:
      - service: thermal_printer.print_text
        data:
          text: |
            ⚠️  ALERTA DE SEGURANÇA ⚠️
            {{ now().strftime('%d/%m/%Y %H:%M:%S') }}
            Porta de entrada aberta
          font_size: "normal"
          alignment: "center"
          bold: true
      - service: thermal_printer.feed_paper
        data:
          lines: 3
```

### Imprimir recibo de compras

```yaml
automation:
  - alias: "Recibo de Compra"
    trigger:
      - platform: state
        entity_id: sensor.compra_finalizada
        to: "on"
    action:
      - service: thermal_printer.print_text
        data:
          text: |
            ================================
                   LOJA EXEMPLO
            ================================
          alignment: "center"
          bold: true
      - service: thermal_printer.print_text
        data:
          text: |
            Data: {{ now().strftime('%d/%m/%Y %H:%M') }}
            Cliente: {{ states('input_text.cliente_nome') }}
            --------------------------------
          alignment: "left"
      - service: thermal_printer.print_text
        data:
          text: |
            ITEM                      VALOR
            {{ states('sensor.item_compra') }}
            {{ states('sensor.valor_compra') }}
            --------------------------------
            TOTAL: {{ states('sensor.total_compra') }}
          alignment: "left"
      - service: thermal_printer.print_qr_code
        data:
          data: "{{ states('sensor.qr_recibo') }}"
          size: 6
      - service: thermal_printer.feed_paper
        data:
          lines: 4
```

### Sistema de Senhas

```yaml
automation:
  - alias: "Imprimir Senha"
    trigger:
      - platform: state
        entity_id: button.nova_senha
        to: "on"
    action:
      - service: counter.increment
        target:
          entity_id: counter.numero_senha
      - service: thermal_printer.print_text
        data:
          text: |
            SENHA DE ATENDIMENTO
          font_size: "large"
          alignment: "center"
          bold: true
      - service: thermal_printer.print_text
        data:
          text: |
            Nº {{ states('counter.numero_senha') | int }}
          font_size: "large"
          alignment: "center"
          bold: true
      - service: thermal_printer.print_text
        data:
          text: |
            {{ now().strftime('%d/%m/%Y - %H:%M') }}
            Aguarde ser chamado
          alignment: "center"
      - service: thermal_printer.feed_paper
        data:
          lines: 3
```

## 📝 Solução de Problemas

### Impressora não conecta

1. **Verifique se a impressora está ligada** e em modo de pareamento
2. **Confirme o endereço MAC correto** na configuração
3. **Verifique a distância** - mantenha próximo ao Home Assistant
4. **Reinicie a impressora** e tente novamente
5. **Verifique os logs** do Home Assistant para erros específicos

### Caracteres especiais não aparecem

A impressora pode não suportar acentos. Soluções:
- Use caracteres ASCII quando possível
- Configure a impressora para CP850 ou UTF-8
- Teste com texto simples primeiro

### Impressão lenta ou travando

- **Reduza o tamanho dos dados** enviados por vez
- **Verifique a qualidade** da conexão Bluetooth
- **Aumente o delay** entre chunks no código (const.py)
- **Reinicie o Home Assistant** se necessário

### QR Code não imprime

1. **Verifique se a impressora suporta** comandos ESC/POS para QR
2. **Teste com dados simples** primeiro (ex: "teste")
3. **Ajuste o tamanho** do QR Code (valores entre 1-8)
4. **Verifique os logs** para erros específicos

## 📊 Logs e Debug

Para ativar logs detalhados, adicione ao `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.thermal_printer: debug
    bleak: debug
```

## 🖨 Impressoras Testadas

Esta integração foi testada com:

- ✅ **Impressoras POS genéricas** de 58mm e 80mm
- ✅ **Modelos compatíveis com ESC/POS**
- ✅ **Impressoras térmicas Bluetooth** de diversas marcas

### Modelos Específicos Relatados:
- Epson TM-P20
- Bixolon SPP-R200III
- Impressoras POS genéricas Chinesas
- [Adicione seu modelo nos issues se testou]

## 🛠️ Desenvolvimento

### Estrutura do Código

```
thermal_printer/
├── __init__.py          # Lógica principal e serviços
├── config_flow.py       # Fluxo de configuração
├── const.py            # Constantes e comandos ESC/POS
├── manifest.json       # Metadados da integração
├── services.yaml       # Definição dos serviços
├── strings.json        # Strings da UI
└── translations/       # Traduções
    └— pt.json
```

### Contribuindo

1. **Fork** este repositório
2. **Crie uma branch** para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. **Abra um Pull Request**

### Testando Localmente

1. Copie os arquivos para `config/custom_components/thermal_printer/`
2. Reinicie o Home Assistant
3. Configure via UI
4. Teste os serviços no Developer Tools

## ⚡ Comandos ESC/POS Suportados

A integração usa comandos ESC/POS padrão:

- **Inicialização:** `ESC @`
- **Alinhamento:** `ESC a [0,1,2]`
- **Negrito:** `ESC E [0,1]`
- **Tamanho:** `GS ! [valor]`
- **QR Code:** `GS ( k`
- **Código de Barras:** `GS k`

## 📱 Características Bluetooth

- **UUID padrão:** `0000ff02-0000-1000-8000-00805f9b34fb`
- **Chunk size:** 20 bytes por pacote
- **Delay:** 50ms entre pacotes
- **Timeout:** 10 segundos para descoberta

> **Nota:** Alguns modelos podem usar UUIDs diferentes. Verifique a documentação da sua impressora.

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🐝 Suporte

- 🐛 **Bugs:** Abra uma [issue](https://github.com/alexlitwinski/impressora-etiquetas/issues)
- 💡 **Sugestões:** Use as [discussions](https://github.com/alexlitwinski/impressora-etiquetas/discussions)
- 💬 **Comunidade:** [Fórum Home Assistant](https://community.home-assistant.io/)

## 🌟 Roadmap

- [ ] Suporte para imagens/logos
- [ ] Templates de recibos
- [ ] Interface gráfica para criar layouts
- [ ] Suporte para múltiplas impressoras
- [ ] Integração com sistemas de PDV
- [ ] Backup/restore de configurações

---

⭐ **Se esta integração foi útil, considere dar uma estrela no repositório!**

## 🔗 Links Úteis

- [Documentação ESC/POS](https://reference.epson-biz.com/modules/ref_escpos/index.php)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Bleak Library](https://github.com/hbldh/bleak)
- [Python ESC/POS](https://python-escpos.readthedocs.io/)
