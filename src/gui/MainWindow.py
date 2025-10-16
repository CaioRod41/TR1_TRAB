# src/gui/MainWindow.py
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class MainWindow(Gtk.Window):
    """
    Janela principal do simulador TR1.
    Permite escolher o exercício (1.1.1, 1.1.2, 2.1.1, etc.)
    """
    def __init__(self, on_select_callback):
        super().__init__(title="Simulador TR1 - Menu Principal")
        self.set_default_size(400, 300)
        self.set_border_width(15)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        lbl = Gtk.Label(label="Escolha o exercício para simular:")
        vbox.pack_start(lbl, False, False, 0)

        # Botões de navegação
        self.btn_111 = Gtk.Button(label="1.1.1 - Codificação (Camada Física)")
        self.btn_111.connect("clicked", lambda b: on_select_callback("1.1.1", self))
        vbox.pack_start(self.btn_111, False, False, 0)

        self.btn_112 = Gtk.Button(label="1.1.2 - Modulação por Portadora (ASK)")
        self.btn_112.connect("clicked", lambda b: on_select_callback("1.1.2", self))
        vbox.pack_start(self.btn_112, False, False, 0)

        self.btn_211 = Gtk.Button(label="2.1.1 - Em desenvolvimento")
        self.btn_211.connect("clicked", lambda b: on_select_callback("2.1.1", self))
        vbox.pack_start(self.btn_211, False, False, 0)

        self.connect("destroy", Gtk.main_quit)

    def show(self):
        self.show_all()
        Gtk.main()