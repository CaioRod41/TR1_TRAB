# ============================================================
# src/gui/InterfaceGUI.py
# ============================================================

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import matplotlib
matplotlib.use("GTK3Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
import numpy as np
from camada_enlace.CamadaEnlace import CamadaEnlace


# ============================================================
#   INTERFACE DA CAMADA FÍSICA (1.1.1 e 1.1.2)
# ============================================================

class InterfaceGUI(Gtk.Window):

    def __init__(self, title, modulations, on_close_callback):
        super().__init__(title=title)
        self.on_close_callback = on_close_callback
        self.connect("destroy", self.on_window_destroy)

        self.set_default_size(900, 600)
        self.set_border_width(8)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # --------------------------------------------------------
        # CONTROLES SUPERIORES (GRID)
        # --------------------------------------------------------
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        vbox.pack_start(grid, False, False, 0)

        # --- LINHA 0: Texto ---
        lbl_in = Gtk.Label(label="Texto para transmitir:")
        grid.attach(lbl_in, 0, 0, 1, 1)

        self.entry_text = Gtk.Entry()
        self.entry_text.set_text("Mensagem teste")
        grid.attach(self.entry_text, 1, 0, 3, 1)

        # --- LINHA 1: Modulação e Samples ---
        # Coluna 0, 1: Modulação
        lbl_mod = Gtk.Label(label="Modulação:")
        grid.attach(lbl_mod, 0, 1, 1, 1)

        self.combo_mod = Gtk.ComboBoxText()
        for mod in modulations:
            self.combo_mod.append_text(mod)
        self.combo_mod.set_active(0)

        if len(modulations) == 1:
            self.combo_mod.set_sensitive(False)

        grid.attach(self.combo_mod, 1, 1, 1, 1)

        # Coluna 2, 3: Samples/bit
        lbl_spb = Gtk.Label(label="Samples/bit:")
        grid.attach(lbl_spb, 2, 1, 1, 1)

        self.spin_spb = Gtk.SpinButton.new_with_range(4, 1000, 1)
        self.spin_spb.set_value(50)
        grid.attach(self.spin_spb, 3, 1, 1, 1)

        # --- LINHA 2: Amplitude e SNR ---
        lbl_V = Gtk.Label(label="Amplitude V:")
        grid.attach(lbl_V, 0, 2, 1, 1)

        self.spin_V = Gtk.SpinButton.new_with_range(0.1, 5.0, 0.1)
        self.spin_V.set_value(1.0)
        grid.attach(self.spin_V, 1, 2, 1, 1)

        lbl_snr = Gtk.Label(label="SNR (dB):")
        grid.attach(lbl_snr, 2, 2, 1, 1)

        self.spin_snr = Gtk.SpinButton.new_with_range(-60.0, 60.0, 0.001)
        self.spin_snr.set_digits(3)  
        self.spin_snr.set_value(0.0)
        grid.attach(self.spin_snr, 3, 2, 1, 1)


        # --- LINHA 3: Enquadramento (NOVO) ---
        lbl_enq = Gtk.Label(label="Enquadramento:")
        grid.attach(lbl_enq, 0, 3, 1, 1)

        self.combo_enq = Gtk.ComboBoxText()
        self.combo_enq.append_text("Nenhum")
        self.combo_enq.append_text("Contagem de Caracteres")
        self.combo_enq.append_text("FLAGS: Inserção de bytes")
        self.combo_enq.append_text("FLAGS: Inserção de bits")
        self.combo_enq.set_active(0)
        grid.attach(self.combo_enq, 1, 3, 3, 1)

        # Detecção de Erro
        lbl_det = Gtk.Label(label="Detecção de Erro:")
        grid.attach(lbl_det, 0, 4, 1, 1)

        self.combo_det = Gtk.ComboBoxText()
        self.combo_det.append_text("Paridade Par")
        self.combo_det.append_text("Checksum")
        self.combo_det.append_text("CRC-32")
        self.combo_det.set_active(0)
        grid.attach(self.combo_det, 1, 4, 3, 1)

        # --- LINHA 4.5: CHECKBOX HAMMING (NOVO) ---
        self.check_hamming = Gtk.CheckButton(label="Correção de Erros (Hamming 7,4)")
        grid.attach(self.check_hamming, 0, 5, 4, 1)

        # Botão transmitir
        self.btn_tx = Gtk.Button(label="Transmitir")
        self.btn_tx.connect("clicked", self.on_transmit_clicked)
        grid.attach(self.btn_tx, 0, 6, 1, 1)

        # Label recebido
        self.lbl_received = Gtk.Label(label="Recebido: -")
        grid.attach(self.lbl_received, 1, 6, 3, 1)

        # --------------------------------------------------------
        # LABELS DE BITS E GRÁFICOS
        # --------------------------------------------------------
        self.lbl_bits_tx = Gtk.Label(label="Bits TX: -")
        self.lbl_bits_tx.set_xalign(0)
        vbox.pack_start(self.lbl_bits_tx, False, False, 0)

        self.lbl_bits_rx = Gtk.Label(label="Bits RX: -")
        self.lbl_bits_rx.set_xalign(0)
        vbox.pack_start(self.lbl_bits_rx, False, False, 0)

        self.lbl_err_result = Gtk.Label(label="Resultado da detecção: -")
        self.lbl_err_result.set_xalign(0)
        vbox.pack_start(self.lbl_err_result, False, False, 0)

        # --------------------------------------------------------
        # GRÁFICOS
        # --------------------------------------------------------
        self.fig = Figure(figsize=(8, 4))
        self.ax_tx = self.fig.add_subplot(211)
        self.ax_rx = self.fig.add_subplot(212, sharex=self.ax_tx)
        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvas(self.fig)
        vbox.pack_start(self.canvas, True, True, 0)

        self._tx_callback = None

    # --------------------------------------------------------
    def set_tx_callback(self, fn):
        self._tx_callback = fn

    # --------------------------------------------------------
    def on_transmit_clicked(self, button):
        if not self._tx_callback:
            print("Callback não registrado.")
            return

        params = {
        "text": self.entry_text.get_text(),
        "modulation": self.combo_mod.get_active_text(),
        "framing": self.combo_enq.get_active_text(),
        "samples_per_bit": int(self.spin_spb.get_value()),
        "V": float(self.spin_V.get_value()),
        "snr_db": float(self.spin_snr.get_value()),
        "error_detec": self.combo_det.get_active_text(),
        "apply_hamming": self.check_hamming.get_active()
    }


        result = self._tx_callback(params)
        if not result:
            return

        t_tx = result.get("t_tx")
        s_tx = result.get("s_tx")
        t_rx = result.get("t_rx")
        s_rx = result.get("s_rx")
        bits_tx = result.get("bits_tx")
        bits_rx = result.get("bits_rx")
        text_rx = result.get("text_rx")
        erro = result.get("erro")

        self.ax_tx.cla()
        self.ax_rx.cla()

        if t_tx is not None and s_tx is not None:
            self.ax_tx.plot(t_tx, s_tx)
            self.ax_tx.grid(True)

        if t_rx is not None and s_rx is not None:
            self.ax_rx.plot(t_rx, s_rx)
            self.ax_rx.grid(True)

        self.canvas.draw_idle()

        if bits_tx:
            self.lbl_bits_tx.set_text(f"Bits TX: {''.join(map(str,bits_tx[:64]))}...")
        if bits_rx:
            self.lbl_bits_rx.set_text(f"Bits RX: {''.join(map(str,bits_rx[:64]))}...")

        self.lbl_received.set_text("Recebido: " + text_rx)

        erro = bool(erro)
        if erro is True:
            self.lbl_err_result.set_text("Resultado da detecção: ERRO detectado")
        elif erro is False:
            self.lbl_err_result.set_text("Resultado da detecção: Sem erro")
        else:
            self.lbl_err_result.set_text("Resultado da detecção: -")

    # --------------------------------------------------------
    def on_window_destroy(self, widget):
        if self.on_close_callback:
            self.on_close_callback()

    def show(self):
        self.show_all()



# ============================================================
#   INTERFACE DO EXERCÍCIO 1.5 — HAMMING (7,4)
# ============================================================

class InterfaceGUI_Hamming(Gtk.Window):

    def __init__(self, on_close_callback):
        super().__init__(title="Camada de Enlace — Hamming (7,4)")
        self.on_close_callback = on_close_callback
        self.connect("destroy", self.on_destroy)

        self.set_default_size(600, 350)
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        label = Gtk.Label(label="Mensagem para codificar:")
        label.set_xalign(0)
        vbox.pack_start(label, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_text("NUM TA PRONTO AINDA NAO")
        vbox.pack_start(self.entry, False, False, 0)

        btn = Gtk.Button(label="Executar Hamming (7,4)")
        btn.connect("clicked", self.execute)
        vbox.pack_start(btn, False, False, 0)

        self.out1 = Gtk.Label(label="Bits originais: -")
        self.out2 = Gtk.Label(label="Codificado: -")
        self.out3 = Gtk.Label(label="Com erro: -")
        self.out4 = Gtk.Label(label="Decodificado: -")
        self.out5 = Gtk.Label(label="Texto final: -")

        for o in [self.out1, self.out2, self.out3, self.out4, self.out5]:
            o.set_xalign(0)
            vbox.pack_start(o, False, False, 0)

        
        self.enlace = CamadaEnlace()

    # --------------------------------------------------------
    def execute(self, widget):
        text = self.entry.get_text()

        # texto → bits
        bits = []
        for c in text.encode():
            for i in range(8):
                bits.append((c >> (7-i)) & 1)

        self.out1.set_text("Bits originais: " + ''.join(map(str,bits[:64])) + "...")

        enc = self.enlace.hamming_encode(bits)
        self.out2.set_text("Codificado: " + ''.join(map(str,enc[:64])) + "...")

        err = enc.copy()
        err[5] ^= 1
        self.out3.set_text("Com erro: " + ''.join(map(str,err[:64])) + "...")

        dec = self.enlace.hamming_decode(err)
        self.out4.set_text("Decodificado: " + ''.join(map(str,dec[:64])) + "...")

        # bits → texto
        text_out = ""
        for i in range(0,len(dec),8):
            byte = dec[i:i+8]
            if len(byte)==8:
                val=0
                for b in byte:
                    val = (val<<1)|b
                text_out += chr(val)

        self.out5.set_text("Texto final: " + text_out)

    # --------------------------------------------------------
    def on_destroy(self, widget):
        if self.on_close_callback:
            self.on_close_callback()

    def show(self):
        self.show_all()
