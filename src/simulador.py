# src/simulador.py
import sys
from pathlib import Path

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
        title="TR1 - 1.1.1 - Codificação de Linha",
        modulations=["NRZ-Polar", "Manchester", "Bipolar (AMI)"],
        on_close_callback=on_close
    )

    def tx_callback(params):
        text = params["text"]
        modulation = params["modulation"]
        spb = params["samples_per_bit"]
        V = params["V"]
        snr_db = params["snr_db"]

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

        s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
        text_rx = bits_to_text(bits_rx)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_tx, "bits_rx": bits_rx,
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
        title="TR1 - 1.1.2 - Modulação Digital",
        modulations=["ASK", "FSK", "QPSK", "16-QAM"],
        on_close_callback=on_close
    )

    def tx_callback(params):
        text = params["text"]
        spb = params["samples_per_bit"]
        modulation = params["modulation"]
        V = params["V"]
        snr_db = params["snr_db"]

        cf = CamadaFisica(samples_per_bit=spb, V=V)
        bits_tx = text_to_bits(text)

        if modulation == "ASK":
            t_tx, s_tx = cf.ask(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx = cf.decode_ask(s_rx)

        elif modulation == "FSK":
            t_tx, s_tx = cf.fsk(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx = cf.decode_fsk(s_rx)

        elif modulation == "QPSK":
            t_tx, s_tx = cf.qpsk(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx = cf.decode_qpsk(s_rx)

        elif modulation == "16-QAM":
            t_tx, s_tx = cf.st_qam(bits_tx)
            s_rx = cf.add_awgn(s_tx, snr_db) if snr_db > 0 else s_tx
            bits_rx = cf.decode_st_qam(s_rx)

        text_rx = bits_to_text(bits_rx)

        return {
            "t_tx": t_tx, "s_tx": s_tx,
            "t_rx": t_tx, "s_rx": s_rx,
            "bits_tx": bits_tx, "bits_rx": bits_rx,
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

