# src/simulador.py
import sys
from pathlib import Path

from camada_enlace.CamadaEnlace import CamadaEnlace

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "camada_fisica"))
sys.path.insert(0, str(ROOT / "gui"))
sys.path.insert(0, str(ROOT / "camada_enlace"))

from gui.MainWindow import MainWindow
from gui.InterfaceGUI import InterfaceGUI, InterfaceGUI_Hamming
from camada_fisica.CamadaFisica import CamadaFisica

import numpy as np
from gi.repository import Gtk


# ----------------------------
# Utilidades
# ----------------------------
def text_to_bits(s: str):
    b = s.encode("utf-8")
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_text(bits):
    pad = (-len(bits)) % 8
    bits = bits + [0] * pad
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        out.append(byte)
    try:
        return out.decode("utf-8", errors="replace")
    except:
        return "<decode error>"


# ----------------------------
# Exercício 1.1.1
# ----------------------------
def run_exercicio_111(menu_window):
    def on_close():
        menu_window.show()

    gui = InterfaceGUI(
        title="1.1.1 - Modulação digital",
        modulations=["NRZ-Polar", "Manchester", "Bipolar (AMI)"],
        on_close_callback=on_close
    )

    def tx_callback(params):
        text = params["text"]
        modulation = params["modulation"]
        spb = params["samples_per_bit"]
        V = params["V"]
        snr_db = params["snr_db"]

        # Pega o tipo de enquadramento escolhido na GUI
        framing_type = params.get("framing", "Nenhum")
        # Pega o método de detecção de erro
        error_detection = params.get("error_detec", "Nenhum")

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        # 1. Converte Texto -> Bits puros
        bits_tx = text_to_bits(text)

        # 2. Aplica Enquadramento
        bits_para_transmitir = bits_tx

        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        if len(bits_para_transmitir) == 0:
            return {}

        # 2.5. Aplica Detecção de Erro (APÓS enquadramento)
        bits_com_deteccao = bits_para_transmitir
        if error_detection == "Paridade Par":
            bits_com_deteccao = enlace.encode_paridade(bits_para_transmitir)
        elif error_detection == "Checksum":
            bits_com_deteccao = enlace.encode_checksum(bits_para_transmitir)
        elif error_detection == "CRC-32":
            bits_com_deteccao = enlace.encode_crc(bits_para_transmitir)

        # 3. Modulação (Camada Física)
        if modulation == "NRZ-Polar":
            t_tx, s_tx = cf.nrz_polar(bits_com_deteccao)
        elif modulation == "Manchester":
            t_tx, s_tx = cf.manchester(bits_com_deteccao)
        elif modulation == "Bipolar (AMI)":
            t_tx, s_tx = cf.bipolar_ami(bits_com_deteccao)

        # Adiciona Ruído SEMPRE quando SNR > 0
        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
        
        # Decodificação usando sinal com ruído
        if modulation == "NRZ-Polar":
            bits_rx_encoded = cf.decode_nrz_polar(s_rx)
        elif modulation == "Manchester":
            bits_rx_encoded = cf.decode_manchester(s_rx)
        elif modulation == "Bipolar (AMI)":
            bits_rx_encoded = cf.decode_bipolar_ami(s_rx)

        # --- Receptor ---

        # 4. Verificação de Detecção de Erro (ANTES do desenquadramento)
        erro_detectado = False
        bits_apos_verificacao = bits_rx_encoded

        if error_detection == "Paridade Par":
            if len(bits_rx_encoded) >= 1:
                bits_apos_verificacao, erro_detectado = enlace.decode_paridade(bits_rx_encoded)
            else:
                bits_apos_verificacao, erro_detectado = [], True
        elif error_detection == "Checksum":
            if len(bits_rx_encoded) >= 3:
                bits_apos_verificacao, erro_detectado = enlace.decode_checksum(bits_rx_encoded)
            else:
                bits_apos_verificacao, erro_detectado = [], True
        elif error_detection == "CRC-32":
            if len(bits_rx_encoded) >= 32:
                bits_apos_verificacao, erro_detectado = enlace.decode_crc(bits_rx_encoded)
            else:
                bits_apos_verificacao, erro_detectado = [], True
        else:
            # Se não há detecção de erro, passa direto
            bits_apos_verificacao = bits_rx_encoded
            erro_detectado = False

        # 5. Desenquadramento (Camada de Enlace RX)
        bits_desenquadrados = bits_apos_verificacao

        try:
            if framing_type == "Contagem de Caracteres":
                bits_desenquadrados = enlace.desenquadramento_contagem_caracteres(bits_apos_verificacao)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_desenquadrados = enlace.desenquadramento_flag_bytes(bits_apos_verificacao)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_desenquadrados = enlace.desenquadramento_flag_bits(bits_apos_verificacao)
        except Exception as e:
            print(f"Erro no desenquadramento: {e}")
            bits_desenquadrados = []
            erro_detectado = True

        # 6. Converte Bits -> Texto
        text_rx = bits_to_text(bits_desenquadrados)
        
        # Verificação adicional: se texto contém caracteres inválidos
        if not erro_detectado:
            try:
                # Verifica se o texto é válido (apenas ASCII imprimível)
                if any(ord(c) > 127 or (ord(c) < 32 and c not in '\n\r\t') for c in text_rx):
                    erro_detectado = True
            except:
                erro_detectado = True

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_com_deteccao,
            "bits_rx": bits_rx_encoded,
            "text_rx": text_rx,
            "erro": erro_detectado
        }

    gui.set_tx_callback(tx_callback)
    gui.show()


