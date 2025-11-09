# src/camada_fisica/CamadaFisica.py
import numpy as np
from math import sqrt

class CamadaFisica:

    #--------------------------------------INICIO DA 1.1.1-------------------------------------------------
    """
    Implementa codificações banda-base digitais:
      - NRZ-Polar
      - Manchester
      - Bipolar (AMI)

    Cada método de codificação retorna (t, waveform) onde:
      - t: vetor de tempos (numpy array)
      - waveform: amostras (numpy array, float)
    Decodificadores retornam lista de bits (0/1).
    """

    def __init__(self, samples_per_bit=50, V=1.0, fs=None):
        """
        samples_per_bit: número de amostras por bit (inteiro)
        V: amplitude de pico
        fs: taxa de amostragem (opcional). Se None, fs = samples_per_bit / Tb (Tb=1s por bit nominal)
        """
        self.samples_per_bit = int(samples_per_bit)
        self.V = float(V)
        # se precisar usar tempo absoluto, assumimos Tb = 1.0 por símbolo para simplicidade
        self.Tb = 1.0
        self.fs = fs if fs is not None else self.samples_per_bit / self.Tb
        self.fc = 10.0 / self.Tb

        self.f1_fsk = 2.0 / self.Tb  # Frequência para bit '1' (ex: 2 Hz)
        self.f2_fsk = 1.0 / self.Tb  # Frequência para bit '0' (ex: 1 Hz)
        
        # -1 significa que o próximo '1' deve ser +1 (alterna de -1 para 1).
        self.last_polarity = -1 
        
    # -------------------------
    # Utilitários
    # -------------------------
    @staticmethod
    def bits_from_bytes(b: bytes):
        bits = []
        for byte in b:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    @staticmethod
    def bytes_from_bits(bits):
        # agrupa 8 bits MSB first
        pad = (-len(bits)) % 8
        bits = bits + [0] * pad
        out = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            out.append(byte)
        return bytes(out)

    # -------------------------
    # Codificadores (Ex 1.1.1)
    # -------------------------
    def nrz_polar(self, bits):
        """NRZ-Polar: 1 -> +V ; 0 -> -V"""
        s_per_bit = self.samples_per_bit
        waveform = np.zeros(len(bits) * s_per_bit, dtype=float)
        for i, b in enumerate(bits):
            level = self.V if b == 1 else -self.V
            waveform[i * s_per_bit : (i + 1) * s_per_bit] = level
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def manchester(self, bits):
        """Manchester:
           1 -> +V then -V
           0 -> -V then +V
        """
        s_per_bit = self.samples_per_bit
        half = s_per_bit // 2
        # If samples_per_bit is odd, make second half one sample longer
        waveform = []
        for b in bits:
            if b == 1:
                waveform.extend([self.V] * half)
                waveform.extend([-self.V] * (s_per_bit - half))
            else:
                waveform.extend([-self.V] * half)
                waveform.extend([self.V] * (s_per_bit - half))
        waveform = np.array(waveform, dtype=float)
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def bipolar_ami(self, bits):
        """
        Bipolar AMI:
           0 -> 0
           1 -> alterna +V / -V (primeiro 1 -> +V, próximo 1 -> -V, etc)
        """
        s_per_bit = self.samples_per_bit
        waveform = np.zeros(len(bits) * s_per_bit, dtype=float)
        
        last_polarity = -1
                          
        # OPÇÃO A (Se o chamador (simulador) cria nova CamadaFisica a cada Tx):
        last_polarity = -1 # Assim o primeiro '1' é sempre +V.

        for i, b in enumerate(bits):
            if b == 0:
                level = 0.0
            else:
                # alternate polarity
                last_polarity *= -1 # -1 -> 1 (primeiro 1) ; 1 -> -1 (segundo 1)
                level = self.V * last_polarity
            waveform[i * s_per_bit : (i + 1) * s_per_bit] = level
            
        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    # -------------------------
    # Decodificadores (simples, por amostragem)
    # -------------------------
    def decode_nrz_polar(self, waveform):
        """Decodifica NRZ-Polar por média em cada intervalo de bit (threshold 0)."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            m = np.mean(chunk)
            bits.append(1 if m > 0.0 else 0)
        return bits

    def decode_manchester(self, waveform):
        """Decodifica Manchester examinando as duas metades do bit."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        half = s//2
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            first_mean = np.mean(chunk[:half])
            second_mean = np.mean(chunk[half:])
 
            bits.append(1 if first_mean > second_mean else 0)
        return bits

    def decode_bipolar_ami(self, waveform):
        """Decodifica AMI: decide 0 se média próxima de 0, senão 1."""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []
        for i in range(nb):
            chunk = waveform[i*s:(i+1)*s]
            m = np.mean(chunk)
            # threshold: se |m| < V/2 -> zero
            if abs(m) < (self.V * 0.4):
                bits.append(0)
            else:
                bits.append(1)
        return bits

    # -------------------------
    # Função utilitária: adicionar ruído AWGN
    # -------------------------
    def add_awgn(self, waveform, snr_db):
        """
        Adiciona ruído AWGN ao waveform para um SNR (dB) fornecido.
        SNR definido como 10*log10(signal_power / noise_power).
        """
        sig_pow = np.mean(waveform**2)
        snr_linear = 10**(snr_db/10.0)
        noise_pow = sig_pow / snr_linear if snr_linear != 0 else sig_pow * 0.001
        noise = np.sqrt(noise_pow) * np.random.randn(len(waveform))
        return waveform + noise
    

    #--------------------------------------FIM DA 1.1.1-------------------------------------------------

    # -------------------------
    # Modulador (Ex 1.1.2) ASK
    # -------------------------
    def ask(self, bits):
        s_per_bit = self.samples_per_bit
        t_bit = np.arange(s_per_bit) / self.fs
        carrier = self.V * np.sin(2 * np.pi * self.fc * t_bit)

        waveform = np.array([], dtype=float)
        zero_signal = np.zeros(s_per_bit)

        for b in bits:
            if b == 1:
                waveform = np.append(waveform, carrier)
            else:
                waveform = np.append(waveform, zero_signal)

        t = np.arange(len(waveform)) / self.fs
        return t, waveform
    def decode_ask(self, waveform):
        s = self.samples_per_bit
        nb = len(waveform) // s
        threshold = (self.V ** 2) / 4.0  # Limiar baseado em 1/4 da potência
        bits = []
        for i in range(nb):
            chunk = waveform[i * s:(i + 1) * s]
            power = np.mean(chunk ** 2)
            bits.append(1 if power > threshold else 0)
        return bits

    # -------------------------
    # Modulador (Ex 1.1.2) FSK
    # -------------------------
    def fsk(self, bits):
        """Modulação FSK, baseada na imagem (reinicia a fase a cada bit)"""
        s_per_bit = self.samples_per_bit
        t_bit = np.arange(s_per_bit) / self.fs

        # Pré-calcula a portadora para bit '1' (freq f1)
        carrier_1 = self.V * np.sin(2 * np.pi * self.f1_fsk * t_bit)

        # Pré-calcula a portadora para bit '0' (freq f2)
        carrier_0 = self.V * np.sin(2 * np.pi * self.f2_fsk * t_bit)

        waveform = np.array([], dtype=float)

        # Constrói a forma de onda bit a bit
        for b in bits:
            if b == 1:
                waveform = np.append(waveform, carrier_1)
            else:
                waveform = np.append(waveform, carrier_0)

        t = np.arange(len(waveform)) / self.fs
        return t, waveform

    def decode_fsk(self, waveform):
        """Decodificador FSK não-coerente (baseado em energia)"""
        s = self.samples_per_bit
        nb = len(waveform) // s
        bits = []

        # Cria vetores de tempo e referências (seno/cosseno) uma vez
        t_bit = np.arange(s) / self.fs
        ref_sin_f1 = np.sin(2 * np.pi * self.f1_fsk * t_bit)
        ref_cos_f1 = np.cos(2 * np.pi * self.f1_fsk * t_bit)
        ref_sin_f2 = np.sin(2 * np.pi * self.f2_fsk * t_bit)
        ref_cos_f2 = np.cos(2 * np.pi * self.f2_fsk * t_bit)

        for i in range(nb):
            chunk = waveform[i * s:(i + 1) * s]

            # Calcula a energia na frequência f1
            corr_sin_f1 = np.sum(chunk * ref_sin_f1)
            corr_cos_f1 = np.sum(chunk * ref_cos_f1)
            energy_f1 = corr_sin_f1 ** 2 + corr_cos_f1 ** 2

            # Calcula a energia na frequência f2
            corr_sin_f2 = np.sum(chunk * ref_sin_f2)
            corr_cos_f2 = np.sum(chunk * ref_cos_f2)
            energy_f2 = corr_sin_f2 ** 2 + corr_cos_f2 ** 2

            # Decide o bit com base na maior energia
            bits.append(1 if energy_f1 > energy_f2 else 0)

        return bits

    def bits_to_symbols(self, bits):
        if len(bits)%2 != 0:
            bits.append(0)

        simbolos = []
        for i in range(0, len(bits), 2):
            simbolo = (bits[i], bits[i+1])
            simbolos.append(simbolo)

        return simbolos

    def qpsk(self, bits):
        simbolos = self.bits_to_symbols(bits)
        samples_per_symbol = 2 * self.samples_per_bit

        waveform = np.zeros(len(simbolos) * samples_per_symbol, dtype=float)

        mapping = {
            (0, 0): (self.V, self.V),
            (0, 1): (-self.V, self.V),
            (1, 1): (-self.V, -self.V),
            (1, 0): (self.V, -self.V)
        }

        for i, simbolo in enumerate(simbolos):
            inicio = i * samples_per_symbol
            fim = inicio + samples_per_symbol

            t_sim = np.arange(inicio, fim) / self.fs

            portadora_I = np.sqrt(2 / self.Tb) * np.cos(2 * np.pi * self.fc * t_sim)
            portadora_Q = np.sqrt(2 / self.Tb) * np.sin(2 * np.pi * self.fc * t_sim)

            I, Q = mapping[simbolo]
            waveform[inicio:fim] = (I * portadora_I) + (Q * portadora_Q)

        t = np.arange(len(waveform)) / self.fs

        return t, waveform
