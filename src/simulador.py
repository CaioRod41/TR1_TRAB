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

        framing_type = params.get("framing", "Nenhum")
        error_detection = params.get("error_detec", "Paridade Par")
        apply_hamming = params.get("apply_hamming", False)

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        # 1. Texto → bits
        bits_tx = text_to_bits(text)

        # 2. Se Hamming estiver ativado → aplica antes de tudo
        if apply_hamming:
            bits_tx = enlace.hamming_encode(bits_tx)

        # 3. Enquadramento
        bits_para_transmitir = bits_tx
        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        if len(bits_para_transmitir) == 0:
            return {}

        # 4. Detecção de erro (somente se NÃO for Hamming)
        bits_com_deteccao = bits_para_transmitir
        if not apply_hamming:
            if error_detection == "Paridade Par":
                bits_com_deteccao = enlace.encode_paridade(bits_para_transmitir)
            elif error_detection == "Checksum":
                bits_com_deteccao = enlace.encode_checksum(bits_para_transmitir)
            elif error_detection == "CRC-32":
                bits_com_deteccao = enlace.encode_crc(bits_para_transmitir)

        # 5. Modulação
        if modulation == "NRZ-Polar":
            t_tx, s_tx = cf.nrz_polar(bits_com_deteccao)
        elif modulation == "Manchester":
            t_tx, s_tx = cf.manchester(bits_com_deteccao)
        elif modulation == "Bipolar (AMI)":
            t_tx, s_tx = cf.bipolar_ami(bits_com_deteccao)

        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx

        # 6. Demodulação
        if modulation == "NRZ-Polar":
            bits_rx_encoded = cf.decode_nrz_polar(s_rx)
        elif modulation == "Manchester":
            bits_rx_encoded = cf.decode_manchester(s_rx)
        elif modulation == "Bipolar (AMI)":
            bits_rx_encoded = cf.decode_bipolar_ami(s_rx)

        # 7. Se tiver Hamming → decodifica AGORA
        if apply_hamming:
            bits_corrigidos = enlace.hamming_decode(bits_rx_encoded)
            erro_detectado = False
        else:
            # detecção de erro normal
            bits_corrigidos = bits_rx_encoded
            erro_detectado = False

            if error_detection == "Paridade Par":
                bits_corrigidos, erro_detectado = enlace.decode_paridade(bits_rx_encoded)
            elif error_detection == "Checksum":
                bits_corrigidos, erro_detectado = enlace.decode_checksum(bits_rx_encoded)
            elif error_detection == "CRC-32":
                bits_corrigidos, erro_detectado = enlace.decode_crc(bits_rx_encoded)

        # 8. Desenquadramento
        bits_final = bits_corrigidos

        try:
            if framing_type == "Contagem de Caracteres":
                bits_final = enlace.desenquadramento_contagem_caracteres(bits_corrigidos)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_final = enlace.desenquadramento_flag_bytes(bits_corrigidos)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_final = enlace.desenquadramento_flag_bits(bits_corrigidos)
        except:
            erro_detectado = True
            bits_final = []

        # 9. Se tinha Hamming → já está corrigido
        text_rx = bits_to_text(bits_final)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_para_transmitir,
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
        modulation = params["modulation"]
        spb = params["samples_per_bit"]
        V = params["V"]
        snr_db = params["snr_db"]

          # 1. Pega o enquadramento escolhido
        framing_type = params.get("framing", "Nenhum")
        # Pega o método de detecção de erro
        error_detection = params.get("error_detec", "Paridade Par")
        # Aplica o hamming
        apply_hamming = params.get("apply_hamming", False)

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        bits_tx = text_to_bits(text)

        if apply_hamming:
            bits_tx = enlace.hamming_encode(bits_tx)

        bits_para_transmitir = bits_tx
        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        if apply_hamming:
            bits_com_deteccao = bits_para_transmitir
        else:
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
            aux = bits_com_deteccao.copy()
            if len(aux) % 2 != 0:
                aux.append(0)
            t_tx, s_tx = cf.qpsk(aux)
        elif modulation == "16-QAM":
            aux = bits_com_deteccao.copy()
            pad = (4 - len(aux) % 4) % 4
            aux += [0] * pad
            t_tx, s_tx = cf.st_qam(aux)

        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx

        if modulation == "ASK":
            bits_rx_encoded = cf.decode_ask(s_rx)
        elif modulation == "FSK":
            bits_rx_encoded = cf.decode_fsk(s_rx)
        elif modulation == "QPSK":
            tmp = cf.decode_qpsk(s_rx)
            bits_rx_encoded = tmp[:len(bits_com_deteccao)]
        elif modulation == "16-QAM":
            tmp = cf.decode_st_qam(s_rx)
            bits_rx_encoded = tmp[:len(bits_com_deteccao)]

        if apply_hamming:
            bits_corrigidos = enlace.hamming_decode(bits_rx_encoded)
            erro_detectado = False
        else:
            bits_corrigidos = bits_rx_encoded
            erro_detectado = False

            if error_detection == "Paridade Par":
                bits_corrigidos, erro_detectado = enlace.decode_paridade(bits_rx_encoded)
            elif error_detection == "Checksum":
                bits_corrigidos, erro_detectado = enlace.decode_checksum(bits_rx_encoded)
            elif error_detection == "CRC-32":
                bits_corrigidos, erro_detectado = enlace.decode_crc(bits_rx_encoded)

        bits_final = bits_corrigidos
        try:
            if framing_type == "Contagem de Caracteres":
                bits_final = enlace.desenquadramento_contagem_caracteres(bits_corrigidos)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_final = enlace.desenquadramento_flag_bytes(bits_corrigidos)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_final = enlace.desenquadramento_flag_bits(bits_corrigidos)
        except:
            erro_detectado = True
            bits_final = []

        text_rx = bits_to_text(bits_final)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_para_transmitir,
            "bits_rx": bits_rx_encoded,
            "text_rx": text_rx,
            "erro": erro_detectado
        }

    gui.set_tx_callback(tx_callback)
    gui.show()


# ----------------------------
# Exercício 1.5 — Hamming (interface antiga)
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

