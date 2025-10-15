# src/gui/InterfaceGUI.py
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

import matplotlib
matplotlib.use("GTK3Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

import numpy as np

class InterfaceGUI(Gtk.Window):
    """
    Janela GTK que fornece:
      - entrada de texto
      - seleção de modulação (NRZ Polar, Manchester, Bipolar)
      - parâmetros: samples_per_bit, V, SNR
      - botão Transmitir
      - área de plot com dois painéis: transmitido e recebido
      - label com texto recebido após decodificação
    """

    def __init__(self):
        super().__init__(title="TR1 - Simulador Camada Física (1.1.1)")
        self.set_default_size(900, 600)
        self.set_border_width(8)

        # layout principal
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # controles
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        vbox.pack_start(grid, False, False, 0)

        # Texto de entrada
        lbl_in = Gtk.Label(label="Texto para transmitir:")
        grid.attach(lbl_in, 0, 0, 1, 1)
        self.entry_text = Gtk.Entry()
        self.entry_text.set_text("Caio teste msg 123")
        grid.attach(self.entry_text, 1, 0, 3, 1)

        # Modulação
        lbl_mod = Gtk.Label(label="Modulação:")
        grid.attach(lbl_mod, 0, 1, 1, 1)
        self.combo_mod = Gtk.ComboBoxText()
        self.combo_mod.append_text("NRZ-Polar")
        self.combo_mod.append_text("Manchester")
        self.combo_mod.append_text("Bipolar (AMI)")
        self.combo_mod.set_active(0)
        grid.attach(self.combo_mod, 1, 1, 1, 1)

        # Samples per bit
        lbl_spb = Gtk.Label(label="Samples/bit:")
        grid.attach(lbl_spb, 2, 1, 1, 1)
        self.spin_spb = Gtk.SpinButton()
        self.spin_spb.set_range(4, 1000)
        self.spin_spb.set_increments(1, 10)
        self.spin_spb.set_value(50)
        grid.attach(self.spin_spb, 3, 1, 1, 1)

        # Amplitude V
        lbl_V = Gtk.Label(label="Amplitude V:")
        grid.attach(lbl_V, 0, 2, 1, 1)
        self.spin_V = Gtk.SpinButton()
        self.spin_V.set_range(0.1, 5.0)
        self.spin_V.set_increments(0.1, 0.5)
        self.spin_V.set_value(1.0)
        grid.attach(self.spin_V, 1, 2, 1, 1)

        # SNR
        lbl_snr = Gtk.Label(label="SNR (dB, 0 => sem ruído):")
        grid.attach(lbl_snr, 2, 2, 1, 1)
        self.spin_snr = Gtk.SpinButton()
        self.spin_snr.set_range(0, 60)
        self.spin_snr.set_increments(1,5)
        self.spin_snr.set_value(0)
        grid.attach(self.spin_snr, 3, 2, 1, 1)

        # Botão transmitir
        self.btn_tx = Gtk.Button(label="Transmitir")
        grid.attach(self.btn_tx, 0, 3, 1, 1)

                # Label recebido
        self.lbl_received = Gtk.Label(label="Recebido: ")
        grid.attach(self.lbl_received, 1, 3, 3, 1)

        # Adiciona o grid inteiro primeiro
        vbox.pack_start(grid, False, False, 0)

        # Labels de bits (AGORA abaixo do grid)
        self.lbl_bits_tx = Gtk.Label(label="Bits TX: -")
        self.lbl_bits_tx.set_xalign(0)
        vbox.pack_start(self.lbl_bits_tx, False, False, 0)

        self.lbl_bits_rx = Gtk.Label(label="Bits RX: -")
        self.lbl_bits_rx.set_xalign(0)
        vbox.pack_start(self.lbl_bits_rx, False, False, 0)

        # Agora os gráficos
        self.fig = Figure(figsize=(8,4))
        self.ax_tx = self.fig.add_subplot(211)
        self.ax_rx = self.fig.add_subplot(212, sharex=self.ax_tx)
        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvas(self.fig)
        vbox.pack_start(self.canvas, True, True, 0)


        # Ligar sinal do botão a uma função externa (callback set via set_tx_callback)
        self._tx_callback = None
        self.btn_tx.connect("clicked", self.on_transmit_clicked)

    # -------------------------
    # API para o simulador conectar callbacks
    # -------------------------
    def set_tx_callback(self, fn):
        """fn should accept a dict of parameters and return a dict with results"""
        self._tx_callback = fn

    # -------------------------
    # Eventos
    # -------------------------
    def on_transmit_clicked(self, button):
        if not self._tx_callback:
            print("Nenhum callback de transmissão registrado.")
            return
        params = {
            "text": self.entry_text.get_text(),
            "modulation": self.combo_mod.get_active_text(),
            "samples_per_bit": int(self.spin_spb.get_value()),
            "V": float(self.spin_V.get_value()),
            "snr_db": float(self.spin_snr.get_value())
        }
        # chama o simulador (bloqueante curto)
        result = self._tx_callback(params)
        # atualiza gráficos e label
        t_tx = result.get("t_tx")
        s_tx = result.get("s_tx")
        t_rx = result.get("t_rx")
        s_rx = result.get("s_rx")
        bits_tx = result.get("bits_tx")
        bits_rx = result.get("bits_rx")
        text_rx = result.get("text_rx")

        # limpar e plotar
        self.ax_tx.cla()
        self.ax_rx.cla()
        if t_tx is not None and s_tx is not None:
            self.ax_tx.plot(t_tx, s_tx, linewidth=0.8)
            self.ax_tx.set_ylabel("Tx")
            self.ax_tx.grid(True)
        if t_rx is not None and s_rx is not None:
            self.ax_rx.plot(t_rx, s_rx, linewidth=0.8)
            self.ax_rx.set_ylabel("Rx")
            self.ax_rx.set_xlabel("Tempo (s)")
            self.ax_rx.grid(True)

        if bits_tx is not None:
            nb = len(bits_tx)
            s = int(params["samples_per_bit"])
            for i in range(nb):
                x = i * s / (params["samples_per_bit"] / 1.0)  # tempo index when Tb=1

        self.canvas.draw_idle()

        # atualizar texto recebido
        self.lbl_received.set_text("Recebido: " + (text_rx if text_rx is not None else "<vazio>"))
        # Mostrar bits TX e RX na tela
        if bits_tx is not None:
            bits_tx_str = ''.join(str(b) for b in bits_tx[:64])  # mostra até 64 bits
            if len(bits_tx) > 64:
                bits_tx_str += "..."
            self.lbl_bits_tx.set_text("Bits TX: " + bits_tx_str)
        else:
            self.lbl_bits_tx.set_text("Bits TX: -")

        if bits_rx is not None:
            bits_rx_str = ''.join(str(b) for b in bits_rx[:64])
            if len(bits_rx) > 64:
                bits_rx_str += "..."
            self.lbl_bits_rx.set_text("Bits RX: " + bits_rx_str)
        else:
            self.lbl_bits_rx.set_text("Bits RX: -")


    def show(self):
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        Gtk.main()
