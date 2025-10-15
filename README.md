# 📡 Simulador TR1 — Camada Física e Enlace (GNU Radio + Python + GTK)

Projeto desenvolvido para a disciplina **TR1 (Teoria de Redes 1)**.
O objetivo é **simular o funcionamento das Camadas Física e Enlace** de um sistema de comunicação digital — codificando, transmitindo e decodificando sinais binários.

---

## ⚙️ Requisitos e Instalação

### 🧩 Sistema operacional
Ubuntu 22.04+ (ou qualquer distro compatível com GTK3)

---

### 🧱 1. Instalar dependências do sistema

Abra o terminal e execute:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-gi \
gir1.2-gtk-3.0 python3-gi-cairo libgirepository1.0-dev libcairo2-dev \
pkg-config python3-numpy python3-matplotlib git
pip install numpy matplotlib
