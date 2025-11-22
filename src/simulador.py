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

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        # 1. Converte Texto -> Bits puros
        bits_tx = text_to_bits(text)

        # 2. Aplica Enquadramento
        # Se for "Nenhum", bits_para_transmitir é igual ao original
        bits_para_transmitir = bits_tx

        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        if len(bits_para_transmitir) == 0:
            return {}

        # 3. Modulação (Camada Física)
        # ATENÇÃO: Aqui usamos 'bits_para_transmitir' (Enquadrados), NÃO 'bits_tx'
        if modulation == "NRZ-Polar":
            t_tx, s_tx = cf.nrz_polar(bits_para_transmitir)
            bits_rx_encoded = cf.decode_nrz_polar(s_tx)

        elif modulation == "Manchester":
            t_tx, s_tx = cf.manchester(bits_para_transmitir)
            bits_rx_encoded = cf.decode_manchester(s_tx)

        elif modulation == "Bipolar (AMI)":
            t_tx, s_tx = cf.bipolar_ami(bits_para_transmitir)
            bits_rx_encoded = cf.decode_bipolar_ami(s_tx)

        # Adiciona Ruído
        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx

        # --- Receptor ---

        # 4. Desenquadramento (Camada de Enlace RX)
        # Começamos assumindo que o que chegou é o que vale
        bits_desenquadrados = bits_rx_encoded

        try:
            if framing_type == "Contagem de Caracteres":
                bits_desenquadrados = enlace.desenquadramento_contagem_caracteres(bits_rx_encoded)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_desenquadrados = enlace.desenquadramento_flag_bytes(bits_rx_encoded)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_desenquadrados = enlace.desenquadramento_flag_bits(bits_rx_encoded)
        except Exception as e:
            print(f"Erro no desenquadramento: {e}")
            bits_desenquadrados = []  # Falha silenciosa para não travar GUI

        # 5. Converte Bits -> Texto
        text_rx = bits_to_text(bits_desenquadrados)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            # Na GUI, queremos ver os bits JÁ ENQUADRADOS no campo "Bits TX"
            "bits_tx": bits_para_transmitir,
            # E os bits brutos que chegaram antes de desenquadrar (ou depois, depende do que vc quer ver)
            # Geralmente mostra-se o que chegou na física:
            "bits_rx": bits_rx_encoded,
            "text_rx": text_rx
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

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        enlace = CamadaEnlace()

        # 2. Texto -> Bits Brutos
        bits_tx = text_to_bits(text)

        # 3. Aplica Enquadramento (bits_tx -> bits_para_transmitir)
        bits_para_transmitir = bits_tx  # Default

        if framing_type == "Contagem de Caracteres":
            bits_para_transmitir = enlace.enquadramento_contagem_caracteres(bits_tx)
        elif framing_type == "FLAGS: Inserção de bytes":
            bits_para_transmitir = enlace.enquadramento_flag_bytes(bits_tx)
        elif framing_type == "FLAGS: Inserção de bits":
            bits_para_transmitir = enlace.enquadramento_flag_bits(bits_tx)

        # Se não houver bits para transmitir (msg vazia), retorna vazio
        if not bits_para_transmitir:
            return {}

        # 4. Modulação (Usa os bits ENQUADRADOS)
        # 'bits_rx_encoded' são os bits demodulados, ainda contendo o quadro (headers/stuffing)

        if modulation == "ASK":
            t_tx, s_tx = cf.ask(bits_para_transmitir)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx_encoded = cf.decode_ask(s_rx)

        elif modulation == "FSK":
            t_tx, s_tx = cf.fsk(bits_para_transmitir)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx_encoded = cf.decode_fsk(s_rx)

        elif modulation == "QPSK":
            t_tx, s_tx = cf.qpsk(bits_para_transmitir)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx_encoded = cf.decode_qpsk(s_rx)

        elif modulation == "16-QAM":
            t_tx, s_tx = cf.st_qam(bits_para_transmitir)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx_encoded = cf.decode_st_qam(s_rx)

        # 5. Desenquadramento (bits_rx_encoded -> bits_desenquadrados)
        bits_desenquadrados = bits_rx_encoded  # Default

        try:
            if framing_type == "Contagem de Caracteres":
                bits_desenquadrados = enlace.desenquadramento_contagem_caracteres(bits_rx_encoded)
            elif framing_type == "FLAGS: Inserção de bytes":
                bits_desenquadrados = enlace.desenquadramento_flag_bytes(bits_rx_encoded)
            elif framing_type == "FLAGS: Inserção de bits":
                bits_desenquadrados = enlace.desenquadramento_flag_bits(bits_rx_encoded)
        except Exception as e:
            print(f"Erro no desenquadramento (1.1.2): {e}")
            bits_desenquadrados = []

        # 6. Bits -> Texto Final
        text_rx = bits_to_text(bits_desenquadrados)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_para_transmitir,
            "bits_rx": bits_rx_encoded,
            "text_rx": text_rx
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

