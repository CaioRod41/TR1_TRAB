# src/simulador.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "camada_fisica"))
sys.path.insert(0, str(ROOT / "gui"))

from gui.MainWindow import MainWindow
from gui.InterfaceGUI import InterfaceGUI
from camada_fisica.CamadaFisica import CamadaFisica

import numpy as np
from gi.repository import Gtk

# Utilitários de conversão
def text_to_bits(s: str):
    b = s.encode('utf-8')
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> (7-i)) & 1)
    return bits

def bits_to_text(bits):
    pad = (-len(bits)) % 8
    bits = bits + [0]*pad
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i+j]
        out.append(byte)
    try:
        return out.decode('utf-8', errors='replace')
    except:
        return "<decode error>"

# ----------------------------
# Função para o exercício 1.1.1
# ----------------------------
def run_exercicio_111(menu_window):

    def on_sim_close():
        menu_window.show()

    gui = InterfaceGUI(
        title="TR1 - 1.1.1 - Codificação de Linha",
        modulations=["NRZ-Polar", "Manchester", "Bipolar (AMI)"],
        on_close_callback=on_sim_close
    )

    def tx_callback(params):
        text = params["text"]
        modulation = params["modulation"]
        spb = int(params["samples_per_bit"])
        V = float(params["V"])
        snr_db = float(params["snr_db"])

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        bits_tx = text_to_bits(text)
        if len(bits_tx) == 0:
            return {}

        if modulation == "NRZ-Polar":
            t_tx, s_tx = cf.nrz_polar(bits_tx)
            bits_rx = cf.decode_nrz_polar(s_tx)
        elif modulation == "Manchester":
            t_tx, s_tx = cf.manchester(bits_tx)
            bits_rx = cf.decode_manchester(s_tx)
        elif modulation == "Bipolar (AMI)":
            t_tx, s_tx = cf.bipolar_ami(bits_tx)
            bits_rx = cf.decode_bipolar_ami(s_tx)

        if snr_db > 0:
            s_rx = cf.add_awgn(s_tx, snr_db)
        else:
            s_rx = s_tx

        text_rx = bits_to_text(bits_rx)
        return {"t_tx": t_tx, "s_tx": s_tx, "t_rx": t_tx, "s_rx": s_rx,
                "bits_tx": bits_tx, "bits_rx": bits_rx, "text_rx": text_rx}

    gui.set_tx_callback(tx_callback)
    gui.show()

# ----------------------------
# NOVA FUNÇÃO para o exercício 1.1.2
# ----------------------------
def run_exercicio_112(menu_window):

    def on_sim_close():
        menu_window.show()

    gui = InterfaceGUI(
        title="1.1.2 - Codificação (Camada Física)",
        modulations=["ASK", "FSK", "QPSK"],
        on_close_callback=on_sim_close
    )

    def tx_callback(params):
        text = params["text"]
        spb = int(params["samples_per_bit"])
        modulation = params["modulation"]
        V = float(params["V"])
        snr_db = float(params["snr_db"])

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        bits_tx = text_to_bits(text)
        if not bits_tx: return {}

        if modulation == "ASK":
            t_tx, s_tx = cf.ask(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else np.copy(s_tx)
            bits_rx = cf.decode_ask(s_rx)

        elif modulation == "FSK":
            t_tx, s_tx = cf.fsk(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else np.copy(s_tx)
            bits_rx = cf.decode_fsk(s_rx)

        elif modulation == "QPSK":
            t_tx, s_tx = cf.qpsk(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else np.copy(s_tx)
            bits_rx = cf.decode_qpsk(s_rx)

        else:  # Fallback
            t_tx, s_tx, s_rx, bits_rx = None, None, None, None

        text_rx = bits_to_text(bits_rx)
        return {"t_tx": t_tx, "s_tx": s_tx, "t_rx": t_tx, "s_rx": s_rx,
                "bits_tx": bits_tx, "bits_rx": bits_rx, "text_rx": text_rx}

    gui.set_tx_callback(tx_callback)
    gui.show()

# ----------------------------
# Callback do menu principal ATUALIZADO
# ----------------------------

# A função agora aceita a janela do menu como um argumento
def on_select_exercicio(ex, menu_window):
    # Esconde a janela do menu em vez de fechar o loop do programa
    menu_window.hide()

    if ex == "1.1.1":
        run_exercicio_111(menu_window)
    elif ex == "1.1.2":
        run_exercicio_112(menu_window)
    elif ex == "2.1.1":
        print("Exercício 2.1.1 em desenvolvimento...")
        Gtk.main_quit()

def main():
    menu = MainWindow(on_select_exercicio)
    menu.show()

if __name__ == "__main__":
    main()