# ----------------------------
# Exercício 1.1.2
# ----------------------------
def run_exercicio_112(menu_window):
    def on_close():
        menu_window.show()

    gui = InterfaceGUI(
        title="1.1.2 - Modulação por portadora",
        modulations=["ASK", "FSK", "QPSK", "16-QAM"],
        on_close_callback=on_close
    )

    def tx_callback(params):
        text = params["text"]
        spb = params["samples_per_bit"]
        modulation = params["modulation"]
        V = params["V"]
        snr_db = params["snr_db"]

        # 1. Pega o enquadramento escolhido
        framing_type = params.get("framing", "Nenhum")
        # Pega o método de detecção de erro
        error_detection = params.get("error_detec", "Nenhum")

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        # 2. Texto -> Bits Brutos
        bits_tx = text_to_bits(text)

        # 3. Aplica Enquadramento
        bits_para_transmitir = bits_tx

        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        if not bits_para_transmitir:
            return {}

        # 3.5. Aplica Detecção de Erro (APÓS enquadramento)
        bits_com_deteccao = bits_para_transmitir
        if error_detection == "Paridade Par":
            bits_com_deteccao = enlace.encode_paridade(bits_para_transmitir)
        elif error_detection == "Checksum":
            bits_com_deteccao = enlace.encode_checksum(bits_para_transmitir)
        elif error_detection == "CRC-32":
            bits_com_deteccao = enlace.encode_crc(bits_para_transmitir)

        # 4. Modulação - CORREÇÕES ESPECÍFICAS PARA QPSK E 16-QAM
        if modulation == "ASK":
            t_tx, s_tx = cf.ask(bits_com_deteccao)
        elif modulation == "FSK":
            t_tx, s_tx = cf.fsk(bits_com_deteccao)
        elif modulation == "QPSK":
            # QPSK: Garantir que tenha número par de bits para demodulação correta
            qpsk_bits = bits_com_deteccao.copy()
            if len(qpsk_bits) % 2 != 0:
                qpsk_bits.append(0)  # Adiciona bit zero se necessário
            t_tx, s_tx = cf.qpsk(qpsk_bits)
        elif modulation == "16-QAM":
            # 16-QAM: Garantir múltiplo de 4 bits
            qam_bits = bits_com_deteccao.copy()
            padding_needed = (4 - len(qam_bits) % 4) % 4
            for _ in range(padding_needed):
                qam_bits.append(0)
            t_tx, s_tx = cf.st_qam(qam_bits)

        # Aplica ruído uma única vez
        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
        
        # Decodificação usando sinal com ruído
        if modulation == "ASK":
            bits_rx_encoded = cf.decode_ask(s_rx)
        elif modulation == "FSK":
            bits_rx_encoded = cf.decode_fsk(s_rx)
        elif modulation == "QPSK":
            bits_rx_demod = cf.decode_qpsk(s_rx)
            # Remove o bit extra que foi adicionado apenas para modulação
            bits_rx_encoded = bits_rx_demod[:len(bits_com_deteccao)]
        elif modulation == "16-QAM":
            bits_rx_demod = cf.decode_st_qam(s_rx)
            # Remove apenas o padding que adicionamos
            bits_rx_encoded = bits_rx_demod[:len(bits_com_deteccao)]

        # 5. Verificação de Detecção de Erro - CORREÇÃO PARA EVITAR FALSOS POSITIVOS
        erro_detectado = False
        bits_apos_verificacao = bits_rx_encoded

        # Só aplica verificação se temos bits suficientes
        if error_detection == "Paridade Par":
            if len(bits_rx_encoded) >= 1:
                bits_apos_verificacao, erro_detectado = enlace.decode_paridade(bits_rx_encoded)
            else:
                # Se não tem bits suficientes, considera erro
                bits_apos_verificacao, erro_detectado = [], True

        elif error_detection == "Checksum":
            if len(bits_rx_encoded) >= 3:
                bits_apos_verificacao, erro_detectado = enlace.decode_checksum(bits_rx_encoded)
            else:
                bits_apos_verificacao, erro_detectado = [], True

        elif error_detection == "CRC-32":
            if len(bits_rx_encoded) >= 32:
                bits_apos_verificacao, erro_detectado = enlace.decode_crc(bits_rx_encoded)
            else:
                bits_apos_verificacao, erro_detectado = [], True

        else:
            # Se não há detecção de erro, passa direto
            bits_apos_verificacao = bits_rx_encoded
            erro_detectado = False

        # 6. Desenquadramento
        bits_desenquadrados = bits_apos_verificacao

        try:
            if framing_type == "Contagem de Caracteres":
                bits_desenquadrados = enlace.desenquadramento_contagem_caracteres(bits_apos_verificacao)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_desenquadrados = enlace.desenquadramento_flag_bytes(bits_apos_verificacao)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_desenquadrados = enlace.desenquadramento_flag_bits(bits_apos_verificacao)
        except Exception as e:
            print(f"Erro no desenquadramento (1.1.2): {e}")
            bits_desenquadrados = []
            erro_detectado = True

        # 7. Bits -> Texto Final
        text_rx = bits_to_text(bits_desenquadrados)
        
        # Verificação adicional: se texto contém caracteres inválidos
        if not erro_detectado:
            try:
                # Verifica se o texto é válido (apenas ASCII imprimível)
                if any(ord(c) > 127 or (ord(c) < 32 and c not in '\n\r\t') for c in text_rx):
                    erro_detectado = True
            except:
                erro_detectado = True

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_com_deteccao,
            "bits_rx": bits_rx_encoded,
            "text_rx": text_rx,
            "erro": erro_detectado
        }

    gui.set_tx_callback(tx_callback)
    gui.show()
# ----------------------------
# Exercício 1.5 — Hamming (7,4)
# ----------------------------
def run_exercicio_hamming(menu_window):

    def on_close():
        menu_window.show()

    gui = InterfaceGUI_Hamming(on_close)
    gui.show()



# ----------------------------
# Callback do Menu Principal
# ----------------------------
def on_select_exercicio(ex, menu_window):
    menu_window.hide()

    if ex == "1.1.1":
        run_exercicio_111(menu_window)

    elif ex == "1.1.2":
        run_exercicio_112(menu_window)

    elif ex == "hamming":
        run_exercicio_hamming(menu_window)




def main():
    menu = MainWindow(on_select_exercicio)
    menu.show()


if __name__ == "__main__":
    main()
    Gtk.main()
